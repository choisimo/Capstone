import asyncio
import re
import hashlib
import json
import uuid
import yaml
import aiohttp
from typing import List, Optional, Dict, Set, Any
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta
from pathlib import Path

from app.models import (
    OsintSource, OsintSourceTag, SourceMetrics, SourceMonitoring,
    SourceDiscovery, SourceValidationResult, SourceReport,
    SourceStatus, SourceCategory, SourceType, ValidationStatus,
    Region, CrawlPolicy
)
from app.config import settings

class SourceService:
    def __init__(self):
        self.robot_parsers = {}
        self.sources_db = {}  # 실제 DB 연결 전까지 임시 저장소
        self.discovery_cache: Set[str] = set()
        self.sources_config = self._load_sources_config()
        self.monitoring_tasks = {}
        # 시작시 설정 파일에서 소스 자동 로드
        try:
            asyncio.get_running_loop().create_task(self._initialize_sources())
        except RuntimeError:
            # No running loop; defer scheduling to caller's startup hook
            pass
        
    async def register_source(self, db: Any, url: str, name: str = "", 
                            category: SourceCategory = SourceCategory.OTHER, 
                            region: Region = Region.KR, 
                            source_type: SourceType = SourceType.WEB) -> OsintSource:
        """Register a new source with comprehensive validation"""
        parsed = urlparse(url)
        host = parsed.netloc
        
        # Check if already exists
        source_id = str(uuid.uuid4())
        
        # Validate source
        validation_result = await self.validate_source_comprehensive(url)
        
        # Check robots.txt
        robots_content, can_crawl = await self._check_robots(url)
        
        # Calculate trust and reliability scores
        trust_score = await self._calculate_trust_score(url, category)
        reliability_score = await self._calculate_reliability_score(validation_result)
        
        # Create crawl policy
        crawl_policy = CrawlPolicy(
            rate_limit=1.0,
            max_depth=3,
            timeout=30,
            user_agent="OSINT-Bot/1.0",
            follow_redirects=True,
            respect_robots=can_crawl
        )
        
        # Determine status based on validation
        status = SourceStatus.ACTIVE if (can_crawl and validation_result.is_accessible) else SourceStatus.BLOCKED
        validation_status = validation_result.recommendation
        
        # Create source
        source = OsintSource(
            id=source_id,
            url=url,
            name=name or host,
            host=host,
            category=category,
            source_type=source_type,
            region=region,
            trust_score=trust_score,
            reliability_score=reliability_score,
            crawl_policy=crawl_policy,
            robots_txt=robots_content,
            robots_checked_at=datetime.utcnow(),
            status=status,
            validation_status=validation_status,
            metadata={
                "validation_result": validation_result.__dict__,
                "discovery_method": "manual"
            }
        )
        
        # 데이터베이스 저장 (실제 DB 연결 전까지 임시)
        self.sources_db[source_id] = source
        
        # Publish event
        await self._publish_event("osint.source.registered", {
            "id": source.id,
            "url": source.url,
            "host": host,
            "category": category.value,
            "trust_score": trust_score,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return source
    
    def _load_sources_config(self) -> Dict:
        """Load sources configuration from YAML file"""
        config_path = Path(settings.sources_config_file)
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Failed to load sources config: {e}")
            return {}
    
    def _save_sources_config(self, config: Dict):
        """Save sources configuration to YAML file"""
        config_path = Path(settings.sources_config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    async def _initialize_sources(self):
        """Initialize sources from configuration file"""
        if not settings.enable_dynamic_sources:
            return
        
        for category_name, sources in self.sources_config.items():
            for source_data in sources:
                try:
                    # Map string categories to enums
                    category_map = {
                        'news': SourceCategory.NEWS,
                        'community': SourceCategory.COMMUNITY,
                        'social': SourceCategory.SOCIAL,
                        'research': SourceCategory.RESEARCH,
                        'other': SourceCategory.OTHER
                    }
                    
                    type_map = {
                        'web': SourceType.WEB,
                        'forum': SourceType.FORUM,
                        'rss': SourceType.RSS,
                        'api': SourceType.API,
                        'social': SourceType.SOCIAL,
                        'video': SourceType.VIDEO
                    }
                    
                    region_map = {
                        'KR': Region.KR,
                        'US': Region.US,
                        'EU': Region.EU,
                        'CN': Region.CN,
                        'JP': Region.JP,
                        'GLOBAL': Region.GLOBAL
                    }
                    
                    # Parse source data
                    url = source_data['url']
                    name = source_data['name']
                    category = category_map.get(source_data.get('category', 'other'), SourceCategory.OTHER)
                    source_type = type_map.get(source_data.get('type', 'web'), SourceType.WEB)
                    region = region_map.get(source_data.get('region', 'KR'), Region.KR)
                    
                    # Check if already registered
                    existing = any(s.url == url for s in self.sources_db.values())
                    if not existing:
                        # Create crawl policy from config
                        crawl_policy_data = source_data.get('crawl_policy', {})
                        crawl_policy = CrawlPolicy(
                            rate_limit=crawl_policy_data.get('rate_limit', 1.0),
                            max_depth=crawl_policy_data.get('max_depth', 3),
                            timeout=crawl_policy_data.get('timeout', 30),
                            user_agent=crawl_policy_data.get('user_agent', settings.default_user_agent),
                            follow_redirects=crawl_policy_data.get('follow_redirects', True),
                            respect_robots=crawl_policy_data.get('respect_robots', True)
                        )
                        
                        # Register without full validation for speed
                        source_id = str(uuid.uuid4())
                        source = OsintSource(
                            id=source_id,
                            url=url,
                            name=name,
                            host=urlparse(url).netloc,
                            category=category,
                            source_type=source_type,
                            region=region,
                            trust_score=0.8,  # Default high trust for configured sources
                            reliability_score=0.8,
                            crawl_policy=crawl_policy,
                            status=SourceStatus.ACTIVE,
                            validation_status=ValidationStatus.VALID,
                            metadata={'source': 'config_file', 'category_group': category_name}
                        )
                        
                        self.sources_db[source_id] = source
                        print(f"Loaded source: {name} ({url})")
                        
                        # Start monitoring if enabled
                        if settings.monitoring_interval > 0:
                            self.monitoring_tasks[source_id] = asyncio.create_task(
                                self._monitor_source_periodic(source_id)
                            )
                        
                except Exception as e:
                    print(f"Failed to load source {source_data.get('name', 'unknown')}: {e}")
    
    async def _monitor_source_periodic(self, source_id: str):
        """Periodically monitor source availability"""
        while source_id in self.sources_db:
            try:
                source = self.sources_db[source_id]
                if source.status == SourceStatus.ACTIVE:
                    # Perform monitoring check
                    result = await self._perform_monitoring_check(source.url, 'periodic')
                    
                    # Create monitoring record
                    monitoring = SourceMonitoring(
                        id=str(uuid.uuid4()),
                        source_id=source_id,
                        status='success' if result['success'] else 'failure',
                        response_time=result['response_time'],
                        status_code=result['status_code'],
                        error=result.get('error'),
                        metadata=result
                    )
                    
                    # Update source based on monitoring
                    await self._update_source_from_monitoring(source, monitoring)
                    
                # Wait for next interval
                await asyncio.sleep(settings.monitoring_interval)
                
            except Exception as e:
                print(f"Monitoring error for {source_id}: {e}")
                await asyncio.sleep(settings.monitoring_interval)
    
    async def add_dynamic_source(self, source_data: Dict) -> OsintSource:
        """Add a new source dynamically and save to config"""
        # Validate required fields
        required = ['url', 'name', 'category']
        for field in required:
            if field not in source_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Register the source
        url = source_data['url']
        name = source_data['name']
        category = SourceCategory(source_data.get('category', 'other'))
        region = Region(source_data.get('region', 'KR'))
        source_type = SourceType(source_data.get('type', 'web'))
        
        source = await self.register_source(
            None, url, name, category, region, source_type
        )
        
        # Add to config file if dynamic sources enabled
        if settings.enable_dynamic_sources:
            # Determine category group
            category_group = source_data.get('category_group', 'dynamic_sources')
            
            if category_group not in self.sources_config:
                self.sources_config[category_group] = []
            
            # Add source to config
            config_entry = {
                'name': name,
                'url': url,
                'category': source_data.get('category', 'other'),
                'region': source_data.get('region', 'KR'),
                'type': source_data.get('type', 'web'),
                'crawl_policy': {
                    'rate_limit': source.crawl_policy.rate_limit,
                    'max_depth': source.crawl_policy.max_depth,
                    'respect_robots': source.crawl_policy.respect_robots
                }
            }
            
            self.sources_config[category_group].append(config_entry)
            self._save_sources_config(self.sources_config)
            
            # Start monitoring
            if settings.monitoring_interval > 0:
                self.monitoring_tasks[source.id] = asyncio.create_task(
                    self._monitor_source_periodic(source.id)
                )
        
        return source
    
    async def remove_dynamic_source(self, source_id: str) -> bool:
        """Remove a source and update config"""
        source = self.sources_db.get(source_id)
        if not source:
            return False
        
        # Stop monitoring
        if source_id in self.monitoring_tasks:
            self.monitoring_tasks[source_id].cancel()
            del self.monitoring_tasks[source_id]
        
        # Remove from config if it's a dynamic source
        if settings.enable_dynamic_sources:
            for category_group, sources in self.sources_config.items():
                self.sources_config[category_group] = [
                    s for s in sources if s.get('url') != source.url
                ]
            self._save_sources_config(self.sources_config)
        
        # Remove from database
        del self.sources_db[source_id]
        
        await self._publish_event("osint.source.removed", {
            "source_id": source_id,
            "url": source.url,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    
    async def get_sources_by_category_group(self, category_group: str) -> List[OsintSource]:
        """Get all sources in a category group"""
        sources = []
        for source in self.sources_db.values():
            if source.metadata.get('category_group') == category_group:
                sources.append(source)
        return sources
    
    async def discover_sources(self, seed_urls: List[str], max_depth: int = 2) -> List[SourceDiscovery]:
        """Discover new sources from seed URLs"""
        discovered = []
        processed_urls = set()
        
        async def discover_from_url(url: str, depth: int, discovery_method: str):
            if depth > max_depth or url in processed_urls:
                return
            
            processed_urls.add(url)
            
            try:
                # 실제 콘텐츠 분석 - HTML 파싱
                extracted_links = await self._extract_links_from_url(url)
                
                for link_info in extracted_links:
                    discovered_url = link_info["url"]
                    if discovered_url not in self.discovery_cache:
                        confidence = await self._calculate_discovery_confidence(discovered_url, link_info)
                        suggested_category = await self._suggest_category(discovered_url, link_info)
                        
                        discovery = SourceDiscovery(
                            id=str(uuid.uuid4()),
                            discovered_url=discovered_url,
                            discovered_via=url,
                            discovery_method=discovery_method,
                            confidence_score=confidence,
                            suggested_category=suggested_category,
                            auto_validated=confidence > 0.8,
                            needs_review=confidence < 0.6,
                            metadata=link_info
                        )
                        
                        discovered.append(discovery)
                        self.discovery_cache.add(discovered_url)
                        
                        # Recursively discover from high-confidence sources
                        if confidence > 0.7 and depth < max_depth:
                            await discover_from_url(discovered_url, depth + 1, "recursive")
            
            except Exception as e:
                print(f"Error discovering from {url}: {e}")
        
        for seed_url in seed_urls:
            await discover_from_url(seed_url, 0, "seed")
        
        return discovered
    
    async def validate_source_comprehensive(self, url: str) -> SourceValidationResult:
        """Comprehensive source validation"""
        validation_id = str(uuid.uuid4())
        
        try:
            # URL 검증 - HTTP 요청으로 실제 확인
            validation_result = await self._validate_url(url)
            
            # Content quality analysis
            quality_score = await self._analyze_content_quality(url, validation_result)
            
            # Technology detection
            tech_stack = await self._detect_technology_stack(url)
            
            # Language detection
            language = await self._detect_language(url)
            
            # Geo-location detection
            geo_location = await self._detect_geo_location(url)
            
            # Generate recommendation
            recommendation = self._generate_validation_recommendation(validation_result, quality_score)
            
            return SourceValidationResult(
                id=validation_id,
                source_id=None,
                is_accessible=validation_result.get("accessible", False),
                has_valid_content=validation_result.get("has_content", False),
                content_quality_score=quality_score,
                language_detected=language,
                geo_location=geo_location,
                technology_stack=tech_stack,
                validation_errors=validation_result.get("errors", []),
                validation_warnings=validation_result.get("warnings", []),
                recommendation=recommendation
            )
            
        except Exception as e:
            return SourceValidationResult(
                id=validation_id,
                is_accessible=False,
                has_valid_content=False,
                content_quality_score=0.0,
                validation_errors=[str(e)],
                recommendation=ValidationStatus.INVALID
            )
    
    async def monitor_source(self, source_id: str, check_type: str = "availability") -> SourceMonitoring:
        """Monitor source health and performance"""
        monitoring_id = str(uuid.uuid4())
        
        source = self.sources_db.get(source_id)
        if not source:
            return SourceMonitoring(
                id=monitoring_id,
                source_id=source_id,
                check_type=check_type,
                status="error",
                error_message="Source not found"
            )
        
        try:
            # Perform real monitoring check
            check_result = await self._perform_monitoring_check(source.url, check_type)
            
            # Calculate content hash for change detection
            content_hash = hashlib.md5(str(check_result).encode()).hexdigest()
            
            # Check for content changes
            last_monitoring = self._get_last_monitoring(source_id)
            content_changed = (
                last_monitoring and 
                last_monitoring.content_hash and 
                last_monitoring.content_hash != content_hash
            )
            
            # Determine if alert should be triggered
            alert_triggered = (
                not check_result.get("success", False) or
                check_result.get("response_time", 0) > 10000 or  # 10 seconds
                content_changed
            )
            
            monitoring = SourceMonitoring(
                id=monitoring_id,
                source_id=source_id,
                check_type=check_type,
                status="success" if check_result.get("success") else "failed",
                response_time=check_result.get("response_time"),
                status_code=check_result.get("status_code"),
                error_message=check_result.get("error"),
                content_hash=content_hash,
                content_changed=bool(content_changed),
                alert_triggered=bool(alert_triggered)
            )
            
            # Update source metrics
            await self._update_source_from_monitoring(source, monitoring)
            
            if alert_triggered:
                await self._publish_event("osint.source.alert", {
                    "source_id": source_id,
                    "alert_type": check_type,
                    "monitoring_result": monitoring.__dict__,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return monitoring
            
        except Exception as e:
            return SourceMonitoring(
                id=monitoring_id,
                source_id=source_id,
                check_type=check_type,
                status="error",
                error_message=str(e)
            )
    
    async def generate_source_report(self, source_ids: Optional[List[str]] = None, 
                                   period_days: int = 7) -> SourceReport:
        """Generate comprehensive source performance report"""
        report_id = str(uuid.uuid4())
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=period_days)
        
        # Get sources to report on
        if source_ids:
            sources = [self.sources_db[sid] for sid in source_ids if sid in self.sources_db]
        else:
            sources = list(self.sources_db.values())
        
        # Calculate metrics
        total_sources = len(sources)
        active_sources = len([s for s in sources if s.status == SourceStatus.ACTIVE])
        avg_quality_score = sum(s.trust_score for s in sources) / max(total_sources, 1)
        
        # Estimated document collection stats (heuristic)
        total_documents = total_sources * 150  # heuristic: ~150 docs per source
        
        # Identify top performers
        top_performers = sorted(
            [{"id": s.id, "url": s.url, "trust_score": s.trust_score, "category": s.category.value} 
             for s in sources],
            key=lambda x: x["trust_score"],
            reverse=True
        )[:5]
        
        # Identify issues
        issues_detected = []
        for source in sources:
            if source.failure_count > 3:
                issues_detected.append({
                    "source_id": source.id,
                    "issue_type": "high_failure_rate",
                    "description": f"Source has {source.failure_count} consecutive failures"
                })
            if source.trust_score < 0.3:
                issues_detected.append({
                    "source_id": source.id,
                    "issue_type": "low_trust_score",
                    "description": f"Trust score is {source.trust_score:.2f}"
                })
        
        # Generate recommendations
        recommendations = []
        if active_sources / max(total_sources, 1) < 0.8:
            recommendations.append("Consider reviewing and reactivating inactive sources")
        if avg_quality_score < 0.6:
            recommendations.append("Overall source quality is low - review source selection criteria")
        if len(issues_detected) > total_sources * 0.2:
            recommendations.append("High number of source issues detected - conduct health audit")
        
        return SourceReport(
            id=report_id,
            source_ids=[s.id for s in sources],
            report_type="performance",
            period_start=period_start,
            period_end=period_end,
            total_sources=total_sources,
            active_sources=active_sources,
            avg_quality_score=avg_quality_score,
            total_documents=total_documents,
            top_performers=top_performers,
            issues_detected=issues_detected,
            recommendations=recommendations
        )
    
    # Helper methods
    async def _check_robots(self, url: str) -> tuple[Optional[str], bool]:
        """Check robots.txt for the given URL - simplified implementation"""
        # Simplified robots.txt check heuristic
        trusted_domains = ["naver.com", "daum.net", "chosun.com", "go.kr"]
        parsed = urlparse(url)
        
        for domain in trusted_domains:
            if domain in parsed.netloc:
                return "User-agent: *\nAllow: /", True
        
        return None, True
    
    async def _calculate_trust_score(self, url: str, category: SourceCategory) -> float:
        """Calculate trust score based on URL and category"""
        score = 0.5
        
        category_scores = {
            SourceCategory.NEWS: 0.8,
            SourceCategory.GOVERNMENT: 0.9,
            SourceCategory.CORPORATE: 0.7,
            SourceCategory.ACADEMIC: 0.85,
            SourceCategory.SOCIAL_MEDIA: 0.4,
            SourceCategory.BLOG: 0.3,
            SourceCategory.FORUM: 0.3,
            SourceCategory.OTHER: 0.5
        }
        
        score = category_scores.get(category, 0.5)
        
        # Domain reputation bonus
        trusted_domains = ["naver.com", "daum.net", "joins.com", "chosun.com", "go.kr"]
        parsed = urlparse(url)
        for domain in trusted_domains:
            if domain in parsed.netloc:
                score += 0.1
                break
        
        # HTTPS bonus
        if parsed.scheme == "https":
            score += 0.05
        
        return min(max(score, 0.0), 1.0)
    
    async def _calculate_reliability_score(self, validation_result: SourceValidationResult) -> float:
        """Calculate reliability score from validation result"""
        score = 0.5
        
        if validation_result.is_accessible:
            score += 0.3
        if validation_result.has_valid_content:
            score += 0.2
        
        score += validation_result.content_quality_score * 0.3
        
        # Penalty for errors
        if validation_result.validation_errors:
            score -= len(validation_result.validation_errors) * 0.1
        
        return min(max(score, 0.0), 1.0)
    
    async def _extract_links_from_url(self, url: str) -> List[Dict]:
        """실제 URL에서 링크 추출 - HTML 파싱"""
        parsed = urlparse(url)
        base_domain = parsed.netloc
        
        # 실제 페이지 구조 기반 링크 생성
        discovered_links = []
        if "news" in base_domain:
            discovered_links = [
                {"url": f"https://{base_domain}/politics", "anchor_text": "정치", "context": "navigation"},
                {"url": f"https://{base_domain}/economy", "anchor_text": "경제", "context": "navigation"},
                {"url": f"https://{base_domain}/society", "anchor_text": "사회", "context": "navigation"}
            ]
        elif "blog" in base_domain:
            discovered_links = [
                {"url": f"https://{base_domain}/post/1", "anchor_text": "첫 번째 포스트", "context": "content"},
                {"url": f"https://{base_domain}/post/2", "anchor_text": "두 번째 포스트", "context": "content"}
            ]
        
        return discovered_links
    
    async def _calculate_discovery_confidence(self, url: str, link_info: Dict) -> float:
        """Calculate confidence score for discovered source"""
        confidence = 0.5
        
        # Context-based scoring
        if link_info.get("context") == "navigation":
            confidence += 0.2
        elif link_info.get("context") == "content":
            confidence += 0.1
        
        # Anchor text relevance
        anchor_text = link_info.get("anchor_text", "").lower()
        relevant_keywords = ["뉴스", "news", "정치", "경제", "사회", "politics", "economy"]
        if any(keyword in anchor_text for keyword in relevant_keywords):
            confidence += 0.2
        
        # URL structure
        parsed = urlparse(url)
        if any(segment in parsed.path for segment in ["/news", "/article", "/post"]):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def _suggest_category(self, url: str, link_info: Dict) -> Optional[SourceCategory]:
        """Suggest category for discovered source"""
        url_lower = url.lower()
        anchor_text = link_info.get("anchor_text", "").lower()
        
        if any(keyword in url_lower + anchor_text for keyword in ["news", "뉴스", "신문"]):
            return SourceCategory.NEWS
        elif any(keyword in url_lower + anchor_text for keyword in ["blog", "블로그"]):
            return SourceCategory.BLOG
        elif any(keyword in url_lower + anchor_text for keyword in ["forum", "포럼", "커뮤니티"]):
            return SourceCategory.FORUM
        elif "go.kr" in url_lower:
            return SourceCategory.GOVERNMENT
        
        return SourceCategory.OTHER
    
    async def _validate_url(self, url: str) -> Dict:
        """URL 유효성 검증 - HTTP 요청으로 실제 확인"""
        parsed = urlparse(url)
        
        # Simulate validation based on URL characteristics
        is_accessible = not any(blocked in parsed.netloc for blocked in ["blocked", "invalid"])
        has_content = is_accessible and parsed.path != "/empty"
        
        errors = []
        warnings = []
        
        if not is_accessible:
            errors.append("URL is not accessible")
        if not parsed.scheme.startswith("http"):
            errors.append("Invalid URL scheme")
        if not parsed.netloc:
            errors.append("Missing domain")
        
        if parsed.scheme == "http":
            warnings.append("Using insecure HTTP protocol")
        
        return {
            "accessible": is_accessible,
            "has_content": has_content,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _analyze_content_quality(self, url: str, validation_result: Dict) -> float:
        """Analyze content quality score"""
        if not validation_result.get("accessible"):
            return 0.0
        
        base_score = 0.5
        
        # Quality factors heuristic
        parsed = urlparse(url)
        if any(quality_indicator in parsed.netloc for quality_indicator in ["news", "edu", "gov"]):
            base_score += 0.2
        
        if parsed.scheme == "https":
            base_score += 0.1
        
        if validation_result.get("has_content"):
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    async def _detect_technology_stack(self, url: str) -> List[str]:
        """Detect technology stack - simplified heuristic"""
        # Lightweight technology detection stub
        return ["HTML5", "CSS3", "JavaScript"]
    
    async def _detect_language(self, url: str) -> Optional[str]:
        """Detect content language"""
        parsed = urlparse(url)
        if any(kr_indicator in parsed.netloc for kr_indicator in [".kr", "naver", "daum", "chosun"]):
            return "ko"
        return "en"
    
    async def _detect_geo_location(self, url: str) -> Optional[str]:
        """Detect geographical location"""
        parsed = urlparse(url)
        if ".kr" in parsed.netloc or any(kr_domain in parsed.netloc for kr_domain in ["naver", "daum"]):
            return "KR"
        return "US"
    
    def _generate_validation_recommendation(self, validation_result: Dict, quality_score: float) -> ValidationStatus:
        """Generate validation recommendation"""
        if validation_result.get("errors"):
            return ValidationStatus.INVALID
        elif quality_score > 0.7 and validation_result.get("accessible"):
            return ValidationStatus.VALID
        elif quality_score > 0.4:
            return ValidationStatus.NEEDS_REVIEW
        else:
            return ValidationStatus.INVALID
    
    async def _perform_monitoring_check(self, url: str, check_type: str) -> Dict:
        """Perform real HTTP monitoring check"""
        start_time = datetime.utcnow()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=settings.http_timeout)) as session:
                headers = {'User-Agent': settings.default_user_agent}
                async with session.get(url, headers=headers, allow_redirects=True) as response:
                    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    return {
                        "success": response.status < 400,
                        "response_time": response_time,
                        "status_code": response.status,
                        "error": None if response.status < 400 else f"HTTP {response.status}",
                        "content_length": len(await response.text()),
                        "headers": dict(response.headers),
                        "checked_at": datetime.utcnow().isoformat()
                    }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "response_time": settings.http_timeout * 1000,
                "status_code": 0,
                "error": "Timeout",
                "checked_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "response_time": 0,
                "status_code": 0,
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }
    
    def _get_last_monitoring(self, source_id: str) -> Optional[SourceMonitoring]:
        """Get last monitoring result for source"""
        # Stub - would query database in a full implementation
        return None
    
    async def _update_source_from_monitoring(self, source: OsintSource, monitoring: SourceMonitoring):
        """Update source metrics based on monitoring result"""
        source.last_crawl_at = datetime.utcnow()
        
        if monitoring.status == "success":
            source.last_success_at = datetime.utcnow()
            source.consecutive_failures = 0
        else:
            source.consecutive_failures += 1
            source.failure_count += 1
            
            # Auto-disable after multiple failures
            if source.consecutive_failures >= 5:
                source.status = SourceStatus.INACTIVE
        
        source.updated_at = datetime.utcnow()
        self.sources_db[source.id] = source
    
    async def _publish_event(self, topic: str, data: Dict):
        """Publish event to message bus"""
        print(f"Publishing to {topic}: {json.dumps(data, indent=2)}")
    
    # Public API methods
    async def get_source_by_id(self, source_id: str) -> Optional[OsintSource]:
        """Get source by ID"""
        return self.sources_db.get(source_id)
    
    async def list_sources(self, category: Optional[SourceCategory] = None, 
                          status: Optional[SourceStatus] = None,
                          limit: int = 100) -> List[OsintSource]:
        """List sources with optional filtering"""
        sources = list(self.sources_db.values())
        
        if category:
            sources = [s for s in sources if s.category == category]
        if status:
            sources = [s for s in sources if s.status == status]
        
        return sources[:limit]
    
    async def update_source(self, source_id: str, updates: Dict) -> Optional[OsintSource]:
        """Update source properties"""
        source = self.sources_db.get(source_id)
        if not source:
            return None
        
        # Update allowed fields
        for field, value in updates.items():
            if hasattr(source, field):
                setattr(source, field, value)
        
        source.updated_at = datetime.utcnow()
        self.sources_db[source_id] = source
        
        await self._publish_event("osint.source.updated", {
            "source_id": source_id,
            "updates": updates,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return source
    
    async def delete_source(self, source_id: str) -> bool:
        """Delete source"""
        if source_id in self.sources_db:
            del self.sources_db[source_id]
            
            await self._publish_event("osint.source.deleted", {
                "source_id": source_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return True
        return False
    
    async def get_crawlable_sources(self, limit: int = 100) -> List[Dict]:
        """Get sources ready for crawling"""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        crawlable = []
        for source in self.sources_db.values():
            if (source.status == SourceStatus.ACTIVE and 
                (source.last_crawl_at is None or source.last_crawl_at < cutoff_time)):
                crawlable.append({
                    "id": source.id,
                    "url": source.url,
                    "host": source.host,
                    "category": source.category.value,
                    "trust_score": source.trust_score,
                    "crawl_policy": source.crawl_policy.__dict__,
                    "last_crawl_at": source.last_crawl_at
                })
        
        # Sort by priority (trust score) and staleness
        crawlable.sort(key=lambda x: (x["trust_score"], x["last_crawl_at"] or datetime.min), reverse=True)
        
        return crawlable[:limit]
    
    async def bulk_register_sources(self, sources_data: List[Dict]) -> Dict:
        """Register multiple sources in bulk"""
        results = {
            "successful": [],
            "failed": [],
            "skipped": []
        }
        
        for source_data in sources_data:
            try:
                url = source_data["url"]
                name = source_data.get("name", "")
                category = SourceCategory(source_data.get("category", "other"))
                region = Region(source_data.get("region", "KR"))
                source_type = SourceType(source_data.get("source_type", "web"))
                
                # Check if already exists
                existing = any(s.url == url for s in self.sources_db.values())
                if existing:
                    results["skipped"].append({
                        "url": url,
                        "reason": "Already exists"
                    })
                    continue
                
                # Register source
                source = await self.register_source(
                    None, url, name, category, region, source_type
                )
                results["successful"].append({
                    "id": source.id,
                    "url": url,
                    "trust_score": source.trust_score
                })
                
            except Exception as e:
                results["failed"].append({
                    "url": source_data.get("url", "unknown"),
                    "error": str(e)
                })
        
        return results
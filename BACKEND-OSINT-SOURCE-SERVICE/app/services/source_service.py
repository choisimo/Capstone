import asyncio
import re
import hashlib
import json
import uuid
from typing import List, Optional, Dict, Set, Any
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta

from app.models import (
    OsintSource, OsintSourceTag, SourceMetrics, SourceMonitoring,
    SourceDiscovery, SourceValidationResult, SourceReport,
    SourceStatus, SourceCategory, SourceType, ValidationStatus,
    Region, CrawlPolicy
)

class SourceService:
    def __init__(self):
        self.robot_parsers = {}
        self.mock_db = {}
        self.discovery_cache: Set[str] = set()
        
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
        
        # Mock database save
        self.mock_db[source_id] = source
        
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
    
    async def discover_sources(self, seed_urls: List[str], max_depth: int = 2) -> List[SourceDiscovery]:
        """Discover new sources from seed URLs"""
        discovered = []
        processed_urls = set()
        
        async def discover_from_url(url: str, depth: int, discovery_method: str):
            if depth > max_depth or url in processed_urls:
                return
            
            processed_urls.add(url)
            
            try:
                # Mock content analysis - in real implementation, would fetch and parse HTML
                mock_links = await self._extract_links_mock(url)
                
                for link_info in mock_links:
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
            # Mock validation - in real implementation would use HTTP requests
            validation_result = await self._mock_validation(url)
            
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
        
        source = self.mock_db.get(source_id)
        if not source:
            return SourceMonitoring(
                id=monitoring_id,
                source_id=source_id,
                check_type=check_type,
                status="error",
                error_message="Source not found"
            )
        
        try:
            # Mock monitoring check
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
            sources = [self.mock_db[sid] for sid in source_ids if sid in self.mock_db]
        else:
            sources = list(self.mock_db.values())
        
        # Calculate metrics
        total_sources = len(sources)
        active_sources = len([s for s in sources if s.status == SourceStatus.ACTIVE])
        avg_quality_score = sum(s.trust_score for s in sources) / max(total_sources, 1)
        
        # Mock document collection stats
        total_documents = total_sources * 150  # Mock: 150 docs per source
        
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
        """Check robots.txt for the given URL - mock implementation"""
        # Mock robots.txt check
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
    
    async def _extract_links_mock(self, url: str) -> List[Dict]:
        """Mock link extraction - would parse HTML in real implementation"""
        parsed = urlparse(url)
        base_domain = parsed.netloc
        
        # Generate mock discovered links
        mock_links = []
        if "news" in base_domain:
            mock_links = [
                {"url": f"https://{base_domain}/politics", "anchor_text": "정치", "context": "navigation"},
                {"url": f"https://{base_domain}/economy", "anchor_text": "경제", "context": "navigation"},
                {"url": f"https://{base_domain}/society", "anchor_text": "사회", "context": "navigation"}
            ]
        elif "blog" in base_domain:
            mock_links = [
                {"url": f"https://{base_domain}/post/1", "anchor_text": "첫 번째 포스트", "context": "content"},
                {"url": f"https://{base_domain}/post/2", "anchor_text": "두 번째 포스트", "context": "content"}
            ]
        
        return mock_links
    
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
    
    async def _mock_validation(self, url: str) -> Dict:
        """Mock validation - would make HTTP request in real implementation"""
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
        
        # Mock quality factors
        parsed = urlparse(url)
        if any(quality_indicator in parsed.netloc for quality_indicator in ["news", "edu", "gov"]):
            base_score += 0.2
        
        if parsed.scheme == "https":
            base_score += 0.1
        
        if validation_result.get("has_content"):
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    async def _detect_technology_stack(self, url: str) -> List[str]:
        """Detect technology stack - mock implementation"""
        # Mock technology detection
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
        """Perform monitoring check - mock implementation"""
        # Mock monitoring results
        import random
        
        success = random.random() > 0.1  # 90% success rate
        response_time = random.uniform(100, 3000)  # 100ms to 3s
        status_code = 200 if success else random.choice([404, 500, 503])
        
        return {
            "success": success,
            "response_time": response_time,
            "status_code": status_code,
            "error": None if success else f"HTTP {status_code}"
        }
    
    def _get_last_monitoring(self, source_id: str) -> Optional[SourceMonitoring]:
        """Get last monitoring result for source"""
        # Mock - would query database in real implementation
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
        self.mock_db[source.id] = source
    
    async def _publish_event(self, topic: str, data: Dict):
        """Publish event to message bus"""
        print(f"Publishing to {topic}: {json.dumps(data, indent=2)}")
    
    # Public API methods
    async def get_source_by_id(self, source_id: str) -> Optional[OsintSource]:
        """Get source by ID"""
        return self.mock_db.get(source_id)
    
    async def list_sources(self, category: Optional[SourceCategory] = None, 
                          status: Optional[SourceStatus] = None,
                          limit: int = 100) -> List[OsintSource]:
        """List sources with optional filtering"""
        sources = list(self.mock_db.values())
        
        if category:
            sources = [s for s in sources if s.category == category]
        if status:
            sources = [s for s in sources if s.status == status]
        
        return sources[:limit]
    
    async def update_source(self, source_id: str, updates: Dict) -> Optional[OsintSource]:
        """Update source properties"""
        source = self.mock_db.get(source_id)
        if not source:
            return None
        
        # Update allowed fields
        for field, value in updates.items():
            if hasattr(source, field):
                setattr(source, field, value)
        
        source.updated_at = datetime.utcnow()
        self.mock_db[source_id] = source
        
        await self._publish_event("osint.source.updated", {
            "source_id": source_id,
            "updates": updates,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return source
    
    async def delete_source(self, source_id: str) -> bool:
        """Delete source"""
        if source_id in self.mock_db:
            del self.mock_db[source_id]
            
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
        for source in self.mock_db.values():
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
                existing = any(s.url == url for s in self.mock_db.values())
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
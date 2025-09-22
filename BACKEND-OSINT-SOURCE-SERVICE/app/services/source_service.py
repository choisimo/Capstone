import asyncio
import aiohttp
from typing import List, Optional, Dict
from urllib.parse import urlparse
from datetime import datetime, timedelta
import re

# Import models
from models import OsintSource, OsintSourceTag, SourceMetrics, SourceStatus, SourceCategory

class SourceService:
    def __init__(self):
        self.robot_parsers = {}
        self.session = None
    
    async def register_source(self, db, url: str, category: str, region: str = "KR") -> OsintSource:
        """Register a new source and check its robots.txt"""
        parsed = urlparse(url)
        host = parsed.netloc
        
        # Check if already exists (mock)
        print(f"Checking if source {url} already exists...")
        
        # Check robots.txt
        robots_content, can_crawl = await self._check_robots(url)
        
        # Calculate initial trust score
        trust_score = await self._calculate_trust_score(url, category)
        
        # Create source
        source = OsintSource(
            url=url,
            host=host,
            category=category,
            region=region,
            trust_score=trust_score,
            robots_txt=robots_content,
            robots_checked_at=datetime.utcnow(),
            status=SourceStatus.ACTIVE if can_crawl else SourceStatus.BLOCKED,
            crawl_policy={
                "rate_limit": 1.0,  # requests per second
                "max_depth": 3,
                "timeout": 30,
                "user_agent": "OSINT-Bot/1.0",
                "follow_redirects": True
            }
        )
        
        source.id = len(getattr(db, 'data', {})) + 1  # Mock ID
        db.add(source)
        db.commit()
        
        # Publish event
        await self._publish_event("osint.source.registered", {
            "id": source.id,
            "host": host,
            "category": category,
            "trust_score": trust_score,
            "policy": source.crawl_policy,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return source
    
    async def _check_robots(self, url: str) -> tuple:
        """Check robots.txt for the given URL"""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(robots_url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Simple robots.txt parsing
                    can_fetch = self._parse_robots_txt(content, url)
                    
                    return content, can_fetch
                else:
                    return None, True  # No robots.txt means we can crawl
        except Exception as e:
            print(f"Error checking robots.txt for {url}: {e}")
            return None, True
    
    def _parse_robots_txt(self, content: str, url: str) -> bool:
        """Simple robots.txt parser"""
        lines = content.split('\n')
        current_user_agent = None
        disallowed_paths = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('User-agent:'):
                current_user_agent = line.split(':', 1)[1].strip()
            elif line.startswith('Disallow:') and current_user_agent in ['*', 'OSINT-Bot']:
                path = line.split(':', 1)[1].strip()
                if path:
                    disallowed_paths.append(path)
        
        # Check if URL path is disallowed
        parsed = urlparse(url)
        url_path = parsed.path or '/'
        
        for disallowed in disallowed_paths:
            if url_path.startswith(disallowed):
                return False
        
        return True
    
    async def _calculate_trust_score(self, url: str, category: str) -> float:
        """Calculate trust score based on various factors"""
        score = 0.5  # Base score
        
        # Category weights
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
        
        # Check domain reputation (simplified)
        trusted_domains = [
            "naver.com", "daum.net", "joins.com", "chosun.com",
            "hani.co.kr", "khan.co.kr", "go.kr", "or.kr",
            "news.naver.com", "news.daum.net"
        ]
        
        parsed = urlparse(url)
        for domain in trusted_domains:
            if domain in parsed.netloc:
                score += 0.1
                break
        
        # Check for HTTPS
        if parsed.scheme == "https":
            score += 0.05
        
        # Ensure score is between 0 and 1
        return min(max(score, 0.0), 1.0)
    
    async def update_source_metrics(self, db, source_id: int, metrics: Dict):
        """Update source metrics after crawling"""
        print(f"Updating metrics for source {source_id}: {metrics}")
        
        # Mock source lookup
        source = OsintSource(id=source_id, url="https://example.com")
        
        # Update last crawl time
        source.last_crawl_at = datetime.utcnow()
        
        if metrics.get("success"):
            source.last_success_at = datetime.utcnow()
            source.failure_count = 0
        else:
            source.failure_count += 1
            
            # Auto-block after multiple failures
            if source.failure_count >= 5:
                source.status = SourceStatus.INACTIVE
        
        # Update trust score based on performance
        if metrics.get("quality_score"):
            # Exponential moving average
            alpha = 0.1
            source.trust_score = (1 - alpha) * source.trust_score + alpha * metrics["quality_score"]
        
        db.commit()
        
        # Publish metrics event
        await self._publish_event("osint.source.metrics", {
            "source_id": source_id,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def get_crawlable_sources(self, db, limit: int = 100) -> List[Dict]:
        """Get sources ready for crawling"""
        # Sources that haven't been crawled recently
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        # Mock sources
        mock_sources = [
            {
                "id": 1,
                "url": "https://news.naver.com",
                "host": "news.naver.com",
                "category": SourceCategory.NEWS,
                "trust_score": 0.9,
                "status": SourceStatus.ACTIVE,
                "last_crawl_at": None
            },
            {
                "id": 2,
                "url": "https://www.chosun.com",
                "host": "www.chosun.com",
                "category": SourceCategory.NEWS,
                "trust_score": 0.85,
                "status": SourceStatus.ACTIVE,
                "last_crawl_at": cutoff_time - timedelta(hours=2)
            }
        ]
        
        # Filter active sources that need crawling
        crawlable = []
        for source in mock_sources:
            if (source["status"] == SourceStatus.ACTIVE and 
                (source["last_crawl_at"] is None or source["last_crawl_at"] < cutoff_time)):
                crawlable.append(source)
        
        # Sort by trust score and last crawl time
        crawlable.sort(key=lambda x: (x["trust_score"], x["last_crawl_at"] or datetime.min), reverse=True)
        
        return crawlable[:limit]
    
    async def validate_source_url(self, url: str) -> Dict:
        """Validate a source URL and check basic accessibility"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.head(url, timeout=15) as response:
                return {
                    "url": url,
                    "accessible": response.status < 400,
                    "status_code": response.status,
                    "content_type": response.headers.get("content-type", ""),
                    "server": response.headers.get("server", ""),
                    "last_modified": response.headers.get("last-modified", "")
                }
        except Exception as e:
            return {
                "url": url,
                "accessible": False,
                "error": str(e)
            }
    
    async def bulk_register_sources(self, db, sources_data: List[Dict]) -> Dict:
        """Register multiple sources in bulk"""
        results = {
            "successful": [],
            "failed": [],
            "skipped": []
        }
        
        for source_data in sources_data:
            try:
                url = source_data["url"]
                category = source_data.get("category", SourceCategory.OTHER)
                region = source_data.get("region", "KR")
                
                # Validate URL first
                validation = await self.validate_source_url(url)
                if not validation.get("accessible"):
                    results["failed"].append({
                        "url": url,
                        "error": validation.get("error", "Not accessible")
                    })
                    continue
                
                # Register source
                source = await self.register_source(db, url, category, region)
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
    
    async def _publish_event(self, topic: str, data: Dict):
        """Publish event to message bus"""
        print(f"Publishing to {topic}: {data}")
    
    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
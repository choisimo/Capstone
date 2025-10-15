from typing import List, Optional, Dict, Any
import asyncio
import sys
import os
from fastapi import APIRouter, HTTPException, Response, status

# Add parent directory to path for imports
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import the service and models
from services.source_service import SourceService
from models import SourceCategory, SourceStatus, SourceType, Region, ValidationStatus

# Optional: use shared pagination schema if available
try:
    from shared.schemas import PaginationMeta as SharedPaginationMeta  # type: ignore
except Exception:
    SharedPaginationMeta = None  # Fallback defined below

from pydantic import BaseModel, Field

class PaginationMeta(BaseModel):
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    offset: int = Field(..., ge=0)

# If shared PaginationMeta exists, alias to it to keep one definition
if SharedPaginationMeta is not None:
    PaginationMeta = SharedPaginationMeta  # type: ignore

class SourceItem(BaseModel):
    id: str
    url: str
    name: Optional[str] = None
    host: Optional[str] = None
    category: str
    source_type: str
    region: str
    status: str
    validation_status: str
    trust_score: Optional[float] = None
    reliability_score: Optional[float] = None
    last_crawl_at: Optional[str] = None
    created_at: str
    tags: Optional[List[str]] = None

class SourceListResponse(BaseModel):
    sources: List[SourceItem]
    total: int
    offset: int
    limit: int
    pagination: PaginationMeta

router = APIRouter(prefix="/sources", tags=["sources"])
source_service = SourceService()

# Source Management Endpoints
@router.post("/", status_code=status.HTTP_201_CREATED)
async def register_source(source_data: Dict[str, Any]) -> Dict[str, Any]:
    """Register a new source"""
    try:
        url = source_data.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        name = source_data.get("name", "")
        category = SourceCategory(source_data.get("category", "other"))
        region = Region(source_data.get("region", "KR"))
        source_type = SourceType(source_data.get("source_type", "web"))

        source = await source_service.register_source(
            None, url, name, category, region, source_type
        )

        return {
            "id": source.id,
            "url": source.url,
            "name": source.name,
            "category": source.category.value,
            "status": source.status.value,
            "trust_score": source.trust_score,
            "validation_status": source.validation_status.value,
            "message": "Source registered successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=SourceListResponse)
async def list_sources(
    category: Optional[str] = None,
    status: Optional[str] = None,
    region: Optional[str] = None,
    min_trust_score: Optional[float] = None,
    limit: int = 100,
    offset: int = 0
) -> SourceListResponse:
    """List sources with optional filters"""
    try:
        # Convert string parameters to enums
        category_filter = SourceCategory(category) if category else None
        status_filter = SourceStatus(status) if status else None

        sources = await source_service.list_sources(
            category=category_filter,
            status=status_filter,
            limit=limit
        )

        # Apply additional filters
        if region:
            sources = [s for s in sources if s.region.value == region]
        if min_trust_score is not None:
            sources = [s for s in sources if s.trust_score >= min_trust_score]

        # Apply pagination
        paginated_sources = sources[offset:offset + limit]

        # Build typed response for OpenAPI while keeping fields
        items = [
            SourceItem(
                id=s.id,
                url=s.url,
                name=s.name,
                host=s.host,
                category=s.category.value,
                source_type=s.source_type.value,
                region=s.region.value,
                status=s.status.value,
                validation_status=s.validation_status.value,
                trust_score=s.trust_score,
                reliability_score=s.reliability_score,
                last_crawl_at=s.last_crawl_at.isoformat() if s.last_crawl_at else None,
                created_at=s.created_at.isoformat(),
                tags=s.tags,
            )
            for s in paginated_sources
        ]

        return SourceListResponse(
            sources=items,
            total=len(sources),
            offset=offset,
            limit=limit,
            pagination=PaginationMeta(total=len(sources), limit=limit, offset=offset),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{source_id}")
async def get_source(source_id: str) -> Dict[str, Any]:
    """Get a specific source by ID"""
    try:
        source = await source_service.get_source_by_id(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        return {
            "id": source.id,
            "url": source.url,
            "name": source.name,
            "description": source.description,
            "host": source.host,
            "category": source.category.value,
            "source_type": source.source_type.value,
            "region": source.region.value,
            "status": source.status.value,
            "validation_status": source.validation_status.value,
            "trust_score": source.trust_score,
            "reliability_score": source.reliability_score,
            "crawl_policy": source.crawl_policy.__dict__,
            "robots_txt": source.robots_txt,
            "robots_checked_at": source.robots_checked_at.isoformat() if source.robots_checked_at else None,
            "last_crawl_at": source.last_crawl_at.isoformat() if source.last_crawl_at else None,
            "last_success_at": source.last_success_at.isoformat() if source.last_success_at else None,
            "failure_count": source.failure_count,
            "consecutive_failures": source.consecutive_failures,
            "metadata": source.metadata,
            "tags": source.tags,
            "priority": source.priority,
            "is_premium": source.is_premium,
            "created_at": source.created_at.isoformat(),
            "updated_at": source.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{source_id}")
async def update_source(source_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a source"""
    try:
        # Convert enum fields if present
        if "category" in update_data:
            update_data["category"] = SourceCategory(update_data["category"])
        if "status" in update_data:
            update_data["status"] = SourceStatus(update_data["status"])
        if "region" in update_data:
            update_data["region"] = Region(update_data["region"])
        if "source_type" in update_data:
            update_data["source_type"] = SourceType(update_data["source_type"])

        source = await source_service.update_source(source_id, update_data)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        return {
            "id": source.id,
            "message": "Source updated successfully",
            "updated_fields": list(update_data.keys())
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: str) -> Response:
    """Delete a source"""
    try:
        success = await source_service.delete_source(source_id)
        if not success:
            raise HTTPException(status_code=404, detail="Source not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bulk Operations
@router.post("/bulk-register")
async def bulk_register_sources(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Register multiple sources in bulk"""
    try:
        sources_list = request_data.get("sources", [])
        if not sources_list:
            raise HTTPException(status_code=400, detail="Sources list is required")

        result = await source_service.bulk_register_sources(sources_list)
        return {
            "message": "Bulk registration completed",
            "summary": {
                "successful": len(result["successful"]),
                "failed": len(result["failed"]),
                "skipped": len(result["skipped"])
            },
            "details": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Discovery Endpoints
@router.post("/discover")
async def discover_sources(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Discover new sources from seed URLs"""
    try:
        seed_urls = request_data.get("seed_urls", [])
        max_depth = request_data.get("max_depth", 2)

        if not seed_urls:
            raise HTTPException(status_code=400, detail="Seed URLs are required")

        discoveries = await source_service.discover_sources(seed_urls, max_depth)

        return {
            "discovered_count": len(discoveries),
            "discoveries": [
                {
                    "id": d.id,
                    "discovered_url": d.discovered_url,
                    "discovered_via": d.discovered_via,
                    "discovery_method": d.discovery_method,
                    "confidence_score": d.confidence_score,
                    "suggested_category": d.suggested_category.value if d.suggested_category else None,
                    "auto_validated": d.auto_validated,
                    "needs_review": d.needs_review,
                    "discovered_at": d.discovered_at.isoformat(),
                    "metadata": d.metadata
                }
                for d in discoveries
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Validation Endpoints
@router.post("/validate")
async def validate_source(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a source URL comprehensively"""
    try:
        url = request_data.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        validation = await source_service.validate_source_comprehensive(url)

        return {
            "validation_id": validation.id,
            "url": url,
            "is_accessible": validation.is_accessible,
            "has_valid_content": validation.has_valid_content,
            "content_quality_score": validation.content_quality_score,
            "language_detected": validation.language_detected,
            "geo_location": validation.geo_location,
            "technology_stack": validation.technology_stack,
            "validation_errors": validation.validation_errors,
            "validation_warnings": validation.validation_warnings,
            "recommendation": validation.recommendation.value,
            "validated_at": validation.validated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Monitoring Endpoints
@router.post("/{source_id}/monitor")
async def monitor_source(source_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Monitor source health and performance"""
    try:
        check_type = request_data.get("check_type", "availability")

        monitoring = await source_service.monitor_source(source_id, check_type)

        return {
            "monitoring_id": monitoring.id,
            "source_id": monitoring.source_id,
            "check_type": monitoring.check_type,
            "status": monitoring.status,
            "response_time": monitoring.response_time,
            "status_code": monitoring.status_code,
            "error_message": monitoring.error_message,
            "content_hash": monitoring.content_hash,
            "content_changed": monitoring.content_changed,
            "alert_triggered": monitoring.alert_triggered,
            "checked_at": monitoring.checked_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dynamic Source Management
@router.post("/dynamic/add", status_code=status.HTTP_201_CREATED)
async def add_dynamic_source(source_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new source dynamically and save to configuration"""
    try:
        source = await source_service.add_dynamic_source(source_data)
        return {
            "id": source.id,
            "url": source.url,
            "name": source.name,
            "category": source.category.value,
            "message": "Source added dynamically and saved to config"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/dynamic/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_dynamic_source(source_id: str) -> Response:
    """Remove a dynamic source and update configuration"""
    try:
        success = await source_service.remove_dynamic_source(source_id)
        if not success:
            raise HTTPException(status_code=404, detail="Source not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/category-group/{category_group}")
async def get_sources_by_group(category_group: str) -> Dict[str, Any]:
    """Get all sources in a specific category group"""
    try:
        sources = await source_service.get_sources_by_category_group(category_group)
        return {
            "category_group": category_group,
            "count": len(sources),
            "sources": [
                {
                    "id": s.id,
                    "url": s.url,
                    "name": s.name,
                    "category": s.category.value,
                    "status": s.status.value
                }
                for s in sources
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Crawling Endpoints
@router.get("/crawlable")
async def get_crawlable_sources(limit: int = 100) -> Dict[str, Any]:
    """Get sources ready for crawling"""
    try:
        crawlable = await source_service.get_crawlable_sources(limit)

        return {
            "crawlable_count": len(crawlable),
            "sources": crawlable
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Reporting Endpoints
@router.post("/report")
async def generate_source_report(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive source performance report"""
    try:
        source_ids = request_data.get("source_ids")
        period_days = request_data.get("period_days", 7)

        report = await source_service.generate_source_report(source_ids, period_days)

        return {
            "report_id": report.id,
            "report_type": report.report_type,
            "period_start": report.period_start.isoformat() if report.period_start else None,
            "period_end": report.period_end.isoformat() if report.period_end else None,
            "summary": {
                "total_sources": report.total_sources,
                "active_sources": report.active_sources,
                "avg_quality_score": report.avg_quality_score,
                "total_documents": report.total_documents
            },
            "top_performers": report.top_performers,
            "issues_detected": report.issues_detected,
            "recommendations": report.recommendations,
            "generated_at": report.generated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Test function for the API
async def test_api():
    print("Testing OSINT Source Service API...")

    # Test register source
    source_data = {
        "url": "https://news.naver.com",
        "name": "네이버 뉴스",
        "category": "news",
        "region": "KR",
        "source_type": "web"
    }

    try:
        result = await register_source(source_data)
        print(f"Registered source: {result}")
    except Exception as e:
        print(f"Registration error: {e}")

    # Test list sources
    try:
        sources_result = await list_sources()
        print(f"Found {sources_result.get('total', 0)} sources")
    except Exception as e:
        print(f"List sources error: {e}")

    # Test bulk register
    bulk_data = {
        "sources": [
            {
                "url": "https://www.chosun.com",
                "name": "조선일보",
                "category": "news",
                "region": "KR"
            },
            {
                "url": "https://www.hani.co.kr",
                "name": "한겨레",
                "category": "news",
                "region": "KR"
            }
        ]
    }

    try:
        bulk_result = await bulk_register_sources(bulk_data)
        print(f"Bulk registration: {bulk_result}")
    except Exception as e:
        print(f"Bulk registration error: {e}")

    # Test source validation
    validation_data = {
        "url": "https://www.nps.or.kr"
    }

    try:
        validation_result = await validate_source(validation_data)
        print(f"Validation result: {validation_result}")
    except Exception as e:
        print(f"Validation error: {e}")

    # Test discovery
    discovery_data = {
        "seed_urls": ["https://news.naver.com"],
        "max_depth": 2
    }

    try:
        discovery_result = await discover_sources(discovery_data)
        print(f"Discovery result: {discovery_result}")
    except Exception as e:
        print(f"Discovery error: {e}")

    # Test crawlable sources
    try:
        crawlable_result = await get_crawlable_sources(10)
        print(f"Crawlable sources: {crawlable_result}")
    except Exception as e:
        print(f"Crawlable sources error: {e}")

    # Test report generation
    report_data = {
        "period_days": 7
    }

    try:
        report_result = await generate_source_report(report_data)
        print(f"Report generated: {report_result}")
    except Exception as e:
        print(f"Report generation error: {e}")

    print("API tests completed")

if __name__ == "__main__":
    asyncio.run(test_api())

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
from app.config import settings

router = APIRouter()

async def proxy_request(request: Request, path: str = ""):
    """
    Proxy requests to the Collector Service
    """
    # Remove the /api/v1/collector prefix from the path
    target_path = path if path else ""
    
    # Build the target URL
    target_url = f"{settings.COLLECTOR_SERVICE_URL}/{target_path}"
    
    # Get the request method and prepare headers
    method = request.method
    headers = dict(request.headers)
    
    # Remove host header to avoid conflicts
    headers.pop("host", None)
    
    try:
        async with httpx.AsyncClient(timeout=settings.DEFAULT_TIMEOUT) as client:
            # Handle different HTTP methods
            if method == "GET":
                response = await client.get(
                    target_url,
                    headers=headers,
                    params=request.query_params
                )
            elif method == "POST":
                body = await request.body()
                response = await client.post(
                    target_url,
                    headers=headers,
                    params=request.query_params,
                    content=body
                )
            elif method == "PUT":
                body = await request.body()
                response = await client.put(
                    target_url,
                    headers=headers,
                    params=request.query_params,
                    content=body
                )
            elif method == "DELETE":
                response = await client.delete(
                    target_url,
                    headers=headers,
                    params=request.query_params
                )
            elif method == "PATCH":
                body = await request.body()
                response = await client.patch(
                    target_url,
                    headers=headers,
                    params=request.query_params,
                    content=body
                )
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            # Return the response from the target service
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Collector service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Collector service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Collector Service Endpoints

@router.get("/health")
async def health_check(request: Request):
    """Health check for Collector Service"""
    return await proxy_request(request, "health")

@router.get("/")
async def root(request: Request):
    """Root endpoint for Collector Service"""
    return await proxy_request(request, "")

# Data Source Management Routes
@router.post("/sources")
async def create_source(request: Request):
    """Create a new data source"""
    return await proxy_request(request, "sources")

@router.get("/sources")
async def list_sources(request: Request):
    """List all data sources"""
    return await proxy_request(request, "sources")

@router.get("/sources/{source_id}")
async def get_source(source_id: str, request: Request):
    """Get specific data source"""
    return await proxy_request(request, f"sources/{source_id}")

@router.put("/sources/{source_id}")
async def update_source(source_id: str, request: Request):
    """Update a data source"""
    return await proxy_request(request, f"sources/{source_id}")

@router.delete("/sources/{source_id}")
async def delete_source(source_id: str, request: Request):
    """Delete a data source"""
    return await proxy_request(request, f"sources/{source_id}")

@router.post("/sources/{source_id}/test")
async def test_source(source_id: str, request: Request):
    """Test a data source connection"""
    return await proxy_request(request, f"sources/{source_id}/test")

@router.post("/sources/{source_id}/enable")
async def enable_source(source_id: str, request: Request):
    """Enable a data source"""
    return await proxy_request(request, f"sources/{source_id}/enable")

@router.post("/sources/{source_id}/disable")
async def disable_source(source_id: str, request: Request):
    """Disable a data source"""
    return await proxy_request(request, f"sources/{source_id}/disable")

# Collection Management Routes
@router.post("/collections/start")
async def start_collection(request: Request):
    """Start data collection"""
    return await proxy_request(request, "collections/start")

@router.post("/collections/stop")
async def stop_collection(request: Request):
    """Stop data collection"""
    return await proxy_request(request, "collections/stop")

@router.get("/collections/status")
async def get_collection_status(request: Request):
    """Get collection status"""
    return await proxy_request(request, "collections/status")

@router.get("/collections/stats")
async def get_collection_stats(request: Request):
    """Get collection statistics"""
    return await proxy_request(request, "collections/stats")

@router.get("/collections/history")
async def get_collection_history(request: Request):
    """Get collection history"""
    return await proxy_request(request, "collections/history")

@router.get("/collections/jobs")
async def list_collection_jobs(request: Request):
    """List collection jobs"""
    return await proxy_request(request, "collections/jobs")

@router.get("/collections/jobs/{job_id}")
async def get_collection_job(job_id: str, request: Request):
    """Get specific collection job"""
    return await proxy_request(request, f"collections/jobs/{job_id}")

@router.delete("/collections/jobs/{job_id}")
async def cancel_collection_job(job_id: str, request: Request):
    """Cancel a collection job"""
    return await proxy_request(request, f"collections/jobs/{job_id}")

# Data Feed Management Routes
@router.get("/feeds")
async def list_feeds(request: Request):
    """List all data feeds"""
    return await proxy_request(request, "feeds")

@router.get("/feeds/{feed_id}")
async def get_feed(feed_id: str, request: Request):
    """Get specific data feed"""
    return await proxy_request(request, f"feeds/{feed_id}")

@router.get("/feeds/{feed_id}/data")
async def get_feed_data(feed_id: str, request: Request):
    """Get data from specific feed"""
    return await proxy_request(request, f"feeds/{feed_id}/data")

@router.post("/feeds/{feed_id}/refresh")
async def refresh_feed(feed_id: str, request: Request):
    """Refresh a data feed"""
    return await proxy_request(request, f"feeds/{feed_id}/refresh")

# Catch-all route for any other endpoints
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path: str, request: Request):
    """Catch-all route for any other Collector Service endpoints"""
    return await proxy_request(request, path)
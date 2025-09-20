from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
from app.config import settings

router = APIRouter()

async def proxy_request(request: Request, path: str = ""):
    """
    Proxy requests to the Analysis Service
    """
    # Remove the /api/v1/analysis prefix from the path
    target_path = path if path else ""
    
    # Build the target URL
    target_url = f"{settings.ANALYSIS_SERVICE_URL}/{target_path}"
    
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
        raise HTTPException(status_code=504, detail="Analysis service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Analysis service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Analysis Service Endpoints

@router.get("/health")
async def health_check(request: Request):
    """Health check for Analysis Service"""
    return await proxy_request(request, "health")

@router.get("/")
async def root(request: Request):
    """Root endpoint for Analysis Service"""
    return await proxy_request(request, "")

# Sentiment Analysis Routes
@router.post("/sentiment/analyze")
async def analyze_sentiment(request: Request):
    """Analyze sentiment of text"""
    return await proxy_request(request, "sentiment/analyze")

@router.get("/sentiment/history")
async def get_sentiment_history(request: Request):
    """Get sentiment analysis history"""
    return await proxy_request(request, "sentiment/history")

@router.get("/sentiment/stats")
async def get_sentiment_stats(request: Request):
    """Get sentiment statistics"""
    return await proxy_request(request, "sentiment/stats")

# Trend Analysis Routes
@router.post("/trends/analyze")
async def analyze_trends(request: Request):
    """Analyze trends in data"""
    return await proxy_request(request, "trends/analyze")

@router.get("/trends/history")
async def get_trend_history(request: Request):
    """Get trend analysis history"""
    return await proxy_request(request, "trends/history")

@router.get("/trends/current")
async def get_current_trends(request: Request):
    """Get current trending topics"""
    return await proxy_request(request, "trends/current")

# Report Routes
@router.post("/reports/generate")
async def generate_report(request: Request):
    """Generate analysis report"""
    return await proxy_request(request, "reports/generate")

@router.get("/reports/{report_id}")
async def get_report(report_id: str, request: Request):
    """Get specific report"""
    return await proxy_request(request, f"reports/{report_id}")

@router.get("/reports")
async def list_reports(request: Request):
    """List all reports"""
    return await proxy_request(request, "reports")

@router.delete("/reports/{report_id}")
async def delete_report(report_id: str, request: Request):
    """Delete a report"""
    return await proxy_request(request, f"reports/{report_id}")

# ML Model Routes
@router.post("/models/train")
async def train_model(request: Request):
    """Train ML model"""
    return await proxy_request(request, "models/train")

@router.get("/models/status")
async def get_model_status(request: Request):
    """Get model training status"""
    return await proxy_request(request, "models/status")

@router.get("/models")
async def list_models(request: Request):
    """List available models"""
    return await proxy_request(request, "models")

@router.post("/models/{model_id}/predict")
async def predict_with_model(model_id: str, request: Request):
    """Make prediction with specific model"""
    return await proxy_request(request, f"models/{model_id}/predict")

# Catch-all route for any other endpoints
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path: str, request: Request):
    """Catch-all route for any other Analysis Service endpoints"""
    return await proxy_request(request, path)
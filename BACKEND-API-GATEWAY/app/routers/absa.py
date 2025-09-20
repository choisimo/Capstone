from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
from app.config import settings

router = APIRouter()

async def proxy_request(request: Request, path: str = ""):
    """
    Proxy requests to the ABSA Service
    """
    # Remove the /api/v1/absa prefix from the path
    target_path = path if path else ""
    
    # Build the target URL
    target_url = f"{settings.ABSA_SERVICE_URL}/{target_path}"
    
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
        raise HTTPException(status_code=504, detail="ABSA service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="ABSA service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ABSA Service Endpoints

@router.get("/health")
async def health_check(request: Request):
    """Health check for ABSA Service"""
    return await proxy_request(request, "health")

@router.get("/")
async def root(request: Request):
    """Root endpoint for ABSA Service"""
    return await proxy_request(request, "")

# Aspect-Based Sentiment Analysis Routes
@router.post("/aspects/extract")
async def extract_aspects(request: Request):
    """Extract aspects from text"""
    return await proxy_request(request, "aspects/extract")

@router.post("/aspects/analyze")
async def analyze_aspects(request: Request):
    """Analyze sentiment for specific aspects"""
    return await proxy_request(request, "aspects/analyze")

@router.get("/aspects")
async def list_aspects(request: Request):
    """List all discovered aspects"""
    return await proxy_request(request, "aspects")

@router.get("/aspects/{aspect_id}")
async def get_aspect(aspect_id: str, request: Request):
    """Get specific aspect details"""
    return await proxy_request(request, f"aspects/{aspect_id}")

@router.get("/aspects/{aspect_id}/sentiment")
async def get_aspect_sentiment(aspect_id: str, request: Request):
    """Get sentiment analysis for specific aspect"""
    return await proxy_request(request, f"aspects/{aspect_id}/sentiment")

# Analysis Routes
@router.post("/analysis/full")
async def full_analysis(request: Request):
    """Perform complete ABSA analysis"""
    return await proxy_request(request, "analysis/full")

@router.post("/analysis/batch")
async def batch_analysis(request: Request):
    """Perform batch ABSA analysis"""
    return await proxy_request(request, "analysis/batch")

@router.get("/analysis/history")
async def get_analysis_history(request: Request):
    """Get ABSA analysis history"""
    return await proxy_request(request, "analysis/history")

@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str, request: Request):
    """Get specific analysis results"""
    return await proxy_request(request, f"analysis/{analysis_id}")

@router.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str, request: Request):
    """Delete an analysis"""
    return await proxy_request(request, f"analysis/{analysis_id}")

# Model Management Routes
@router.get("/models")
async def list_models(request: Request):
    """List available ABSA models"""
    return await proxy_request(request, "models")

@router.get("/models/{model_id}")
async def get_model(model_id: str, request: Request):
    """Get specific model details"""
    return await proxy_request(request, f"models/{model_id}")

@router.post("/models/{model_id}/train")
async def train_model(model_id: str, request: Request):
    """Train ABSA model"""
    return await proxy_request(request, f"models/{model_id}/train")

@router.get("/models/{model_id}/status")
async def get_model_status(model_id: str, request: Request):
    """Get model training status"""
    return await proxy_request(request, f"models/{model_id}/status")

@router.post("/models/{model_id}/evaluate")
async def evaluate_model(model_id: str, request: Request):
    """Evaluate model performance"""
    return await proxy_request(request, f"models/{model_id}/evaluate")

# Catch-all route for any other endpoints
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path: str, request: Request):
    """Catch-all route for any other ABSA Service endpoints"""
    return await proxy_request(request, path)
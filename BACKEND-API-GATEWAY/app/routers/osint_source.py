"""
OSINT Source Service 프록시 라우터

OSINT 소스 서비스로의 요청을 프록시하는 라우터 모듈입니다.
OSINT 데이터 소스 관리, 수집, 처리 등의 요청을 처리합니다.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
from app.config import settings

# 라우터 인스턴스 생성
router = APIRouter()
sources_alias_router = APIRouter()

SOURCES_BASE_PATH = "api/v1/sources"

async def proxy_request(request: Request, path: str = ""):
    """
    OSINT Source Service로 요청을 프록시하는 핵심 함수
    
    들어온 요청을 그대로 OSINT Source Service로 전달하고,
    응답을 클라이언트에게 반환합니다.
    """
    # Backend expects /api/v1 for most OSINT source endpoints
    if not path:
        target_path = ""
    elif path == "health":
        target_path = "health"
    elif path.startswith("api/"):
        target_path = path
    else:
        target_path = f"api/v1/{path}"
    target_url = f"{settings.OSINT_SOURCE_SERVICE_URL}/{target_path}"
    
    method = request.method
    headers = dict(request.headers)
    headers.pop("host", None)
    
    try:
        async with httpx.AsyncClient(timeout=settings.DEFAULT_TIMEOUT) as client:
            if method == "GET":
                response = await client.get(target_url, headers=headers, params=request.query_params)
            elif method == "POST":
                body = await request.body()
                response = await client.post(target_url, headers=headers, params=request.query_params, content=body)
            elif method == "PUT":
                body = await request.body()
                response = await client.put(target_url, headers=headers, params=request.query_params, content=body)
            elif method == "DELETE":
                response = await client.delete(target_url, headers=headers, params=request.query_params)
            elif method == "PATCH":
                body = await request.body()
                response = await client.patch(target_url, headers=headers, params=request.query_params, content=body)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="OSINT Source service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="OSINT Source service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def health_check(request: Request):
    """OSINT Source Service 헬스 체크"""
    return await proxy_request(request, "health")

@router.get("/")
async def root(request: Request):
    """OSINT Source Service 루트 엔드포인트"""
    return await proxy_request(request, "")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path: str, request: Request):
    """Catch-all 라우트"""
    return await proxy_request(request, path)


@sources_alias_router.api_route("/sources", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def sources_root_alias(request: Request):
    """/api/v1/osint/sources 표준 경로 alias"""
    return await proxy_request(request, SOURCES_BASE_PATH)


@sources_alias_router.api_route("/sources/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def sources_alias_catch_all(path: str, request: Request):
    """/api/v1/osint/sources/* 경로 alias"""
    forward_path = f"{SOURCES_BASE_PATH}/{path}" if path else SOURCES_BASE_PATH
    return await proxy_request(request, forward_path)
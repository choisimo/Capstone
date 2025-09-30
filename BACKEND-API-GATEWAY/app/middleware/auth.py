"""
JWT Authentication Middleware

JWT 기반 인증 미들웨어:
- JWT 토큰 검증
- RBAC 역할 확인
- 권한별 엔드포인트 접근 제어
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import jwt
import logging
from enum import Enum

logger = logging.getLogger(__name__)

# JWT 설정 (환경 변수에서 로드해야 함)
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: 환경 변수로 변경
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Role(str, Enum):
    """사용자 역할"""
    ADMIN = "admin"  # 관리자
    ANALYST = "analyst"  # 분석가
    VIEWER = "viewer"  # 조회자
    SYSTEM = "system"  # 시스템


class Permission(str, Enum):
    """권한"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


# 역할별 권한 매핑
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.ADMIN: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN],
    Role.ANALYST: [Permission.READ, Permission.WRITE],
    Role.VIEWER: [Permission.READ],
    Role.SYSTEM: [Permission.READ, Permission.WRITE, Permission.DELETE]
}

# 엔드포인트별 필요 권한
ENDPOINT_PERMISSIONS: Dict[str, List[Permission]] = {
    "GET": [Permission.READ],
    "POST": [Permission.WRITE],
    "PUT": [Permission.WRITE],
    "PATCH": [Permission.WRITE],
    "DELETE": [Permission.DELETE]
}

# 공개 엔드포인트 (인증 불필요)
PUBLIC_ENDPOINTS = [
    "/health",
    "/docs",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register"
]


class JWTBearer(HTTPBearer):
    """JWT Bearer 인증 스킴"""
    
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme."
                )
            
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token or expired token."
                )
            
            return credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code."
            )
    
    def verify_jwt(self, jwtoken: str) -> bool:
        """JWT 토큰 검증"""
        is_token_valid: bool = False
        
        try:
            payload = decode_jwt(jwtoken)
            is_token_valid = payload is not None
        except Exception as e:
            logger.error(f"JWT verification failed: {e}")
            is_token_valid = False
        
        return is_token_valid


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 만료 시간
        
    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    JWT 토큰 디코딩
    
    Args:
        token: JWT 토큰 문자열
        
    Returns:
        디코딩된 페이로드 또는 None
    """
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 만료 확인
        if decoded_token["exp"] >= datetime.utcnow().timestamp():
            return decoded_token
        else:
            return None
            
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        return None


async def auth_middleware(request: Request, call_next):
    """
    인증 미들웨어
    
    JWT 토큰을 검증하고 사용자 정보를 request.state에 저장
    """
    path = request.url.path
    
    # 공개 엔드포인트 확인
    if any(path.startswith(endpoint) for endpoint in PUBLIC_ENDPOINTS):
        return await call_next(request)
    
    # Authorization 헤더 확인
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    
    # 토큰 검증 및 디코딩
    payload = decode_jwt(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 사용자 정보 저장
    request.state.user = {
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "role": payload.get("role", Role.VIEWER),
        "permissions": ROLE_PERMISSIONS.get(Role(payload.get("role", Role.VIEWER)), [])
    }
    
    logger.info(f"Authenticated user: {request.state.user['username']} ({request.state.user['role']})")
    
    response = await call_next(request)
    return response


async def rbac_middleware(request: Request, call_next):
    """
    RBAC (Role-Based Access Control) 미들웨어
    
    사용자 역할에 따라 엔드포인트 접근 제어
    """
    path = request.url.path
    method = request.method
    
    # 공개 엔드포인트 또는 인증되지 않은 요청은 통과
    if any(path.startswith(endpoint) for endpoint in PUBLIC_ENDPOINTS):
        return await call_next(request)
    
    if not hasattr(request.state, "user"):
        return await call_next(request)
    
    user = request.state.user
    user_permissions = user.get("permissions", [])
    
    # 필요한 권한 확인
    required_permissions = ENDPOINT_PERMISSIONS.get(method, [])
    
    # 관리자 전용 엔드포인트
    if "/admin/" in path and Permission.ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin access required."
        )
    
    # 권한 확인
    has_permission = any(perm in user_permissions for perm in required_permissions)
    
    if not has_permission:
        logger.warning(
            f"Access denied for user {user['username']}: "
            f"{method} {path} requires {required_permissions}, "
            f"but user has {user_permissions}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {required_permissions}"
        )
    
    logger.info(f"Access granted: {user['username']} - {method} {path}")
    
    response = await call_next(request)
    return response


def require_role(allowed_roles: List[Role]):
    """
    특정 역할 요구 데코레이터
    
    Usage:
        @router.get("/admin/users")
        @require_role([Role.ADMIN])
        async def get_users():
            ...
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            if not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            user_role = Role(request.state.user.get("role"))
            
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {user_role} not allowed. Required: {allowed_roles}"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def get_current_user(request: Request) -> Dict[str, Any]:
    """
    현재 인증된 사용자 정보 가져오기
    
    Usage:
        @router.get("/me")
        async def get_me(request: Request):
            user = get_current_user(request)
            return user
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return request.state.user

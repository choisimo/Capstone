"""
Security utilities: JWT parsing and RBAC dependencies.
"""
from typing import List, Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from app.config import settings

security_scheme = HTTPBearer(auto_error=False)

class Actor(BaseModel):
    sub: Optional[str] = None
    role: str = "anonymous"

async def get_current_actor(creds: HTTPAuthorizationCredentials = Depends(security_scheme)) -> Actor:
    if not settings.auth_required:
        # In non-auth mode, allow anonymous actor
        return Actor(sub=None, role="admin")  # permissive for local/dev if AUTH_REQUIRED=false
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.auth_jwt_secret, algorithms=[settings.auth_jwt_algorithm])
        sub = payload.get("sub")
        role = payload.get("role", "user")
        return Actor(sub=sub, role=role)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(allowed_roles: List[str]):
    async def _dep(actor: Actor = Depends(get_current_actor)) -> Actor:
        # If auth is not required, allow
        if not settings.auth_required:
            return actor
        if actor.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: insufficient role")
        return actor
    return _dep

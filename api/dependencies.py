"""FastAPI dependencies for auth and database access."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth import verify_token
from approv.db import DatabaseManager, db_manager
from approv.models import UserContext

security = HTTPBearer()


def get_db() -> DatabaseManager:
    return db_manager


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserContext:
    """Extract and verify JWT from Authorization header."""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return UserContext(
        user_id=int(payload["sub"]),
        username=payload["username"],
        roles=payload.get("roles", []),
    )

from typing import Optional

from fastapi import Header, HTTPException

from .config import settings


async def requireAuth(authorization: Optional[str] = Header(None)) -> str:
    if not settings.authEnabled:
        return "anonymous_user"

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    if not settings.apiAuthSecret or token != settings.apiAuthSecret:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return "authenticated_user"

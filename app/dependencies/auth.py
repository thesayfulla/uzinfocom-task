from typing import Annotated

import asyncpg
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import Settings, get_settings
from ..repositories.user import User, UserRepository
from ..services.user import UserService

bearer_scheme = HTTPBearer(description="JWT token")


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


def get_user_service(
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserService:
    return UserService(
        user_repo=UserRepository(pool),
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        access_token_expire_days=settings.ACCESS_TOKEN_EXPIRE_DAYS,
        refresh_token_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_access_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    return credentials.credentials


async def get_current_user(
    token: Annotated[str, Depends(get_access_token)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    try:
        return await service.get_current_user(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc)
        ) from exc

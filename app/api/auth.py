from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies.auth import get_current_user, get_user_service
from ..schemas.user import (
    RefreshRequest,
    RegisterResponse,
    Token,
    UserLogin,
    UserRegister,
    User,
)
from ..services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegister, service: UserService = Depends(get_user_service)
):
    try:
        user, token = await service.register(payload)
    except Exception as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    return RegisterResponse(user=User.model_validate(user), token=token)


@router.post(
    "/login", 
    response_model=Token
)
async def login(
    payload: UserLogin, service: UserService = Depends(get_user_service)
):
    try:
        token = await service.login(payload)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            str(exc)
        ) from exc

    return Token.model_validate(token)


@router.post(
    "/refresh",
    response_model=Token,
)
async def refresh(
    payload: RefreshRequest, service: UserService = Depends(get_user_service)
):
    try:
        token = await service.refresh(payload.refresh_token)
        return Token.model_validate(token)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            str(exc)
        ) from exc

@router.get("/me", response_model=User)
async def me(user: User = Depends(get_current_user)):
    return User.model_validate(user)

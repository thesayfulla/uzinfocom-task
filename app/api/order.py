from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from ..dependencies.auth import get_current_user
from ..dependencies.order import get_order_service
from ..schemas.order import Order, OrderCreate
from ..schemas.user import User
from ..services.order import (
    InsufficientStockError,
    OrderNotFoundError,
    OrderService,
    OrderStatusError,
    ProductNotFoundError,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    payload: OrderCreate,
    response: Response,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=255)
    ],
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    try:
        order, replayed = await service.create(user.id, idempotency_key, payload)
    except ProductNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InsufficientStockError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    if replayed:
        response.headers["Idempotent-Replayed"] = "true"
    return order


@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: int,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    try:
        return await service.get(user.id, order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/{order_id}/confirm", response_model=Order)
async def confirm_order(
    order_id: int,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    try:
        return await service.confirm(user.id, order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except OrderStatusError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/{order_id}/cancel", response_model=Order)
async def cancel_order(
    order_id: int,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    try:
        return await service.cancel(user.id, order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except OrderStatusError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

from datetime import timedelta
from typing import Annotated

import asyncpg
from fastapi import Depends

from ..config import Settings, get_settings
from ..repositories.order import OrderRepository
from ..repositories.product import ProductRepository
from ..services.order import OrderService
from .auth import get_pool


def build_order_service(pool: asyncpg.Pool, settings: Settings) -> OrderService:
    return OrderService(
        pool=pool,
        order_repo=OrderRepository(pool),
        product_repo=ProductRepository(pool),
        payment_timeout=timedelta(minutes=settings.PAYMENT_TIMEOUT),
    )


def get_order_service(
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> OrderService:
    return build_order_service(pool, settings)

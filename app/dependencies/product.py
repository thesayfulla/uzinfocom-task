from typing import Annotated

import asyncpg
from fastapi import Depends

from ..repositories.product import ProductRepository
from ..services.product import ProductService
from .auth import get_pool


def get_product_service(
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> ProductService:
    return ProductService(product_repo=ProductRepository(pool))

from fastapi import APIRouter, Depends, status

from ..dependencies.auth import get_current_user
from ..dependencies.product import get_product_service
from ..schemas.product import Product, ProductCreate
from ..services.product import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[Product])
async def list_products(
    service: ProductService = Depends(get_product_service),
):
    return await service.list_all()


@router.post(
    "",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
async def create_product(
    payload: ProductCreate,
    service: ProductService = Depends(get_product_service),
):
    product = await service.create(payload)
    return Product.model_validate(product)

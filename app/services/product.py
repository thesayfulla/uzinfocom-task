from ..repositories.product import ProductRepository
from ..schemas.product import Product, ProductCreate


class ProductService:
    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    async def create(self, data: ProductCreate) -> Product:
        return await self.product_repo.create(
            data.name.strip(),
            data.price,
            data.stock_quantity,
        )

    async def list_all(self) -> list[Product]:
        return await self.product_repo.list_all()

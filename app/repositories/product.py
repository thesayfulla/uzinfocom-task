from decimal import Decimal

import asyncpg

from ..schemas.product import Product


class ProductRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create(
        self, name: str, price: Decimal, stock_quantity: int
    ) -> Product:
        row = await self.pool.fetchrow(
            """
            INSERT INTO products (name, price, stock_quantity)
            VALUES ($1, $2, $3)
            RETURNING id, name, price, stock_quantity, created_at
            """,
            name,
            price,
            stock_quantity,
        )
        return Product.model_validate(dict(row))

    async def get_by_id(self, product_id: int) -> Product | None:
        row = await self.pool.fetchrow(
            """
            SELECT id, name, price, stock_quantity, created_at
            FROM products
            WHERE id = $1
            """,
            product_id,
        )
        if row is None:
            return None
        return Product.model_validate(dict(row))

    async def list_all(self) -> list[Product]:
        rows = await self.pool.fetch(
            """
            SELECT id, name, price, stock_quantity, created_at
            FROM products
            ORDER BY id
            """
        )
        return [Product.model_validate(dict(row)) for row in rows]

    async def lock_many(
        self, conn: asyncpg.Connection, product_ids: list[int]
    ) -> dict[int, Product]:
        rows = await conn.fetch(
            """
            SELECT id, name, price, stock_quantity, created_at
            FROM products
            WHERE id = ANY($1::bigint[])
            ORDER BY id
            FOR UPDATE
            """,
            product_ids,
        )
        return {row["id"]: Product.model_validate(dict(row)) for row in rows}

    async def decrease_stock(
        self, conn: asyncpg.Connection, quantities: dict[int, int]
    ) -> None:
        await conn.execute(
            """
            UPDATE products AS p
            SET stock_quantity = p.stock_quantity - t.quantity
            FROM unnest($1::bigint[], $2::int[]) AS t(id, quantity)
            WHERE p.id = t.id
            """,
            list(quantities.keys()),
            list(quantities.values()),
        )

    async def increase_stock(
        self, conn: asyncpg.Connection, quantities: dict[int, int]
    ) -> None:
        await conn.execute(
            """
            UPDATE products AS p
            SET stock_quantity = p.stock_quantity + t.quantity
            FROM unnest($1::bigint[], $2::int[]) AS t(id, quantity)
            WHERE p.id = t.id
            """,
            list(quantities.keys()),
            list(quantities.values()),
        )

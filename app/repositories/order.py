from datetime import timedelta
from decimal import Decimal

import asyncpg

from ..schemas.order import Order, OrderItem, OrderStatus


class OrderRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def claim_idempotency_key(
        self,
        conn: asyncpg.Connection,
        user_id: int,
        idempotency_key: str,
    ) -> int | None:
        return await conn.fetchval(
            """
            INSERT INTO orders (user_id, idempotency_key)
            VALUES ($1, $2)
            ON CONFLICT (user_id, idempotency_key) DO NOTHING
            RETURNING id
            """,
            user_id,
            idempotency_key,
        )

    async def get_by_idempotency_key(
        self, conn: asyncpg.Connection, user_id: int, idempotency_key: str
    ) -> Order | None:
        order_id = await conn.fetchval(
            """
            SELECT id
            FROM orders
            WHERE user_id = $1 AND idempotency_key = $2
            """,
            user_id,
            idempotency_key,
        )
        if order_id is None:
            return None
        return await self.get_by_id(conn, order_id)

    async def get_by_id(
        self, conn: asyncpg.Connection, order_id: int
    ) -> Order | None:
        order = await conn.fetchrow(
            """
            SELECT id, user_id, status, total_price, created_at
            FROM orders
            WHERE id = $1
            """,
            order_id,
        )
        if order is None:
            return None
        items = await conn.fetch(
            """
            SELECT product_id, quantity, unit_price
            FROM order_items
            WHERE order_id = $1
            ORDER BY product_id
            """,
            order_id,
        )
        return Order(
            **dict(order),
            items=[OrderItem.model_validate(dict(item)) for item in items],
        )

    async def add_items(
        self,
        conn: asyncpg.Connection,
        order_id: int,
        items: list[OrderItem],
        total_price: Decimal,
    ) -> None:
        await conn.execute(
            """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            SELECT $1, product_id, quantity, unit_price
            FROM unnest($2::bigint[], $3::int[], $4::numeric[])
                AS t(product_id, quantity, unit_price)
            """,
            order_id,
            [item.product_id for item in items],
            [item.quantity for item in items],
            [item.unit_price for item in items],
        )
        await conn.execute(
            "UPDATE orders SET total_price = $2 WHERE id = $1",
            order_id,
            total_price,
        )

    async def lock_for_user(
        self, conn: asyncpg.Connection, order_id: int, user_id: int
    ) -> asyncpg.Record | None:
        return await conn.fetchrow(
            """
            SELECT status, created_at
            FROM orders
            WHERE id = $1 AND user_id = $2
            FOR UPDATE
            """,
            order_id,
            user_id,
        )

    async def set_status(
        self, conn: asyncpg.Connection, order_id: int, status: OrderStatus
    ) -> None:
        await conn.execute(
            "UPDATE orders SET status = $2 WHERE id = $1",
            order_id,
            status,
        )

    async def cancel_expired(
        self, conn: asyncpg.Connection, older_than: timedelta, limit: int
    ) -> list[int]:
        rows = await conn.fetch(
            """
            UPDATE orders
            SET status = 'cancelled'
            WHERE id IN (
                SELECT id
                FROM orders
                WHERE status = 'pending' AND created_at < now() - $1::interval
                ORDER BY id
                LIMIT $2
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id
            """,
            older_than,
            limit,
        )
        return [row["id"] for row in rows]

    async def get_item_quantities(
        self, conn: asyncpg.Connection, order_ids: list[int]
    ) -> dict[int, int]:
        rows = await conn.fetch(
            """
            SELECT product_id, SUM(quantity)::int AS quantity
            FROM order_items
            WHERE order_id = ANY($1::bigint[])
            GROUP BY product_id
            ORDER BY product_id
            """,
            order_ids,
        )
        return {row["product_id"]: row["quantity"] for row in rows}

from datetime import datetime, timedelta, timezone

import asyncpg

from ..repositories.order import OrderRepository
from ..repositories.product import ProductRepository
from ..schemas.order import Order, OrderCreate, OrderItem, OrderStatus


class ProductNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class OrderStatusError(Exception):
    pass


class OrderService:
    def __init__(
        self,
        pool: asyncpg.Pool,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
        payment_timeout: timedelta = timedelta(minutes=15),
    ):
        self.pool = pool
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.payment_timeout = payment_timeout

    async def create(
        self, user_id: int, idempotency_key: str, data: OrderCreate
    ) -> tuple[Order, bool]:
        quantities = {
            item.product_id: item.quantity
            for item in sorted(data.items, key=lambda item: item.product_id)
        }

        async with self.pool.acquire() as conn, conn.transaction():
            order_id = await self.order_repo.claim_idempotency_key(
                conn, user_id, idempotency_key
            )
            if order_id is None:
                order = await self.order_repo.get_by_idempotency_key(
                    conn, user_id, idempotency_key
                )
                return order, True

            products = await self.product_repo.lock_many(conn, list(quantities))

            missing = [pid for pid in quantities if pid not in products]
            if missing:
                raise ProductNotFoundError(f"Products not found: {missing}")

            short = [
                pid
                for pid, quantity in quantities.items()
                if products[pid].stock_quantity < quantity
            ]
            if short:
                raise InsufficientStockError(f"Insufficient stock for products: {short}")

            await self.product_repo.decrease_stock(conn, quantities)

            items = [
                OrderItem(
                    product_id=pid,
                    quantity=quantity,
                    unit_price=products[pid].price,
                )
                for pid, quantity in quantities.items()
            ]
            total_price = sum(item.unit_price * item.quantity for item in items)
            await self.order_repo.add_items(conn, order_id, items, total_price)

            return await self.order_repo.get_by_id(conn, order_id), False

    async def get(self, user_id: int, order_id: int) -> Order:
        async with self.pool.acquire() as conn:
            order = await self.order_repo.get_by_id(conn, order_id)

        if order is None or order.user_id != user_id:
            raise OrderNotFoundError("Order not found")
        return order

    async def confirm(self, user_id: int, order_id: int) -> Order:
        async with self.pool.acquire() as conn, conn.transaction():
            order = await self.order_repo.lock_for_user(conn, order_id, user_id)
            if order is None:
                raise OrderNotFoundError("Order not found")
            if order["status"] != OrderStatus.PENDING:
                raise OrderStatusError(f"Order is already {order['status']}")

            expires_at = order["created_at"] + self.payment_timeout
            if expires_at <= datetime.now(timezone.utc):
                raise OrderStatusError("Order payment window has expired")

            await self.order_repo.set_status(conn, order_id, OrderStatus.CONFIRMED)
            return await self.order_repo.get_by_id(conn, order_id)

    async def cancel(self, user_id: int, order_id: int) -> Order:
        async with self.pool.acquire() as conn, conn.transaction():
            order = await self.order_repo.lock_for_user(conn, order_id, user_id)
            if order is None:
                raise OrderNotFoundError("Order not found")
            if order["status"] != OrderStatus.PENDING:
                raise OrderStatusError(f"Order is already {order['status']}")

            await self.order_repo.set_status(conn, order_id, OrderStatus.CANCELLED)

            quantities = await self.order_repo.get_item_quantities(conn, [order_id])
            await self.product_repo.lock_many(conn, list(quantities))
            await self.product_repo.increase_stock(conn, quantities)

            return await self.order_repo.get_by_id(conn, order_id)

    async def cancel_expired(self, limit: int = 500) -> list[int]:
        async with self.pool.acquire() as conn, conn.transaction():
            order_ids = await self.order_repo.cancel_expired(
                conn, self.payment_timeout, limit
            )
            if not order_ids:
                return []

            quantities = await self.order_repo.get_item_quantities(conn, order_ids)
            await self.product_repo.lock_many(conn, list(quantities))
            await self.product_repo.increase_stock(conn, quantities)

            return order_ids or []

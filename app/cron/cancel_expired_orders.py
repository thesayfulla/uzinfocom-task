import asyncio

from .. import db
from ..config import get_settings
from ..dependencies.order import build_order_service



async def main() -> None:
    settings = get_settings()

    pool = await db.connect()
    try:
        service = build_order_service(pool, settings)
        order_ids = await service.cancel_expired()
        print(f"Cancelled expired orders: {order_ids}")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from . import db


async def main() -> None:
    pool = await db.connect()
    try:
        await db.run_migrations(pool)
    finally:
        await db.disconnect()


if __name__ == "__main__":
    print("Running database migration")
    asyncio.run(main())
    print("Migration completed")

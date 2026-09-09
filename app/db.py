from pathlib import Path

import asyncpg

from .config import Settings


_pool: asyncpg.Pool | None = None

MIGRATION_FILE = Path(__file__).resolve().parent.parent / "migrations" / "init.sql"

async def run_migrations(pool: asyncpg.Pool) -> None:
    sql = MIGRATION_FILE.read_text()
    async with pool.acquire() as conn:
        await conn.execute(sql)

async def connect() -> asyncpg.Pool:
    global _pool
    settings = Settings()
    _pool = await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        command_timeout=10,
    )
    return _pool

async def disconnect() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

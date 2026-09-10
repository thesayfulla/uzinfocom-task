import asyncpg

from ..schemas.user import User, UserWithPassword


class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create(self, username: str, password_hash: str) -> User:
        row = await self.pool.fetchrow(
            """
            INSERT INTO users (username, password)
            VALUES ($1, $2)
            RETURNING id, username, created_at
            """,
            username,
            password_hash,
        )
        return User.model_validate(dict(row))

    async def get_by_id(self, user_id: int) -> User | None:
        row = await self.pool.fetchrow(
            "SELECT id, username, created_at FROM users WHERE id = $1",
            user_id,
        )
        if row is None:
            return None
        return User.model_validate(dict(row))

    async def get_by_username(self, username: str) -> UserWithPassword | None:
        row = await self.pool.fetchrow(
            "SELECT id, username, password, created_at FROM users WHERE username = $1",
            username,
        )
        if row is None:
            return None
        return UserWithPassword.model_validate(dict(row))

    async def exists_by_username(self, username: str) -> bool:
        return await self.pool.fetchval(
            "SELECT EXISTS (SELECT 1 FROM users WHERE username = $1)",
            username,
        )

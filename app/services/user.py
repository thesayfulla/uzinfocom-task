from datetime import datetime, timedelta, timezone

import asyncpg
import bcrypt
from jose import JWTError, jwt

from ..repositories.user import UserRepository
from ..schemas.user import Token, UserLogin, UserRegister, User


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_days: int = 1,
        refresh_token_expire_days: int = 7,
    ):
        self.user_repo = user_repo
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_days = access_token_expire_days
        self.refresh_token_expire_days = refresh_token_expire_days

    async def register(self, data: UserRegister) -> tuple[User, Token]:
        if await self.user_repo.exists_by_username(data.username):
            raise Exception("Username already exists")

        password_hash = self._hash_password(data.password)

        try:
            user = await self.user_repo.create(data.username, password_hash)
        except asyncpg.UniqueViolationError as exc:
            raise Exception("Username already exists") from exc

        return user, self._generate_tokens(user.id)

    async def login(self, data: UserLogin) -> Token:
        user = await self.user_repo.get_by_username(data.username)

        if user is None or not self._verify_password(data.password, user.password):
            raise Exception("Invalid username or password")

        return self._generate_tokens(user.id)

    async def refresh(self, refresh_token: str) -> Token:
        payload = self._decode_token(refresh_token)
        user = await self._load_user(payload)
        return self._generate_tokens(user.id)

    async def get_current_user(self, access_token: str) -> User:
        payload = self._decode_token(access_token)
        return await self._load_user(payload)

    def _generate_tokens(self, user_id: int) -> Token:
        return Token(
            access_token=self._generate_access_token(user_id),
            refresh_token=self._generate_refresh_token(user_id),
            expires_in=self.access_token_expire_days * 24 * 60 * 60,
            refresh_expires_in=self.refresh_token_expire_days * 24 * 60 * 60,
        )

    def _generate_access_token(self, user_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            days=self.access_token_expire_days
        )
        return jwt.encode(
            {
                "user_id": user_id,
                "exp": expire,
            },
            self.secret_key,
            algorithm=self.algorithm,
        )

    def _generate_refresh_token(self, user_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            days=self.refresh_token_expire_days
        )
        return jwt.encode(
            {
                "user_id": user_id,
                "exp": expire,
                "type": "refresh",
            },
            self.secret_key,
            algorithm=self.algorithm,
        )

    def _decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError as exc:
            raise Exception("Could not validate credentials") from exc

    async def _load_user(self, payload: dict) -> User:
        user_id = payload.get("user_id")
        if user_id is None:
            raise Exception("Could not validate credentials")

        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise Exception("User not found")
        return user

    @staticmethod
    def _hash_password(password: str) -> str:
        secret = password.encode("utf-8")
        return bcrypt.hashpw(secret, bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        secret = password.encode("utf-8")
        return bcrypt.checkpw(secret, password_hash.encode("utf-8"))

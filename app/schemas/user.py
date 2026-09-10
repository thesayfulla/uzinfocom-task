from datetime import datetime

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: int
    username: str
    created_at: datetime


class UserWithPassword(User):
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterResponse(BaseModel):
    user: User
    token: Token

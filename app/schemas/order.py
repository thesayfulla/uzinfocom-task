from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1, max_length=100)


class OrderItem(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal


class Order(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    total_price: Decimal
    items: list[OrderItem]
    created_at: datetime

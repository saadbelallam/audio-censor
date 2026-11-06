from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: UUID
    created_at: datetime
    email: str
    credits: int


class TokenData(BaseModel):
    access_token: str
    token_type: str

class CheckoutSessionCreate(BaseModel):
    amount: Decimal = Field(
        default=Decimal("0.5"),
        ge=Decimal("0.5"),
        decimal_places=2,
    )
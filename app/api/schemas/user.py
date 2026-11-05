from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: UUID
    created_at: datetime
    email: str


class TokenData(BaseModel):
    access_token: str
    token_type: str

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


class AudioRead(BaseModel):
    id: UUID
    created_at: datetime
    censored_file_path: str
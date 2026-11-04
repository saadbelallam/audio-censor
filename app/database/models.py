from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlmodel import DateTime, Field, SQLModel

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    __tablename__ = "user"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
    email: str
    password_hash: str

class Audio(SQLModel, table=True):
    __tablename__ = "audio"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
    file_path: str
    censored_file_path: str
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlmodel import DateTime, Field, Relationship, SQLModel

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
    audios: list["Audio"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

class Audio(SQLModel, table=True):
    __tablename__ = "audio"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
    file_path: str
    censored_file_path: str
    user_id: UUID = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="audios", sa_relationship_kwargs={"lazy": "selectin"})
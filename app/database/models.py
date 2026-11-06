from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy.dialects import postgresql
from sqlmodel import DateTime, Field, Relationship, SQLModel
from enum import Enum

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AudioStatus(Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

    
class User(SQLModel, table=True):
    __tablename__ = "user"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    propelauth_id: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
    email: str
    # password_hash: str
    credits: int = Field(default=50)

    audios: list["Audio"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

    sound_effects: list["SoundEffect"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    

class SoundEffect(SQLModel, table=True):
    __tablename__ = "sound_effect"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
    name: str
    file_path: str

    user_id: UUID = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="sound_effects", sa_relationship_kwargs={"lazy": "selectin"})




class Audio(SQLModel, table=True):
    __tablename__ = "audio"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": utc_now},
    )

    name: str
    duration: int
    file_path: str
    censored_file_path: str | None = Field(default=None)

    credits_used: int = Field(default=0)
    credits_reseverd: int = Field(default=0)

    transcription: list[dict] | None = Field(default=None, sa_column = Column(postgresql.JSONB))


    use_beep: bool = Field(default=False)
    user_list: list[str] | None = Field(default=None, sa_column = Column(postgresql.ARRAY(postgresql.TEXT)))
    sound_effect_id: UUID | None = Field(default=None, foreign_key="sound_effect.id")
    sound_effect: SoundEffect | None = Relationship(sa_relationship_kwargs={"lazy": "selectin"})


    status: AudioStatus = Field(default=AudioStatus.pending)
    user_id: UUID = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="audios", sa_relationship_kwargs={"lazy": "selectin"})
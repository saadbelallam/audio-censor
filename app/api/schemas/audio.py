from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.models import AudioStatus


class AudioRead(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    duration: int
    credits_used: int
    censored_file_path: str | None
    status: AudioStatus
    user_list: list[str] | None
    use_beep: bool
    sound_effect_id: UUID | None


class CensorOptions(BaseModel):
    user_list: list[str] | None = Field(default=None)
    use_beep: bool = Field(default=False)
    sound_effect_id: UUID | None = Field(default=None)


class SubtitleOptions(BaseModel):
    symbol: str = Field(default="*", min_length=1)
    visible_chars: int = Field(
        default=1,
        description="Number of characters to remain visible in the censored word.",
    )

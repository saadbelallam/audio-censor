from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SoundEffectRead(BaseModel):
    id: UUID
    created_at: datetime
    name: str

from uuid import uuid4

from fastapi import UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.audio_file import AudioFileUpload
from app.database.models import SoundEffect, User
from app.object_storage import storage

class SoundEffectService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_sound_effect(
        self,
        audio_file: AudioFileUpload,
        user: User,
    ) -> SoundEffect:
        
        file_key = f"users/{user.id}/sound_effects/{uuid4()}.{audio_file.file_extension}"
        storage.upload_file(
            audio_file.file.file,
            key=file_key, 
            content_type=audio_file.file.content_type
        )

        sound_effect = SoundEffect(
            name=audio_file.sanitized_filename,
            file_path=file_key,
            user_id=user.id,
        )
        self.session.add(sound_effect)
        await self.session.commit()
        await self.session.refresh(sound_effect)
        return sound_effect

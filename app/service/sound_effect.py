from fastapi import UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.models import SoundEffect, User
from app.utils import save_file


class SoundEffectService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_sound_effect(
        self,
        file: UploadFile,
        user: User,
    ) -> SoundEffect:
        save_file(file)
        sound_effect = SoundEffect(
            name=file.filename.split(".")[0],
            file_path=file.filename,
            user_id=user.id,
        )
        self.session.add(sound_effect)
        await self.session.commit()
        await self.session.refresh(sound_effect)
        return sound_effect

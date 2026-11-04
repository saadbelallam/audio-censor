from fastapi import UploadFile
from sqlmodel import UUID
from sqlmodel.ext.asyncio.session import AsyncSession

from app.worker.audio_censor import AudioCensor
from app.database.models import Audio, User
from app.utils import save_file
from app.worker.tasks import censor_audio_task


class AudioService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.ac = AudioCensor()

    async def get_audio(self, id: UUID) -> Audio | None:
        return await self.session.get(Audio, id)
    
    async def add_audio(self, file: UploadFile, user: User) -> Audio:
        save_file(file)
        
        audio = Audio(file_path=file.filename, user_id=user.id)
        self.session.add(audio)
        await self.session.commit()
        await self.session.refresh(audio)

        censor_audio_task.delay(str(audio.id))  # Trigger the Celery task to process the audio
        
        
        return audio
        
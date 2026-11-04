from fastapi import UploadFile
from sqlmodel import UUID
from sqlmodel.ext.asyncio.session import AsyncSession

from app.audio_censor import AudioCensor
from app.database.models import Audio
from app.utils import get_file_path, save_file


class AudioService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.ac = AudioCensor()

    async def get_audio(self, id: UUID) -> Audio | None:
        return await self.session.get(Audio, id)
    
    async def add_audio(self, file: UploadFile) -> Audio:
        file_path = save_file(file)
        output_path = get_file_path(f"censored_{file.filename}")
        
        audio = Audio(file_path=file.filename, censored_file_path=f"censored_{file.filename}")
        self.session.add(audio)
        await self.session.commit()
        await self.session.refresh(audio)
        
        words = self.ac.transcribe_audio(file_path)
        self.ac.mute_audio(
            input_path=file_path,
            output_path=output_path,
            word_segments=self.ac.detect_profanity(words),
        )
        return audio
        
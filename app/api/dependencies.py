from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.session import get_session
from app.service.audio import AudioService

#dependency chaining
def get_audio_service(
    session: AsyncSession = Depends(get_session),
) -> AudioService:
    return AudioService(session)

AudioServiceDep = Annotated[AudioService, Depends(get_audio_service)]
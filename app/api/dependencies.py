from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.session import get_session
from app.service.audio import AudioService
from app.service.user import UserService


SessionDep = Annotated[AsyncSession, Depends(get_session)]

#dependency chaining
def get_audio_service(session: SessionDep) -> AudioService:
    return AudioService(session)

AudioServiceDep = Annotated[AudioService, Depends(get_audio_service)]


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
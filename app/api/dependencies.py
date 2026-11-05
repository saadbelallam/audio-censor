from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database.session import get_session
from app.database.models import User
from app.service.audio import AudioService
from app.service.sound_effect import SoundEffectService
from app.service.user import UserService


ouath2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

SessionDep = Annotated[AsyncSession, Depends(get_session)]

#dependency chaining
def get_audio_service(session: SessionDep) -> AudioService:
    return AudioService(session)



def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


async def get_current_user(
    service: UserService = Depends(get_user_service),
    token: str = Depends(ouath2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise credentials_exception

    user = await service.get_user(user_id)
    if user is None:
        raise credentials_exception

    return user

AudioServiceDep = Annotated[AudioService, Depends(get_audio_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
UserDep = Annotated[User, Depends(get_current_user)]


def get_sound_effect_service(session: SessionDep) -> SoundEffectService:
    return SoundEffectService(session)


SoundEffectServiceDep = Annotated[
    SoundEffectService,
    Depends(get_sound_effect_service),
]
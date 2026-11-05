from fastapi import APIRouter, UploadFile

from app.api.dependencies import SoundEffectServiceDep, UserDep
from app.api.schemas.sound_effect import SoundEffectRead



router = APIRouter(prefix="/sfx", tags=["Sound Effects"])


@router.post("/", response_model=SoundEffectRead)
async def add_sound_effect(
    file: UploadFile,
    user: UserDep,
    service: SoundEffectServiceDep,
) -> SoundEffectRead:
    return await service.add_sound_effect(file, user)


@router.get("/", response_model=list[SoundEffectRead])
async def get_all_sound_effects(user: UserDep) -> list[SoundEffectRead]:
    return user.sound_effects

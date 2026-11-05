from fastapi import APIRouter

from app.api.routers import audio_router, sound_effect_router, user_router


master_router = APIRouter()
master_router.include_router(user_router)
master_router.include_router(audio_router)
master_router.include_router(sound_effect_router)

# Backwards-compatible alias for existing imports.
router = master_router

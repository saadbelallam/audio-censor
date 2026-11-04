from fastapi import APIRouter, HTTPException, UploadFile, status
from uuid import UUID

from app.api.dependencies import AudioServiceDep, UserServiceDep
from app.api.schemas import AudioRead, UserCreate, UserRead


router = APIRouter()

@router.post("/signup", response_model=UserRead)
async def register_user(user: UserCreate, service: UserServiceDep) -> UserRead:
    created_user = await service.add_user(user)
    return created_user

@router.get("/audio/{id}", response_model=AudioRead)
async def read_audio(id: UUID, service: AudioServiceDep):
    audio = await service.get_audio(id)
    if not audio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio not found")
    
    return audio

@router.post("/audio", response_model=AudioRead)
async def submit_audio(audio_file: UploadFile, service: AudioServiceDep):
    audio = await service.add_audio(audio_file)
    
    return audio
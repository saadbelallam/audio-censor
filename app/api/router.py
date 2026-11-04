from fastapi import APIRouter, HTTPException, UploadFile
from uuid import UUID

from app.api.dependencies import AudioServiceDep
from app.api.schemas import AudioRead


router = APIRouter()

@router.get("/audio/{id}", response_model=AudioRead)
async def read_audio(id: UUID, service: AudioServiceDep):
    audio = await service.get_audio(id)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    return audio

@router.post("/audio", response_model=AudioRead)
async def submit_audio(audio_file: UploadFile, service: AudioServiceDep):
    audio = await service.add_audio(audio_file)
    
    return audio
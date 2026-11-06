from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import Json

from app.api.dependencies import AudioServiceDep, UserDep
from app.api.audio_file import AudioFileUpload
from app.api.schemas.audio import AudioRead, CensorOptions, SubtitleOptions
from app.api.schemas.user import UserRead
from app.object_storage import storage
from app.utils import get_file_path


router = APIRouter(prefix="/audio", tags=["Audio"])


@router.get("/", response_model=list[AudioRead])
async def read_all_audio(service: AudioServiceDep, user: UserDep):
    return user.audios



@router.get("/{id}", response_model=AudioRead)
async def read_audio(id: UUID, service: AudioServiceDep, user: UserDep):
    audio = await service.get_audio(id)
    if not audio or audio.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found",
        )


    return audio


@router.post("/", response_model=AudioRead)
async def submit_audio(
    audio_file: AudioFileUpload,
    service: AudioServiceDep,
    user: UserDep,
    options: Annotated[Json[CensorOptions], Form()] = None,
):
    
    return await service.add_audio(audio_file, user, options)



@router.patch("/{id}", response_model=AudioRead)
async def update_audio(
    id: UUID,
    options: CensorOptions,
    service: AudioServiceDep,
    user: UserDep,
) -> AudioRead:
    try:
        audio = await service.update_audio(id, options, user)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    if audio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found",
        )
    return audio



@router.post("/{id}/subtitle")
async def download_subtitle(
    id: UUID,
    options: SubtitleOptions,
    service: AudioServiceDep,
    user: UserDep,
):
    subtitle = await service.get_subtitle(id, options, user)
    if subtitle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio or transcription not found",
        )

    return PlainTextResponse(subtitle, media_type="application/x-subrip")

@router.get("/{id}/download")
async def download_audio(
    id: UUID,
    service: AudioServiceDep,
    user: UserDep,
):
    audio_file = await service.get_audio(id)
    if audio_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found",
        )

    url = storage.get_file_url(audio_file.censored_file_path)
    return {"file_url": url}
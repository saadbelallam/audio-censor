from pathlib import Path
from typing import Annotated

from dataclasses import dataclass
from fastapi import Depends, File, HTTPException, UploadFile, status
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

from app.utils import slugify


ALLOWED_AUDIO_EXTENSIONS = frozenset({"aac", "flac", "m4a", "mp3", "ogg", "wav", "webm"})

@dataclass
class AudioFileUpload:
    file: UploadFile
    duration: int
    sanitized_filename: str
    file_extension: str


def get_audio_file(file: UploadFile = File(...)) -> AudioFileUpload:
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The uploaded file must be an audio file",
        )

    extension = Path(file.filename or "").suffix.lower().removeprefix(".")
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The uploaded file has an unsupported audio extension",
        )

    try:
        audio = AudioSegment.from_file(file.file, format=extension)
    except (CouldntDecodeError, OSError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is not a valid audio file",
        ) from error
    finally:
        file.file.seek(0)

    return AudioFileUpload(
        file=file,
        duration=int(audio.duration_seconds),
        sanitized_filename=slugify(Path(file.filename or "unknown").name),
        file_extension=extension
    )

AudioFileUpload = Annotated[AudioFileUpload, Depends(get_audio_file)]
from pathlib import Path
from typing import Annotated

from dataclasses import dataclass
from fastapi import Depends, File, UploadFile
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

from app.utils import slugify
from app.core.exceptions import (
    AudioDurationTooLong,
    AudioFileTooLarge,
    InvalidAudioFile,
    UndecodableAudioFile,
)


ALLOWED_AUDIO_EXTENSIONS = frozenset({"aac", "flac", "m4a", "mp3", "ogg", "wav", "webm"})
MAX_AUDIO_FILE_SIZE = 100 * 1024 * 1024
MAX_AUDIO_DURATION_SECONDS = 120

@dataclass
class AudioFileUpload:
    file: UploadFile
    duration: int
    sanitized_filename: str
    file_extension: str


class AudioFileValidator:
    def __init__(self, max_size: int, max_audio_duration_seconds: int):
        if max_size <= 0:
            raise ValueError("max_size must be greater than zero")
        if max_audio_duration_seconds <= 0:
            raise ValueError("max_audio_duration_seconds must be greater than zero")
        self.max_size = max_size
        self.max_audio_duration_seconds = max_audio_duration_seconds

    def __call__(self, file: UploadFile = File(...)) -> AudioFileUpload:
        return self.validate(file)

    def validate(self, file: UploadFile) -> AudioFileUpload:
        file_size = file.size
        if file_size is None:
            current_position = file.file.tell()
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(current_position)

        if file_size > self.max_size:
            raise AudioFileTooLarge(self.max_size // (1024 * 1024))

        if not file.content_type or not file.content_type.startswith("audio/"):
            raise InvalidAudioFile()

        extension = Path(file.filename or "").suffix.lower().removeprefix(".")
        if extension not in ALLOWED_AUDIO_EXTENSIONS:
            raise InvalidAudioFile()

        try:
            audio = AudioSegment.from_file(file.file, format=extension)
        except (CouldntDecodeError, OSError, ValueError) as error:
            raise UndecodableAudioFile() from error
        finally:
            file.file.seek(0)

        if audio.duration_seconds > self.max_audio_duration_seconds:
            raise AudioDurationTooLong(self.max_audio_duration_seconds)

        return AudioFileUpload(
            file=file,
            duration=int(audio.duration_seconds),
            sanitized_filename=slugify(Path(file.filename or "unknown").name),
            file_extension=extension
        )


get_audio_file = AudioFileValidator(
    max_size=MAX_AUDIO_FILE_SIZE,
    max_audio_duration_seconds=MAX_AUDIO_DURATION_SECONDS,
)

AudioFileDep = Annotated[AudioFileUpload, Depends(get_audio_file)]

SoundEffectFileDep = Annotated[
    AudioFileUpload,
    Depends(AudioFileValidator(max_size=10 * 1024 * 1024, max_audio_duration_seconds=60))
    ]
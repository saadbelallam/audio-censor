import random
from uuid import uuid4

from fastapi import HTTPException, status
from sqlmodel import UUID
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.audio_file import AudioFileUpload
from app.service.user import UserService
from app.worker.audio_censor import AudioCensor
from app.database.models import Audio, SoundEffect, User, AudioStatus
from app.api.schemas.audio import CensorOptions, SubtitleOptions
from app.object_storage import storage
from celery import chain
from pydub import AudioSegment


from app.worker.tasks import (
    detect_profanity_task,
    render_audio_task,
    transcribe_audio_task,
)


class AudioService:
    def __init__(self, session: AsyncSession, user_service: UserService):
        self.session = session
        self.ac = AudioCensor()
        self.user_service = user_service

    async def get_audio(self, id: UUID) -> Audio | None:
        return await self.session.get(Audio, id)
    
    async def add_audio(
        self,
        audio_file: AudioFileUpload,
        user: User,
        options: CensorOptions | None = None
        ) -> Audio:

        duration = audio_file.duration
        required_credits = duration * 3
        await self.user_service.deduct_credits(user, required_credits)

        # Save the uploaded file to object storage
        file_key = f"users/{user.id}/audios/{uuid4()}.{audio_file.file_extension}"

        storage.upload_file(
            audio_file.file.file,
            key= file_key,
            content_type= audio_file.file.content_type,
        )
        
        audio = Audio(
            name=audio_file.sanitized_filename,
            duration=duration,
            file_path=file_key,
            credits_used=required_credits,
            user_id=user.id,
            user_list=options.user_list if options else None,
            use_beep=options.use_beep if options else None,
            sound_effect_id=options.sound_effect_id if options else None
            )
        self.session.add(audio)
        await self.session.commit()
        await self.session.refresh(audio)

        audio_id = str(audio.id)
        chain(
            transcribe_audio_task.si(audio_id),
            detect_profanity_task.si(audio_id),
            render_audio_task.si(audio_id),
        ).apply_async()
        
        
        return audio

    async def update_audio(
        self,
        audio_id: UUID,
        options: CensorOptions,
        user: User,
    ) -> Audio | None:
        audio = await self.session.get(Audio, audio_id)
        if audio is None or audio.user_id != user.id:
            return None

        if audio.status == AudioStatus.processing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Audio is currently being processed. Please wait until processing is complete.",
            )

        
        user_list_changed = audio.user_list != options.user_list

        if (
            not user_list_changed
            and audio.use_beep == options.use_beep
            and audio.sound_effect_id == options.sound_effect_id
        ):
            return audio #no changes detected, return the existing audio object

        required_credits = audio.duration * (2 if user_list_changed else 1)
        await self.user_service.deduct_credits(user, required_credits)
        audio.credits_reseverd += required_credits

        if options.sound_effect_id is not None:
            sound_effect = await self.session.get(SoundEffect, options.sound_effect_id)
            if sound_effect is None or sound_effect.user_id != user.id:
                raise ValueError("Sound effect not found")

        audio.user_list = options.user_list
        audio.use_beep = options.use_beep
        audio.sound_effect_id = options.sound_effect_id
        
        self.session.add(audio)
        await self.session.commit()
        await self.session.refresh(audio)

        audio_id_value = str(audio.id)
        if user_list_changed:
            chain(
                detect_profanity_task.si(audio_id_value),
                render_audio_task.si(audio_id_value),
            ).apply_async()
        else:
            render_audio_task.delay(audio_id_value)

        return audio

    async def get_subtitle(
        self,
        audio_id: UUID,
        options: SubtitleOptions,
        user: User,
    ) -> str | None:
        audio = await self.session.get(Audio, audio_id)
        if audio is None or audio.user_id != user.id:
            return None
        if audio.transcription is None:
            return None

        cues: list[str] = []
        for cue_number, word_segment in enumerate(audio.transcription, start=1):
            word = str(word_segment["word"])
            if word_segment.get("flagged", False):
                leading_length = len(word) - len(word.lstrip())
                trailing_length = len(word) - len(word.rstrip())
                leading = word[:leading_length]
                trailing = word[len(word) - trailing_length:] if trailing_length else ""
                content = word[leading_length:len(word) - trailing_length if trailing_length else None]
                visible_chars = max(0, options.visible_chars)
                if visible_chars < len(content):
                    mask_symbol = random.choice(options.symbol)
                    content = (
                        content[:visible_chars]
                        + mask_symbol * (len(content) - visible_chars)
                    )
                word = leading + content + trailing

            cues.append(
                "\n".join(
                    (
                        str(cue_number),
                        f"{self._format_srt_timestamp(word_segment['start'])} --> "
                        f"{self._format_srt_timestamp(word_segment['end'])}",
                        word,
                    )
                )
            )

        return "\n\n".join(cues)

    @staticmethod
    def _format_srt_timestamp(seconds: float) -> str:
        milliseconds = max(0, round(seconds * 1000))
        hours, milliseconds = divmod(milliseconds, 3_600_000)
        minutes, milliseconds = divmod(milliseconds, 60_000)
        seconds, milliseconds = divmod(milliseconds, 1_000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
        
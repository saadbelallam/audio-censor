from uuid import UUID, uuid4
from pathlib import Path

from celery import Celery

from app.config import settings
from app.database.models import Audio, AudioStatus
from app.utils import get_file_path
from app.worker.audio_censor import AudioCensor

celery_app = Celery("tasks", broker=settings.BROKER_URL)


@celery_app.task(base=AudioCensor, bind=True)
def transcribe_audio_task(self: AudioCensor, id: str) -> None:
    with self.session_local() as session:
        audio = session.get(Audio, UUID(id))
        if audio is None:
            return

        audio.status = AudioStatus.processing
        session.add(audio)
        session.commit()

        
        audio.transcription = self.transcribe_audio(audio.file_path)
        audio.credits_reseverd -= audio.duration
        audio.credits_used += audio.duration

        
        session.add(audio)
        session.commit()


@celery_app.task(base=AudioCensor, bind=True)
def detect_profanity_task(self: AudioCensor, id: str) -> None:
    with self.session_local() as session:
        audio = session.get(Audio, UUID(id))
        if audio is None:
            return

        if audio.status != AudioStatus.processing:
            audio.status = AudioStatus.processing
            session.add(audio)
            session.commit()

        
        audio.transcription = self.detect_profanity(
            audio.transcription,
            audio.user_list,
        )
        audio.credits_reseverd -= audio.duration
        audio.credits_used += audio.duration
        
        session.add(audio)
        session.commit()


@celery_app.task(base=AudioCensor, bind=True)
def render_audio_task(self: AudioCensor, id: str) -> None:
    with self.session_local() as session:
        audio = session.get(Audio, UUID(id))
        if audio is None:
            return

        if audio.status != AudioStatus.processing:
            audio.status = AudioStatus.processing
            session.add(audio)
            session.commit()

        
        input_path = audio.file_path
        output_path = audio.censored_file_path or f"users/{audio.user_id}/audios/{uuid4()}{Path(audio.file_path).suffix}"

        sound_effect_path = (
            get_file_path(audio.sound_effect.file_path)
            if audio.sound_effect is not None
            else None
        )
        self.render_audio(
            input_path=input_path,
            output_path=output_path,
            word_segments=audio.transcription,
            beep=audio.use_beep,
            sound_effect_path=sound_effect_path,
        )
        audio.censored_file_path = output_path
        audio.status = AudioStatus.completed
        audio.credits_reseverd -= audio.duration
        audio.credits_used += audio.duration
    

        session.add(audio)
        session.commit()

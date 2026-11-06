import warnings
from pathlib import Path
from typing import NotRequired, TypedDict

from better_profanity import profanity
from celery import Task
from pydub import AudioSegment
from pydub.generators import Sine
from rich import print_json
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine
from uuid import UUID
from app.config import settings
from app.object_storage import storage
from replicate.client import Client

from app.database.models import Audio, AudioStatus

warnings.filterwarnings("ignore")


class Word(TypedDict):
    word: str
    start: float
    end: float
    score: float
    flagged: NotRequired[bool]


class AudioCensor(Task):
    def __init__(self) -> None:
        self.replicate_client = Client(settings.REPLICATE_API_TOKEN)

        self.punctuation_table = str.maketrans("", "", """!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~""")

        # Initialize the database engine for synchronous operations
        # Because celery tasks are synchronous, we need to use a synchronous database engine here.
        self.engine = create_engine(url=settings.DB_URL.replace("+asyncpg", "+psycopg2"))
        self.session_local = sessionmaker(
            bind=self.engine, class_=Session, expire_on_commit=False
        )

        
    def transcribe_audio(self, audio_path: str) -> list[dict]:
        url = storage.get_file_url(audio_path)

        output = self.replicate_client.run(
            "victor-upmeet/whisperx:655845d6190ef70573c669245f245892cd039df4b880a1e3a65852c09252f5cc",
            input={
                "audio_file": url,
                "language": "en",
                "align_output": True,
            }
        )

        return [
            word 
            for segment in output["segments"]
            for word in segment["words"]
        ]


    def detect_profanity(self, word_segments: list[Word], user_list: list[str] | None = None) -> list[Word]:
        
        updated_segment = []
       
        for segment in word_segments:
            #Remove the punctuation from the word usinf string translation
            word = segment["word"].translate(self.punctuation_table)

            updated_segment.append({
                **segment,
                "flagged": profanity.contains_profanity(word) or (
                     user_list is not None and word.lower() in user_list
                )
            })
            
            
        return updated_segment


    def render_audio(
        self,
        input_path: str,
        output_path: str,
        word_segments: list[Word],
        beep: bool = True,
        sound_effect_path: str | None = None,
    ) -> None:
        audio = storage.download_audio(input_path)
        sound_effect = None
        if sound_effect_path is not None and not beep:
            sound_effect = storage.download_audio(sound_effect_path)


        for word_segment in word_segments:
            if not word_segment.get("flagged", False):
                continue

            start_ms = max(0, round(word_segment["start"] * 1000))
            end_ms = min(len(audio), round(word_segment["end"] * 1000))
            if start_ms >= end_ms:
                continue

            replacement = AudioSegment.silent(
                duration=end_ms - start_ms,
                frame_rate=audio.frame_rate,
            )
            if beep:
                replacement = (
                    Sine(1000)
                    .to_audio_segment(duration=end_ms - start_ms)
                    .apply_gain(-6)
                )
            elif sound_effect is not None:
                replacement = (
                    sound_effect
                    * ((end_ms - start_ms + len(sound_effect) - 1) // len(sound_effect))
                )[:end_ms - start_ms]
                replacement = replacement.set_frame_rate(audio.frame_rate).set_channels(
                    audio.channels
                )

            audio = audio[:start_ms] + replacement + audio[end_ms:]

        output_format = Path(output_path).suffix.lstrip(".") or None
        storage.upload_audio(audio, output_path, format=output_format)


    def on_failure(self, exc, task_id, args, kwargs, einfo):
        id = args[0] if args else kwargs.get("id")
        if id is not None:
            with self.session_local() as session:
                audio = session.get(Audio, UUID(id))
                if audio is not None:
                    audio.status = AudioStatus.failed

                    audio.user.credits += audio.credits_reseverd
                    audio.credits_reseverd = 0

                    session.add(audio)
                    session.commit()

        return super().on_failure(exc, task_id, args, kwargs, einfo)
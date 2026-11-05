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
import whisperx

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
        self.model_name = "small"
        self.device = "cpu"
        self.compute_type = "int8"
        self.language = "fr"
        self.transcription_model = None
        self.alignment_model,  self.alignment_metadata = None, None

        self.punctuation_table = str.maketrans("", "", """!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~""")

        # Initialize the database engine for synchronous operations
        # Because celery tasks are synchronous, we need to use a synchronous database engine here.
        self.engine = create_engine(url=settings.DB_URL.replace("+asyncpg", "+psycopg2"))
        self.session_local = sessionmaker(
            bind=self.engine, class_=Session, expire_on_commit=False
        )

        
    def transcribe_audio(self, audio_path: str) -> list[dict]:
        """Transcribe and forced-align an audio file using the CPU."""

        if self.transcription_model is None:
            self.transcription_model = whisperx.load_model(
                self.model_name, device=self.device, compute_type=self.compute_type
            )
        if self.alignment_model is None or self.alignment_metadata is None:
            self.alignment_model, self.alignment_metadata = whisperx.load_align_model(
                language_code=self.language, device=self.device
            )

        audio = whisperx.load_audio(audio_path)
        transcription = self.transcription_model.transcribe(
            audio,
            batch_size=1,
            language=self.language,
        )
        aligned_transcription = whisperx.align(
            transcription["segments"],
            self.alignment_model,
            self.alignment_metadata,
            audio,
            self.device,
            return_char_alignments=False,
        )

        return aligned_transcription["word_segments"]

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
        audio = AudioSegment.from_file(input_path)
        sound_effect = None
        if sound_effect_path is not None and not beep:
            sound_effect = AudioSegment.from_file(sound_effect_path)


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
        if output_format is None:
            audio.export(output_path)
        else:
            audio.export(output_path, format=output_format)


    def on_failure(self, exc, task_id, args, kwargs, einfo):
        id = args[0] if args else kwargs.get("id")
        if id is not None:
            with self.session_local() as session:
                audio = session.get(Audio, UUID(id))
                if audio is not None:
                    audio.status = AudioStatus.failed
                    session.add(audio)
                    session.commit()

        return super().on_failure(exc, task_id, args, kwargs, einfo)
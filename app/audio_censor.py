import warnings
from pathlib import Path
from typing import NotRequired, TypedDict

from better_profanity import profanity
from pydub import AudioSegment
from pydub.generators import Sine
from rich import print_json
import whisperx

warnings.filterwarnings("ignore")


class Word(TypedDict):
    word: str
    start: float
    end: float
    score: float
    flagged: NotRequired[bool]


class AudioCensor:
    def __init__(self) -> None:
        self.model_name = "small"
        self.device = "cpu"
        self.compute_type = "int8"
        self.language = "fr"
        self.transcription_model = whisperx.load_model(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type,
            language=self.language,
        )
        self.alignment_model,  self.alignment_metadata = whisperx.load_align_model(
            language_code=self.language, device=self.device,
        )

    def transcribe_audio(self, audio_path: str) -> list[dict]:
        """Transcribe and forced-align a French audio file using the CPU."""
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

    def detect_profanity(self, word_segments: list[Word]) -> list[Word]:
        for word_segment in word_segments:
            word_segment["flagged"] = profanity.contains_profanity(word_segment["word"])

        return word_segments


    def mute_audio(
        self,
        input_path: str,
        output_path: str,
        word_segments: list[Word],
        beep: bool = True,
    ) -> None:
        audio = AudioSegment.from_file(input_path)

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

            audio = audio[:start_ms] + replacement + audio[end_ms:]

        output_format = Path(output_path).suffix.lstrip(".") or None
        if output_format is None:
            audio.export(output_path)
        else:
            audio.export(output_path, format=output_format)
 
    
ac = AudioCensor()
result = ac.transcribe_audio("./test.ogg")
words = ac.detect_profanity(result)
ac.mute_audio("./test.ogg", "./test_muted.ogg", words)
print_json(data=words)
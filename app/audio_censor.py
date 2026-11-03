from typing import NotRequired, TypedDict

from better_profanity import profanity
from rich import print_json
import whisperx

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

    
ac = AudioCensor()
result = ac.transcribe_audio("./test.ogg")
print_json(data = ac.detect_profanity(result))
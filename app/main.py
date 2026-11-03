from fastapi import FastAPI, UploadFile
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import get_scalar_api_reference

from app.audio_censor import AudioCensor

UPLOADS_DIR = "uploads"


app = FastAPI(docs_url=None)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
ac = AudioCensor()


def save_file(upload_file: UploadFile, path: str) -> None:
    """Save an uploaded file to the specified path."""
    with open(path, "wb") as buffer:
        buffer.write(upload_file.file.read())

@app.post("/censor")
def censor_audio(audio_file: UploadFile):
    file_path = f"{UPLOADS_DIR}/{audio_file.filename}"
    output_path = f"{UPLOADS_DIR}/censored_{audio_file.filename}"

    save_file(audio_file, file_path)
    words = ac.transcribe_audio(file_path)
    ac.mute_audio(
        input_path=file_path,
        output_path=output_path,
        word_segments=ac.detect_profanity(words)
    )
    return {"url": f"/uploads/censored_{audio_file.filename}"}

@app.get("/docs", include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(openapi_url=app.openapi_url, title="API Docs")
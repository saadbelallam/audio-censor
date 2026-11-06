from datetime import timedelta
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from pydub import AudioSegment

import boto3
from botocore.client import Config
from app.config import settings

class ObjectStorage:
    def __init__(self):
        self.Client = boto3.client(
            service_name="s3",
            aws_access_key_id= settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key= settings.R2_SECRET_ACCESS_KEY,
            endpoint_url= settings.R2_ENDPOINT_URL,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )
        self.bucket_name = settings.R2_BUCKET_NAME

    def get_file_url(self, key: str, expiry: timedelta = timedelta(hours=1)) -> str:
        return self.Client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': key},
            ExpiresIn=expiry.total_seconds()
        )

    def upload_file(self, file: BinaryIO, key: str, content_type: str | None) -> None:
        file.seek(0)
        self.Client.upload_fileobj(
            file,
            self.bucket_name,
            key,
            ExtraArgs={"ContentType": content_type} if content_type else None,
        )

    def download_file(self, key: str) -> BinaryIO:
        file = BytesIO()
        self.Client.download_fileobj(self.bucket_name, key, file)
        file.seek(0)
        return file



    def upload_audio(self, audio: AudioSegment, key: str, format: str) -> None:
        file = BytesIO()
        audio.export(file, format=format)
        file.seek(0)
        self.upload_file(file, key, f"audio/{format}")

    def download_audio(self, key: str) -> AudioSegment:
        file = self.download_file(key)
        audio_format = Path(key).suffix.lstrip(".") or None
        return AudioSegment.from_file(file, format=audio_format)

storage = ObjectStorage()
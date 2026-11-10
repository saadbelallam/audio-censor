from pydantic import AliasChoices, Field

from .base import AppBaseSettings


class DataBaseSettings(AppBaseSettings):
    DB_URL: str
    CELERY_BROKER_URL: str = Field(
        validation_alias=AliasChoices("CELERY_BROKER_URL", "BROKER_URL")
    )


class ObjectStorageSettings(AppBaseSettings):
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_ENDPOINT_URL: str
    R2_BUCKET_NAME: str


db_settings = DataBaseSettings()
storage_settings = ObjectStorageSettings()
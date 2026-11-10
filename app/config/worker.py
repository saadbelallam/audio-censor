from app.config.base import AppBaseSettings


class WorkerSettings(AppBaseSettings):
    REPLICATE_API_TOKEN: str

worker_settings = WorkerSettings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_URL: str


    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str

    BROKER_URL: str

    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_ENDPOINT_URL: str
    R2_BUCKET_NAME: str

    REPLICATE_API_TOKEN: str

    POLAR_PRODUCT_ID: str
    POLAR_API_KEY: str
    POLAR_WEBHOOK_SECRET: str

    PROPELAUTH_AUTH_URL: str
    PROPELAUTH_API_KEY: str
    PROPELAUTH_WEBHOOK_SECRET: str

    ENABLE_DOCS: bool = True

    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
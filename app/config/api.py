from app.config.base import AppBaseSettings


class APISettings(AppBaseSettings):

    POLAR_PRODUCT_ID: str
    POLAR_API_KEY: str
    POLAR_WEBHOOK_SECRET: str

    PROPELAUTH_AUTH_URL: str
    PROPELAUTH_API_KEY: str
    PROPELAUTH_WEBHOOK_SECRET: str

    FRONTEND_URL: str
    ENABLE_DOCS: bool = True

api_settings = APISettings()
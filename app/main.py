from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import get_scalar_api_reference

from app.api.router import master_router
from app.core.exceptions import add_exception_handlers
from app.database.session import init_db
from app.utils import UPLOADS_DIR
from app.config.api import api_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("Database initialized.")
    yield
    print("Application shutdown.")


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json" if api_settings.ENABLE_DOCS else None,
    generate_unique_id_function=lambda route: route.name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[api_settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)

# app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.include_router(master_router)

# Add exception handlers
add_exception_handlers(app)

# @app.get("/health", include_in_schema=False)
# def health_check():
#     return {"status": "ok"}

if api_settings.ENABLE_DOCS:
    @app.get("/docs", include_in_schema=False)
    def scalar_docs():
        return get_scalar_api_reference(openapi_url=app.openapi_url, title="API Docs")
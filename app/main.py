from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import get_scalar_api_reference

from app.api.router import master_router
from app.database.session import init_db
from app.utils import UPLOADS_DIR
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("Database initialized.")
    yield
    print("Application shutdown.")


app = FastAPI(docs_url=None, lifespan=lifespan)
# app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.include_router(master_router)

if settings.ENABLE_DOCS:
    @app.get("/docs", include_in_schema=False)
    def scalar_docs():
        return get_scalar_api_reference(openapi_url=app.openapi_url, title="API Docs")
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

engine = create_async_engine(
    settings.DB_URL,
    echo=True,
)


session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():
    async with session_maker() as session:
        yield session


async def init_db():
    from app.database import models

    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)
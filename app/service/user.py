import jwt
from passlib.context import CryptContext
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from app.api.schemas import UserCreate
from app.config import settings
from app.database.models import User

password_context = CryptContext(schemes=["argon2"], deprecated="auto")

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        

    async def add_user(self,user: UserCreate) -> User:    
        db_user = User(
            email=user.email,
            password_hash= password_context.hash(user.password),
        )
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def generate_token(self, email: str, password: str) -> str | None:
        user = await self.session.scalar(
            select(User).where(User.email == email)
        )

        if user is None or not password_context.verify(password, user.password_hash):
            return None

        payload = {"sub": str(user.id)}
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    async def get_user(self, id: UUID) -> User | None:
        return await self.session.get(User, id)

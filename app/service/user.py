import jwt
from passlib.context import CryptContext
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from app.api.schemas.user import UserCreate
from app.database.models import User
from app.core.exceptions import InsufficientCredits, UserNotFoundError

password_context = CryptContext(schemes=["argon2"], deprecated="auto")

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        

    # async def add_user(self,user: UserCreate) -> User:    
    #     db_user = User(
    #         email=user.email,
    #         password_hash= password_context.hash(user.password),
    #     )
    #     self.session.add(db_user)
    #     await self.session.commit()
    #     await self.session.refresh(db_user)
    #     return db_user

    # async def generate_token(self, email: str, password: str) -> str | None:
    #     user = await self.session.scalar(
    #         select(User).where(User.email == email)
    #     )

    #     if user is None or not password_context.verify(password, user.password_hash):
    #         return None

    #     payload = {"sub": str(user.id)}
    #     return jwt.encode(
    #         payload,
    #         settings.JWT_SECRET_KEY,
    #         algorithm=settings.JWT_ALGORITHM,
    #     )

    async def get_user(self, id: UUID) -> User | None:
        return await self.session.get(User, id)

    async def add_user(self, user_data: dict) -> User:
        existing = await self.session.exec(
            select(User).where(User.propelauth_id == user_data["user_id"])
        )
        user = existing.first()
        if user is not None:
            return user

        user = User(
            email=user_data["email"],
            propelauth_id=user_data["user_id"],
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user


    async def get_user_by_propelauth_id(self, propelauth_id: str) -> User | None:
        user = await self.session.scalar(
            select(User).where(User.propelauth_id == propelauth_id)
        )
        return user

    async def deduct_credits(self, user: User, amount: int) -> User:
        if user.credits < amount:
            raise InsufficientCredits()
        
        user.credits -= amount
        self.session.add(user)
        await self.session.commit()

    async def add_credits(self, user_id: UUID, amount: int) -> None:
        user = await self.get_user(user_id)
        if user is None:
            raise UserNotFoundError()
        print(f"Adding {amount} credits to user {user.email}")
        user.credits += amount
        self.session.add(user)
        await self.session.commit()
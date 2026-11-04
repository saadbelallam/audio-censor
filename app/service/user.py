from passlib.context import CryptContext
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.schemas import UserCreate
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

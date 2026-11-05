from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import UserServiceDep
from app.api.schemas.user import TokenData, UserCreate, UserRead


router = APIRouter(tags=["User"])


@router.post("/signup", response_model=UserRead)
async def register_user(user: UserCreate, service: UserServiceDep) -> UserRead:
    return await service.add_user(user)


@router.post("/token", response_model=TokenData)
async def login_user(
    service: UserServiceDep,
    credentials: OAuth2PasswordRequestForm = Depends(),
):
    access_token = await service.generate_token(
        credentials.username,
        credentials.password,
    )
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": access_token, "token_type": "bearer"}

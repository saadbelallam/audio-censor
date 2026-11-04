from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from uuid import UUID

from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import AudioServiceDep, UserDep, UserServiceDep
from app.api.schemas import AudioRead, TokenData, UserCreate, UserRead


router = APIRouter()

@router.post("/signup", response_model=UserRead)
async def register_user(user: UserCreate, service: UserServiceDep) -> UserRead:
    created_user = await service.add_user(user)
    return created_user



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


@router.get("/audio/{id}", response_model=AudioRead)
async def read_audio(id: UUID, service: AudioServiceDep, user: UserDep):
    audio = await service.get_audio(id)
    if not audio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio not found")
    
    return audio

@router.post("/audio", response_model=AudioRead)
async def submit_audio(audio_file: UploadFile, service: AudioServiceDep):
    audio = await service.add_audio(audio_file)
    
    return audio
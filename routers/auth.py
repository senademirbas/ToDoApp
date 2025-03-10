from typing import Annotated
from aiohttp import Payload
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from pytest import Session
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, status, Path, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import timedelta, datetime, timezone


#router tüm api noktalarını tek uygulamada kullanmayı saglar
router = APIRouter(
    prefix="/auth",
    tags=["Authentications"]
)

SECRET_KEY = "senaasdcow82r8fushf03r8hfray03hfacn209uej0jd0mc0qdu03opapq0r"
ALGORITHM = "HS256"


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated= "auto")


def get_db():
    db = SessionLocal()
    try:
        yield db #return ile aynı ama birden fazla veri gelirse onları da döndürür
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)] 

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str


def create_access_token(username:str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id':user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


@router.post(path="/", status_code= status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    user = User(
        username = create_user_request.username,
        email = create_user_request.email,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        role = create_user_request.role,
        hashed_password = bcrypt_context.hash(create_user_request.password)
    )
    db.add(user)
    db.commit()


@router.post(path="/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}
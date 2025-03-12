from typing import Annotated
from aiohttp import Payload
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from pytest import Session
from database import SessionLocal
from models import Todo, User
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, status, Path, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import timedelta, datetime, timezone
from fastapi.templating import Jinja2Templates


#router tüm api noktalarını tek uygulamada kullanmayı saglar
router = APIRouter(
    prefix="/auth",
    tags=["Authentications"]
)


templates = Jinja2Templates(directory="templates")


SECRET_KEY = "senaasdcow82r8fushf03r8hfray03hfacn209uej0jd0mc0qdu03opapq0r"
ALGORITHM = "HS256"


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated= "auto")
oauth2_bearer = OAuth2PasswordBearer("/auth/token")

def get_db():
    db = SessionLocal()
    try:
        yield db #return ile aynı ama birden fazla veri gelirse onları da döndürür
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)] 


async def get_current_user(request: Request):  # Accept request instead of token directly
    token = request.cookies.get('access_token')  # Get token from cookies
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        user_id = payload.get('id')
        user_role = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Username or ID is invalid")
        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")


user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/")
async def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(Todo).all()

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

class Token(BaseModel):
    access_token: str
    token_type: str

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



@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post(path="/", status_code= status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    user = User(
        username = create_user_request.username,
        email = create_user_request.email,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        role = create_user_request.role,
        hashed_password = bcrypt_context.hash(create_user_request.password),
        phone_number = create_user_request.phone_number
    )
    db.add(user)
    db.commit()


@router.post(path="/token", response_model= Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=60))

    return {"access_token": token, "token_type": "bearer"}

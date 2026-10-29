import os
from typing import Annotated, Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from passlib.context import CryptContext
from jose import jwt, JWTError
from pathlib import Path
from database import SessionLocal
from models import Users
from dotenv import load_dotenv

   

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Add it to your .env file.")
ALGORITHM = 'HS256'
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# auto_error=False prevents it from throwing a 401 before we can check the cookie
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token', auto_error=False)


BASE_DIR = Path(__file__).resolve().parent.parent  # routers/ -> project root
templates = Jinja2Templates(directory=BASE_DIR / "templates")

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

### Pages ###

@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"request": request})

@router.post("/register-page")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    db: Session = Depends(get_db)
):
    # 1. Check if the username or email already exists
    existing_user = db.query(Users).filter(
        (Users.username == username) | (Users.email == email)
    ).first()
    
    if existing_user:
        return templates.TemplateResponse(
            request, 
            "register.html", 
            {"request": request, "error": "Username or email already registered."}
        )

    # 2. Create the new user model
    create_user_model = Users(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        role=role,
        hashed_password=bcrypt_context.hash(password),
        is_active=True,
        phone_number=phone_number
    )
    
    # 3. Save to database
    db.add(create_user_model)
    db.commit()
    
    # 4. Redirect to the login page after successful registration
    return RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)


@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})

@router.post("/login-page")
async def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate(username, password, db)
    
    if not user:
        return templates.TemplateResponse(
            request, 
            "login.html", 
            {"request": request, "error": "Invalid username or password"}
        )
    
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
    
    # FIXED: Added trailing slash to /todos/ to prevent 307 redirect
    response = RedirectResponse(url="/todos/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    
    return response

# NEW: The Logout Route
@router.get("/logout")
def logout():
    response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response


### Endpoints ###

def authenticate(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    request: Request,
    token: Annotated[Optional[str], Depends(oauth2_bearer)] = None
):
    cookie_token = request.cookies.get("access_token")
    final_token = cookie_token or token
    
    if not final_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Not authenticated"
        )
        
    try:
        payload = jwt.decode(final_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_name: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        
        if user_name is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Could not validate the user"
            )
        return {"username": user_name, "id": user_id, "user_role": user_role}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Could not validate the user"
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, new_user: CreateUserRequest):
    create_user_model = Users(
        email=new_user.email,
        username=new_user.username,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        role=new_user.role,
        hashed_password=bcrypt_context.hash(new_user.password),
        is_active=True,
        phone_number=new_user.phone_number
    )
    db.add(create_user_model)
    db.commit()

@router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate the user")

    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}
from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, HTTPException, Body
from starlette import status
from passlib.context import CryptContext

from models import Users
from database import SessionLocal
from routers.auth import get_current_user

router = APIRouter(
    prefix='/users',
    tags=['users']
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# --- SCHEMAS ---

class PasswordChangeRequest(BaseModel):
    password: str
    new_password: str = Field(min_length=5)

# NEW: Response model to safely return user data WITHOUT the password
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    phone_number: str

    class Config:
        from_attributes = True # Tells Pydantic to read data from SQLAlchemy models


# --- ROUTES ---

# FIXED: Added response_model=UserResponse to hide the hashed_password
@router.get("/", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def user_data(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_model = db.query(Users).filter(Users.id == user.get("id")).first()
    return user_model

@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user: user_dependency,
    db: db_dependency,
    password_request: PasswordChangeRequest
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_model = db.query(Users).filter(Users.id == user.get("id")).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify the old password
    if not bcrypt_context.verify(password_request.password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # Update to the new password
    user_model.hashed_password = bcrypt_context.hash(password_request.new_password)
    db.add(user_model)
    db.commit()

@router.put("/update_phone_number", status_code=status.HTTP_204_NO_CONTENT)
async def update_phone(
    user: user_dependency, 
    db: db_dependency, 
    new_phone_number: str = Body(min_length=9, max_length=15, embed=True) # Added embed=True for JSON body
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="Not found")
        
    user_model.phone_number = new_phone_number
    db.add(user_model)
    db.commit()
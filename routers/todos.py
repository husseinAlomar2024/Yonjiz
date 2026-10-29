from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, HTTPException, Path, Request
from fastapi.templating import Jinja2Templates
from models import Todos
from database import SessionLocal
from starlette import status
from routers.auth import get_current_user
from datetime import datetime
from typing import Optional
from pathlib import Path as FilePath
from fastapi import APIRouter, Depends, HTTPException, Path, Request

router = APIRouter(
     prefix='/todos',
     tags=['todos']
)


BASE_DIR = FilePath(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
"""
class todo_request(BaseModel):
    priority: int = Field(gt=0, lt=6)
    # Change this line to allow empty descriptions:
    description: str = Field(default="", max_length=100) 
    title: str = Field(min_length=3, max_length=30)
    complete: bool

"""
class todo_request(BaseModel):
    priority: int = Field(gt=0, lt=6)
    description: str = Field(default="", max_length=100)
    title: str = Field(min_length=3, max_length=30)
    complete: bool
    deadline: Optional[datetime] = None # NEW

# --- UPDATED: Now returns the HTML page ---
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(request: Request, user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    
    todos = db.query(Todos).filter(Todos.owner_id == user.get('id')).all()
    
    # Return the HTML template instead of JSON
    return templates.TemplateResponse(
        request, 
        "home.html", 
        {"request": request, "todos": todos}
    )

@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_query(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
  
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is not None:
        return todo_model
    
    raise HTTPException(status_code=404, detail="todo is not found ")

# --- UPDATED: Returns the newly created todo so JS can render it ---
@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, new_todo: todo_request):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
        
    # Ensure created_at is set to now, and pass the deadline
    todo_model = Todos(
        **new_todo.model_dump(exclude={"deadline"}), 
        deadline=new_todo.deadline,
        owner_id=user.get('id'),
        created_at=datetime.utcnow()
    )
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model) 
    return todo_model 


@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency, db: db_dependency, todo_request: todo_request, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
 
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
         raise HTTPException(status_code=404, detail="not found")
         
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    db.add(todo_model)
    db.commit()

@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
 
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="todo not found")
        
    db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).delete()
    db.commit()
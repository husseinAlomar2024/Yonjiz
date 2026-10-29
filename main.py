from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import models
from database import engine
from routers import auth, todos, admin, users

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/")
def test(request:Request):
    return templates.TemplateResponse(request, "home.html", {"request": request})




@app.get("/healthy")
async def health_check():
    return {'status':'healthy'}



app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)

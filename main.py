"""Daymark — a focused todo workspace with a calendar, live clock and
three-seat administrator console."""

from __future__ import annotations

from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette import status

from config import APP_NAME
from database import SessionLocal, init_db
from dependencies import OptionalUser, user_from_cookie
from templating import BASE_DIR, templates
from routers import admin, auth, todos


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title=f"{APP_NAME} · Todo workspace", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self'; "
        "script-src 'self'; font-src 'self'; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; "
        "frame-ancestors 'none'",
    )
    if request.url.path.startswith(("/api/", "/auth/", "/todos", "/admin")):
        response.headers.setdefault("Cache-Control", "no-store")
    if request.url.path.startswith("/admin"):
        response.headers.setdefault("X-Robots-Tag", "noindex, nofollow")
    return response


@app.get("/")
def landing_page(request: Request, user: OptionalUser):
    return templates.TemplateResponse(
        request,
        "landing.html",
        {"request": request, "user": user},
    )


@app.get("/healthy")
@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": APP_NAME}


@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_handler(request: Request, _exc):
    if request.url.path.startswith("/api/") or request.url.path == "/auth/token":
        return JSONResponse(
            {"detail": "Please sign in to continue."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    next_path = request.url.path
    if request.url.query:
        next_path = f"{next_path}?{request.url.query}"
    return RedirectResponse(
        url=f"/auth/login-page?next={quote(next_path, safe='')}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def forbidden_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            {"detail": getattr(exc, "detail", "Access denied.")},
            status_code=status.HTTP_403_FORBIDDEN,
        )
    db = SessionLocal()
    try:
        current_user = user_from_cookie(request, db)
    finally:
        db.close()
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "request": request,
            "user": current_user,
            "status_code": 403,
            "title": "Administrator access required",
            "message": getattr(exc, "detail", "You do not have access to this page."),
            "show_admin_access": True,
        },
        status_code=status.HTTP_403_FORBIDDEN,
    )


@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def not_found_handler(request: Request, _exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            {"detail": "Not found."}, status_code=status.HTTP_404_NOT_FOUND
        )
    db = SessionLocal()
    try:
        current_user = user_from_cookie(request, db)
    finally:
        db.close()
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "request": request,
            "user": current_user,
            "status_code": 404,
            "title": "Page not found",
            "message": "The page you were looking for has moved or never existed.",
            "show_admin_access": False,
        },
        status_code=status.HTTP_404_NOT_FOUND,
    )


app.include_router(auth.router)
app.include_router(todos.page_router)
app.include_router(todos.api_router)
app.include_router(admin.router)

"""The signed-in workspace page plus the owner-scoped todo JSON API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette import status

from database import get_db
from dependencies import CurrentUser
from models import Todo, utcnow
from schemas import TodoCompletePayload, TodoPayload, TodoRead
from templating import templates


page_router = APIRouter(tags=["pages"])
api_router = APIRouter(prefix="/api/todos", tags=["todos"])


def _normalize_deadline(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _owned_todo(db: Session, todo_id: int, owner_id: int) -> Todo:
    todo = (
        db.query(Todo)
        .filter(Todo.id == todo_id, Todo.owner_id == owner_id)
        .first()
    )
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    return todo


@page_router.get("/todos")
def todos_page(
    request: Request,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    todos = (
        db.query(Todo)
        .filter(Todo.owner_id == user.id)
        .order_by(
            Todo.complete.asc(),
            Todo.deadline.is_(None).asc(),
            Todo.deadline.asc(),
            Todo.created_at.desc(),
        )
        .all()
    )
    total = len(todos)
    completed = sum(1 for todo in todos if todo.complete)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "todos": todos,
            "total": total,
            "completed": completed,
            "open_count": total - completed,
            "message": request.query_params.get("message"),
            "message_kind": request.query_params.get("kind", "success"),
        },
    )


@page_router.get("/todos/")
def todos_page_slash():
    return RedirectResponse(url="/todos", status_code=status.HTTP_308_PERMANENT_REDIRECT)


@api_router.get("", response_model=list[TodoRead])
def list_todos(
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    return (
        db.query(Todo)
        .filter(Todo.owner_id == user.id)
        .order_by(
            Todo.complete.asc(),
            Todo.deadline.is_(None).asc(),
            Todo.deadline.asc(),
            Todo.created_at.desc(),
        )
        .all()
    )


@api_router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
def create_todo(
    payload: TodoPayload,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    now = utcnow()
    todo = Todo(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        complete=payload.complete,
        owner_id=user.id,
        created_at=now,
        updated_at=now,
        deadline=_normalize_deadline(payload.deadline),
        completed_at=now if payload.complete else None,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@api_router.put("/{todo_id}", response_model=TodoRead)
def update_todo(
    todo_id: int,
    payload: TodoPayload,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    todo = _owned_todo(db, todo_id, user.id)
    was_complete = todo.complete

    todo.title = payload.title
    todo.description = payload.description
    todo.priority = payload.priority
    todo.complete = payload.complete
    todo.deadline = _normalize_deadline(payload.deadline)
    todo.updated_at = utcnow()

    if payload.complete and not was_complete:
        todo.completed_at = utcnow()
    elif not payload.complete:
        todo.completed_at = None
    elif todo.completed_at is None:
        todo.completed_at = utcnow()

    db.commit()
    db.refresh(todo)
    return todo


@api_router.patch("/{todo_id}/complete", response_model=TodoRead)
def set_todo_complete(
    todo_id: int,
    payload: TodoCompletePayload,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    todo = _owned_todo(db, todo_id, user.id)
    if todo.complete != payload.complete:
        todo.complete = payload.complete
        todo.completed_at = utcnow() if payload.complete else None
        todo.updated_at = utcnow()
        db.commit()
        db.refresh(todo)
    return todo


@api_router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: int,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    todo = _owned_todo(db, todo_id, user.id)
    db.delete(todo)
    db.commit()
    return None

"""API router for todo CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app import database as db_module
from app.database import (
    create_todo,
    delete_todo,
    fetch_all_todos,
    fetch_todo_by_id,
    get_db,
    update_todo,
)
from app.models import TodoCreate, TodoResponse, TodoUpdate

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("/", response_model=list[TodoResponse])
async def list_todos(db=Depends(get_db)):
    """Return all todos ordered by position ASC, created_at DESC."""
    todos = await fetch_all_todos(db)
    return todos


@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo_endpoint(payload: TodoCreate, db=Depends(get_db)):
    """Create a new todo. Returns 422 if title is empty or whitespace-only."""
    todo = await create_todo(db, payload.title)
    return todo


@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo_endpoint(todo_id: int, payload: TodoUpdate, db=Depends(get_db)):
    """Update a todo's title and/or completed state.

    Returns 400 if neither title nor completed is provided.
    Returns 404 if todo not found.
    """
    if payload.title is None and payload.completed is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="title 또는 completed 중 하나 이상 제공해야 합니다",
        )

    existing = await fetch_todo_by_id(db, todo_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo {todo_id}를 찾을 수 없습니다",
        )

    updated = await update_todo(db, todo_id, title=payload.title, completed=payload.completed)
    return updated


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo_endpoint(todo_id: int, db=Depends(get_db)):
    """Delete a todo by ID.

    Returns 404 if todo not found.
    Returns 204 No Content on success.
    """
    deleted = await delete_todo(db, todo_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo {todo_id}를 찾을 수 없습니다",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

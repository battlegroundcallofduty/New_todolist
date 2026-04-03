"""API router for todo CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.database import (
    _UNSET,
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
    """Return all todos: incomplete first, then completed, ordered by position."""
    todos = await fetch_all_todos(db)
    return todos


@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo_endpoint(payload: TodoCreate, db=Depends(get_db)):
    """Create a new todo. Returns 422 if title is empty or whitespace-only."""
    todo = await create_todo(db, payload.title, due_date=payload.due_date, category_id=payload.category_id)
    return todo


@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo_endpoint(todo_id: int, payload: TodoUpdate, db=Depends(get_db)):
    """Update a todo's fields.

    Returns 400 if no fields are provided.
    Returns 404 if todo not found.
    """
    if all(v is None for v in (payload.title, payload.completed, payload.due_date, payload.category_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="변경할 필드를 하나 이상 제공해야 합니다",
        )

    existing = await fetch_todo_by_id(db, todo_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo {todo_id}를 찾을 수 없습니다",
        )

    updated = await update_todo(
        db,
        todo_id,
        title=payload.title if payload.title is not None else _UNSET,
        completed=payload.completed if payload.completed is not None else _UNSET,
        due_date=payload.due_date if payload.due_date is not None else _UNSET,
        category_id=payload.category_id if payload.category_id is not None else _UNSET,
    )
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

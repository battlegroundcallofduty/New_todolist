"""API router for category CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.database import (
    create_category,
    delete_category,
    fetch_all_categories,
    fetch_category_by_id,
    get_db,
    update_category,
)
from app.models import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryResponse])
async def list_categories(db=Depends(get_db)):
    """Return all categories ordered by position ASC."""
    return await fetch_all_categories(db)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category_endpoint(payload: CategoryCreate, db=Depends(get_db)):
    """Create a new category. Returns 422 if name is empty."""
    return await create_category(db, payload.name)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category_endpoint(
    category_id: int, payload: CategoryUpdate, db=Depends(get_db)
):
    """Update a category's name.

    Returns 400 if name not provided.
    Returns 404 if category not found.
    """
    if payload.name is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="name을 제공해야 합니다",
        )
    existing = await fetch_category_by_id(db, category_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id}를 찾을 수 없습니다",
        )
    return await update_category(db, category_id, payload.name)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category_endpoint(category_id: int, db=Depends(get_db)):
    """Delete a category by ID.

    Returns 404 if category not found.
    Returns 204 No Content on success.
    """
    deleted = await delete_category(db, category_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id}를 찾을 수 없습니다",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

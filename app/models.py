"""Pydantic models for request validation and response serialization."""

from typing import Optional

from pydantic import BaseModel, field_validator


class TodoCreate(BaseModel):
    """Request model for creating a new todo."""

    title: str

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        """Strip whitespace and reject empty strings."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("할 일 내용을 입력해주세요")
        return stripped


class TodoUpdate(BaseModel):
    """Request model for updating an existing todo (all fields optional)."""

    title: Optional[str] = None
    completed: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace and reject empty strings if title is provided."""
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("할 일 내용을 입력해주세요")
        return stripped


class TodoResponse(BaseModel):
    """Response model for a todo item."""

    id: int
    title: str
    completed: bool
    position: int
    created_at: str

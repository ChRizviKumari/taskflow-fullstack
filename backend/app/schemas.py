"""Pydantic request models (all reject unknown fields)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Priority = Literal["low", "medium", "high"]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RegisterIn(_Base):
    email: str = Field(max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(_Base):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class BoardIn(_Base):
    name: str = Field(min_length=1, max_length=100)


class ColumnIn(_Base):
    name: str = Field(min_length=1, max_length=60)


class TaskCreate(_Base):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    priority: Priority = "medium"


class TaskPatch(_Base):
    version: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    priority: Priority | None = None
    column_id: int | None = Field(default=None, ge=1)
    position: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _needs_change(self) -> "TaskPatch":
        if all(getattr(self, f) is None for f in ("title", "description", "priority", "column_id", "position")):
            raise ValueError("at least one field to update is required")
        return self


class PageQuery(_Base):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    q: str | None = Field(default=None, max_length=100)


class TaskQuery(PageQuery):
    column_id: int | None = Field(default=None, ge=1)
    priority: Priority | None = None

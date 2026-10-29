from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIError(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str
    database: dict[str, Any]
    storage: dict[str, Any]
    matching: dict[str, Any]
    email: dict[str, Any]
    llm: dict[str, Any]


class IdName(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class Message(BaseModel):
    message: str
    extra: dict[str, Any] = Field(default_factory=dict)

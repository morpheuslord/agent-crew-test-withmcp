"""Shared schema building blocks."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Password = Annotated[str, Field(min_length=1, max_length=256)]
Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        min_length=3,
        max_length=320,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]


class RequestModel(BaseModel):
    """Requests accept only the fields they declare."""

    model_config = ConfigDict(extra="forbid")


class ResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageParams(RequestModel):
    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=50, ge=1, le=200)


class PageMeta(ResponseModel):
    total: int
    page: int
    page_size: int


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str
    fields: list[dict[str, str]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody

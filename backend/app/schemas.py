from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Source(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    url: str
    snippet: str = ""
    domain: str = ""


class Message(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    sources: list[Source] = Field(default_factory=list)
    created_at: str


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0
    preview: str = ""


class ConversationDetail(ConversationSummary):
    messages: list[Message] = Field(default_factory=list)


class CreateConversationRequest(BaseModel):
    title: Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=100)] = None


class UpdateConversationRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ChatRequest(BaseModel):
    content: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50_000)
    ]
    search_mode: Literal["auto", "web", "off"] = "auto"

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.app.config import Settings
from backend.app.db import ConversationNotFoundError, ConversationStore
from backend.app.schemas import (
    ChatRequest,
    ConversationDetail,
    ConversationSummary,
    CreateConversationRequest,
    UpdateConversationRequest,
)
from backend.app.services.model import (
    ChatModel,
    ModelError,
    ModelUnavailableError,
    build_generation_messages,
    build_model,
)
from backend.app.services.search import SearchError, SearchService, should_search

logger = logging.getLogger(__name__)
_HEARTBEAT = object()
_HEARTBEAT_FRAME = ": keep-alive\n\n"
SSE_HEARTBEAT_INTERVAL_SECONDS = 15.0


@dataclass(frozen=True, slots=True)
class _Awaited:
    value: Any


def _event(event: str, payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {data}\n\n"


def _not_found(conversation_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Conversation '{conversation_id}' was not found",
    )


async def _with_heartbeat(
    stream: AsyncIterator[str], interval_seconds: float = 15.0
) -> AsyncIterator[str | object]:
    """Yield stream values while keeping SSE connections active between tokens."""
    iterator = stream.__aiter__()
    pending: asyncio.Task[str] | None = None
    try:
        while True:
            if pending is None:
                pending = asyncio.create_task(anext(iterator))
            done, _ = await asyncio.wait({pending}, timeout=interval_seconds)
            if not done:
                yield _HEARTBEAT
                continue
            try:
                value = pending.result()
            except StopAsyncIteration:
                return
            pending = None
            yield value
    finally:
        if pending is not None and not pending.done():
            pending.cancel()
            with suppress(asyncio.CancelledError, StopAsyncIteration):
                await pending
        closer = getattr(iterator, "aclose", None)
        if closer is not None:
            with suppress(asyncio.CancelledError, RuntimeError):
                await closer()


async def _await_with_heartbeat(
    awaitable: Awaitable[Any],
    interval_seconds: float = 15.0,
    on_abandoned_result: Callable[[Any], None] | None = None,
) -> AsyncIterator[_Awaited | object]:
    """Await one operation while yielding SSE heartbeat markers."""
    task = asyncio.ensure_future(awaitable)
    result_retrieved = False
    try:
        while True:
            done, _ = await asyncio.wait({task}, timeout=interval_seconds)
            if not done:
                yield _HEARTBEAT
                continue
            value = task.result()
            result_retrieved = True
            yield _Awaited(value)
            return
    finally:
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        elif not result_retrieved and not task.cancelled():
            # Cancellation can race completion. Consume the result and release any
            # resource acquired by an operation whose result was never delivered.
            task_exception = task.exception()
            if task_exception is None and on_abandoned_result is not None:
                on_abandoned_result(task.result())


def create_app(
    *,
    settings: Settings | None = None,
    store: ConversationStore | None = None,
    search_service: SearchService | Any | None = None,
    model: ChatModel | Any | None = None,
    serve_frontend: bool = True,
) -> FastAPI:
    active_settings = settings or Settings.from_env()
    active_store = store or ConversationStore(active_settings.database_path)
    active_search = search_service or SearchService(active_settings)
    active_model = model or build_model(active_settings)
    turn_locks: dict[str, asyncio.Lock] = {}

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        try:
            yield
        finally:
            closer = getattr(active_model, "aclose", None)
            if closer is not None:
                result = closer()
                if inspect.isawaitable(result):
                    await result

    application = FastAPI(
        title="Sovereign AI iBuddy API",
        version="1.0.0",
        description="Private-by-default local AI workspace with optional search grounding.",
        docs_url="/api/docs" if active_settings.environment != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    application.state.settings = active_settings
    application.state.store = active_store
    application.state.search = active_search
    application.state.model = active_model
    application.state.turn_locks = turn_locks

    origins = list(active_settings.cors_origins)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials="*" not in origins,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )
    application.add_middleware(
        TrustedHostMiddleware, allowed_hosts=list(active_settings.allowed_hosts)
    )

    @application.exception_handler(ConversationNotFoundError)
    async def conversation_not_found_handler(
        _request: Request, exc: ConversationNotFoundError
    ) -> JSONResponse:
        conversation_id = str(exc.args[0]) if exc.args else "unknown"
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"Conversation '{conversation_id}' was not found"},
        )

    @application.get("/api/health")
    def health() -> dict[str, Any]:
        model_ready = bool(getattr(active_model, "ready", False))
        model_state = str(
            getattr(
                active_model,
                "state",
                "ready" if model_ready else "unconfigured",
            )
        )
        model_configured = bool(
            getattr(
                active_model,
                "configured",
                model_state not in {"missing_assets", "unconfigured"},
            )
        )
        model_operational = getattr(active_model, "operational", None)
        if model_operational is None and model_state in {"ready", "operational"}:
            model_operational = True
        runtime_status = "ok"
        detail = getattr(active_model, "detail", None)
        if model_state in {"configured", "idle", "loading", "starting"}:
            runtime_status = "loading"
            detail = detail or "The model becomes operational on the first message"
        elif model_state in {"closed", "error", "missing_assets", "unconfigured"}:
            runtime_status = "error"
            detail = detail or "The local model is not available"
        elif not model_ready:
            detail = detail or "Add HF_TOKEN to .env to enable Hugging Face inference"
        model_id = (
            active_settings.llama_cpp_model_path.name
            if active_settings.model_backend == "llama_cpp"
            else active_settings.hf_model
        )
        payload: dict[str, Any] = {
            "status": runtime_status,
            "app": active_settings.app_name,
            "offline_mode": active_settings.offline_mode,
            "model": {
                "backend": active_settings.model_backend,
                "id": model_id,
                "provider": active_settings.hf_provider,
                "ready": model_ready,
                "configured": model_configured,
                "operational": model_operational,
                "state": model_state,
            },
            "search": {
                "provider": getattr(active_search, "provider_name", "custom"),
                "ready": bool(getattr(active_search, "ready", True)),
                "operational": getattr(active_search, "operational", None),
                "detail": getattr(active_search, "detail", None),
            },
            "history": {"ready": True},
        }
        if detail:
            payload["detail"] = detail
        return payload

    @application.get("/api/conversations", response_model=list[ConversationSummary])
    def list_conversations(
        q: str | None = Query(default=None, max_length=100),
        limit: int = Query(default=500, ge=1, le=500),
    ) -> list[dict[str, Any]]:
        return active_store.list_conversations(query=q, limit=limit)

    @application.post(
        "/api/conversations",
        response_model=ConversationDetail,
        status_code=status.HTTP_201_CREATED,
    )
    def create_conversation(
        payload: CreateConversationRequest,
    ) -> dict[str, Any]:
        return active_store.create_conversation(payload.title)

    @application.get("/api/conversations/{conversation_id}", response_model=ConversationDetail)
    def get_conversation(conversation_id: str) -> dict[str, Any]:
        try:
            return active_store.get_conversation(conversation_id)
        except ConversationNotFoundError as exc:
            raise _not_found(conversation_id) from exc

    @application.patch("/api/conversations/{conversation_id}", response_model=ConversationDetail)
    def update_conversation(
        conversation_id: str, payload: UpdateConversationRequest
    ) -> dict[str, Any]:
        try:
            return active_store.rename_conversation(conversation_id, payload.title)
        except ConversationNotFoundError as exc:
            raise _not_found(conversation_id) from exc

    @application.delete(
        "/api/conversations/{conversation_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete_conversation(conversation_id: str) -> Response:
        turn_lock = turn_locks.setdefault(conversation_id, asyncio.Lock())
        async with turn_lock:
            try:
                await asyncio.to_thread(active_store.delete_conversation, conversation_id)
            except ConversationNotFoundError as exc:
                raise _not_found(conversation_id) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @application.post("/api/conversations/{conversation_id}/messages/stream")
    async def stream_message(conversation_id: str, payload: ChatRequest) -> StreamingResponse:
        if len(payload.content) > active_settings.max_user_chars:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Message exceeds {active_settings.max_user_chars} characters",
            )
        try:
            await asyncio.to_thread(active_store.get_conversation, conversation_id)
        except ConversationNotFoundError as exc:
            raise _not_found(conversation_id) from exc

        search_requested = should_search(payload.content, payload.search_mode)
        searched = search_requested and not active_settings.offline_mode

        async def generate_events():
            sources: list[dict[str, str]] = []
            pieces: list[str] = []
            completed = False
            assistant_message: dict[str, Any] | None = None
            turn_lock = turn_locks.setdefault(conversation_id, asyncio.Lock())

            def persist_partial() -> None:
                if assistant_message is None or completed:
                    return
                partial = "".join(pieces).strip()
                if not partial:
                    return
                try:
                    active_store.update_assistant_message(
                        conversation_id,
                        assistant_message["id"],
                        partial,
                        sources,
                    )
                except Exception:
                    logger.exception(
                        "Could not persist partial response for conversation %s",
                        conversation_id,
                    )

            lock_acquired = False
            try:
                async for wait_item in _await_with_heartbeat(
                    turn_lock.acquire(),
                    interval_seconds=SSE_HEARTBEAT_INTERVAL_SECONDS,
                    on_abandoned_result=lambda acquired: turn_lock.release() if acquired else None,
                ):
                    if wait_item is _HEARTBEAT:
                        yield _HEARTBEAT_FRAME
                    elif isinstance(wait_item, _Awaited):
                        lock_acquired = bool(wait_item.value)
                if not lock_acquired:
                    raise RuntimeError("Conversation turn lock was not acquired")

                try:
                    # These short SQLite writes stay on the event loop so cancellation
                    # cannot race a detached worker and duplicate a terminal message.
                    user_message = active_store.add_message(
                        conversation_id, "user", payload.content
                    )
                    updated_conversation = active_store.get_conversation(conversation_id)
                    yield _event(
                        "meta",
                        {
                            "user_message": user_message,
                            "conversation": updated_conversation,
                            "searched": searched,
                        },
                    )

                    search_error: str | None = None
                    if (
                        search_requested
                        and active_settings.offline_mode
                        and payload.search_mode == "web"
                    ):
                        search_error = "Web search is unavailable while offline mode is enabled"
                    if searched:
                        try:
                            async for search_item in _await_with_heartbeat(
                                active_search.search(payload.content),
                                interval_seconds=SSE_HEARTBEAT_INTERVAL_SECONDS,
                            ):
                                if search_item is _HEARTBEAT:
                                    yield _HEARTBEAT_FRAME
                                elif isinstance(search_item, _Awaited):
                                    sources = search_item.value
                        except SearchError as exc:
                            search_error = str(exc)
                        except Exception:
                            logger.exception("Unexpected search adapter error")
                            search_error = "Web search is temporarily unavailable"
                    source_payload: dict[str, Any] = {
                        "sources": sources,
                        "offline": active_settings.offline_mode,
                    }
                    if search_error:
                        source_payload["search_error"] = search_error
                    yield _event("sources", source_payload)

                    history = active_store.context_messages(
                        conversation_id,
                        limit=active_settings.history_message_limit,
                    )
                    model_messages = build_generation_messages(history, sources)
                    model_stream = active_model.generate(model_messages)
                    async for piece in _with_heartbeat(
                        model_stream,
                        interval_seconds=SSE_HEARTBEAT_INTERVAL_SECONDS,
                    ):
                        if piece is _HEARTBEAT:
                            yield _HEARTBEAT_FRAME
                            continue
                        if not piece:
                            continue
                        text_piece = str(piece)
                        pieces.append(text_piece)
                        partial = "".join(pieces).strip()
                        if assistant_message is None and partial:
                            assistant_message = active_store.add_message(
                                conversation_id,
                                "assistant",
                                partial,
                                sources,
                            )
                        yield _event("delta", {"text": text_piece})

                    answer = "".join(pieces).strip()
                    if not answer:
                        raise ModelUnavailableError("The model returned an empty response")
                    if assistant_message is None:
                        assistant_message = active_store.add_message(
                            conversation_id, "assistant", answer, sources
                        )
                    else:
                        assistant_message = active_store.update_assistant_message(
                            conversation_id,
                            assistant_message["id"],
                            answer,
                            sources,
                        )
                    completed = True
                    conversation = active_store.get_conversation(conversation_id)
                    yield _event(
                        "done",
                        {
                            "message": assistant_message,
                            "conversation": conversation,
                        },
                    )
                except asyncio.CancelledError:
                    persist_partial()
                    raise
                except ModelError as exc:
                    persist_partial()
                    yield _event("error", {"message": str(exc), "code": exc.code})
                except Exception:
                    persist_partial()
                    logger.exception(
                        "Unhandled streaming error for conversation %s", conversation_id
                    )
                    yield _event(
                        "error",
                        {
                            "message": "iBuddy could not complete this response",
                            "code": "internal_error",
                        },
                    )
            finally:
                if lock_acquired:
                    turn_lock.release()

        return StreamingResponse(
            generate_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @application.get("/api/{unmatched_path:path}", include_in_schema=False)
    def unknown_api_route(unmatched_path: str) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"API route '/api/{unmatched_path}' was not found"},
        )

    frontend_dist = Path(active_settings.frontend_dist)
    if serve_frontend and frontend_dist.is_dir():
        assets = frontend_dist / "assets"
        if assets.is_dir():
            application.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

        @application.get("/{full_path:path}", include_in_schema=False)
        def frontend(full_path: str) -> FileResponse:
            requested = (frontend_dist / full_path).resolve()
            if full_path and requested.is_file() and frontend_dist.resolve() in requested.parents:
                return FileResponse(requested)
            return FileResponse(frontend_dist / "index.html")
    else:

        @application.get("/", include_in_schema=False)
        def api_root() -> dict[str, str]:
            return {
                "name": "Sovereign AI iBuddy API",
                "docs": "/api/docs",
                "frontend": "Build frontend/ to serve the web interface here.",
            }

    return application

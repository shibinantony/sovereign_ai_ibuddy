from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from collections.abc import AsyncIterator, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.db import ConversationStore
from backend.app.main import create_app
from backend.app.services.model import (
    HostedHuggingFaceModel,
    ModelNotConfiguredError,
    ModelUnavailableError,
)
from backend.app.services.search import SearchError


def parse_sse(body: str) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    for block in body.strip().split("\n\n"):
        event_name = "message"
        data = ""
        for line in block.splitlines():
            if line.startswith("event: "):
                event_name = line[7:]
            elif line.startswith("data: "):
                data += line[6:]
        if data:
            events.append((event_name, json.loads(data)))
    return events


class FakeSearch:
    provider_name = "fake-search"
    ready = True

    def __init__(self) -> None:
        self.queries: list[str] = []

    async def search(self, query: str) -> list[dict[str, str]]:
        self.queries.append(query)
        return [
            {
                "title": "Primary source",
                "url": "https://example.com/report",
                "snippet": "A concise result used by the test model.",
                "domain": "example.com",
            }
        ]


class FakeModel:
    ready = True

    def __init__(self) -> None:
        self.messages: Sequence[dict[str, str]] = []

    async def generate(self, messages: Sequence[dict[str, str]]) -> AsyncIterator[str]:
        self.messages = messages
        yield "Grounded "
        yield "answer [1]."


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        temporary_path = Path(self.temporary_directory.name)
        self.settings = Settings(
            database_path=temporary_path / "history.db",
            frontend_dist=temporary_path / "missing-frontend",
            model_backend="hosted",
            offline_mode=False,
            hf_token="test-token",
        )
        self.store = ConversationStore(self.settings.database_path)
        self.search = FakeSearch()
        self.model = FakeModel()
        app = create_app(
            settings=self.settings,
            store=self.store,
            search_service=self.search,
            model=self.model,
            serve_frontend=False,
        )
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.temporary_directory.cleanup()

    def create_conversation(self) -> dict[str, Any]:
        response = self.client.post("/api/conversations", json={})
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_health_reports_runtime_readiness(self) -> None:
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["model"]["ready"])
        self.assertTrue(payload["model"]["configured"])
        self.assertTrue(payload["model"]["operational"])
        self.assertEqual(
            payload["search"],
            {
                "provider": "fake-search",
                "ready": True,
                "operational": None,
                "detail": None,
            },
        )
        self.assertTrue(payload["history"]["ready"])

    def test_hosted_health_distinguishes_configured_from_operational(self) -> None:
        hosted_model = HostedHuggingFaceModel(self.settings)
        app = create_app(
            settings=self.settings,
            store=self.store,
            search_service=self.search,
            model=hosted_model,
            serve_frontend=False,
        )

        with TestClient(app) as client:
            payload = client.get("/api/health").json()

        self.assertEqual(payload["status"], "loading")
        self.assertTrue(payload["model"]["configured"])
        self.assertIsNone(payload["model"]["operational"])
        self.assertEqual(payload["model"]["state"], "configured")
        self.assertIn("awaits the first generation", payload["detail"])

    def test_local_health_identifies_missing_runtime_assets(self) -> None:
        missing_root = Path(self.temporary_directory.name) / "local-assets"
        local_settings = replace(
            self.settings,
            model_backend="llama_cpp",
            offline_mode=True,
            llama_cpp_server_path=missing_root / "llama-server.exe",
            llama_cpp_model_path=missing_root / "Qwen3-8B-Q5_K_M.gguf",
        )
        app = create_app(
            settings=local_settings,
            store=self.store,
            search_service=self.search,
            serve_frontend=False,
        )

        with TestClient(app) as client:
            payload = client.get("/api/health").json()

        self.assertEqual(payload["status"], "error")
        self.assertTrue(payload["offline_mode"])
        self.assertFalse(payload["model"]["configured"])
        self.assertFalse(payload["model"]["ready"])
        self.assertEqual(payload["model"]["state"], "missing_assets")
        self.assertEqual(payload["model"]["id"], "Qwen3-8B-Q5_K_M.gguf")

    def test_conversation_crud_and_validation(self) -> None:
        created = self.create_conversation()
        conversation_id = created["id"]
        self.assertEqual(created["title"], "New conversation")
        self.assertEqual(created["messages"], [])

        renamed = self.client.patch(
            f"/api/conversations/{conversation_id}",
            json={"title": "Research thread"},
        )
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(renamed.json()["title"], "Research thread")
        self.assertEqual(
            self.client.patch(
                f"/api/conversations/{conversation_id}", json={"title": "   "}
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                f"/api/conversations/{conversation_id}/messages/stream",
                json={"content": "", "search_mode": "auto"},
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                f"/api/conversations/{conversation_id}/messages/stream",
                json={"content": "hello", "search_mode": "invalid"},
            ).status_code,
            422,
        )

        self.assertEqual(
            self.client.delete(f"/api/conversations/{conversation_id}").status_code,
            204,
        )
        self.assertEqual(
            self.client.get(f"/api/conversations/{conversation_id}").status_code,
            404,
        )

    def test_stream_searches_generates_and_persists(self) -> None:
        created = self.create_conversation()
        question = "What is in the latest report?"
        response = self.client.post(
            f"/api/conversations/{created['id']}/messages/stream",
            json={"content": question, "search_mode": "auto"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["content-type"].startswith("text/event-stream"))
        events = parse_sse(response.text)
        self.assertEqual(
            [name for name, _ in events],
            ["meta", "sources", "delta", "delta", "done"],
        )
        self.assertTrue(events[0][1]["searched"])
        self.assertEqual(events[1][1]["sources"][0]["domain"], "example.com")
        self.assertEqual(events[-1][1]["message"]["content"], "Grounded answer [1].")
        self.assertEqual(self.search.queries, [question])
        self.assertIn("<WEB_RESEARCH_JSON>", self.model.messages[0]["content"])

        detail = self.client.get(f"/api/conversations/{created['id']}").json()
        self.assertEqual(detail["title"], question)
        self.assertEqual(
            [message["role"] for message in detail["messages"]],
            ["user", "assistant"],
        )
        self.assertTrue(detail["messages"][1]["sources"][0]["url"].startswith("https://"))
        self.assertEqual(self.client.get("/api/conversations").json()[0]["id"], created["id"])

    def test_search_off_skips_search(self) -> None:
        created = self.create_conversation()
        response = self.client.post(
            f"/api/conversations/{created['id']}/messages/stream",
            json={"content": "What is a B-tree?", "search_mode": "off"},
        )
        events = parse_sse(response.text)

        self.assertFalse(events[0][1]["searched"])
        self.assertEqual(events[1][1]["sources"], [])
        self.assertEqual(self.search.queries, [])

    def test_search_failure_degrades_to_model_answer(self) -> None:
        async def fail(_query: str) -> list[dict[str, str]]:
            raise SearchError("Search timed out")

        self.search.search = fail  # type: ignore[method-assign]
        created = self.create_conversation()
        response = self.client.post(
            f"/api/conversations/{created['id']}/messages/stream",
            json={"content": "What happened today?", "search_mode": "web"},
        )
        events = parse_sse(response.text)

        self.assertEqual(
            events[1],
            (
                "sources",
                {"sources": [], "offline": False, "search_error": "Search timed out"},
            ),
        )
        self.assertEqual(events[-1][0], "done")

    @patch("backend.app.main.SSE_HEARTBEAT_INTERVAL_SECONDS", 0.005)
    def test_search_wait_emits_sse_heartbeat(self) -> None:
        async def slow_search(query: str) -> list[dict[str, str]]:
            await asyncio.sleep(0.04)
            return await FakeSearch().search(query)

        self.search.search = slow_search  # type: ignore[method-assign]
        created = self.create_conversation()
        response = self.client.post(
            f"/api/conversations/{created['id']}/messages/stream",
            json={"content": "What happened today?", "search_mode": "web"},
        )

        self.assertIn(": keep-alive\n\n", response.text)
        self.assertEqual(parse_sse(response.text)[-1][0], "done")

    def test_model_configuration_error_is_an_sse_error(self) -> None:
        async def missing(
            _messages: Sequence[dict[str, str]],
        ) -> AsyncIterator[str]:
            raise ModelNotConfiguredError("Add HF_TOKEN to .env")
            yield ""  # pragma: no cover

        self.model.generate = missing  # type: ignore[method-assign]
        created = self.create_conversation()
        response = self.client.post(
            f"/api/conversations/{created['id']}/messages/stream",
            json={"content": "hello", "search_mode": "off"},
        )
        events = parse_sse(response.text)

        self.assertEqual(
            events[-1],
            (
                "error",
                {
                    "message": "Add HF_TOKEN to .env",
                    "code": "model_not_configured",
                },
            ),
        )

    def test_partial_model_failure_persists_one_assistant_message(self) -> None:
        async def partial_then_fail(
            _messages: Sequence[dict[str, str]],
        ) -> AsyncIterator[str]:
            yield "Useful partial answer"
            raise ModelUnavailableError("Upstream stream ended")

        self.model.generate = partial_then_fail  # type: ignore[method-assign]
        created = self.create_conversation()
        response = self.client.post(
            f"/api/conversations/{created['id']}/messages/stream",
            json={"content": "Explain it", "search_mode": "off"},
        )
        events = parse_sse(response.text)

        self.assertEqual([name for name, _ in events], ["meta", "sources", "delta", "error"])
        detail = self.client.get(f"/api/conversations/{created['id']}").json()
        self.assertEqual(
            [(item["role"], item["content"]) for item in detail["messages"]],
            [
                ("user", "Explain it"),
                ("assistant", "Useful partial answer"),
            ],
        )

    def test_unknown_api_route_is_json_404(self) -> None:
        response = self.client.get("/api/not-a-real-route")

        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.headers["content-type"].startswith("application/json"))
        self.assertIn("not found", response.json()["detail"])


class SerializedTurnTests(unittest.IsolatedAsyncioTestCase):
    @patch("backend.app.main.SSE_HEARTBEAT_INTERVAL_SECONDS", 0.005)
    async def test_same_conversation_turns_are_serialized(self) -> None:
        class ControlledModel:
            ready = True

            def __init__(self) -> None:
                self.calls: list[Sequence[dict[str, str]]] = []
                self.first_started = asyncio.Event()
                self.release_first = asyncio.Event()

            async def generate(self, messages: Sequence[dict[str, str]]) -> AsyncIterator[str]:
                self.calls.append(messages)
                call_number = len(self.calls)
                if call_number == 1:
                    self.first_started.set()
                    await self.release_first.wait()
                yield f"answer {call_number}"

        with tempfile.TemporaryDirectory() as directory:
            temporary_path = Path(directory)
            settings = Settings(
                database_path=temporary_path / "serialized.db",
                frontend_dist=temporary_path / "missing",
                model_backend="hosted",
                offline_mode=False,
                hf_token="test-token",
            )
            store = ConversationStore(settings.database_path)
            conversation = store.create_conversation()
            model = ControlledModel()
            app = create_app(
                settings=settings,
                store=store,
                search_service=FakeSearch(),
                model=model,
                serve_frontend=False,
            )
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                first = asyncio.create_task(
                    client.post(
                        f"/api/conversations/{conversation['id']}/messages/stream",
                        json={"content": "first", "search_mode": "off"},
                    )
                )
                await asyncio.wait_for(model.first_started.wait(), timeout=2)
                second = asyncio.create_task(
                    client.post(
                        f"/api/conversations/{conversation['id']}/messages/stream",
                        json={"content": "second", "search_mode": "off"},
                    )
                )
                await asyncio.sleep(0.05)
                self.assertEqual(len(model.calls), 1)
                persisted = store.get_conversation(conversation["id"])["messages"]
                self.assertEqual(
                    [item["role"] for item in persisted],
                    ["user"],
                )
                model.release_first.set()
                first_response, second_response = await asyncio.gather(first, second)

            self.assertEqual(first_response.status_code, 200)
            self.assertEqual(second_response.status_code, 200)
            self.assertIn(": keep-alive\n\n", second_response.text)
            detail = store.get_conversation(conversation["id"])
            self.assertEqual(
                [(item["role"], item["content"]) for item in detail["messages"]],
                [
                    ("user", "first"),
                    ("assistant", "answer 1"),
                    ("user", "second"),
                    ("assistant", "answer 2"),
                ],
            )


if __name__ == "__main__":
    unittest.main()

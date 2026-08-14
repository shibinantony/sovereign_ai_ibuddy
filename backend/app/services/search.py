from __future__ import annotations

import asyncio
import html
import ipaddress
import logging
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx

from backend.app.config import Settings
from backend.app.services.retrieval import (
    _is_public_ip_address,
    _is_public_web_url,
    enrich_sources,
)

logger = logging.getLogger(__name__)


class SearchError(RuntimeError):
    """A search provider failed without exposing credentials or raw internals."""


@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    domain: str

    def as_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "domain": self.domain,
        }


_SEARCH_CUES = re.compile(
    r"\b(today|tonight|current|currently|latest|recent|recently|news|update|"
    r"price|cost|weather|forecast|score|schedule|standings|election|president|"
    r"prime minister|ceo|release|version|availability|near me|research|source|"
    r"verify|fact[ -]?check|who is|what happened|when did)\b",
    re.IGNORECASE,
)

_NO_SEARCH_PREFIXES = (
    "write ",
    "rewrite ",
    "translate ",
    "summarize this",
    "brainstorm ",
    "draft ",
    "roleplay ",
    "create a poem",
    "create a story",
)


def should_search(query: str, mode: str) -> bool:
    if mode == "web":
        return True
    if mode == "off":
        return False
    compact = re.sub(r"\s+", " ", query).strip().lower()
    if not compact or compact in {"hi", "hello", "hey", "thanks", "thank you"}:
        return False
    # Freshness requirements take precedence over the requested writing style.
    # "Write a summary of today's news" still needs current evidence.
    if _SEARCH_CUES.search(compact):
        return True
    if compact.startswith(_NO_SEARCH_PREFIXES):
        return False
    # A question asking for factual information benefits from retrieval by default.
    return "?" in compact or compact.startswith(
        ("what ", "why ", "how ", "where ", "when ", "which ", "compare ")
    )


class SearchService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._operational: bool | None = None
        self._circuit_until = 0.0
        self._detail: str | None = None

    @property
    def operational(self) -> bool | None:
        return self._operational

    @property
    def detail(self) -> str | None:
        return self._detail

    @property
    def provider_name(self) -> str:
        if self.settings.offline_mode:
            return "offline"
        configured = self.settings.search_provider
        if configured != "auto":
            return configured
        if self.settings.tavily_api_key:
            return "tavily"
        if self.settings.brave_search_api_key:
            return "brave"
        return "duckduckgo"

    @property
    def ready(self) -> bool:
        provider = self.provider_name
        if provider == "offline":
            return False
        if provider == "tavily":
            return bool(self.settings.tavily_api_key)
        if provider == "brave":
            return bool(self.settings.brave_search_api_key)
        return provider in {"duckduckgo", "ddg"}

    async def search(self, query: str) -> list[dict[str, str]]:
        provider = self.provider_name
        if provider == "offline":
            return []
        if time.monotonic() < self._circuit_until:
            raise SearchError("Web search is offline; continuing with local knowledge")
        try:
            if provider == "tavily":
                raw = await self._search_tavily(query)
            elif provider == "brave":
                raw = await self._search_brave(query)
            elif provider in {"duckduckgo", "ddg"}:
                raw = await self._search_duckduckgo(query)
            else:
                raise SearchError(f"Unknown search provider: {provider}")
        except SearchError as exc:
            self._record_failure(exc)
            raise
        except (httpx.HTTPError, TimeoutError, OSError) as exc:
            logger.warning("%s search is unavailable (%s)", provider, type(exc).__name__)
            search_error = SearchError(f"{provider.title()} search is temporarily unavailable")
            self._record_failure(search_error)
            raise search_error from exc
        except Exception as exc:
            logger.warning("%s search failed (%s)", provider, type(exc).__name__, exc_info=True)
            search_error = SearchError(f"{provider.title()} search failed")
            self._record_failure(search_error)
            raise search_error from exc

        normalized = _normalize_results(raw)
        public_results = await _filter_public_results(normalized)
        sources = [item.as_dict() for item in public_results[: self.settings.search_result_count]]
        enriched = await enrich_sources(
            query,
            sources,
            timeout_seconds=self.settings.search_timeout_seconds,
        )
        self._operational = True
        self._circuit_until = 0.0
        self._detail = f"{provider.title()} search is available"
        return enriched

    def _record_failure(self, exc: SearchError) -> None:
        self._operational = False
        self._circuit_until = time.monotonic() + 30.0
        self._detail = str(exc)

    async def _search_tavily(self, query: str) -> Iterable[dict[str, Any]]:
        if not self.settings.tavily_api_key:
            raise SearchError("Tavily is selected but TAVILY_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=self.settings.search_timeout_seconds) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.settings.tavily_api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": self.settings.search_result_count,
                    "include_answer": False,
                    "include_raw_content": False,
                },
            )
            response.raise_for_status()
            payload = response.json()
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            }
            for item in payload.get("results", [])
        ]

    async def _search_brave(self, query: str) -> Iterable[dict[str, Any]]:
        if not self.settings.brave_search_api_key:
            raise SearchError("Brave is selected but BRAVE_SEARCH_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=self.settings.search_timeout_seconds) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={
                    "q": query,
                    "count": self.settings.search_result_count,
                    "safesearch": self.settings.search_safesearch,
                    "text_decorations": False,
                },
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.settings.brave_search_api_key,
                },
            )
            response.raise_for_status()
            payload = response.json()
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", ""),
            }
            for item in payload.get("web", {}).get("results", [])
        ]

    async def _search_duckduckgo(self, query: str) -> Iterable[dict[str, Any]]:
        def run() -> list[dict[str, Any]]:
            try:
                from ddgs import DDGS
            except ImportError as exc:
                raise SearchError("DuckDuckGo search requires the backend dependencies") from exc
            with DDGS(timeout=int(self.settings.search_timeout_seconds)) as client:
                return list(
                    client.text(
                        query,
                        region="wt-wt",
                        safesearch=self.settings.search_safesearch,
                        max_results=self.settings.search_result_count,
                    )
                )

        results = await asyncio.to_thread(run)
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("href") or item.get("url", ""),
                "snippet": item.get("body") or item.get("description", ""),
            }
            for item in results
        ]


def _clean_text(value: Any, maximum: int) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > maximum:
        text = f"{text[: maximum - 1].rstrip()}…"
    return text


def _normalize_url(value: Any) -> tuple[str, str] | None:
    raw = str(value or "").strip()
    try:
        parsed = urlparse(raw)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 80, 443}
    ):
        return None
    host = parsed.hostname.casefold().rstrip(".")
    if host == "localhost" or host.endswith(".localhost"):
        return None
    try:
        if not _is_public_ip_address(ipaddress.ip_address(host)):
            return None
    except ValueError:
        # Hostnames receive DNS-aware public-address validation before they can
        # be returned to the model, persistence layer, or UI.
        pass
    if host.startswith("www."):
        host = host[4:]
    normalized = urlunparse(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, "", parsed.query, "")
    )
    return normalized, host


async def _filter_public_results(results: Iterable[SearchResult]) -> list[SearchResult]:
    """Keep only results whose current DNS resolution is entirely public."""

    candidates = list(results)
    if not candidates:
        return []
    verdicts = await asyncio.gather(
        *(_is_public_web_url(item.url) for item in candidates),
        return_exceptions=True,
    )
    return [
        item
        for item, verdict in zip(candidates, verdicts, strict=True)
        if verdict is True
    ]


def _normalize_results(raw: Iterable[dict[str, Any]]) -> list[SearchResult]:
    results: list[SearchResult] = []
    seen: set[str] = set()
    for item in raw:
        normalized_url = _normalize_url(item.get("url") or item.get("href"))
        if normalized_url is None:
            continue
        url, domain = normalized_url
        dedupe_key = url.rstrip("/").lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        title = _clean_text(item.get("title"), 180) or domain
        results.append(
            SearchResult(
                title=title,
                url=url,
                snippet=_clean_text(
                    item.get("snippet") or item.get("body") or item.get("description"),
                    600,
                ),
                domain=domain,
            )
        )
    return results

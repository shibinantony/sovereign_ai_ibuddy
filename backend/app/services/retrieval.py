from __future__ import annotations

import asyncio
import html
import ipaddress
import re
import socket
from collections.abc import Sequence
from urllib.parse import urljoin, urlparse

import httpx

_WORD = re.compile(r"[\w'-]{3,}", re.UNICODE)
_SPACE = re.compile(r"\s+")
_STOP_WORDS = {
    "about",
    "after",
    "before",
    "could",
    "from",
    "have",
    "into",
    "latest",
    "should",
    "that",
    "their",
    "there",
    "these",
    "this",
    "what",
    "when",
    "where",
    "which",
    "with",
    "would",
}
_MAX_DOWNLOAD_BYTES = 1_000_000
_MAX_EXCERPT_CHARS = 1_200
_LOW_AUTHORITY_DOMAINS = (
    "geeksforgeeks.org",
    "medium.com",
    "nproxy.org",
    "pinterest.com",
    "quora.com",
    "wikipedia.org",
)


def _is_public_ip_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        address.is_global
        and not address.is_multicast
        and not address.is_reserved
        and not address.is_unspecified
    )


def _terms(value: str) -> set[str]:
    return {word.casefold() for word in _WORD.findall(value) if word.casefold() not in _STOP_WORDS}


def rank_sources(query: str, sources: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    """Apply a small deterministic relevance boost without needing another model."""

    query_terms = _terms(query)
    ranked: list[tuple[float, int, dict[str, str]]] = []
    for index, source in enumerate(sources):
        title_terms = _terms(source.get("title", ""))
        snippet_terms = _terms(source.get("snippet", ""))
        domain = source.get("domain", "").casefold()
        if not domain:
            domain = (urlparse(source.get("url", "")).hostname or "").casefold()
        domain_terms = _terms(domain.replace(".", " ").replace("-", " "))
        title_overlap = len(query_terms & title_terms)
        snippet_overlap = len(query_terms & snippet_terms)
        domain_overlap = len(query_terms & domain_terms)
        provider_order = max(0.0, 2.0 - index * 0.15)
        authority = 0.0
        if domain.endswith(".gov"):
            authority += 5.0
        elif domain.endswith(".edu"):
            authority += 3.0
        if domain.startswith(("developer.", "devguide.", "docs.", "status.")):
            authority += 3.0
        if "official" in title_terms:
            authority += 2.0
        if any(domain == item or domain.endswith(f".{item}") for item in _LOW_AUTHORITY_DOMAINS):
            authority -= 4.0
        score = (
            provider_order
            + authority
            + title_overlap * 3.0
            + domain_overlap * 2.0
            + snippet_overlap
        )
        ranked.append((score, index, dict(source)))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in ranked]


async def enrich_sources(
    query: str,
    sources: Sequence[dict[str, str]],
    *,
    timeout_seconds: float,
    fetch_count: int = 2,
) -> list[dict[str, str]]:
    """Rank search hits and attach bounded excerpts from the strongest public pages."""

    ranked = rank_sources(query, sources)
    if not ranked or fetch_count <= 0:
        return ranked

    timeout = httpx.Timeout(
        timeout=min(6.0, timeout_seconds),
        connect=min(3.0, timeout_seconds),
    )
    limits = httpx.Limits(max_connections=fetch_count, max_keepalive_connections=fetch_count)
    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=False) as client:
        tasks = [
            asyncio.create_task(_fetch_excerpt(client, source.get("url", "")))
            for source in ranked[:fetch_count]
        ]
        excerpts = await asyncio.gather(*tasks, return_exceptions=True)

    for source, excerpt in zip(ranked, excerpts, strict=False):
        if not isinstance(excerpt, str) or not excerpt:
            continue
        original = source.get("snippet", "").strip()
        combined = f"{original}\n\nPage excerpt: {excerpt}" if original else excerpt
        source["snippet"] = combined[:1_600].rstrip()
    return ranked


async def _fetch_excerpt(client: httpx.AsyncClient, initial_url: str) -> str:
    url = initial_url
    for _redirect in range(3):
        if not await _is_public_web_url(url):
            return ""
        async with client.stream(
            "GET",
            url,
            headers={
                "Accept": "text/html, text/plain;q=0.9",
                "User-Agent": "iBuddy/1.0 (+local research assistant)",
            },
        ) as response:
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location:
                    return ""
                url = urljoin(url, location)
                continue
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").casefold()
            if not (content_type.startswith("text/html") or content_type.startswith("text/plain")):
                return ""
            content_length = response.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > _MAX_DOWNLOAD_BYTES:
                        return ""
                except ValueError:
                    pass
            chunks: list[bytes] = []
            size = 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > _MAX_DOWNLOAD_BYTES:
                    return ""
                chunks.append(chunk)
            encoding = response.encoding or "utf-8"
            text = b"".join(chunks).decode(encoding, errors="replace")
            return _extract_readable_text(text, content_type)
    return ""


async def _is_public_web_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 80, 443}
    ):
        return False

    host = parsed.hostname.casefold().rstrip(".")
    if host == "localhost" or host.endswith(".localhost"):
        return False
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            records = await asyncio.get_running_loop().getaddrinfo(
                host,
                port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except OSError:
            return False
        addresses = []
        for record in records:
            try:
                addresses.append(ipaddress.ip_address(record[4][0]))
            except ValueError:
                return False
    return bool(addresses) and all(_is_public_ip_address(address) for address in addresses)


def _extract_readable_text(value: str, content_type: str) -> str:
    if content_type.startswith("text/plain"):
        return _SPACE.sub(" ", value).strip()[:_MAX_EXCERPT_CHARS]
    try:
        from lxml import html as lxml_html

        document = lxml_html.fromstring(value)
        for node in document.xpath("//script|//style|//noscript|//svg|//form|//nav|//footer"):
            node.drop_tree()
        candidates = document.xpath("//article//p | //main//p | //p")
        paragraphs = [_SPACE.sub(" ", " ".join(node.itertext())).strip() for node in candidates]
    except (ImportError, ValueError):
        without_code = re.sub(
            r"<(script|style|noscript)\b[^>]*>.*?</\1>",
            " ",
            value,
            flags=re.IGNORECASE | re.DOTALL,
        )
        paragraphs = [html.unescape(re.sub(r"<[^>]+>", " ", without_code))]

    selected: list[str] = []
    length = 0
    seen: set[str] = set()
    for paragraph in paragraphs:
        paragraph = _SPACE.sub(" ", paragraph).strip()
        key = paragraph.casefold()
        if len(paragraph) < 60 or key in seen:
            continue
        seen.add(key)
        remaining = _MAX_EXCERPT_CHARS - length
        if remaining <= 0:
            break
        selected.append(paragraph[:remaining])
        length += len(selected[-1]) + 1
    return " ".join(selected).strip()

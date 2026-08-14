from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from backend.app.config import Settings
from backend.app.services.retrieval import (
    _extract_readable_text,
    _is_public_web_url,
    enrich_sources,
    rank_sources,
)
from backend.app.services.search import (
    SearchError,
    SearchService,
    _normalize_results,
    should_search,
)


class SearchTests(unittest.TestCase):
    def test_private_policy_defaults_are_offline_with_moderate_safe_search(self) -> None:
        settings = Settings()

        self.assertTrue(settings.offline_mode)
        self.assertEqual(settings.search_safesearch, "moderate")

    def test_auto_search_decision(self) -> None:
        self.assertTrue(should_search("What changed in the latest Python release?", "auto"))
        self.assertTrue(should_search("Explain B-trees?", "auto"))
        self.assertTrue(should_search("Write a summary of the latest security news", "auto"))
        self.assertTrue(should_search("Draft a current market analysis", "auto"))
        self.assertTrue(should_search("Summarize today's release notes", "auto"))
        self.assertFalse(should_search("Write a haiku about databases", "auto"))
        self.assertFalse(should_search("hello", "auto"))
        self.assertTrue(should_search("write a haiku", "web"))
        self.assertFalse(should_search("what happened today?", "off"))

    def test_result_normalization_deduplicates_and_rejects_invalid_urls(self) -> None:
        results = _normalize_results(
            [
                {
                    "title": "<b>Result</b>",
                    "url": "https://www.example.com/report#section",
                    "snippet": "Useful &amp; current",
                },
                {
                    "title": "Duplicate",
                    "url": "https://www.example.com/report#other",
                    "snippet": "duplicate",
                },
                {
                    "title": "Unsafe",
                    "url": "javascript:alert(1)",
                    "snippet": "",
                },
                {
                    "title": "Credential bearing",
                    "url": "https://user:password@example.com/private",
                    "snippet": "",
                },
                {
                    "title": "Loopback",
                    "url": "http://127.0.0.1/admin",
                    "snippet": "",
                },
                {
                    "title": "Localhost",
                    "url": "http://service.localhost/admin",
                    "snippet": "",
                },
                {
                    "title": "Private network",
                    "url": "http://10.0.0.7/admin",
                    "snippet": "",
                },
                {
                    "title": "Link local",
                    "url": "http://169.254.169.254/latest/meta-data",
                    "snippet": "",
                },
                {
                    "title": "Reserved",
                    "url": "http://192.0.2.10/example",
                    "snippet": "",
                },
                {
                    "title": "Multicast",
                    "url": "http://224.0.0.1/example",
                    "snippet": "",
                },
                {
                    "title": "Non-web port",
                    "url": "https://example.com:8080/admin",
                    "snippet": "",
                },
            ]
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Result")
        self.assertEqual(results[0].snippet, "Useful & current")
        self.assertEqual(results[0].domain, "example.com")

    def test_relevance_ranking_and_readable_extraction(self) -> None:
        ranked = rank_sources(
            "current battery recycling policy",
            [
                {
                    "title": "General policy archive",
                    "url": "https://archive.example/",
                    "snippet": "Older material",
                },
                {
                    "title": "Current battery recycling policy",
                    "url": "https://policy.example/",
                    "snippet": "The latest recycling requirements",
                },
            ],
        )
        self.assertEqual(ranked[0]["url"], "https://policy.example/")

        authority_ranked = rank_sources(
            "latest Python release status",
            [
                {
                    "title": "Latest Python release tutorial",
                    "url": "https://www.geeksforgeeks.org/python/latest/",
                    "snippet": "A third-party tutorial",
                    "domain": "geeksforgeeks.org",
                },
                {
                    "title": "Status of Python versions",
                    "url": "https://devguide.python.org/versions/",
                    "snippet": "Maintained release status",
                    "domain": "devguide.python.org",
                },
            ],
        )
        self.assertEqual(authority_ranked[0]["domain"], "devguide.python.org")

        extracted = _extract_readable_text(
            """
            <html><nav>Navigation should disappear</nav><main>
            <p>This is a substantive current-policy paragraph with enough text
            to be selected by the retrieval extractor for grounding.</p>
            <script>ignore_me()</script></main></html>
            """,
            "text/html",
        )
        self.assertIn("substantive current-policy paragraph", extracted)
        self.assertNotIn("ignore_me", extracted)


class RetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def test_enrichment_is_bounded_and_rejects_private_targets(self) -> None:
        self.assertFalse(await _is_public_web_url("http://127.0.0.1/private"))
        self.assertFalse(await _is_public_web_url("http://[::1]/private"))
        self.assertFalse(await _is_public_web_url("http://service.localhost/private"))
        self.assertFalse(await _is_public_web_url("http://224.0.0.1/multicast"))
        self.assertFalse(await _is_public_web_url("https://user@example.com/private"))
        self.assertFalse(await _is_public_web_url("https://@example.com/private"))
        self.assertFalse(await _is_public_web_url("https://example.com:8443/private"))
        self.assertFalse(await _is_public_web_url("file:///etc/passwd"))

        source = {
            "title": "Battery policy",
            "url": "https://example.com/policy",
            "snippet": "Search summary",
            "domain": "example.com",
        }
        with patch(
            "backend.app.services.retrieval._fetch_excerpt",
            new=AsyncMock(return_value="Verified page text " * 300),
        ):
            enriched = await enrich_sources(
                "current battery policy",
                [source],
                timeout_seconds=2,
            )

        self.assertIn("Page excerpt:", enriched[0]["snippet"])
        self.assertLessEqual(len(enriched[0]["snippet"]), 1_600)

    async def test_search_discards_hostnames_that_fail_public_address_validation(self) -> None:
        class StaticSearch(SearchService):
            async def _search_duckduckgo(self, _query: str):
                return [
                    {
                        "title": "Public result",
                        "url": "https://public.example/report",
                        "snippet": "Public evidence",
                    },
                    {
                        "title": "DNS-rebound result",
                        "url": "https://rebind.example/admin",
                        "snippet": "Unsafe evidence",
                    },
                ]

        async def validate(url: str) -> bool:
            return url.startswith("https://public.example/")

        async def passthrough(_query: str, sources, **_kwargs):
            return list(sources)

        service = StaticSearch(
            Settings(
                offline_mode=False,
                search_provider="duckduckgo",
                search_result_count=4,
            )
        )
        with (
            patch(
                "backend.app.services.search._is_public_web_url",
                new=AsyncMock(side_effect=validate),
            ) as validator,
            patch(
                "backend.app.services.search.enrich_sources",
                new=AsyncMock(side_effect=passthrough),
            ),
        ):
            results = await service.search("latest report")

        self.assertEqual([item["url"] for item in results], ["https://public.example/report"])
        self.assertEqual(validator.await_count, 2)

    async def test_offline_mode_never_calls_a_search_provider(self) -> None:
        service = SearchService(Settings(offline_mode=True))
        self.assertEqual(service.provider_name, "offline")
        self.assertFalse(service.ready)
        self.assertEqual(await service.search("latest news"), [])

    async def test_search_failure_opens_a_short_circuit(self) -> None:
        class FailingSearch(SearchService):
            def __init__(self) -> None:
                super().__init__(Settings(offline_mode=False, search_provider="duckduckgo"))
                self.calls = 0

            async def _search_duckduckgo(self, _query: str):
                self.calls += 1
                raise OSError("offline")

        service = FailingSearch()
        with self.assertRaises(SearchError):
            await service.search("latest update")
        with self.assertRaisesRegex(SearchError, "continuing with local knowledge"):
            await service.search("another update")
        self.assertEqual(service.calls, 1)
        self.assertFalse(service.operational)


if __name__ == "__main__":
    unittest.main()

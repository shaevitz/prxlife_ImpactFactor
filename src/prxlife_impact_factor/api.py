from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from typing import Any


class APIError(RuntimeError):
    """Raised when a remote API request fails."""


def normalize_openalex_source_id(source_id: str) -> str:
    if source_id.startswith("https://openalex.org/"):
        return source_id
    if source_id.startswith("S") and source_id[1:].isdigit():
        return f"https://openalex.org/{source_id}"
    raise ValueError(f"Unsupported OpenAlex source id: {source_id}")


class JsonAPIClient:
    def __init__(self, user_agent: str | None = None, pause_seconds: float = 0.1) -> None:
        self.user_agent = user_agent or (
            "prxlife-impact-factor/0.1 "
            "(https://github.com/shaevitz/prxlife_ImpactFactor)"
        )
        self.pause_seconds = pause_seconds

    def _get_json(self, url: str) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except Exception as exc:  # pragma: no cover - exercised in integration with live APIs
            raise APIError(f"Request failed for {url}: {exc}") from exc

    def fetch_openalex_source(self, source_id: str) -> dict[str, Any]:
        normalized = normalize_openalex_source_id(source_id)
        source_key = normalized.rsplit("/", 1)[-1]
        return self._get_json(f"https://api.openalex.org/sources/{source_key}")

    def fetch_openalex_works(self, source_id: str, publication_year: int) -> list[dict[str, Any]]:
        normalized = normalize_openalex_source_id(source_id)
        cursor = "*"
        works: list[dict[str, Any]] = []

        while True:
            params = urllib.parse.urlencode(
                {
                    "filter": (
                        f"primary_location.source.id:{normalized},"
                        f"publication_year:{publication_year}"
                    ),
                    "per-page": 200,
                    "cursor": cursor,
                }
            )
            payload = self._get_json(f"https://api.openalex.org/works?{params}")
            works.extend(payload.get("results", []))

            meta = payload.get("meta", {})
            cursor = meta.get("next_cursor")
            if not cursor:
                break

            if self.pause_seconds:
                time.sleep(self.pause_seconds)

        return works

    def fetch_crossref_journal(self, issn: str) -> dict[str, Any]:
        return self._get_json(f"https://api.crossref.org/journals/{issn}")

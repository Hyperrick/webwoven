from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qs, urlparse

from webwoven_pipeline.wikidata import WikidataClient, entities_from_batches


class RecordingTransport:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, Mapping[str, str]]] = []

    def get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
    ) -> dict[str, Any]:
        self.calls.append((url, headers))
        return self.responses.pop(0)


def test_client_retries_maxlag_then_reuses_immutable_cache(tmp_path) -> None:
    transport = RecordingTransport(
        [
            {"error": {"code": "maxlag"}},
            {"entities": {"Q2": {"id": "Q2"}, "Q1": {"id": "Q1"}}},
        ]
    )
    sleeps: list[float] = []
    client = WikidataClient(
        tmp_path,
        "Webwoven/0.1 (build@example.test)",
        transport=transport,
        sleeper=sleeps.append,
        max_retries=1,
    )

    first = client.fetch_entities(["Q2", "Q1", "Q2"])
    second = client.fetch_entities(["Q1", "Q2"])

    assert sleeps == [1]
    assert len(transport.calls) == 2
    assert first[0].sha256 == second[0].sha256
    assert entities_from_batches(second) == {"Q1": {"id": "Q1"}, "Q2": {"id": "Q2"}}
    query = parse_qs(urlparse(transport.calls[0][0]).query)
    assert query["action"] == ["wbgetentities"]
    assert query["maxlag"] == ["5"]
    assert query["ids"] == ["Q1|Q2"]
    assert transport.calls[0][1]["User-Agent"].startswith("Webwoven/")


def test_client_splits_batches_at_fifty(tmp_path) -> None:
    transport = RecordingTransport([{"entities": {}}, {"entities": {}}])
    client = WikidataClient(tmp_path, "Webwoven/0.1 (build@example.test)", transport=transport)

    batches = client.fetch_entities(f"Q{index}" for index in range(1, 52))

    assert [len(batch.qids) for batch in batches] == [50, 1]
    assert len(transport.calls) == 2


def test_client_supports_bounded_lag_and_request_pacing(tmp_path) -> None:
    transport = RecordingTransport([{"entities": {"Q1": {"id": "Q1"}}}])
    sleeps: list[float] = []
    client = WikidataClient(
        tmp_path,
        "Webwoven/0.1 (build@example.test)",
        transport=transport,
        sleeper=sleeps.append,
        max_lag=120,
        request_interval=0.25,
    )

    client.fetch_entities(["Q1"])

    query = parse_qs(urlparse(transport.calls[0][0]).query)
    assert query["maxlag"] == ["120"]
    assert sleeps == [0.25]

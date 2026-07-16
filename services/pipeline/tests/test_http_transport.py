from __future__ import annotations

from urllib.error import HTTPError

import httpx
import pytest
from webwoven_pipeline.http_transport import HttpxBinaryTransport


def _client(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(transport=handler, follow_redirects=True)


def test_pooled_binary_transport_streams_a_bounded_image() -> None:
    client = _client(
        httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"Content-Type": "image/jpeg", "Content-Length": "4"},
                content=b"data",
                request=request,
            )
        )
    )
    transport = HttpxBinaryTransport(client)

    response = transport.get_bytes(
        "https://upload.wikimedia.org/example.jpg",
        headers={"User-Agent": "Webwoven test"},
        timeout=1,
        max_bytes=4,
    )

    assert response.body == b"data"
    assert response.content_type == "image/jpeg"
    assert response.final_url == "https://upload.wikimedia.org/example.jpg"
    client.close()


def test_pooled_binary_transport_rejects_an_oversized_image() -> None:
    client = _client(
        httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"Content-Type": "image/png"},
                content=b"oversized",
                request=request,
            )
        )
    )
    transport = HttpxBinaryTransport(client)

    with pytest.raises(ValueError, match="size limit"):
        transport.get_bytes(
            "https://upload.wikimedia.org/example.png",
            headers={},
            timeout=1,
            max_bytes=4,
        )
    client.close()


def test_pooled_binary_transport_preserves_http_status_for_retries() -> None:
    client = _client(
        httpx.MockTransport(
            lambda request: httpx.Response(
                429,
                headers={"Retry-After": "2"},
                request=request,
            )
        )
    )
    transport = HttpxBinaryTransport(client)

    with pytest.raises(HTTPError) as raised:
        transport.get_bytes(
            "https://upload.wikimedia.org/example.jpg",
            headers={},
            timeout=1,
            max_bytes=4,
        )
    assert raised.value.code == 429
    assert raised.value.headers.get("Retry-After") == "2"
    raised.value.close()
    client.close()

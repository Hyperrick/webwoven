"""Compact HMAC-signed tokens with explicit purpose separation."""

import base64
import hashlib
import hmac
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, cast

from webwoven_api.domain.errors import ForbiddenError


@dataclass(frozen=True, slots=True)
class EdgeTokenClaims:
    session_id: str
    graph_version: str
    source_id: str
    edge_id: str
    state_version: int
    expires_at: int


class EdgeTokenSigner:
    def __init__(self, secret: str, *, ttl_seconds: int = 300) -> None:
        self._codec = SignedTokenCodec(secret, purpose="edge")
        self._ttl_seconds = ttl_seconds

    def issue(
        self,
        *,
        session_id: str,
        graph_version: str,
        source_id: str,
        edge_id: str,
        state_version: int,
    ) -> str:
        claims = EdgeTokenClaims(
            session_id=session_id,
            graph_version=graph_version,
            source_id=source_id,
            edge_id=edge_id,
            state_version=state_version,
            expires_at=int(time.time()) + self._ttl_seconds,
        )
        return self._codec.encode(asdict(claims))

    def verify(self, token: str) -> EdgeTokenClaims:
        payload = self._codec.decode(token)
        try:
            claims = EdgeTokenClaims(
                session_id=str(payload["session_id"]),
                graph_version=str(payload["graph_version"]),
                source_id=str(payload["source_id"]),
                edge_id=str(payload["edge_id"]),
                state_version=int(payload["state_version"]),
                expires_at=int(payload["expires_at"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ForbiddenError("Malformed edge token") from error
        if claims.expires_at < int(time.time()):
            raise ForbiddenError("Edge token has expired")
        return claims


class GuestCookieSigner:
    def __init__(self, secret: str, *, ttl_seconds: int = 60 * 60 * 24 * 30) -> None:
        self._codec = SignedTokenCodec(secret, purpose="guest-cookie")
        self._ttl_seconds = ttl_seconds

    def issue(self, guest_id: str) -> str:
        return self._codec.encode(
            {"guest_id": guest_id, "expires_at": int(time.time()) + self._ttl_seconds}
        )

    def verify(self, token: str) -> str:
        payload = self._codec.decode(token)
        try:
            guest_id = str(payload["guest_id"])
            expires_at = int(payload["expires_at"])
        except (KeyError, TypeError, ValueError) as error:
            raise ForbiddenError("Malformed guest cookie") from error
        if expires_at < int(time.time()):
            raise ForbiddenError("Guest cookie has expired")
        return guest_id


class SignedTokenCodec:
    def __init__(self, secret: str, *, purpose: str) -> None:
        if len(secret) < 32:
            raise ValueError(f"{purpose} secret must contain at least 32 characters")
        self._key = hmac.new(secret.encode(), purpose.encode(), hashlib.sha256).digest()

    def encode(self, payload: dict[str, Any]) -> str:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        encoded = _urlsafe_encode(body)
        signature = _urlsafe_encode(hmac.new(self._key, encoded.encode(), hashlib.sha256).digest())
        return f"{encoded}.{signature}"

    def decode(self, token: str) -> dict[str, Any]:
        try:
            encoded, supplied = token.split(".", 1)
        except ValueError as error:
            raise ForbiddenError("Malformed signed token") from error
        expected = _urlsafe_encode(hmac.new(self._key, encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied, expected):
            raise ForbiddenError("Invalid signed token")
        try:
            payload = json.loads(_urlsafe_decode(encoded))
        except (ValueError, json.JSONDecodeError) as error:
            raise ForbiddenError("Malformed signed token") from error
        if not isinstance(payload, dict):
            raise ForbiddenError("Malformed signed token")
        return cast(dict[str, Any], payload)


def _urlsafe_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _urlsafe_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)

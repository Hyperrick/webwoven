"""Pseudonymous rate-limit keys that never retain raw network addresses."""

import hashlib
import hmac

from starlette.requests import HTTPConnection

from webwoven_api.domain.errors import ForbiddenError
from webwoven_api.security.tokens import GuestCookieSigner


def request_rate_identity(
    connection: HTTPConnection,
    *,
    cookie_name: str,
    signer: GuestCookieSigner,
    hmac_secret: str,
    prefer_guest: bool,
) -> str:
    if prefer_guest:
        token = connection.cookies.get(cookie_name)
        if token is not None:
            try:
                return guest_rate_identity(signer.verify(token), hmac_secret)
            except ForbiddenError:
                pass
    address = connection.client.host if connection.client is not None else "unknown"
    return _digest(f"network:{address}", hmac_secret)


def guest_rate_identity(guest_id: str, hmac_secret: str) -> str:
    return _digest(f"guest:{guest_id}", hmac_secret)


def _digest(value: str, secret: str) -> str:
    return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()

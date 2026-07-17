#!/usr/bin/env sh
set -eu

: "${UMAMI_ADMIN_PASSWORD:?UMAMI_ADMIN_PASSWORD is required}"
: "${WEBWOVEN_ANALYTICS_WEBSITE_ID:?WEBWOVEN_ANALYTICS_WEBSITE_ID is required}"
: "${WEBWOVEN_ANALYTICS_DOMAIN:?WEBWOVEN_ANALYTICS_DOMAIN is required}"

analytics_port=${WEBWOVEN_ANALYTICS_PORT:-3000}
export WEBWOVEN_ANALYTICS_BOOTSTRAP_URL="http://127.0.0.1:$analytics_port"

python3 <<'PY'
import json
import os
import urllib.error
import urllib.request

base_url = os.environ["WEBWOVEN_ANALYTICS_BOOTSTRAP_URL"]
admin_password = os.environ["UMAMI_ADMIN_PASSWORD"]
website_id = os.environ["WEBWOVEN_ANALYTICS_WEBSITE_ID"]
domain = os.environ["WEBWOVEN_ANALYTICS_DOMAIN"]


def request(
    method,
    path,
    payload=None,
    token=None,
    allow_not_found=False,
    allow_unauthorized=False,
):
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{base_url}{path}", data=body, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            content = response.read()
            return None if not content else json.loads(content)
    except urllib.error.HTTPError as error:
        if allow_not_found and error.code == 404:
            return None
        if allow_unauthorized and error.code == 401:
            return None
        detail = error.read().decode(errors="replace")
        raise SystemExit(
            f"analytics API request failed: {method} {path} returned {error.code}: {detail}"
        ) from error


def login(password):
    return request(
        "POST",
        "/api/auth/login",
        {"username": "admin", "password": password},
        allow_unauthorized=True,
    )


authentication = login(admin_password)
if authentication is None:
    authentication = login("umami")
    if authentication is None:
        raise SystemExit("analytics admin credentials do not match the deployment secret")
    request(
        "POST",
        f"/api/users/{authentication['user']['id']}",
        {"password": admin_password},
        authentication["token"],
    )
    authentication = login(admin_password)
    if authentication is None:
        raise SystemExit("analytics admin password rotation failed")

token = authentication["token"]
website = request(
    "GET", f"/api/websites/{website_id}", token=token, allow_not_found=True
)
if website is None:
    website = request(
        "POST",
        "/api/websites",
        {
            "id": website_id,
            "name": "Webwoven",
            "domain": domain,
            "shareId": None,
        },
        token,
    )

if website.get("domain") != domain:
    raise SystemExit("analytics website ID belongs to a different domain")

request(
    "POST",
    f"/api/websites/{website_id}",
    {
        "name": "Webwoven",
        "domain": domain,
        "shareId": None,
        "replayEnabled": False,
    },
    token,
)

website = request("GET", f"/api/websites/{website_id}", token=token)
if website.get("replayEnabled") is not False:
    raise SystemExit("analytics session recording must remain disabled")

print("analytics bootstrap verified")
PY

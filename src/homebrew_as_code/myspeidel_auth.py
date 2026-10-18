"""Official MySpeidel username/password login; no persistent credential storage.

Only POST /v1.0/auth/authentication is permitted. Recipe calls remain GET-only.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

from .myspeidel import BASE_URL, MySpeidelError, MySpeidelClient


def login(username: str, password: str,
          opener: Callable[..., Any] | None = None) -> str:
    """Return a session token in memory; never log the credentials or response."""
    if not isinstance(username, str) or not username.strip():
        raise MySpeidelError("Username is required")
    if not isinstance(password, str) or not password:
        raise MySpeidelError("Password is required")
    payload = json.dumps({"username": username, "pass": password}).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + "/v1.0/auth/authentication",
        data=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json",
                 "User-Agent": "Homebrew-as-Code/0.3.0"},
        method="POST",
    )
    try:
        with (opener or urllib.request.urlopen)(request, timeout=15) as response:
            raw = response.read(65537)
            if len(raw) > 65536:
                raise MySpeidelError("Authentication response too large")
            data = json.loads(raw)
    except urllib.error.HTTPError as exc:
        raise MySpeidelError(f"Authentication failed (HTTP {exc.code})") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise MySpeidelError("Unable to reach MySpeidel authentication API") from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise MySpeidelError("Authentication returned invalid JSON") from None
    if not isinstance(data, dict) or not isinstance(data.get("token"), str) or not data["token"].strip():
        raise MySpeidelError("Authentication response has no token")
    if "\r" in data["token"] or "\n" in data["token"]:
        raise MySpeidelError("Authentication returned invalid token")
    return data["token"]


def authenticated_client(username: str, password: str,
                         opener: Callable[..., Any] | None = None) -> MySpeidelClient:
    """Construct a token-authenticated GET-only client without saving its token."""
    return MySpeidelClient(token=login(username, password, opener=opener), opener=opener)

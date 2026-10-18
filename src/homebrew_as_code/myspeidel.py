"""Strictly read-only MySpeidel API v1.0 client (no account mutation)."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

BASE_URL = "https://api.cloud.myspeidel.com"
UUID_PATTERN = re.compile(r"^[0-9]+$")


class MySpeidelError(RuntimeError):
    """An API request failed without exposing authentication secrets."""


class MySpeidelClient:
    """API v1.0 client supporting only documented recipe GET operations.

    Token source: MYSPEIDEL_TOKEN environment variable. Never pass a token
    through command-line arguments or commit it to source control.
    """

    def __init__(self, token: str | None = None,
                 opener: Callable[..., Any] | None = None):
        self._token = token if token is not None else os.environ.get("MYSPEIDEL_TOKEN", "")
        if not self._token or not self._token.strip():
            raise MySpeidelError("MYSPEIDEL_TOKEN is missing")
        if "\r" in self._token or "\n" in self._token:
            raise MySpeidelError("Invalid token")
        self._opener = opener or urllib.request.urlopen

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        # Only fixed allowlisted endpoints. No arbitrary URL or path supplied by caller.
        if path != "/v1.0/propfind/recipe" and not re.fullmatch(r"/v1\.0/recipe/[0-9]+", path):
            raise MySpeidelError("Disallowed read endpoint")
        url = BASE_URL + path
        if params:
            if path != "/v1.0/propfind/recipe" or set(params) - {"machineSize", "includePublic", "recipeType"}:
                raise MySpeidelError("Disallowed query parameter")
            url += "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "User-Agent": "Homebrew-as-Code/0.2.0",
        }, method="GET")
        try:
            with self._opener(request, timeout=15) as response:
                raw = response.read(5_000_001)
                if len(raw) > 5_000_000:
                    raise MySpeidelError("API response exceeds 5 MB limit")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            raise MySpeidelError(f"MySpeidel returned HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise MySpeidelError("Unable to reach MySpeidel API") from None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MySpeidelError("MySpeidel returned invalid JSON") from None

    def list_recipes(self, *, machine_size: int | None = None,
                     include_public: bool = False) -> Any:
        params = {"includePublic": "true" if include_public else "false"}
        if machine_size is not None:
            if isinstance(machine_size, bool) or machine_size <= 0:
                raise MySpeidelError("Invalid machine size")
            params["machineSize"] = str(machine_size)
        return self._get("/v1.0/propfind/recipe", params)

    def get_recipe(self, uuid: str) -> Any:
        if not UUID_PATTERN.fullmatch(uuid):
            raise MySpeidelError("Recipe UUID must be numeric")
        return self._get(f"/v1.0/recipe/{uuid}")


def inspect_structure(value: Any, *, depth: int = 0, max_depth: int = 5) -> Any:
    """Return field names and JSON types only; never export private values."""
    if depth >= max_depth:
        return type(value).__name__
    if isinstance(value, dict):
        return {str(key): inspect_structure(child, depth=depth + 1, max_depth=max_depth)
                for key, child in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, list):
        return {"type": "array", "length": len(value),
                "item_schema": inspect_structure(value[0], depth=depth + 1, max_depth=max_depth) if value else None}
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__

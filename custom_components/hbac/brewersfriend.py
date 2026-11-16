"""Read-only Brewer's Friend REST API, with a bounded BeerXML response."""
import json
import re
import time

from aiohttp import ClientError, ClientTimeout

from .api import BrewfatherAuthError, BrewfatherError
from .beerxml import MAX_BYTES, normalized_recipe, parse_beerxml


class BrewersFriendClient:
    def __init__(self, session, api_key):
        self.session = session
        self.api_key = api_key
        self.retry_at = 0

    async def request(self, suffix="", **params):
        if time.monotonic() < self.retry_at:
            raise BrewfatherError("Brewer's Friend: rate limit reached. Try again later.")
        try:
            async with self.session.get("https://api.brewersfriend.com/v1/recipes" + suffix,
                                        headers={"X-API-KEY": self.api_key}, params=params,
                                        timeout=ClientTimeout(total=20), allow_redirects=False) as response:
                if response.status in (401, 403):
                    raise BrewfatherAuthError("Brewer's Friend: invalid API key or missing access.")
                if response.status == 429:
                    try:
                        delay = min(3600, max(1, float(response.headers.get("Retry-After", 60))))
                    except ValueError:
                        delay = 60
                    self.retry_at = time.monotonic() + delay
                    raise BrewfatherError("Brewer's Friend: rate limit reached. Try again later.")
                raw = bytearray()
                async for chunk in response.content.iter_chunked(65536):
                    raw.extend(chunk)
                    if len(raw) > MAX_BYTES:
                        raise BrewfatherError("Brewer's Friend: response is too large.")
                if response.status == 404 and not suffix:
                    # The live collection endpoint uses this exact error for an
                    # authenticated account with no recipes (also end of paging).
                    try:
                        empty = json.loads(raw)
                    except (ValueError, UnicodeError):
                        empty = None
                    if empty == {"message": "not-found", "detail": "no recipes found"}:
                        return b'{"recipes": []}'
                if response.status != 200:
                    raise BrewfatherError(f"Brewer's Friend: request failed (HTTP {response.status}).")
                return bytes(raw)
        except (ClientError, TimeoutError) as err:
            raise BrewfatherError("Brewer's Friend: unavailable or invalid response.") from err

    async def page(self, offset=0, limit=100):
        try:
            data = json.loads(await self.request(offset=offset, limit=limit))
            rows = data["recipes"]
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError
            return rows
        except (ValueError, KeyError, TypeError) as err:
            raise BrewfatherError("Brewer's Friend: unavailable or invalid response.") from err

    async def catalog(self, kind=None):
        result, seen = [], set()
        for offset in range(0, 10000, 100):
            page = await self.page(offset)
            for row in page:
                source_id = str(row.get("id", ""))
                if not re.fullmatch(r"[0-9]+", source_id) or source_id in seen:
                    raise BrewfatherError("Brewer's Friend: unavailable or invalid response.")
                seen.add(source_id)
                result.append({"id": source_id, "name": str(row.get("title") or source_id)})
            if len(page) < 100:
                return result
        raise BrewfatherError("Brewer's Friend: too many recipes. Use a recipe ID.")

    async def get(self, kind, source_id):
        if not isinstance(source_id, str) or not re.fullmatch(r"[0-9]{1,30}", source_id):
            raise BrewfatherError("Brewer's Friend: invalid recipe ID.")
        recipes = parse_beerxml(await self.request(f"/{source_id}.xml"))
        if len(recipes) != 1:
            raise BrewfatherError("Brewer's Friend: unavailable or invalid response.")
        return normalized_recipe(recipes[0])

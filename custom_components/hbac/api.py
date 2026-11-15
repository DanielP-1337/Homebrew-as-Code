"""Read-only Brewfather REST v2 client. Credentials never reach the browser."""
import time
from urllib.parse import quote

from aiohttp import BasicAuth, ClientError, ClientTimeout


class BrewfatherError(Exception):
    """Sanitized API failure."""


class BrewfatherAuthError(BrewfatherError):
    """Invalid credentials or missing scopes."""


class BrewfatherClient:
    def __init__(self, session, user_id, api_key):
        self.session = session
        self.auth = BasicAuth(user_id, api_key)
        self.retry_at = 0

    async def get(self, kind, source_id=None, **params):
        if kind not in ("recipes", "batches"):
            raise BrewfatherError("Unbekannte Quelle.")
        if time.monotonic() < self.retry_at:
            raise BrewfatherError("Brewfather-Anfragelimit erreicht. Bitte später erneut versuchen.")
        url = "https://api.brewfather.app/v2/" + kind
        if source_id is not None:
            if not isinstance(source_id, str) or not source_id or len(source_id) > 256:
                raise BrewfatherError("Ungültige Brewfather-ID.")
            url += "/" + quote(source_id, safe="")
        try:
            async with self.session.get(url, params=params, auth=self.auth,
                                        timeout=ClientTimeout(total=20), allow_redirects=False) as response:
                if response.status in (401, 403):
                    raise BrewfatherAuthError("Brewfather-Zugang oder Leserechte für Rezepte/Batches fehlen.")
                if response.status == 429:
                    try:
                        delay = max(1, float(response.headers.get("Retry-After", 60)))
                    except ValueError:
                        delay = 60
                    self.retry_at = time.monotonic() + delay
                    raise BrewfatherError("Brewfather-Anfragelimit erreicht. Bitte später erneut versuchen.")
                if response.status != 200:
                    raise BrewfatherError(f"Brewfather-Abruf fehlgeschlagen (HTTP {response.status}).")
                data = await response.json()
        except (TimeoutError, ClientError, ValueError) as err:
            raise BrewfatherError("Brewfather nicht erreichbar oder ungültige Antwort.") from err
        if not isinstance(data, dict if source_id is not None else list):
            raise BrewfatherError("Unerwartetes Brewfather-Antwortformat.")
        return data

    async def catalog(self, kind):
        result, cursor = [], None
        while True:
            params = {"limit": 50}
            if cursor:
                params["start_after"] = cursor
            page = await self.get(kind, **params)
            for row in page:
                if not isinstance(row, dict) or not isinstance(row.get("_id"), str):
                    raise BrewfatherError("Ungültiger Brewfather-Katalogeintrag.")
                recipe = row.get("recipe") if isinstance(row.get("recipe"), dict) else {}
                result.append({"id": row["_id"], "name": row.get("name") or recipe.get("name") or row["_id"],
                               "batch_no": row.get("batchNo"), "status": row.get("status")})
            if len(page) < 50:
                return result
            next_cursor = page[-1]["_id"]
            if next_cursor == cursor or len(result) >= 10000:
                raise BrewfatherError("Brewfather-Paginierung konnte nicht abgeschlossen werden.")
            cursor = next_cursor

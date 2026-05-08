from collections.abc import Iterable
import time
import unicodedata

import httpx

from app.core.config import settings


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def normalize_card_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name or "")
    without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
    return without_marks.casefold().strip()



def card_matches_name(card: dict, requested_name: str) -> bool:
    normalized_requested = normalize_card_name(requested_name)

    if normalize_card_name(card.get("name", "")) == normalized_requested:
        return True

    for face in card.get("card_faces") or []:
        if normalize_card_name(face.get("name", "")) == normalized_requested:
            return True

    return False


class ScryfallClient:
    _card_cache: dict[str, tuple[float, dict | None]] = {}

    @classmethod
    def clear_cache(cls) -> None:
        cls._card_cache.clear()

    def _cache_expiry(self) -> float:
        return time.time() + settings.scryfall_cache_ttl_seconds

    def _get_cached_card(self, name: str) -> dict | None | object:
        cached = self._card_cache.get(name)
        if not cached:
            return _CACHE_MISS

        expires_at, value = cached
        if expires_at < time.time():
            self._card_cache.pop(name, None)
            return _CACHE_MISS

        return value

    def _set_cached_card(self, name: str, value: dict | None) -> dict | None:
        self._card_cache[name] = (self._cache_expiry(), value)
        return value

    async def get_card_by_name(self, name: str) -> dict | None:
        cached = self._get_cached_card(name)
        if cached is not _CACHE_MISS:
            return cached

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.scryfall_base_url}/cards/named",
                params={"exact": name},
            )

        if response.status_code != 200:
            return self._set_cached_card(name, None)

        return self._set_cached_card(name, response.json())

    async def get_cards(self, names: Iterable[str]) -> dict[str, dict | None]:
        unique_names = list(dict.fromkeys(name for name in names if name))
        results: dict[str, dict | None] = {name: None for name in unique_names}
        if not unique_names:
            return results

        uncached_names: list[str] = []
        for name in unique_names:
            cached = self._get_cached_card(name)
            if cached is _CACHE_MISS:
                uncached_names.append(name)
            else:
                results[name] = cached

        if not uncached_names:
            return results

        async with httpx.AsyncClient(timeout=20.0) as client:
            for batch in chunked(uncached_names, 75):
                response = await client.post(
                    f"{settings.scryfall_base_url}/cards/collection",
                    json={
                        "identifiers": [{"name": name} for name in batch],
                    },
                )

                if response.status_code != 200:
                    for name in batch:
                        results[name] = await self.get_card_by_name(name)
                    continue

                payload = response.json()
                found_names: set[str] = set()
                returned_cards = payload.get("data", [])
                for name in batch:
                    matching_card = next((card for card in returned_cards if card_matches_name(card, name)), None)
                    if matching_card is not None:
                        found_names.add(name)
                        results[name] = self._set_cached_card(name, matching_card)
                        full_name = matching_card.get("name")
                        if full_name and full_name != name:
                            self._set_cached_card(full_name, matching_card)

                not_found = payload.get("not_found", [])
                for item in not_found:
                    missing_name = item.get("name")
                    if missing_name in results:
                        found_names.add(missing_name)
                        results[missing_name] = await self.get_card_by_name(missing_name)

                for name in batch:
                    if name not in found_names:
                        results[name] = self._set_cached_card(name, None)

        return results


_CACHE_MISS = object()

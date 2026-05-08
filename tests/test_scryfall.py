import asyncio

import httpx

from app.services.scryfall import ScryfallClient


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeAsyncClient:
    get_calls = 0
    post_calls = 0

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def get(self, url, params=None):
        FakeAsyncClient.get_calls += 1
        return FakeResponse(
            200,
            {
                "name": params["exact"],
                "type_line": "Instant",
                "oracle_text": "Draw a card.",
            },
        )

    async def post(self, url, json=None):
        FakeAsyncClient.post_calls += 1
        identifiers = json["identifiers"]
        return FakeResponse(
            200,
            {
                "data": [
                    {
                        "name": item["name"],
                        "type_line": "Instant",
                        "oracle_text": "Draw a card.",
                    }
                    for item in identifiers
                ],
                "not_found": [],
            },
        )


def setup_function() -> None:
    ScryfallClient.clear_cache()
    FakeAsyncClient.get_calls = 0
    FakeAsyncClient.post_calls = 0


def test_get_card_by_name_uses_cache(monkeypatch) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    client = ScryfallClient()

    first = asyncio.run(client.get_card_by_name("Brainstorm"))
    second = asyncio.run(client.get_card_by_name("Brainstorm"))

    assert first == second
    assert first["name"] == "Brainstorm"
    assert FakeAsyncClient.get_calls == 1


def test_get_cards_uses_cache_across_requests(monkeypatch) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    client = ScryfallClient()

    first = asyncio.run(client.get_cards(["Ponder", "Preordain"]))
    second = asyncio.run(client.get_cards(["Ponder", "Preordain", "Consider"]))

    assert first["Ponder"]["name"] == "Ponder"
    assert first["Preordain"]["name"] == "Preordain"
    assert second["Consider"]["name"] == "Consider"
    assert FakeAsyncClient.post_calls == 2


def test_get_cards_only_fetches_uncached_names(monkeypatch) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    client = ScryfallClient()

    asyncio.run(client.get_cards(["Opt", "Serum Visions"]))
    FakeAsyncClient.post_calls = 0
    second = asyncio.run(client.get_cards(["Opt", "Serum Visions", "Sleight of Hand"]))

    assert second["Sleight of Hand"]["name"] == "Sleight of Hand"
    assert FakeAsyncClient.post_calls == 1


class TransformNameAsyncClient(FakeAsyncClient):
    async def post(self, url, json=None):
        TransformNameAsyncClient.post_calls += 1
        return FakeResponse(
            200,
            {
                "data": [
                    {
                        "name": "Esper Origins // Summon: Esper Maduin",
                        "type_line": "Sorcery // Enchantment Creature — Saga Elemental",
                        "oracle_text": "Surveil 2.",
                        "card_faces": [
                            {"name": "Esper Origins"},
                            {"name": "Summon: Esper Maduin"},
                        ],
                    }
                ],
                "not_found": [],
            },
        )


def test_get_cards_matches_front_face_names_for_transform_cards(monkeypatch) -> None:
    ScryfallClient.clear_cache()
    TransformNameAsyncClient.get_calls = 0
    TransformNameAsyncClient.post_calls = 0
    monkeypatch.setattr(httpx, "AsyncClient", TransformNameAsyncClient)
    client = ScryfallClient()

    result = asyncio.run(client.get_cards(["Esper Origins"]))

    assert result["Esper Origins"] is not None
    assert result["Esper Origins"]["name"] == "Esper Origins // Summon: Esper Maduin"
    assert TransformNameAsyncClient.post_calls == 1


class SplitCardFallbackAsyncClient(FakeAsyncClient):
    async def post(self, url, json=None):
        SplitCardFallbackAsyncClient.post_calls += 1
        return FakeResponse(
            200,
            {
                "data": [],
                "not_found": [{"name": "Wear // Tear"}],
            },
        )

    async def get(self, url, params=None):
        SplitCardFallbackAsyncClient.get_calls += 1
        return FakeResponse(
            200,
            {
                "name": "Wear // Tear",
                "type_line": "Instant // Instant",
                "oracle_text": "Destroy target artifact. // Destroy target enchantment.",
            },
        )



def test_get_cards_falls_back_to_named_lookup_for_split_cards_not_found_in_collection(monkeypatch) -> None:
    ScryfallClient.clear_cache()
    SplitCardFallbackAsyncClient.get_calls = 0
    SplitCardFallbackAsyncClient.post_calls = 0
    monkeypatch.setattr(httpx, "AsyncClient", SplitCardFallbackAsyncClient)
    client = ScryfallClient()

    result = asyncio.run(client.get_cards(["Wear // Tear"]))

    assert result["Wear // Tear"] is not None
    assert result["Wear // Tear"]["name"] == "Wear // Tear"
    assert SplitCardFallbackAsyncClient.post_calls == 1
    assert SplitCardFallbackAsyncClient.get_calls == 1


class AccentInsensitiveCollectionAsyncClient(FakeAsyncClient):
    async def post(self, url, json=None):
        AccentInsensitiveCollectionAsyncClient.post_calls += 1
        return FakeResponse(
            200,
            {
                "data": [
                    {
                        "name": "Nazgûl",
                        "type_line": "Creature — Wraith Knight",
                        "oracle_text": "A deck can have up to nine cards named Nazgûl.",
                    }
                ],
                "not_found": [],
            },
        )



def test_get_cards_matches_names_without_diacritics(monkeypatch) -> None:
    ScryfallClient.clear_cache()
    AccentInsensitiveCollectionAsyncClient.post_calls = 0
    monkeypatch.setattr(httpx, "AsyncClient", AccentInsensitiveCollectionAsyncClient)
    client = ScryfallClient()

    result = asyncio.run(client.get_cards(["Nazgul"]))

    assert result["Nazgul"] is not None
    assert result["Nazgul"]["name"] == "Nazgûl"
    assert AccentInsensitiveCollectionAsyncClient.post_calls == 1

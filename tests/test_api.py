from fastapi.testclient import TestClient
import pytest

from app.main import analyze_rate_limiter, app
from app.services.scryfall import ScryfallClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_analyze_rate_limiter() -> None:
    analyze_rate_limiter.reset()
    yield
    analyze_rate_limiter.reset()


def test_homepage_loads() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "MTG Deck Analyzer" in response.text


def test_healthcheck() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_deck_returns_summary(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Sol Ring": {
                "name": "Sol Ring",
                "mana_cost": "{1}",
                "cmc": 1,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "{T}: Add {C}{C}.",
                "image_uris": {
                    "small": "https://img.scryfall.com/sol-ring-small.jpg",
                    "normal": "https://img.scryfall.com/sol-ring-normal.jpg"
                },
                "scryfall_uri": "https://scryfall.com/card/example/sol-ring",
            },
            "Divination": {
                "name": "Divination",
                "mana_cost": "{2}{U}",
                "cmc": 3,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Sorcery",
                "oracle_text": "Draw two cards.",
                "image_uris": {
                    "small": "https://img.scryfall.com/divination-small.jpg",
                    "normal": "https://img.scryfall.com/divination-normal.jpg"
                },
                "scryfall_uri": "https://scryfall.com/card/example/divination",
            },
            "Counterspell": {
                "name": "Counterspell",
                "mana_cost": "{U}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Instant",
                "oracle_text": "Counter target spell.",
                "image_uris": {
                    "small": "https://img.scryfall.com/counterspell-small.jpg",
                    "normal": "https://img.scryfall.com/counterspell-normal.jpg"
                },
                "scryfall_uri": "https://scryfall.com/card/example/counterspell",
            },
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "image_uris": {
                    "small": "https://img.scryfall.com/island-small.jpg",
                    "normal": "https://img.scryfall.com/island-normal.jpg"
                },
                "scryfall_uri": "https://scryfall.com/card/example/island",
            },
            "Baral, Chief of Compliance": {
                "name": "Baral, Chief of Compliance",
                "mana_cost": "{1}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Legendary Creature — Human Wizard",
                "oracle_text": "Instant and sorcery spells you cast cost {1} less to cast.",
                "image_uris": {
                    "small": "https://img.scryfall.com/baral-small.jpg",
                    "normal": "https://img.scryfall.com/baral-normal.jpg"
                },
                "scryfall_uri": "https://scryfall.com/card/example/baral",
                "legalities": {"commander": "legal"},
            },
        }

    async def fail_get_card_by_name(self, name):
        raise AssertionError("get_card_by_name should not be called during deck analysis")

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)
    monkeypatch.setattr(ScryfallClient, "get_card_by_name", fail_get_card_by_name)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Test Deck",
            "format": "commander",
            "commander": "Baral, Chief of Compliance",
            "decklist": "1 Sol Ring\n1 Divination\n1 Counterspell\n96 Island",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deck_name"] == "Test Deck"
    assert data["commander"]["name"] == "Baral, Chief of Compliance"
    assert data["commander"]["color_identity"] == ["U"]
    assert len(data["commanders"]) == 1
    assert data["deck_color_identity"] == ["U"]
    assert data["color_identity_violations"] == []
    assert data["total_cards"] == 99
    assert data["mainboard_count"] == 99
    assert data["sideboard_count"] == 0
    assert data["color_identity"] == ["U"]
    assert data["mana_curve"]["0"] == 96
    assert data["mana_curve"]["1"] == 1
    assert data["mana_curve"]["2"] == 1
    assert data["mana_curve"]["3"] == 1
    assert data["classification_counts"] == {"ramp": 1, "draw": 1, "removal": 1}
    assert "Land count is pretty high; you may be able to trim a few lands for more action cards." in data["recommendations"]
    assert "Ramp looks light; consider adding more mana rocks, dorks, or land ramp." in data["recommendations"]
    assert "Card draw looks a bit low; adding more draw can help the deck stay consistent." in data["recommendations"]
    assert "Interaction looks light; consider a few more targeted removal or counterspell slots." in data["recommendations"]
    assert "You may want at least one boardwipe as a reset button." in data["recommendations"]
    assert data["parsed_cards"][0]["card"]["name"] == "Sol Ring"
    assert data["parsed_cards"][0]["card"]["image_small"] == "https://img.scryfall.com/sol-ring-small.jpg"
    assert data["parsed_cards"][0]["card"]["image_normal"] == "https://img.scryfall.com/sol-ring-normal.jpg"
    assert data["parsed_cards"][0]["categories"] == ["ramp"]
    assert data["parsed_cards"][1]["categories"] == ["draw"]
    assert data["parsed_cards"][2]["categories"] == ["removal"]
    assert data["parsed_cards"][3]["card"]["color_identity"] == ["U"]


def test_detects_commander_spellslinger_archetype(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Baral, Chief of Compliance": {
                "name": "Baral, Chief of Compliance",
                "mana_cost": "{1}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Legendary Creature — Human Wizard",
                "oracle_text": "Instant and sorcery spells you cast cost {1} less to cast.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/baral",
            },
            "Talrand, Sky Summoner": {
                "name": "Talrand, Sky Summoner",
                "mana_cost": "{2}{U}{U}",
                "cmc": 4,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Legendary Creature — Merfolk Wizard",
                "oracle_text": "Whenever you cast an instant or sorcery spell, create a 2/2 blue Drake creature token with flying.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/talrand",
            },
            "Ponder": {
                "name": "Ponder",
                "mana_cost": "{U}",
                "cmc": 1,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Sorcery",
                "oracle_text": "Look at the top three cards of your library, then put them back in any order. You may shuffle your library. Draw a card.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/ponder",
            },
            "Counterspell": {
                "name": "Counterspell",
                "mana_cost": "{U}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Instant",
                "oracle_text": "Counter target spell.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/counterspell",
            },
            "Arcane Denial": {
                "name": "Arcane Denial",
                "mana_cost": "{1}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Instant",
                "oracle_text": "Counter target spell. Its controller may draw up to two cards at the beginning of the next turn's upkeep. You draw a card at the beginning of the next turn's upkeep.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/arcane-denial",
            },
            "Preordain": {
                "name": "Preordain",
                "mana_cost": "{U}",
                "cmc": 1,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Sorcery",
                "oracle_text": "Scry 2, then draw a card.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/preordain",
            },
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/island",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Baral Spells",
            "format": "commander",
            "commander": "Baral, Chief of Compliance",
            "decklist": "1 Talrand, Sky Summoner\n20 Ponder\n20 Preordain\n20 Counterspell\n20 Arcane Denial\n18 Island",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["primary_archetype"] == "Spellslinger"
    assert data["archetype_guesses"][0]["name"] == "Spellslinger"
    assert any("signature cards" in reason.lower() for reason in data["archetype_guesses"][0]["reasons"])
    assert "Baral, Chief of Compliance" in data["archetype_guesses"][0]["support_cards"]
    assert "Talrand, Sky Summoner" in data["archetype_guesses"][0]["support_cards"]



def test_non_commander_format_ignores_stale_commander_value(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        assert "Baral, Chief of Compliance" not in names
        return {
            "Lightning Bolt": {
                "name": "Lightning Bolt",
                "mana_cost": "{R}",
                "cmc": 1,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Instant",
                "oracle_text": "Lightning Bolt deals 3 damage to any target.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/bolt",
            },
            "Mountain": {
                "name": "Mountain",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["R"],
                "type_line": "Basic Land — Mountain",
                "oracle_text": "({T}: Add {R}.)",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/mountain",
            },
            "Baral, Chief of Compliance": {
                "name": "Baral, Chief of Compliance",
                "mana_cost": "{1}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Legendary Creature — Human Wizard",
                "oracle_text": "Instant and sorcery spells you cast cost {1} less to cast.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/baral",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Modern No Commander",
            "format": "modern",
            "commander": "Baral, Chief of Compliance",
            "decklist": "4 Lightning Bolt\n56 Mountain",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["commander"] is None
    assert data["commanders"] == []



def test_commander_format_uses_commander_section_when_field_is_empty(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Sol Ring": {
                "name": "Sol Ring",
                "mana_cost": "{1}",
                "cmc": 1,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "{T}: Add {C}{C}.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/sol-ring",
            },
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/island",
            },
            "Baral, Chief of Compliance": {
                "name": "Baral, Chief of Compliance",
                "mana_cost": "{1}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Legendary Creature — Human Wizard",
                "oracle_text": "Instant and sorcery spells you cast cost {1} less to cast.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/baral",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Arena Commander Export",
            "format": "commander",
            "decklist": "Commander\n1 Baral, Chief of Compliance\n\nDeck\n1 Sol Ring\n98 Island",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["commander"]["name"] == "Baral, Chief of Compliance"
    assert len(data["commanders"]) == 1



def test_companion_section_does_not_inflate_mainboard_count(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Lightning Bolt": {
                "name": "Lightning Bolt",
                "mana_cost": "{R}",
                "cmc": 1,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Instant",
                "oracle_text": "Lightning Bolt deals 3 damage to any target.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/bolt",
            },
            "Mountain": {
                "name": "Mountain",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["R"],
                "type_line": "Basic Land — Mountain",
                "oracle_text": "({T}: Add {R}.)",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/mountain",
            },
            "Yorion, Sky Nomad": {
                "name": "Yorion, Sky Nomad",
                "mana_cost": "{3}{W}{U}",
                "cmc": 5,
                "colors": ["W", "U"],
                "color_identity": ["W", "U"],
                "type_line": "Legendary Creature — Bird Serpent",
                "oracle_text": "Companion — Your starting deck contains at least twenty cards more than the minimum deck size.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/yorion",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Modern Yorion",
            "format": "modern",
            "decklist": "Companion\n1 Yorion, Sky Nomad\n\nDeck\n4 Lightning Bolt\n56 Mountain",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mainboard_count"] == 60
    assert data["sideboard_count"] == 1
    assert [card["name"] for card in data["parsed_cards"]] == ["Lightning Bolt", "Mountain"]
    assert [card["name"] for card in data["parsed_sideboard"]] == ["Yorion, Sky Nomad"]
    assert "No commander provided. Add one to enable color identity validation." not in data["warnings"]



def test_commander_format_uses_inline_commander_entry_when_field_is_empty(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Sol Ring": {
                "name": "Sol Ring",
                "mana_cost": "{1}",
                "cmc": 1,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "{T}: Add {C}{C}.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/sol-ring",
            },
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/island",
            },
            "Baral, Chief of Compliance": {
                "name": "Baral, Chief of Compliance",
                "mana_cost": "{1}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Legendary Creature — Human Wizard",
                "oracle_text": "Instant and sorcery spells you cast cost {1} less to cast.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/baral",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Inline Commander Export",
            "format": "commander",
            "decklist": "Commander: 1 Baral, Chief of Compliance\nDeck\n1 Sol Ring\n98 Island",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["commander"]["name"] == "Baral, Chief of Compliance"
    assert len(data["commanders"]) == 1
    assert data["mainboard_count"] == 99



def test_detects_modern_burn_archetype(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Goblin Guide": {
                "name": "Goblin Guide",
                "mana_cost": "{R}",
                "cmc": 1,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Creature — Goblin Scout",
                "oracle_text": "Haste",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/goblin-guide",
            },
            "Monastery Swiftspear": {
                "name": "Monastery Swiftspear",
                "mana_cost": "{R}",
                "cmc": 1,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Creature — Human Monk",
                "oracle_text": "Haste, prowess",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/swiftspear",
            },
            "Lightning Bolt": {
                "name": "Lightning Bolt",
                "mana_cost": "{R}",
                "cmc": 1,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Instant",
                "oracle_text": "Lightning Bolt deals 3 damage to any target.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/bolt",
            },
            "Lava Spike": {
                "name": "Lava Spike",
                "mana_cost": "{R}",
                "cmc": 1,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Sorcery",
                "oracle_text": "Lava Spike deals 3 damage to target player or planeswalker.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/lava-spike",
            },
            "Boros Charm": {
                "name": "Boros Charm",
                "mana_cost": "{R}{W}",
                "cmc": 2,
                "colors": ["R", "W"],
                "color_identity": ["R", "W"],
                "type_line": "Instant",
                "oracle_text": "Choose one — Boros Charm deals 4 damage to target player or planeswalker; creatures you control gain indestructible until end of turn; target creature gains double strike until end of turn.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/boros-charm",
            },
            "Mountain": {
                "name": "Mountain",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["R"],
                "type_line": "Basic Land — Mountain",
                "oracle_text": "({T}: Add {R}.)",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/mountain",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Burn Test",
            "format": "modern",
            "decklist": "4 Goblin Guide\n4 Monastery Swiftspear\n4 Lightning Bolt\n4 Lava Spike\n4 Boros Charm\n40 Mountain",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["primary_archetype"] == "Burn"
    assert data["archetype_guesses"][0]["name"] == "Burn"
    assert data["archetype_guesses"][0]["confidence"] >= 0.8
    if len(data["archetype_guesses"]) > 1:
        assert data["archetype_guesses"][0]["confidence"] > data["archetype_guesses"][1]["confidence"]



def test_detects_vintage_shops_archetype(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Mishra's Workshop": {
                "name": "Mishra's Workshop",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": [],
                "type_line": "Land",
                "oracle_text": "{T}: Add {C}{C}{C}. Spend this mana only to cast artifact spells.",
                "legalities": {"vintage": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/workshop",
            },
            "Ancient Tomb": {
                "name": "Ancient Tomb",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": [],
                "type_line": "Land",
                "oracle_text": "{T}: Add {C}{C}. Ancient Tomb deals 2 damage to you.",
                "legalities": {"vintage": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/tomb",
            },
            "Chalice of the Void": {
                "name": "Chalice of the Void",
                "mana_cost": "{X}{X}",
                "cmc": 0,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "Whenever a player casts a spell with mana value equal to the number of charge counters on this artifact, counter that spell.",
                "legalities": {"vintage": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/chalice",
            },
            "Trinisphere": {
                "name": "Trinisphere",
                "mana_cost": "{3}",
                "cmc": 3,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "Each spell that would cost less than three mana to cast costs three mana to cast instead.",
                "legalities": {"vintage": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/trinisphere",
            },
            "Lodestone Golem": {
                "name": "Lodestone Golem",
                "mana_cost": "{4}",
                "cmc": 4,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact Creature — Golem",
                "oracle_text": "Nonartifact spells cost {1} more to cast.",
                "legalities": {"vintage": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/lodestone",
            },
            "Wasteland": {
                "name": "Wasteland",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": [],
                "type_line": "Land",
                "oracle_text": "{T}: Add {C}. {T}, Sacrifice this land: Destroy target nonbasic land.",
                "legalities": {"vintage": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/wasteland",
            },
            "Mana Crypt": {
                "name": "Mana Crypt",
                "mana_cost": "{0}",
                "cmc": 0,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "{T}: Add {C}{C}.",
                "legalities": {"vintage": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/crypt",
            },
            "Sol Ring": {
                "name": "Sol Ring",
                "mana_cost": "{1}",
                "cmc": 1,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "{T}: Add {C}{C}.",
                "legalities": {"vintage": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/sol-ring",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Shops Test",
            "format": "vintage",
            "decklist": "4 Mishra's Workshop\n4 Ancient Tomb\n4 Chalice of the Void\n4 Trinisphere\n4 Lodestone Golem\n4 Wasteland\n20 Mana Crypt\n16 Sol Ring",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["primary_archetype"] == "Shops"
    assert data["archetype_guesses"][0]["name"] == "Shops"
    assert any(guess["name"] == "Stax" for guess in data["archetype_guesses"])
    assert any(guess["name"] == "Artifacts" for guess in data["archetype_guesses"])
    assert data["archetype_guesses"][0]["confidence"] > data["archetype_guesses"][1]["confidence"]



def test_detects_modern_tron_archetype(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Urza's Tower": {
                "name": "Urza's Tower",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": [],
                "type_line": "Land — Urza's Tower",
                "oracle_text": "{T}: Add {C}. If you control an Urza's Mine and an Urza's Power-Plant, add {C}{C}{C} instead.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/tower",
            },
            "Urza's Mine": {
                "name": "Urza's Mine",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": [],
                "type_line": "Land — Urza's Mine",
                "oracle_text": "{T}: Add {C}. If you control an Urza's Power-Plant and an Urza's Tower, add {C}{C} instead.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/mine",
            },
            "Urza's Power Plant": {
                "name": "Urza's Power Plant",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": [],
                "type_line": "Land — Urza's Power-Plant",
                "oracle_text": "{T}: Add {C}. If you control an Urza's Mine and an Urza's Tower, add {C}{C} instead.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/plant",
            },
            "Karn Liberated": {
                "name": "Karn Liberated",
                "mana_cost": "{7}",
                "cmc": 7,
                "colors": [],
                "color_identity": [],
                "type_line": "Legendary Planeswalker — Karn",
                "oracle_text": "+4: Target player exiles a card from their hand.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/karn",
            },
            "Chromatic Star": {
                "name": "Chromatic Star",
                "mana_cost": "{1}",
                "cmc": 1,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "{1}, {T}, Sacrifice this artifact: Add one mana of any color. When this artifact is put into a graveyard from the battlefield, draw a card.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/star",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Tron Test",
            "format": "modern",
            "decklist": "4 Urza's Tower\n4 Urza's Mine\n4 Urza's Power Plant\n4 Karn Liberated\n44 Chromatic Star",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["primary_archetype"] == "Tron"
    assert data["archetype_guesses"][0]["name"] == "Tron"
    assert set(data["archetype_guesses"][0]["support_cards"]) >= {"Urza's Tower", "Urza's Mine", "Urza's Power Plant", "Karn Liberated"}



def test_detects_pioneer_spirits_archetype(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Mausoleum Wanderer": {
                "name": "Mausoleum Wanderer",
                "mana_cost": "{U}",
                "cmc": 1,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Creature — Spirit",
                "oracle_text": "Flying",
                "legalities": {"pioneer": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/wanderer",
            },
            "Rattlechains": {
                "name": "Rattlechains",
                "mana_cost": "{1}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Creature — Spirit",
                "oracle_text": "Flash, flying",
                "legalities": {"pioneer": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/rattlechains",
            },
            "Spell Queller": {
                "name": "Spell Queller",
                "mana_cost": "{1}{W}{U}",
                "cmc": 3,
                "colors": ["W", "U"],
                "color_identity": ["W", "U"],
                "type_line": "Creature — Spirit",
                "oracle_text": "Flash, flying",
                "legalities": {"pioneer": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/queller",
            },
            "Supreme Phantom": {
                "name": "Supreme Phantom",
                "mana_cost": "{1}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Creature — Spirit Soldier",
                "oracle_text": "Other Spirits you control get +1/+1.",
                "legalities": {"pioneer": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/phantom",
            },
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "legalities": {"pioneer": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/island",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Spirits Test",
            "format": "pioneer",
            "decklist": "4 Mausoleum Wanderer\n4 Rattlechains\n4 Spell Queller\n4 Supreme Phantom\n44 Island",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["primary_archetype"] == "Spirits"
    assert data["archetype_guesses"][0]["name"] == "Spirits"



def test_modern_validation_rules(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Lightning Bolt": {
                "name": "Lightning Bolt",
                "mana_cost": "{R}",
                "cmc": 1,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Instant",
                "oracle_text": "Lightning Bolt deals 3 damage to any target.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/lightning-bolt",
            },
            "Counterspell": {
                "name": "Counterspell",
                "mana_cost": "{U}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Instant",
                "oracle_text": "Counter target spell.",
                "legalities": {"modern": "not_legal"},
                "scryfall_uri": "https://scryfall.com/card/example/counterspell",
            },
            "Mountain": {
                "name": "Mountain",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["R"],
                "type_line": "Basic Land — Mountain",
                "oracle_text": "({T}: Add {R}.)",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/mountain",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Modern Test",
            "format": "modern",
            "decklist": "Deck\n5 Lightning Bolt\n1 Counterspell\n10 Mountain\nSideboard\n11 Lightning Bolt\n16 Mountain",
            "sideboard": None,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mainboard_count"] == 16
    assert data["sideboard_count"] == 27
    assert len(data["parsed_sideboard"]) == 2
    assert "Modern decks should contain at least 60 cards; found 16" in data["warnings"]
    assert "Modern sideboards can contain at most 15 cards; found 27" in data["warnings"]
    assert "Too many copies for Modern: Lightning Bolt (16)" in data["warnings"]
    assert "Not Modern legal: Counterspell" in data["warnings"]


def test_standard_validation_rules(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Lightning Strike": {
                "name": "Lightning Strike",
                "mana_cost": "{1}{R}",
                "cmc": 2,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Instant",
                "oracle_text": "Lightning Strike deals 3 damage to any target.",
                "legalities": {"standard": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/lightning-strike",
            },
            "Counterspell": {
                "name": "Counterspell",
                "mana_cost": "{U}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Instant",
                "oracle_text": "Counter target spell.",
                "legalities": {"standard": "not_legal"},
                "scryfall_uri": "https://scryfall.com/card/example/counterspell",
            },
            "Mountain": {
                "name": "Mountain",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["R"],
                "type_line": "Basic Land — Mountain",
                "oracle_text": "({T}: Add {R}.)",
                "legalities": {"standard": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/mountain",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Standard Test",
            "format": "standard",
            "decklist": "5 Lightning Strike\n1 Counterspell\n10 Mountain",
            "sideboard": "16 Mountain",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "Standard decks should contain at least 60 cards; found 16" in data["warnings"]
    assert "Standard sideboards can contain at most 15 cards; found 16" in data["warnings"]
    assert "Too many copies for Standard: Lightning Strike (5)" in data["warnings"]
    assert "Not Standard legal: Counterspell" in data["warnings"]
    assert data["parsed_sideboard"][0]["categories"] == []


def test_sideboard_cards_keep_their_categories(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Lightning Bolt": {
                "name": "Lightning Bolt",
                "mana_cost": "{R}",
                "cmc": 1,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Instant",
                "oracle_text": "Lightning Bolt deals 3 damage to any target.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/lightning-bolt",
            },
            "Ponder": {
                "name": "Ponder",
                "mana_cost": "{U}",
                "cmc": 1,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Sorcery",
                "oracle_text": "Look at the top three cards of your library, then put them back in any order. You may shuffle your library. Draw a card.",
                "legalities": {"modern": "not_legal"},
                "scryfall_uri": "https://scryfall.com/card/example/ponder",
            },
            "Mountain": {
                "name": "Mountain",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["R"],
                "type_line": "Basic Land — Mountain",
                "oracle_text": "({T}: Add {R}.)",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/mountain",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Modern Sideboard Tags",
            "format": "modern",
            "decklist": "4 Lightning Bolt\n56 Mountain",
            "sideboard": "2 Ponder",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["parsed_sideboard"][0]["name"] == "Ponder"
    assert data["parsed_sideboard"][0]["categories"] == ["draw"]


def test_pioneer_validation_rules(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Opt": {
                "name": "Opt",
                "mana_cost": "{U}",
                "cmc": 1,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Instant",
                "oracle_text": "Scry 1. Draw a card.",
                "legalities": {"pioneer": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/opt",
            },
            "Brainstorm": {
                "name": "Brainstorm",
                "mana_cost": "{U}",
                "cmc": 1,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Instant",
                "oracle_text": "Draw three cards, then put two cards from your hand on top of your library in any order.",
                "legalities": {"pioneer": "not_legal"},
                "scryfall_uri": "https://scryfall.com/card/example/brainstorm",
            },
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "legalities": {"pioneer": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/island",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Pioneer Test",
            "format": "pioneer",
            "decklist": "4 Opt\n1 Brainstorm\n20 Island",
            "sideboard": "16 Island",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "Pioneer decks should contain at least 60 cards; found 25" in data["warnings"]
    assert "Pioneer sideboards can contain at most 15 cards; found 16" in data["warnings"]
    assert "Not Pioneer legal: Brainstorm" in data["warnings"]


def test_pauper_validation_rules(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Lightning Bolt": {
                "name": "Lightning Bolt",
                "mana_cost": "{R}",
                "cmc": 1,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Instant",
                "oracle_text": "Lightning Bolt deals 3 damage to any target.",
                "legalities": {"pauper": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/lightning-bolt",
            },
            "Counterspell": {
                "name": "Counterspell",
                "mana_cost": "{U}{U}",
                "cmc": 2,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Instant",
                "oracle_text": "Counter target spell.",
                "legalities": {"pauper": "banned"},
                "scryfall_uri": "https://scryfall.com/card/example/counterspell",
            },
            "Mountain": {
                "name": "Mountain",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["R"],
                "type_line": "Basic Land — Mountain",
                "oracle_text": "({T}: Add {R}.)",
                "legalities": {"pauper": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/mountain",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Pauper Test",
            "format": "pauper",
            "decklist": "5 Lightning Bolt\n1 Counterspell\n10 Mountain",
            "sideboard": "16 Mountain",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "Pauper decks should contain at least 60 cards; found 16" in data["warnings"]
    assert "Pauper sideboards can contain at most 15 cards; found 16" in data["warnings"]
    assert "Too many copies for Pauper: Lightning Bolt (5)" in data["warnings"]
    assert "Not Pauper legal: Counterspell" in data["warnings"]


def test_legacy_validation_rules(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Brainstorm": {
                "name": "Brainstorm",
                "mana_cost": "{U}",
                "cmc": 1,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Instant",
                "oracle_text": "Draw three cards, then put two cards from your hand on top of your library in any order.",
                "legalities": {"legacy": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/brainstorm",
            },
            "Demonic Tutor": {
                "name": "Demonic Tutor",
                "mana_cost": "{1}{B}",
                "cmc": 2,
                "colors": ["B"],
                "color_identity": ["B"],
                "type_line": "Sorcery",
                "oracle_text": "Search your library for a card, put that card into your hand, then shuffle.",
                "legalities": {"legacy": "banned"},
                "scryfall_uri": "https://scryfall.com/card/example/demonic-tutor",
            },
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "legalities": {"legacy": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/island",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Legacy Test",
            "format": "legacy",
            "decklist": "5 Brainstorm\n1 Demonic Tutor\n10 Island",
            "sideboard": "16 Island",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "Legacy decks should contain at least 60 cards; found 16" in data["warnings"]
    assert "Legacy sideboards can contain at most 15 cards; found 16" in data["warnings"]
    assert "Too many copies for Legacy: Brainstorm (5)" in data["warnings"]
    assert "Not Legacy legal: Demonic Tutor" in data["warnings"]


def test_vintage_validation_rules(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Ancestral Recall": {
                "name": "Ancestral Recall",
                "mana_cost": "{U}",
                "cmc": 1,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Instant",
                "oracle_text": "Target player draws three cards.",
                "legalities": {"vintage": "restricted"},
                "scryfall_uri": "https://scryfall.com/card/example/ancestral-recall",
            },
            "Demonic Tutor": {
                "name": "Demonic Tutor",
                "mana_cost": "{1}{B}",
                "cmc": 2,
                "colors": ["B"],
                "color_identity": ["B"],
                "type_line": "Sorcery",
                "oracle_text": "Search your library for a card, put that card into your hand, then shuffle.",
                "legalities": {"vintage": "restricted"},
                "scryfall_uri": "https://scryfall.com/card/example/demonic-tutor",
            },
            "Chaos Orb": {
                "name": "Chaos Orb",
                "mana_cost": "{2}",
                "cmc": 2,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "Flip Chaos Orb onto the battlefield from a height of at least one foot.",
                "legalities": {"vintage": "banned"},
                "scryfall_uri": "https://scryfall.com/card/example/chaos-orb",
            },
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "legalities": {"vintage": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/island",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Vintage Test",
            "format": "vintage",
            "decklist": "2 Ancestral Recall\n1 Demonic Tutor\n1 Chaos Orb\n10 Island",
            "sideboard": "1 Demonic Tutor",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "Vintage decks should contain at least 60 cards; found 14" in data["warnings"]
    assert "Not Vintage legal: Chaos Orb" in data["warnings"]
    assert "Restricted cards exceed 1 copy in Vintage: Ancestral Recall (2), Demonic Tutor (2)" in data["warnings"]


def test_modern_duplicate_exceptions(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Dragon's Approach": {
                "name": "Dragon's Approach",
                "mana_cost": "{2}{R}",
                "cmc": 3,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Sorcery",
                "oracle_text": "Dragon's Approach deals 3 damage to each opponent. A deck can have any number of cards named Dragon's Approach.",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/dragons-approach",
            },
            "Mountain": {
                "name": "Mountain",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["R"],
                "type_line": "Basic Land — Mountain",
                "oracle_text": "({T}: Add {R}.)",
                "legalities": {"modern": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/mountain",
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Approach Test",
            "format": "modern",
            "decklist": "20 Dragon's Approach\n40 Mountain",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mainboard_count"] == 60
    assert not any("Too many copies for Modern" in warning for warning in data["warnings"])


def test_commander_duplicate_exceptions(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Nazgul": {
                "name": "Nazgul",
                "mana_cost": "{2}{B}",
                "cmc": 3,
                "colors": ["B"],
                "color_identity": ["B"],
                "type_line": "Creature — Wraith Knight",
                "oracle_text": "Deathtouch. When Nazgul enters the battlefield, the Ring tempts you. A deck can have up to nine cards named Nazgul.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/nazgul",
            },
            "Swamp": {
                "name": "Swamp",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["B"],
                "type_line": "Basic Land — Swamp",
                "oracle_text": "({T}: Add {B}.)",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/swamp",
            },
        }

    async def fake_get_card_by_name(self, name):
        return {
            "name": "The Lord of the Nazgul",
            "color_identity": ["U", "B"],
            "type_line": "Legendary Creature — Wraith Noble",
            "oracle_text": "Flying. Whenever you cast an instant or sorcery spell, amass Orcs 1. This ability triggers only once each turn.",
            "legalities": {"commander": "legal"},
            "scryfall_uri": "https://scryfall.com/card/example/lord-of-the-nazgul",
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)
    monkeypatch.setattr(ScryfallClient, "get_card_by_name", fake_get_card_by_name)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Nazgul Test",
            "format": "commander",
            "commander": "The Lord of the Nazgul",
            "decklist": "9 Nazgul\n90 Swamp",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mainboard_count"] == 99
    assert "Possible illegal duplicates: Nazgul (9)" not in data["warnings"]


def test_commander_validation_rules(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Jace, the Mind Sculptor": {
                "name": "Jace, the Mind Sculptor",
                "mana_cost": "{2}{U}{U}",
                "cmc": 4,
                "colors": ["U"],
                "color_identity": ["U"],
                "type_line": "Legendary Planeswalker — Jace",
                "oracle_text": "+2: Look at the top card of target player's library.",
                "legalities": {"commander": "banned"},
                "scryfall_uri": "https://scryfall.com/card/example/jace",
            },
            "Arcane Signet": {
                "name": "Arcane Signet",
                "mana_cost": "{2}",
                "cmc": 2,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "{T}: Add one mana of any color in your commander's color identity.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/arcane-signet",
            },
            "Black Lotus": {
                "name": "Black Lotus",
                "mana_cost": "{0}",
                "cmc": 0,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "{T}, Sacrifice Black Lotus: Add three mana of any one color.",
                "legalities": {"commander": "banned"},
                "scryfall_uri": "https://scryfall.com/card/example/black-lotus",
            },
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/island",
            },
        }

    async def fake_get_card_by_name(self, name):
        return {
            "name": "Jace, the Mind Sculptor",
            "color_identity": ["U"],
            "type_line": "Legendary Planeswalker — Jace",
            "oracle_text": "+2: Look at the top card of target player's library.",
            "legalities": {"commander": "banned"},
            "scryfall_uri": "https://scryfall.com/card/example/jace",
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)
    monkeypatch.setattr(ScryfallClient, "get_card_by_name", fake_get_card_by_name)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Questionable Commander Deck",
            "format": "commander",
            "commander": "Jace, the Mind Sculptor",
            "decklist": "1 Jace, the Mind Sculptor\n1 Arcane Signet\n1 Black Lotus\n97 Island",
            "sideboard": "1 Arcane Signet",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "Commander decks should contain 99 main-deck cards plus 1 commander(s); found 100" in data["warnings"]
    assert "Commander sideboards are not supported here; found 1 sideboard cards" in data["warnings"]
    assert "Commander appears in the main decklist: Jace, the Mind Sculptor" in data["warnings"]
    assert "Commander is not legal in Commander: Jace, the Mind Sculptor (banned)" in data["warnings"]
    assert "Commander does not appear to be a legal commander: Jace, the Mind Sculptor" in data["warnings"]
    assert "Not Commander legal: Black Lotus" in data["warnings"]


def test_commander_partner_pair_support(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Sol Ring": {
                "name": "Sol Ring",
                "mana_cost": "{1}",
                "cmc": 1,
                "colors": [],
                "color_identity": [],
                "type_line": "Artifact",
                "oracle_text": "{T}: Add {C}{C}.",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/sol-ring",
            },
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/island",
            },
            "Mountain": {
                "name": "Mountain",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["R"],
                "type_line": "Basic Land — Mountain",
                "oracle_text": "({T}: Add {R}.)",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/mountain",
            },
            "Kraum, Ludevic's Opus": {
                "name": "Kraum, Ludevic's Opus",
                "color_identity": ["U", "R"],
                "type_line": "Legendary Creature — Zombie Horror",
                "oracle_text": "Flying, haste\nPartner",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/kraum",
            },
            "Tymna the Weaver": {
                "name": "Tymna the Weaver",
                "color_identity": ["W", "B"],
                "type_line": "Legendary Creature — Human Cleric",
                "oracle_text": "Lifelink\nPartner",
                "legalities": {"commander": "legal"},
                "scryfall_uri": "https://scryfall.com/card/example/tymna",
            },
        }

    async def fail_get_card_by_name(self, name):
        raise AssertionError("get_card_by_name should not be called during deck analysis")

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)
    monkeypatch.setattr(ScryfallClient, "get_card_by_name", fail_get_card_by_name)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Blue Red Partners",
            "format": "commander",
            "commander": "Kraum, Ludevic's Opus / Tymna the Weaver",
            "decklist": "1 Sol Ring\n49 Island\n49 Mountain",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["commander"] is None
    assert [commander["name"] for commander in data["commanders"]] == [
        "Kraum, Ludevic's Opus",
        "Tymna the Weaver",
    ]
    assert data["mainboard_count"] == 99
    assert "Commander decks should contain 98 main-deck cards plus 2 commander(s); found 99" in data["warnings"]
    assert "These two commanders do not appear to form a legal commander pair (partner/background/Doctor's companion not detected)." not in data["warnings"]


def test_commander_color_identity_violation(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Lightning Bolt": {
                "name": "Lightning Bolt",
                "mana_cost": "{R}",
                "cmc": 1,
                "colors": ["R"],
                "color_identity": ["R"],
                "type_line": "Instant",
                "oracle_text": "Lightning Bolt deals 3 damage to any target.",
                "scryfall_uri": "https://scryfall.com/card/example/lightning-bolt",
                "legalities": {"commander": "legal"},
            },
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "scryfall_uri": "https://scryfall.com/card/example/island",
                "legalities": {"commander": "legal"},
            },
            "Baral, Chief of Compliance": {
                "name": "Baral, Chief of Compliance",
                "color_identity": ["U"],
                "type_line": "Legendary Creature — Human Wizard",
                "oracle_text": "Instant and sorcery spells you cast cost {1} less to cast.",
                "scryfall_uri": "https://scryfall.com/card/example/baral",
                "legalities": {"commander": "legal"},
            },
        }

    async def fail_get_card_by_name(self, name):
        raise AssertionError("get_card_by_name should not be called during deck analysis")

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)
    monkeypatch.setattr(ScryfallClient, "get_card_by_name", fail_get_card_by_name)

    response = client.post(
        "/deck/analyze",
        json={
            "name": "Bad Baral Deck",
            "format": "commander",
            "commander": "Baral, Chief of Compliance",
            "decklist": "1 Lightning Bolt\n99 Island",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["color_identity_violations"] == ["Lightning Bolt"]
    assert "Cards outside commander color identity: Lightning Bolt" in data["warnings"]


def test_analyze_endpoint_rate_limits_by_forwarded_ip(monkeypatch) -> None:
    async def fake_get_cards(self, names):
        return {
            "Island": {
                "name": "Island",
                "mana_cost": "",
                "cmc": 0,
                "colors": [],
                "color_identity": ["U"],
                "type_line": "Basic Land — Island",
                "oracle_text": "({T}: Add {U}.)",
                "scryfall_uri": "https://scryfall.com/card/example/island",
                "legalities": {"commander": "legal"},
            },
            "Baral, Chief of Compliance": {
                "name": "Baral, Chief of Compliance",
                "color_identity": ["U"],
                "type_line": "Legendary Creature — Human Wizard",
                "oracle_text": "Instant and sorcery spells you cast cost {1} less to cast.",
                "scryfall_uri": "https://scryfall.com/card/example/baral",
                "legalities": {"commander": "legal"},
            },
        }

    monkeypatch.setattr(ScryfallClient, "get_cards", fake_get_cards)
    analyze_rate_limiter.reset()
    original_max_requests = analyze_rate_limiter.max_requests
    original_window_seconds = analyze_rate_limiter.window_seconds
    analyze_rate_limiter.max_requests = 2
    analyze_rate_limiter.window_seconds = 60

    payload = {
        "name": "Rate Limit Test",
        "format": "commander",
        "commander": "Baral, Chief of Compliance",
        "decklist": "99 Island",
    }
    headers = {"CF-Connecting-IP": "203.0.113.10"}

    try:
        first = client.post("/deck/analyze", json=payload, headers=headers)
        second = client.post("/deck/analyze", json=payload, headers=headers)
        limited = client.post("/deck/analyze", json=payload, headers=headers)
    finally:
        analyze_rate_limiter.max_requests = original_max_requests
        analyze_rate_limiter.window_seconds = original_window_seconds
        analyze_rate_limiter.reset()

    assert first.status_code == 200
    assert second.status_code == 200
    assert limited.status_code == 429
    assert limited.json()["detail"] == "Rate limit reached for deck analysis. Please wait a minute and try again."
    assert limited.headers["Retry-After"]

import re

from fastapi import APIRouter

from app.models.requests import DeckAnalyzeRequest
from app.models.responses import ArchetypeGuess, CardDetails, CommanderSummary, DeckAnalyzeResponse, DeckCardEntry
from app.services.analyzer import analyze_cards
from app.services.parser import parse_deck_input, parse_deck_sections
from app.services.scryfall import ScryfallClient

router = APIRouter(prefix="/deck", tags=["deck"])


def extract_image_urls(details: dict) -> tuple[str | None, str | None]:
    image_uris = details.get("image_uris")
    if image_uris:
        return image_uris.get("small"), image_uris.get("normal")

    card_faces = details.get("card_faces") or []
    for face in card_faces:
        face_images = face.get("image_uris")
        if face_images:
            return face_images.get("small"), face_images.get("normal")

    return None, None


def build_card_details(details: dict | None) -> CardDetails | None:
    if not details:
        return None

    image_small, image_normal = extract_image_urls(details)

    return CardDetails(
        name=details.get("name", "Unknown"),
        mana_cost=details.get("mana_cost"),
        mana_value=details.get("cmc"),
        type_line=details.get("type_line"),
        oracle_text=details.get("oracle_text"),
        colors=details.get("colors", []),
        color_identity=details.get("color_identity", []),
        image_small=image_small,
        image_normal=image_normal,
        scryfall_uri=details.get("scryfall_uri"),
    )


def parse_commander_names(commander_text: str | None) -> list[str]:
    if not commander_text:
        return []

    normalized = commander_text.replace(" // ", "\n").replace(" / ", "\n").replace(";", "\n")
    parts = re.split(r"\n+", normalized)
    return [part.strip() for part in parts if part.strip()]


def build_commander_summary(details: dict | None, fallback_name: str) -> CommanderSummary | None:
    if not details:
        return None

    image_small, _ = extract_image_urls(details)
    return CommanderSummary(
        name=details.get("name", fallback_name),
        color_identity=details.get("color_identity", []),
        type_line=details.get("type_line"),
        image_small=image_small,
        scryfall_uri=details.get("scryfall_uri"),
    )


@router.post("/analyze", response_model=DeckAnalyzeResponse)
async def analyze_deck(payload: DeckAnalyzeRequest) -> DeckAnalyzeResponse:
    parsed_cards, autodetected_sideboard, parsed_commanders = parse_deck_input(payload.decklist)
    sideboard_mainboard, sideboard_detected = parse_deck_sections(payload.sideboard or "")
    parsed_sideboard = autodetected_sideboard + sideboard_mainboard + sideboard_detected
    client = ScryfallClient()
    commander_names = parse_commander_names(payload.commander) if payload.format.lower() == "commander" else []
    if payload.format.lower() == "commander" and not commander_names and parsed_commanders:
        commander_names = [card["name"] for card in parsed_commanders]
    all_names = (
        [card["name"] for card in parsed_cards]
        + [card["name"] for card in parsed_sideboard]
        + commander_names
    )
    card_details = await client.get_cards(all_names)
    commander_details_map = {name: card_details.get(name) for name in commander_names}
    commander_details_list = [commander_details_map.get(name) for name in commander_names]
    analysis = analyze_cards(
        parsed_cards,
        parsed_sideboard,
        card_details,
        payload.format,
        commander_names=commander_names,
        commander_details_list=commander_details_list,
    )

    commanders = [
        summary
        for summary in (build_commander_summary(commander_details_map.get(name), name) for name in commander_names)
        if summary is not None
    ]
    commander = commanders[0] if len(commanders) == 1 else None

    return DeckAnalyzeResponse(
        deck_name=payload.name,
        format=payload.format,
        commander=commander,
        commanders=commanders,
        deck_color_identity=analysis["deck_color_identity"],
        color_identity_violations=analysis["color_identity_violations"],
        total_cards=analysis["total_cards"],
        mainboard_count=analysis["mainboard_count"],
        sideboard_count=analysis["sideboard_count"],
        unique_cards=analysis["unique_cards"],
        color_identity=analysis["color_identity"],
        mana_curve=analysis["mana_curve"],
        type_breakdown=analysis["type_breakdown"],
        classification_counts=analysis["classification_counts"],
        recommendations=analysis["recommendations"],
        warnings=analysis["warnings"],
        primary_archetype=analysis["primary_archetype"],
        archetype_guesses=[ArchetypeGuess(**guess) for guess in analysis["archetype_guesses"]],
        parsed_cards=[
            DeckCardEntry(
                quantity=card["quantity"],
                name=card["name"],
                categories=analysis["card_classifications"].get(card["name"], []),
                card=build_card_details(card_details.get(card["name"])),
            )
            for card in parsed_cards
        ],
        parsed_sideboard=[
            DeckCardEntry(
                quantity=card["quantity"],
                name=card["name"],
                categories=analysis["card_classifications"].get(card["name"], []),
                card=build_card_details(card_details.get(card["name"])),
            )
            for card in parsed_sideboard
        ],
    )

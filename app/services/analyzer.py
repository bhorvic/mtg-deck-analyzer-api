import re
from collections import Counter

BASIC_LANDS = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}
SIXTY_CARD_FORMATS = {"standard", "pioneer", "modern", "pauper", "legacy", "vintage"}
TYPE_KEYS = [
    "Creature",
    "Instant",
    "Sorcery",
    "Artifact",
    "Enchantment",
    "Land",
    "Planeswalker",
]

RAMP_KEYWORDS = (
    "add ",
    "search your library for a basic land",
    "search your library for a land",
    "treasure token",
)
DRAW_KEYWORDS = (
    "draw a card",
    "draw two cards",
    "draw three cards",
    "draw x cards",
)
REMOVAL_KEYWORDS = (
    "destroy target",
    "exile target",
    "return target",
    "damage to any target",
    "counter target",
    "sacrifices ",
)
NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

ARCHETYPE_SIGNATURES = {
    "commander": {
        "Spellslinger": {"Baral, Chief of Compliance", "Talrand, Sky Summoner", "Archmage Emeritus", "Storm-Kiln Artist"},
        "Artifacts": {"Sol Ring", "Arcane Signet", "Thought Vessel", "Mind Stone"},
        "Lands": {"Crucible of Worlds", "Ramunap Excavator", "Exploration", "Azusa, Lost but Seeking"},
        "Enchantress": {"Sythis, Harvest's Hand", "Mesa Enchantress", "Setessan Champion", "Enchantress's Presence"},
    },
    "modern": {
        "Burn": {"Goblin Guide", "Monastery Swiftspear", "Lightning Bolt", "Lava Spike", "Boros Charm"},
        "Tron": {"Urza's Tower", "Urza's Mine", "Urza's Power Plant", "Karn Liberated"},
        "Hammer Time": {"Colossus Hammer", "Sigarda's Aid", "Puresteel Paladin", "Urza's Saga"},
        "Living End": {"Living End", "Violent Outburst", "Shardless Agent", "Street Wraith"},
    },
    "pioneer": {
        "Spirits": {"Mausoleum Wanderer", "Supreme Phantom", "Rattlechains", "Spell Queller"},
        "Phoenix": {"Arclight Phoenix", "Consider", "Treasure Cruise", "Pieces of the Puzzle"},
        "Rakdos Midrange": {"Bloodtithe Harvester", "Fable of the Mirror-Breaker", "Thoughtseize", "Fatal Push"},
    },
    "vintage": {
        "Shops": {"Mishra's Workshop", "Ancient Tomb", "Sphere of Resistance", "Lodestone Golem", "Wasteland"},
        "Stax": {"Trinisphere", "Chalice of the Void", "Lodestone Golem", "Wasteland", "Strip Mine"},
        "Artifacts": {"Mox Sapphire", "Black Lotus", "Mana Crypt", "Sol Ring", "The One Ring"},
        "Dredge": {"Bazaar of Baghdad", "Bridge from Below", "Golgari Grave-Troll", "Ichorid"},
    },
    "standard": {
        "Control": {"Sunfall", "Memory Deluge", "Three Steps Ahead"},
        "Domain": {"Leyline Binding", "Up the Beanstalk", "Herd Migration", "Atraxa, Grand Unifier"},
    },
}


def detect_archetypes(
    parsed_cards: list[dict],
    card_details: dict[str, dict | None],
    summary: dict,
    deck_format: str,
    commander_names: list[str] | None = None,
) -> list[dict]:
    commander_names = commander_names or []
    guesses: dict[str, dict] = {}
    mainboard_total = max(summary["total_cards"], 1)
    type_breakdown = Counter(summary["type_breakdown"])
    classification_counts = Counter(summary["classification_counts"])
    card_names = {entry["name"] for entry in parsed_cards}
    card_names.update(commander_names)
    instants_and_sorceries = type_breakdown.get("instants", 0) + type_breakdown.get("sorceries", 0)
    creatures = type_breakdown.get("creatures", 0)
    lands = type_breakdown.get("lands", 0)
    low_curve = sum(summary["mana_curve"].get(str(bucket), 0) for bucket in (0, 1, 2)) / mainboard_total

    def add_guess(name: str, score: float, reason: str, support_cards: list[str] | None = None) -> None:
        guess = guesses.setdefault(name, {"name": name, "score": 0.0, "reasons": [], "support_cards": []})
        guess["score"] += score
        if reason not in guess["reasons"]:
            guess["reasons"].append(reason)
        for card_name in support_cards or []:
            if card_name not in guess["support_cards"]:
                guess["support_cards"].append(card_name)

    for archetype, signature_cards in ARCHETYPE_SIGNATURES.get(deck_format.lower(), {}).items():
        matches = sorted(card_names & signature_cards)
        if matches:
            match_ratio = len(matches) / max(len(signature_cards), 1)
            specificity_bonus = min(0.12, 0.03 * len(matches))
            add_guess(
                archetype,
                0.34 + (0.26 * match_ratio) + specificity_bonus,
                f"Matched signature cards: {', '.join(matches[:4])}",
                support_cards=matches,
            )

    if instants_and_sorceries / mainboard_total >= 0.28:
        add_guess("Spellslinger", 0.28, "High instant and sorcery density")
    if classification_counts.get("draw", 0) >= 8 and instants_and_sorceries / mainboard_total >= 0.2:
        add_guess("Control", 0.18, "Strong draw package with lots of stack interaction")
    if classification_counts.get("removal", 0) >= 8:
        add_guess("Control", 0.2, "Heavy interaction profile")
    if low_curve >= 0.55 and creatures / mainboard_total >= 0.22:
        add_guess("Aggro", 0.3, "Very low curve with meaningful creature pressure")
    if low_curve >= 0.45 and classification_counts.get("removal", 0) >= 6:
        add_guess("Tempo", 0.22, "Low curve backed by interaction")
    if classification_counts.get("ramp", 0) >= 10 or lands >= 40:
        add_guess("Ramp", 0.24, "Ramp density or land count is above typical baseline")
    if creatures / mainboard_total >= 0.3 and len(summary["deck_color_identity"]) <= 3 and low_curve < 0.45:
        add_guess("Midrange", 0.2, "Creature-heavy shell with a more measured curve")

    artifact_count = type_breakdown.get("artifacts", 0)
    artifact_ratio = artifact_count / mainboard_total
    if artifact_ratio >= 0.35:
        add_guess("Artifacts", 0.24 + min(0.16, artifact_ratio * 0.2), "Artifact density is a major part of the shell")
    if deck_format.lower() == "vintage":
        workshop_names = {"Mishra's Workshop", "Ancient Tomb", "Wasteland", "Strip Mine", "Tolarian Academy"}
        workshop_matches = sorted(card_names & workshop_names)
        if len(workshop_matches) >= 2:
            add_guess("Shops", 0.34 + min(0.16, 0.05 * len(workshop_matches)), f"Workshop-style mana base detected: {', '.join(workshop_matches[:4])}", support_cards=workshop_matches)
        stax_names = {"Chalice of the Void", "Trinisphere", "Lodestone Golem", "Pithing Needle", "The One Ring"}
        stax_matches = sorted(card_names & stax_names)
        if len(stax_matches) >= 2:
            add_guess("Stax", 0.26 + min(0.14, 0.04 * len(stax_matches)), f"Prison/tax pieces detected: {', '.join(stax_matches[:4])}", support_cards=stax_matches)

    burn_names = {"Lightning Bolt", "Lava Spike", "Skewer the Critics", "Boros Charm", "Rift Bolt"}
    burn_matches = sorted(card_names & burn_names)
    if len(burn_matches) >= 3:
        add_guess("Burn", 0.4 + min(0.14, 0.04 * len(burn_matches)), f"Multiple direct-damage staples detected: {', '.join(burn_matches[:4])}", support_cards=burn_matches)

    if commander_names and instants_and_sorceries / mainboard_total >= 0.22:
        add_guess("Commander Value", 0.1, "Commander shell leans on value spells and support pieces")
    if deck_format.lower() == "modern":
        tron_lands = {"Urza's Tower", "Urza's Mine", "Urza's Power Plant"}
        tron_matches = sorted(card_names & tron_lands)
        if len(tron_matches) == 3:
            add_guess("Tron", 0.28, "All three Urza lands are present", support_cards=tron_matches)
        hammer_names = {"Colossus Hammer", "Sigarda's Aid", "Puresteel Paladin", "Urza's Saga"}
        hammer_matches = sorted(card_names & hammer_names)
        if len(hammer_matches) >= 2:
            add_guess("Hammer Time", 0.22, f"Core hammer pieces detected: {', '.join(hammer_matches[:4])}", support_cards=hammer_matches)
    if deck_format.lower() == "pioneer":
        if {"Mausoleum Wanderer", "Rattlechains", "Spell Queller"} <= card_names:
            add_guess("Spirits", 0.22, "Core flash-flying Spirits package detected", support_cards=["Mausoleum Wanderer", "Rattlechains", "Spell Queller"])
        if {"Arclight Phoenix", "Consider", "Treasure Cruise"} <= card_names:
            add_guess("Phoenix", 0.24, "Phoenix cantrip/recursion core detected", support_cards=["Arclight Phoenix", "Consider", "Treasure Cruise"])
        rakdos_names = {"Bloodtithe Harvester", "Fable of the Mirror-Breaker", "Thoughtseize", "Fatal Push"}
        rakdos_matches = sorted(card_names & rakdos_names)
        if len(rakdos_matches) >= 3:
            add_guess("Rakdos Midrange", 0.22, f"Rakdos staple package detected: {', '.join(rakdos_matches[:4])}", support_cards=rakdos_matches)
    if deck_format.lower() == "commander":
        enchantments = type_breakdown.get("enchantments", 0)
        if enchantments / mainboard_total >= 0.12:
            add_guess("Enchantress", 0.18, "Enchantment density suggests an enchantress shell")
        if lands / mainboard_total >= 0.38 and classification_counts.get("ramp", 0) >= 8:
            add_guess("Lands", 0.18, "High land count plus ramp points toward a lands strategy")

    if not guesses:
        return []

    max_score = max(guess["score"] for guess in guesses.values())
    ordered = sorted(guesses.values(), key=lambda item: (-item["score"], item["name"]))

    return [
        {
            "name": guess["name"],
            "confidence": round(min(0.97, 0.45 + (0.48 * (guess["score"] / max_score))), 2),
            "reasons": guess["reasons"],
            "support_cards": guess["support_cards"],
        }
        for guess in ordered[:3]
    ]



def build_recommendations(
    total_cards: int,
    type_breakdown: Counter[str],
    classification_counts: Counter[str],
    deck_format: str,
) -> list[str]:
    recommendations: list[str] = []
    lands = type_breakdown.get("lands", 0)
    ramp = classification_counts.get("ramp", 0)
    draw = classification_counts.get("draw", 0)
    removal = classification_counts.get("removal", 0)
    boardwipes = classification_counts.get("boardwipe", 0)
    format_name = deck_format.lower()

    if format_name == "commander":
        if total_cards >= 90 and lands < 34:
            recommendations.append("Land count looks low for Commander; consider aiming for around 34-38 lands.")
        elif lands > 40:
            recommendations.append("Land count is pretty high; you may be able to trim a few lands for more action cards.")

        if ramp < 8:
            recommendations.append("Ramp looks light; consider adding more mana rocks, dorks, or land ramp.")
        if draw < 8:
            recommendations.append("Card draw looks a bit low; adding more draw can help the deck stay consistent.")
        if removal < 8:
            recommendations.append("Interaction looks light; consider a few more targeted removal or counterspell slots.")
        if boardwipes == 0:
            recommendations.append("You may want at least one boardwipe as a reset button.")
    elif format_name in SIXTY_CARD_FORMATS:
        if lands < 20:
            recommendations.append(f"Land count looks low for a typical {deck_format.title()} deck unless this is an unusually low-curve build.")
        elif lands > 28:
            recommendations.append(f"Land count is on the high side for many {deck_format.title()} decks; make sure the curve really needs it.")

        if removal < 4:
            recommendations.append(f"Interaction looks light for {deck_format.title()}; consider adding more removal or stack interaction.")
        if draw == 0:
            recommendations.append("You may want some card selection or card advantage to improve consistency.")

    if not recommendations:
        recommendations.append("The deck's core ratios look pretty reasonable at a glance.")

    return recommendations


def classify_card(details: dict | None) -> list[str]:
    if not details:
        return []

    categories: list[str] = []
    oracle_text = details.get("oracle_text", "").lower()
    type_line = details.get("type_line", "")
    is_land = "Land" in type_line

    if not is_land and any(keyword in oracle_text for keyword in RAMP_KEYWORDS):
        categories.append("ramp")
    if any(keyword in oracle_text for keyword in DRAW_KEYWORDS):
        categories.append("draw")
    if any(keyword in oracle_text for keyword in REMOVAL_KEYWORDS):
        categories.append("removal")
    if "Boardwipe" in type_line or "each creature" in oracle_text and "destroy" in oracle_text:
        categories.append("boardwipe")

    return categories


def build_card_classifications(parsed_cards: list[dict], card_details: dict[str, dict | None]) -> dict[str, list[str]]:
    return {
        entry["name"]: classify_card(card_details.get(entry["name"]))
        for entry in parsed_cards
    }



def summarize_cards(parsed_cards: list[dict], card_details: dict[str, dict | None]) -> dict:
    total_cards = sum(card["quantity"] for card in parsed_cards)
    unique_cards = len(parsed_cards)
    mana_curve: Counter[str] = Counter()
    type_breakdown: Counter[str] = Counter()
    classification_counts: Counter[str] = Counter()
    color_identity: set[str] = set()
    warnings: list[str] = []
    seen: dict[str, int] = {}
    card_classifications = build_card_classifications(parsed_cards, card_details)

    for entry in parsed_cards:
        name = entry["name"]
        quantity = entry["quantity"]
        seen[name] = seen.get(name, 0) + quantity
        details = card_details.get(name)

        if not details:
            warnings.append(f"Card not found in Scryfall: {name}")
            continue

        mana_value = details.get("cmc", 0)
        bucket = "6+" if mana_value >= 6 else str(int(mana_value))
        mana_curve[bucket] += quantity

        for color in details.get("color_identity", []):
            color_identity.add(color)

        type_line = details.get("type_line", "")
        for type_key in TYPE_KEYS:
            if type_key in type_line:
                type_breakdown[type_key.lower() + "s"] += quantity

        for category in card_classifications[name]:
            classification_counts[category] += quantity

    return {
        "total_cards": total_cards,
        "unique_cards": unique_cards,
        "mana_curve": dict(sorted(mana_curve.items(), key=lambda item: (item[0] != "6+", item[0]))),
        "type_breakdown": dict(type_breakdown),
        "classification_counts": dict(classification_counts),
        "deck_color_identity": sorted(color_identity),
        "card_classifications": card_classifications,
        "seen": seen,
        "warnings": warnings,
    }


def parse_copy_limit_from_text(oracle_text: str) -> int | None | bool:
    text = oracle_text.lower()
    if "a deck can have any number of cards named" in text:
        return None

    match = re.search(r"a deck can have up to ([a-z0-9-]+) cards named", text)
    if not match:
        return False

    raw_value = match.group(1)
    if raw_value.isdigit():
        return int(raw_value)
    return NUMBER_WORDS.get(raw_value, False)


def allowed_copy_count(name: str, details: dict | None, default_limit: int) -> int | None:
    if name in BASIC_LANDS:
        return None
    if not details:
        return default_limit

    parsed_limit = parse_copy_limit_from_text(details.get("oracle_text", ""))
    if parsed_limit is False:
        return default_limit
    return parsed_limit


def can_be_commander(details: dict) -> bool:
    type_line = details.get("type_line", "")
    oracle_text = details.get("oracle_text", "").lower()

    if "Legendary Creature" in type_line:
        return True

    return "can be your commander" in oracle_text


def has_partner_text(details: dict) -> bool:
    oracle_text = details.get("oracle_text", "").lower()
    return any(text in oracle_text for text in ("partner", "friends forever"))


def has_choose_a_background(details: dict) -> bool:
    return "choose a background" in details.get("oracle_text", "").lower()


def is_background(details: dict) -> bool:
    return "Background" in details.get("type_line", "")


def has_doctors_companion(details: dict) -> bool:
    return "doctor's companion" in details.get("oracle_text", "").lower()


def is_doctor(details: dict) -> bool:
    return "Time Lord Doctor" in details.get("type_line", "")


def commanders_can_pair(commander_details_list: list[dict]) -> bool:
    if len(commander_details_list) != 2:
        return False

    first, second = commander_details_list
    if has_partner_text(first) and has_partner_text(second):
        return True
    if (has_choose_a_background(first) and is_background(second)) or (
        has_choose_a_background(second) and is_background(first)
    ):
        return True
    if (has_doctors_companion(first) and is_doctor(second)) or (
        has_doctors_companion(second) and is_doctor(first)
    ):
        return True

    return False


def validate_commander(
    total_cards: int,
    sideboard_total: int,
    seen: dict[str, int],
    parsed_cards: list[dict],
    card_details: dict[str, dict | None],
    commander_names: list[str],
    commander_details_list: list[dict | None],
) -> dict:
    warnings: list[str] = []
    commander_color_identity: list[str] = []
    color_identity_violations: list[str] = []

    commander_count = len(commander_names)
    expected_mainboard = 100 - commander_count if commander_count else 100
    if total_cards != expected_mainboard:
        if commander_count:
            warnings.append(
                f"Commander decks should contain {expected_mainboard} main-deck cards plus {commander_count} commander(s); found {total_cards}"
            )
        else:
            warnings.append(f"Commander decks should contain 100 cards; found {total_cards}")

    if sideboard_total > 0:
        warnings.append(f"Commander sideboards are not supported here; found {sideboard_total} sideboard cards")

    duplicates = []
    for name, qty in seen.items():
        limit = allowed_copy_count(name, card_details.get(name), 1)
        if limit is not None and qty > limit:
            duplicates.append(f"{name} ({qty})")
    if duplicates:
        warnings.append("Possible illegal duplicates: " + ", ".join(sorted(duplicates)))

    if not commander_names:
        warnings.append("No commander provided. Add one to enable color identity validation.")
        return {
            "warnings": warnings,
            "commander_color_identity": commander_color_identity,
            "color_identity_violations": sorted(set(color_identity_violations)),
        }

    if commander_count > 2:
        warnings.append("Only up to two commanders are supported right now.")

    found_commanders = [details for details in commander_details_list if details]
    for commander_name in commander_names:
        if seen.get(commander_name, 0) > 0:
            warnings.append(f"Commander appears in the main decklist: {commander_name}")

    for commander_name, commander_details in zip(commander_names, commander_details_list):
        if not commander_details:
            warnings.append(f"Commander not found in Scryfall: {commander_name}")
            continue

        commander_legality = (commander_details.get("legalities") or {}).get("commander")
        if commander_legality and commander_legality != "legal":
            warnings.append(f"Commander is not legal in Commander: {commander_name} ({commander_legality})")
        if not can_be_commander(commander_details) and not is_background(commander_details):
            warnings.append(f"Commander does not appear to be a legal commander: {commander_name}")

        for color in commander_details.get("color_identity", []):
            if color not in commander_color_identity:
                commander_color_identity.append(color)

    if commander_count == 2 and len(found_commanders) == 2 and not commanders_can_pair(found_commanders):
        warnings.append("These two commanders do not appear to form a legal commander pair (partner/background/Doctor's companion not detected).")

    for entry in parsed_cards:
        details = card_details.get(entry["name"])
        if not details:
            continue
        card_legality = (details.get("legalities") or {}).get("commander")
        if card_legality and card_legality != "legal":
            warnings.append(f"Not Commander legal: {entry['name']}")
        for color in details.get("color_identity", []):
            if color not in commander_color_identity:
                color_identity_violations.append(entry["name"])
                break

    if color_identity_violations:
        warnings.append(
            "Cards outside commander color identity: "
            + ", ".join(sorted(set(color_identity_violations)))
        )

    return {
        "warnings": sorted(set(warnings)),
        "commander_color_identity": sorted(commander_color_identity),
        "color_identity_violations": sorted(set(color_identity_violations)),
    }


def validate_sixty_card_format(
    format_name: str,
    mainboard_total: int,
    sideboard_total: int,
    combined_seen: dict[str, int],
    combined_cards: list[dict],
    card_details: dict[str, dict | None],
    restricted_limit: int | None = None,
) -> dict:
    warnings: list[str] = []
    format_label = format_name.title()

    if mainboard_total < 60:
        warnings.append(f"{format_label} decks should contain at least 60 cards; found {mainboard_total}")
    if sideboard_total > 15:
        warnings.append(f"{format_label} sideboards can contain at most 15 cards; found {sideboard_total}")

    duplicates = []
    for name, qty in combined_seen.items():
        limit = allowed_copy_count(name, card_details.get(name), 4)
        if limit is not None and qty > limit:
            duplicates.append(f"{name} ({qty})")
    if duplicates:
        warnings.append(f"Too many copies for {format_label}: " + ", ".join(sorted(duplicates)))

    illegal_cards: list[str] = []
    restricted_violations: list[str] = []
    for entry in combined_cards:
        details = card_details.get(entry["name"])
        if not details:
            continue
        legality = (details.get("legalities") or {}).get(format_name)
        if legality not in {"legal", "restricted"}:
            illegal_cards.append(entry["name"])
        elif legality == "restricted" and restricted_limit is not None:
            qty = combined_seen.get(entry["name"], 0)
            if qty > restricted_limit:
                restricted_violations.append(f"{entry['name']} ({qty})")

    if illegal_cards:
        warnings.append(f"Not {format_label} legal: " + ", ".join(sorted(set(illegal_cards))))
    if restricted_violations:
        warnings.append(
            f"Restricted cards exceed {restricted_limit} copy in {format_label}: "
            + ", ".join(sorted(set(restricted_violations)))
        )

    return {"warnings": warnings}


def analyze_cards(
    parsed_cards: list[dict],
    sideboard_cards: list[dict],
    card_details: dict[str, dict | None],
    deck_format: str,
    commander_names: list[str] | None = None,
    commander_details_list: list[dict | None] | None = None,
) -> dict:
    summary = summarize_cards(parsed_cards, card_details)
    sideboard_classifications = build_card_classifications(sideboard_cards, card_details)
    mainboard_total = summary["total_cards"]
    sideboard_total = sum(card["quantity"] for card in sideboard_cards)
    format_name = deck_format.lower()
    warnings = list(summary["warnings"])
    color_identity_violations: list[str] = []
    commander_color_identity: list[str] = []

    commander_names = commander_names or []
    commander_details_list = commander_details_list or []

    if format_name == "commander":
        result = validate_commander(
            mainboard_total,
            sideboard_total,
            summary["seen"],
            parsed_cards,
            card_details,
            commander_names,
            commander_details_list,
        )
        warnings.extend(result["warnings"])
        color_identity_violations = result["color_identity_violations"]
        commander_color_identity = result["commander_color_identity"]
    elif format_name in SIXTY_CARD_FORMATS:
        combined_seen = dict(summary["seen"])
        for entry in sideboard_cards:
            combined_seen[entry["name"]] = combined_seen.get(entry["name"], 0) + entry["quantity"]
        result = validate_sixty_card_format(
            format_name,
            mainboard_total,
            sideboard_total,
            combined_seen,
            parsed_cards + sideboard_cards,
            card_details,
            restricted_limit=1 if format_name == "vintage" else None,
        )
        warnings.extend(result["warnings"])

    archetype_guesses = detect_archetypes(
        parsed_cards,
        card_details,
        summary,
        deck_format,
        commander_names=commander_names,
    )

    return {
        "total_cards": mainboard_total,
        "mainboard_count": mainboard_total,
        "sideboard_count": sideboard_total,
        "unique_cards": summary["unique_cards"],
        "color_identity": summary["deck_color_identity"],
        "deck_color_identity": summary["deck_color_identity"],
        "color_identity_violations": color_identity_violations,
        "commander_color_identity": commander_color_identity,
        "mana_curve": summary["mana_curve"],
        "type_breakdown": summary["type_breakdown"],
        "classification_counts": summary["classification_counts"],
        "card_classifications": {
            **summary["card_classifications"],
            **sideboard_classifications,
        },
        "recommendations": build_recommendations(
            mainboard_total,
            Counter(summary["type_breakdown"]),
            Counter(summary["classification_counts"]),
            deck_format,
        ),
        "warnings": warnings,
        "primary_archetype": archetype_guesses[0]["name"] if archetype_guesses else None,
        "archetype_guesses": archetype_guesses,
    }

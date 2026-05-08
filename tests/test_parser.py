from app.services.parser import parse_deck_input, parse_deck_sections, parse_decklist


def test_parse_decklist_handles_counts_and_defaults() -> None:
    decklist = "1 Sol Ring\nArcane Signet\n2 Island"

    result = parse_decklist(decklist)

    assert result == [
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 1, "name": "Arcane Signet"},
        {"quantity": 2, "name": "Island"},
    ]


def test_parse_decklist_ignores_blank_lines() -> None:
    result = parse_decklist("\n1 Mountain\n\n2 Lightning Bolt\n")

    assert result == [
        {"quantity": 1, "name": "Mountain"},
        {"quantity": 2, "name": "Lightning Bolt"},
    ]


def test_parse_deck_sections_detects_sideboard_and_headers() -> None:
    mainboard, sideboard = parse_deck_sections(
        "Deck\n4 Lightning Bolt\n2x Mishra's Bauble\nSideboard\n2 Collector Ouphe\nSB: 1 Endurance"
    )

    assert mainboard == [
        {"quantity": 4, "name": "Lightning Bolt"},
        {"quantity": 2, "name": "Mishra's Bauble"},
    ]
    assert sideboard == [
        {"quantity": 2, "name": "Collector Ouphe"},
        {"quantity": 1, "name": "Endurance"},
    ]


def test_parse_deck_sections_strips_set_codes() -> None:
    mainboard, sideboard = parse_deck_sections("4 Vengevine (UMA) 34\nSideboard\n1 Force of Vigor (MH1) 164")

    assert mainboard == [{"quantity": 4, "name": "Vengevine"}]
    assert sideboard == [{"quantity": 1, "name": "Force of Vigor"}]



def test_parse_deck_input_extracts_commander_section() -> None:
    mainboard, sideboard, commanders = parse_deck_input(
        "Commander\n1 Baral, Chief of Compliance\n\nDeck\n1 Sol Ring\n97 Island\n\nSideboard\n1 Pongify"
    )

    assert commanders == [{"quantity": 1, "name": "Baral, Chief of Compliance"}]
    assert mainboard == [
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 97, "name": "Island"},
    ]
    assert sideboard == [{"quantity": 1, "name": "Pongify"}]



def test_parse_deck_input_extracts_inline_commander_entry() -> None:
    mainboard, sideboard, commanders = parse_deck_input(
        "Commander: 1 Baral, Chief of Compliance\nDeck\n1 Sol Ring\n98 Island"
    )

    assert commanders == [{"quantity": 1, "name": "Baral, Chief of Compliance"}]
    assert mainboard == [
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 98, "name": "Island"},
    ]
    assert sideboard == []



def test_parse_decklist_ignores_notes_comments_and_separators() -> None:
    result = parse_decklist(
        "// maybe board this later\n# burn shell\n* test note\n4 Lightning Bolt # premium burn\n---\n2 Wear // Tear\n20 Mountain\n"
    )

    assert result == [
        {"quantity": 4, "name": "Lightning Bolt"},
        {"quantity": 2, "name": "Wear // Tear"},
        {"quantity": 20, "name": "Mountain"},
    ]



def test_parse_decklist_strips_bracket_set_tags() -> None:
    result = parse_decklist("4 Lightning Bolt [M11]\n20 Mountain [SLD]")

    assert result == [
        {"quantity": 4, "name": "Lightning Bolt"},
        {"quantity": 20, "name": "Mountain"},
    ]



def test_parse_decklist_ignores_malformed_quantity_prefixes() -> None:
    result = parse_decklist(
        "x Lightning Bolt\n-1 Lightning Bolt\n+4 Lightning Bolt\n1.5 Lightning Bolt\n0 Lightning Bolt\n20 Mountain"
    )

    assert result == [
        {"quantity": 20, "name": "Mountain"},
    ]



def test_parse_decklist_supports_comma_quantities() -> None:
    result = parse_decklist("1,000 Rat Colony\n20 Swamp")

    assert result == [
        {"quantity": 1000, "name": "Rat Colony"},
        {"quantity": 20, "name": "Swamp"},
    ]



def test_parse_deck_input_treats_companion_section_as_sideboard() -> None:
    mainboard, sideboard, commanders = parse_deck_input(
        "Companion\n1 Yorion, Sky Nomad\n\nDeck\n4 Lightning Bolt\n56 Mountain"
    )

    assert commanders == []
    assert mainboard == [
        {"quantity": 4, "name": "Lightning Bolt"},
        {"quantity": 56, "name": "Mountain"},
    ]
    assert sideboard == [{"quantity": 1, "name": "Yorion, Sky Nomad"}]


def test_parse_deck_input_ignores_maybeboard_section() -> None:
    mainboard, sideboard, commanders = parse_deck_input(
        "Deck\n4 Lightning Bolt\n20 Mountain\n\nMaybeboard\n2 Skullcrack\n1 Roiling Vortex\n\nSideboard\n2 Path to Exile"
    )

    assert commanders == []
    assert mainboard == [
        {"quantity": 4, "name": "Lightning Bolt"},
        {"quantity": 20, "name": "Mountain"},
    ]
    assert sideboard == [{"quantity": 2, "name": "Path to Exile"}]


def test_parse_deck_input_ignores_counted_section_headers() -> None:
    mainboard, sideboard, commanders = parse_deck_input(
        "Commander (1)\n1 Baral, Chief of Compliance\n\nCreatures (2)\n1 Snapcaster Mage\n1 Talrand, Sky Summoner\n\nSpells (2)\n1 Ponder\n1 Counterspell\n\nLands (2)\n2 Island\n\nSideboard (1)\n1 Pongify"
    )

    assert commanders == [{"quantity": 1, "name": "Baral, Chief of Compliance"}]
    assert mainboard == [
        {"quantity": 1, "name": "Snapcaster Mage"},
        {"quantity": 1, "name": "Talrand, Sky Summoner"},
        {"quantity": 1, "name": "Ponder"},
        {"quantity": 1, "name": "Counterspell"},
        {"quantity": 2, "name": "Island"},
    ]
    assert sideboard == [{"quantity": 1, "name": "Pongify"}]


def test_parse_deck_input_ignores_inline_maybeboard_entries() -> None:
    mainboard, sideboard, commanders = parse_deck_input(
        "Deck\n4 Lightning Bolt\nMaybeboard: 2 Skullcrack\n20 Mountain\nSideboard\n2 Path to Exile"
    )

    assert commanders == []
    assert mainboard == [
        {"quantity": 4, "name": "Lightning Bolt"},
        {"quantity": 20, "name": "Mountain"},
    ]
    assert sideboard == [{"quantity": 2, "name": "Path to Exile"}]


def test_parse_deck_input_treats_unknown_counted_categories_as_section_headers() -> None:
    mainboard, sideboard, commanders = parse_deck_input(
        "Ramp (2)\n1 Sol Ring\n1 Arcane Signet\nDraw (1)\n1 Ponder\nMaybeboard (1)\n1 Brainstorm\nSideboard (1)\n1 Pongify"
    )

    assert commanders == []
    assert mainboard == [
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 1, "name": "Arcane Signet"},
        {"quantity": 1, "name": "Ponder"},
    ]
    assert sideboard == [{"quantity": 1, "name": "Pongify"}]


def test_parse_deck_input_treats_generic_colon_headers_as_section_headers() -> None:
    mainboard, sideboard, commanders = parse_deck_input(
        "Ramp:\n1 Sol Ring\n1 Arcane Signet\nInteraction:\n1 Counterspell\nSideboard:\n1 Pongify"
    )

    assert commanders == []
    assert mainboard == [
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 1, "name": "Arcane Signet"},
        {"quantity": 1, "name": "Counterspell"},
    ]
    assert sideboard == [{"quantity": 1, "name": "Pongify"}]


def test_parse_deck_input_ignores_deck_title_before_real_sections() -> None:
    mainboard, sideboard, commanders = parse_deck_input(
        "Baral Spellslinger\nCommander\n1 Baral, Chief of Compliance\nDeck\n1 Sol Ring\n98 Island"
    )

    assert commanders == [{"quantity": 1, "name": "Baral, Chief of Compliance"}]
    assert mainboard == [
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 98, "name": "Island"},
    ]
    assert sideboard == []


def test_parse_decklist_supports_bullet_prefixed_entries() -> None:
    result = parse_decklist("- 1 Sol Ring\n• Arcane Signet\n– 2 Island")

    assert result == [
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 1, "name": "Arcane Signet"},
        {"quantity": 2, "name": "Island"},
    ]


def test_parse_decklist_strips_set_codes_without_collector_numbers() -> None:
    result = parse_decklist("1 Sol Ring (CMM)\n1 Arcane Signet [CLB]\n2 Island (SLD)")

    assert result == [
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 1, "name": "Arcane Signet"},
        {"quantity": 2, "name": "Island"},
    ]


def test_parse_decklist_strips_common_trailing_metadata_tags() -> None:
    result = parse_decklist(
        "1 Sol Ring (CMM) [Commander]\n1 Arcane Signet *F*\n1 Counterspell {Promo}\n1 Ponder (foil)\n2 Island [Sideboard]"
    )

    assert result == [
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 1, "name": "Arcane Signet"},
        {"quantity": 1, "name": "Counterspell"},
        {"quantity": 1, "name": "Ponder"},
        {"quantity": 2, "name": "Island"},
    ]


def test_parse_decklist_supports_checkbox_style_entries() -> None:
    result = parse_decklist("- [ ] 1 Sol Ring\n* [x] Arcane Signet\n[ ] 2 Island")

    assert result == [
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 1, "name": "Arcane Signet"},
        {"quantity": 2, "name": "Island"},
    ]


def test_parse_decklist_supports_separator_variants_after_quantities() -> None:
    result = parse_decklist(
        "4xLightning Bolt\n2 - Mishra's Bauble\n3 — Counterspell\n1: Sol Ring\n5\tIsland"
    )

    assert result == [
        {"quantity": 4, "name": "Lightning Bolt"},
        {"quantity": 2, "name": "Mishra's Bauble"},
        {"quantity": 3, "name": "Counterspell"},
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 5, "name": "Island"},
    ]


def test_parse_deck_input_supports_separator_variants_in_sections() -> None:
    mainboard, sideboard, commanders = parse_deck_input(
        "Commander: 1xBaral, Chief of Compliance\nDeck\n4xLightning Bolt\n2 - Island\nSideboard\nSB:1—Pongify"
    )

    assert commanders == [{"quantity": 1, "name": "Baral, Chief of Compliance"}]
    assert mainboard == [
        {"quantity": 4, "name": "Lightning Bolt"},
        {"quantity": 2, "name": "Island"},
    ]
    assert sideboard == [{"quantity": 1, "name": "Pongify"}]


def test_parse_decklist_supports_unicode_quantity_marker_and_curly_set_codes() -> None:
    result = parse_decklist("4×Lightning Bolt\n1 Sol Ring {CMM}\n2 Island {SLD}")

    assert result == [
        {"quantity": 4, "name": "Lightning Bolt"},
        {"quantity": 1, "name": "Sol Ring"},
        {"quantity": 2, "name": "Island"},
    ]

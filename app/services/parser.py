import re


LINE_PATTERN = re.compile(r"^(?:(\d[\d,]*)(?:\s*[xX×:\-–—]\s*|\s+))?(.+?)\s*$")
TRAILING_SET_INFO_PATTERN = re.compile(r"\s+\([A-Za-z0-9]{2,6}\)\s+\d+[a-zA-Z]?$")
TRAILING_SET_ONLY_PATTERN = re.compile(r"\s+\([A-Za-z0-9]{2,6}\)$")
TRAILING_BRACKET_SET_PATTERN = re.compile(r"\s+\[[A-Za-z0-9]{2,8}\]$")
TRAILING_CURLY_SET_PATTERN = re.compile(r"\s+\{[A-Za-z0-9]{2,8}\}$")
INVALID_QUANTITY_PREFIX_PATTERN = re.compile(r"^(?:[xX]|[+-]\d|\d+\.\d+)\S*\s+")
SECTION_HEADER_WITH_COUNT_PATTERN = re.compile(r"^([A-Za-z][A-Za-z\s]+?)\s*\(\d+\)\s*$")
GENERIC_SECTION_HEADER_PATTERN = re.compile(r"^([A-Za-z][A-Za-z0-9 '&/+-]{0,80})\s*:\s*$")
LEADING_BULLET_PATTERN = re.compile(r"^[\-•–—]\s+")
LEADING_CHECKBOX_PATTERN = re.compile(r"^(?:[\-*•–—]\s+)?\[[ xX]\]\s+")
TRAILING_ASTERISK_TAG_PATTERN = re.compile(r"\s+\*(?:f|foil|cmdr|commander|maybe|maybeboard|sb|sideboard|mb|mainboard|promo)\*$", re.IGNORECASE)
TRAILING_METADATA_LABEL_PATTERN = re.compile(
    r"\s+(?:\(|\[|\{)(?:foil|etched|showcase|borderless|retro\s+frame|extended\s+art|promo|commander|companion|maybeboard|sideboard|mainboard)(?:\)|\]|\})$",
    re.IGNORECASE,
)
SECTION_HEADERS = {
    "deck",
    "main",
    "mainboard",
    "maindeck",
    "sideboard",
    "commander",
    "commanders",
    "companions",
    "companion",
    "creatures",
    "spells",
    "lands",
    "artifacts",
    "enchantments",
    "instants",
    "sorceries",
    "planeswalkers",
    "maybeboard",
}
SIDEBOARD_MARKERS = {"sideboard", "sb", "side"}
COMMANDER_MARKERS = {"commander", "commanders"}
COMPANION_MARKERS = {"companion", "companions"}
MAYBEBOARD_MARKERS = {"maybeboard"}


def strip_inline_comment(line: str) -> str:
    hash_index = line.find(" #")
    if hash_index != -1:
        line = line[:hash_index]

    slash_index = line.find(" // ")
    if slash_index != -1:
        remainder = line[slash_index + 4 :].strip()
        if remainder and remainder[:1].islower():
            line = line[:slash_index]

    return line.strip()


def is_ignorable_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped in {"---", "***", "___"}:
        return True
    if LEADING_CHECKBOX_PATTERN.match(stripped):
        return False
    if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("*"):
        return True
    return False


def normalize_name(name: str) -> str:
    name = strip_inline_comment(name.strip())
    name = LEADING_CHECKBOX_PATTERN.sub("", name)
    name = LEADING_BULLET_PATTERN.sub("", name)
    previous = None
    while previous != name:
        previous = name
        name = TRAILING_SET_INFO_PATTERN.sub("", name)
        name = TRAILING_SET_ONLY_PATTERN.sub("", name)
        name = TRAILING_BRACKET_SET_PATTERN.sub("", name)
        name = TRAILING_CURLY_SET_PATTERN.sub("", name)
        name = TRAILING_ASTERISK_TAG_PATTERN.sub("", name)
        name = TRAILING_METADATA_LABEL_PATTERN.sub("", name)
    return name.strip()


def normalize_section_header(line: str) -> tuple[str, bool]:
    lowered = line.lower().rstrip(":").strip()
    match = SECTION_HEADER_WITH_COUNT_PATTERN.match(lowered)
    if match:
        return match.group(1).strip(), True

    generic_match = GENERIC_SECTION_HEADER_PATTERN.match(line.strip())
    if generic_match:
        return generic_match.group(1).strip().lower(), True

    return lowered, False


def line_has_explicit_quantity(line: str) -> bool:
    match = LINE_PATTERN.match(line.strip())
    return bool(match and match.group(1))


def should_ignore_deck_title(lines: list[str], index: int, saw_content: bool) -> bool:
    if saw_content or index != 0:
        return False

    line = lines[index].strip()
    if not line or ":" in line or line_has_explicit_quantity(line):
        return False

    normalized, is_header = normalize_section_header(line)
    if is_header or normalized in SECTION_HEADERS:
        return False

    for future_line in lines[index + 1 :]:
        candidate = future_line.strip()
        if is_ignorable_line(candidate):
            continue
        future_normalized, future_is_header = normalize_section_header(candidate)
        return future_is_header or future_normalized in SECTION_HEADERS

    return False


def parse_card_line(line: str) -> dict | None:
    cleaned_line = LEADING_CHECKBOX_PATTERN.sub("", line.strip())
    cleaned_line = LEADING_BULLET_PATTERN.sub("", cleaned_line)

    if INVALID_QUANTITY_PREFIX_PATTERN.match(cleaned_line):
        return None

    match = LINE_PATTERN.match(cleaned_line)
    if not match:
        return None

    quantity_text = match.group(1)
    quantity = int(quantity_text.replace(",", "")) if quantity_text else 1
    if quantity <= 0:
        return None

    name = normalize_name(match.group(2))
    if not name:
        return None

    return {"quantity": quantity, "name": name}


def parse_deck_input(decklist: str) -> tuple[list[dict], list[dict], list[dict]]:
    mainboard: list[dict] = []
    sideboard: list[dict] = []
    commanders: list[dict] = []
    current_section = "mainboard"
    lines = decklist.splitlines()
    saw_content = False

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if is_ignorable_line(line):
            continue

        if should_ignore_deck_title(lines, index, saw_content):
            continue

        lowered, is_generic_header = normalize_section_header(line)
        if lowered in SECTION_HEADERS or is_generic_header:
            if lowered in SIDEBOARD_MARKERS or lowered in COMPANION_MARKERS:
                current_section = "sideboard"
            elif lowered in COMMANDER_MARKERS:
                current_section = "commander"
            elif lowered in MAYBEBOARD_MARKERS:
                current_section = "ignore"
            else:
                current_section = "mainboard"
            saw_content = True
            continue

        if (
            lowered.startswith("sb:")
            or lowered.startswith("sideboard:")
            or lowered.startswith("companion:")
            or lowered.startswith("companions:")
        ):
            card_line = line.split(":", 1)[1].strip()
            parsed = parse_card_line(card_line)
            if parsed:
                sideboard.append(parsed)
            current_section = "sideboard"
            saw_content = True
            continue

        if lowered.startswith("commander:") or lowered.startswith("commanders:"):
            card_line = line.split(":", 1)[1].strip()
            parsed = parse_card_line(card_line)
            if parsed:
                commanders.append(parsed)
            current_section = "commander"
            saw_content = True
            continue

        if lowered.startswith("maybeboard:"):
            continue

        parsed = parse_card_line(line)
        if not parsed:
            continue

        if current_section == "sideboard":
            sideboard.append(parsed)
        elif current_section == "commander":
            commanders.append(parsed)
        elif current_section == "ignore":
            continue
        else:
            mainboard.append(parsed)
        saw_content = True

    return mainboard, sideboard, commanders


def parse_deck_sections(decklist: str) -> tuple[list[dict], list[dict]]:
    mainboard, sideboard, _ = parse_deck_input(decklist)
    return mainboard, sideboard


def parse_decklist(decklist: str) -> list[dict]:
    mainboard, _, _ = parse_deck_input(decklist)
    return mainboard

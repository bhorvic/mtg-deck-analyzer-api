const LINE_PATTERN = /^(?:(\d[\d,]*)(?:\s*[xX×:\-–—]\s*|\s+))?(.+?)\s*$/;
const TRAILING_SET_INFO_PATTERN = /\s+\([A-Za-z0-9]{2,6}\)\s+\d+[a-zA-Z]?$/;
const TRAILING_SET_ONLY_PATTERN = /\s+\([A-Za-z0-9]{2,6}\)$/;
const TRAILING_BRACKET_SET_PATTERN = /\s+\[[A-Za-z0-9]{2,8}\]$/;
const TRAILING_CURLY_SET_PATTERN = /\s+\{[A-Za-z0-9]{2,8}\}$/;
const INVALID_QUANTITY_PREFIX_PATTERN = /^(?:[xX]|[+-]\d|\d+\.\d+)\S*\s+/;
const SECTION_HEADER_WITH_COUNT_PATTERN = /^([A-Za-z][A-Za-z\s]+?)\s*\(\d+\)\s*$/;
const GENERIC_SECTION_HEADER_PATTERN = /^([A-Za-z][A-Za-z0-9 '&/+-]{0,80})\s*:\s*$/;
const LEADING_BULLET_PATTERN = /^[\-•–—]\s+/;
const LEADING_CHECKBOX_PATTERN = /^(?:[\-*•–—]\s+)?\[[ xX]\]\s+/;
const TRAILING_ASTERISK_TAG_PATTERN = /\s+\*(?:f|foil|cmdr|commander|maybe|maybeboard|sb|sideboard|mb|mainboard|promo)\*$/i;
const TRAILING_METADATA_LABEL_PATTERN = /\s+(?:\(|\[|\{)(?:foil|etched|showcase|borderless|retro\s+frame|extended\s+art|promo|commander|companion|maybeboard|sideboard|mainboard)(?:\)|\]|\})$/i;
const SECTION_HEADERS = new Set([
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
]);
const SIDEBOARD_MARKERS = new Set(["sideboard", "sb", "side"]);
const COMMANDER_MARKERS = new Set(["commander", "commanders"]);
const COMPANION_MARKERS = new Set(["companion", "companions"]);
const MAYBEBOARD_MARKERS = new Set(["maybeboard"]);

function stripInlineComment(line) {
  const hashIndex = line.indexOf(" #");
  if (hashIndex !== -1) {
    line = line.slice(0, hashIndex);
  }

  const slashIndex = line.indexOf(" // ");
  if (slashIndex !== -1) {
    const remainder = line.slice(slashIndex + 4).trim();
    if (remainder && remainder[0] === remainder[0].toLowerCase()) {
      line = line.slice(0, slashIndex);
    }
  }

  return line.trim();
}

function normalizeCardName(name) {
  let normalized = stripInlineComment(name.trim())
    .replace(LEADING_CHECKBOX_PATTERN, "")
    .replace(LEADING_BULLET_PATTERN, "")
    .trim();

  let previous = null;
  while (previous !== normalized) {
    previous = normalized;
    normalized = normalized
      .replace(TRAILING_SET_INFO_PATTERN, "")
      .replace(TRAILING_SET_ONLY_PATTERN, "")
      .replace(TRAILING_BRACKET_SET_PATTERN, "")
      .replace(TRAILING_CURLY_SET_PATTERN, "")
      .replace(TRAILING_ASTERISK_TAG_PATTERN, "")
      .replace(TRAILING_METADATA_LABEL_PATTERN, "")
      .trim();
  }

  return normalized;
}

export function parseCardLine(line) {
  const trimmed = line.trim().replace(LEADING_CHECKBOX_PATTERN, "").replace(LEADING_BULLET_PATTERN, "");
  if (!trimmed || INVALID_QUANTITY_PREFIX_PATTERN.test(trimmed)) {
    return null;
  }

  const match = trimmed.match(LINE_PATTERN);
  if (!match) {
    return null;
  }

  const quantityText = match[1];
  const quantity = quantityText ? Number.parseInt(quantityText.replaceAll(",", ""), 10) : 1;
  if (!Number.isFinite(quantity) || quantity <= 0) {
    return null;
  }

  const name = normalizeCardName(match[2] || "");
  if (!name) {
    return null;
  }

  return { quantity, name };
}

function isIgnorableDeckLine(line) {
  const stripped = line.trim();
  if (!stripped) return true;
  if (["---", "***", "___"].includes(stripped)) return true;
  if (LEADING_CHECKBOX_PATTERN.test(stripped)) return false;
  return stripped.startsWith("//") || stripped.startsWith("#") || stripped.startsWith("*");
}

function normalizeSectionHeader(line) {
  const lowered = line.toLowerCase().replace(/:+$/, "").trim();
  const match = lowered.match(SECTION_HEADER_WITH_COUNT_PATTERN);
  if (match) {
    return { header: (match[1] || "").trim(), isGenericHeader: true };
  }

  const genericMatch = line.trim().match(GENERIC_SECTION_HEADER_PATTERN);
  if (genericMatch) {
    return { header: (genericMatch[1] || "").trim().toLowerCase(), isGenericHeader: true };
  }

  return { header: lowered, isGenericHeader: false };
}

function lineHasExplicitQuantity(line) {
  const match = line.trim().match(LINE_PATTERN);
  return Boolean(match && match[1]);
}

function shouldIgnoreDeckTitle(lines, index, sawContent) {
  if (sawContent || index !== 0) return false;

  const line = (lines[index] || "").trim();
  if (!line || line.includes(":") || lineHasExplicitQuantity(line)) return false;

  const current = normalizeSectionHeader(line);
  if (current.isGenericHeader || SECTION_HEADERS.has(current.header)) return false;

  for (let i = index + 1; i < lines.length; i += 1) {
    const candidate = (lines[i] || "").trim();
    if (isIgnorableDeckLine(candidate)) continue;
    const future = normalizeSectionHeader(candidate);
    return future.isGenericHeader || SECTION_HEADERS.has(future.header);
  }

  return false;
}

export function parseDeckInputClientDetailed(decklist = "") {
  const details = {
    counts: { mainboard: 0, sideboard: 0, commanders: 0 },
    mainboard: [],
    sideboard: [],
    commanders: [],
    ignored: [],
  };
  let currentSection = "mainboard";
  let sawContent = false;

  const lines = decklist.split(/\r?\n/);

  const recordEntry = (section, parsed, source) => {
    details[section].push({ ...parsed, source });
    details.counts[section] += parsed.quantity;
  };

  lines.forEach((rawLine, index) => {
    const line = rawLine.trim();
    if (isIgnorableDeckLine(line)) return;

    if (shouldIgnoreDeckTitle(lines, index, sawContent)) {
      details.ignored.push({ line, reason: "deck-title" });
      return;
    }

    const { header: lowered, isGenericHeader } = normalizeSectionHeader(line);
    if (SECTION_HEADERS.has(lowered) || isGenericHeader) {
      if (SIDEBOARD_MARKERS.has(lowered) || COMPANION_MARKERS.has(lowered)) {
        currentSection = "sideboard";
      } else if (COMMANDER_MARKERS.has(lowered)) {
        currentSection = "commander";
      } else if (MAYBEBOARD_MARKERS.has(lowered)) {
        currentSection = "ignore";
      } else {
        currentSection = "mainboard";
      }
      sawContent = true;
      return;
    }

    if (["sb:", "sideboard:", "companion:", "companions:"].some((prefix) => lowered.startsWith(prefix))) {
      const parsed = parseCardLine(line.split(":", 2)[1] || "");
      if (parsed) recordEntry("sideboard", parsed, line);
      currentSection = "sideboard";
      sawContent = true;
      return;
    }

    if (["commander:", "commanders:"].some((prefix) => lowered.startsWith(prefix))) {
      const parsed = parseCardLine(line.split(":", 2)[1] || "");
      if (parsed) recordEntry("commanders", parsed, line);
      currentSection = "commander";
      sawContent = true;
      return;
    }

    if (lowered.startsWith("maybeboard:")) {
      details.ignored.push({ line, reason: "inline-maybeboard" });
      return;
    }

    const parsed = parseCardLine(line);
    if (!parsed) return;

    if (currentSection === "ignore") {
      details.ignored.push({ line, reason: "ignored-section" });
      return;
    }

    recordEntry(currentSection, parsed, line);
    sawContent = true;
  });

  return details;
}

export function parseDeckInputClient(decklist = "") {
  return parseDeckInputClientDetailed(decklist).counts;
}

export function parseCommanderFieldCount(text = "") {
  if (!text.trim()) return 0;

  return text
    .replace(/\s+\/\/\s+/g, "\n")
    .replace(/\s+\/\s+/g, "\n")
    .replace(/;/g, "\n")
    .split(/\n+/)
    .map((part) => part.trim())
    .filter(Boolean).length;
}

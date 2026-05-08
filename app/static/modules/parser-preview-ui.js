import {
  formatEl,
  commanderFieldGroupEl,
  commanderValidationSectionEl,
  commanderFieldMetaEl,
  decklistMetaEl,
  sideboardMetaEl,
  parserPreviewCountEl,
  parserPreviewSummaryEl,
  parserPreviewStatusEl,
  parserPreviewOutputEl,
  formFields,
} from "./dom.js";
import {
  parseCardLine,
  parseDeckInputClientDetailed,
  parseCommanderFieldCount,
} from "./parser.js";

export function setFieldMeta(element, message, tone = "muted") {
  if (!element) return;
  element.textContent = message;
  element.dataset.tone = tone;
}

export function refreshDeckInputMeta() {
  const mainDetails = parseDeckInputClientDetailed(formFields.decklist.value || "");
  const sideDetails = parseDeckInputClientDetailed(formFields.sideboard.value || "");
  const mainCounts = mainDetails.counts;
  const sideCounts = sideDetails.counts;
  const commanderFieldCount = parseCommanderFieldCount(formFields.commander.value || "");
  const isCommander = formatEl.value === "commander";
  const formatName = formatEl.value;
  const sideboardBoxCount = sideCounts.mainboard + sideCounts.sideboard;

  const deckBits = [`Approx: ${mainCounts.mainboard} main-deck cards in pasted text.`];
  if (mainCounts.commanders) {
    deckBits.push(`${mainCounts.commanders} commander card${mainCounts.commanders === 1 ? "" : "s"} detected in the pasted decklist.`);
  }
  if (mainCounts.sideboard) {
    deckBits.push(`${mainCounts.sideboard} sideboard card${mainCounts.sideboard === 1 ? "" : "s"} embedded in the pasted decklist.`);
  }

  let deckTone = "muted";
  if (isCommander) {
    const commanderSourceCount = commanderFieldCount || mainCounts.commanders;
    const expectedMainboard = commanderSourceCount > 0 ? Math.max(0, 100 - commanderSourceCount) : 100;

    if (mainCounts.mainboard === 0) {
      deckBits.push("Commander decks usually want 99 main-deck cards plus commander(s).");
    } else if (mainCounts.mainboard === expectedMainboard) {
      deckBits.push(`That lines up with ${expectedMainboard} expected main-deck cards for Commander.`);
      deckTone = "success";
    } else {
      deckBits.push(`Commander usually expects ${expectedMainboard} main-deck cards here based on the commander count.`);
      deckTone = "warning";
    }
  } else if (mainCounts.mainboard === 0) {
    deckBits.push(`${formatName.charAt(0).toUpperCase() + formatName.slice(1)} decks usually want at least 60 main-deck cards.`);
  } else if (mainCounts.mainboard >= 60) {
    deckBits.push(`${formatName.charAt(0).toUpperCase() + formatName.slice(1)} minimum looks covered.`);
    deckTone = "success";
  } else {
    deckBits.push(`${formatName.charAt(0).toUpperCase() + formatName.slice(1)} decks usually want at least 60 main-deck cards.`);
    deckTone = "warning";
  }
  setFieldMeta(decklistMetaEl, deckBits.join(" "), deckTone);

  let sideboardTone = "muted";
  const sideboardBits = [`Approx: ${sideboardBoxCount} sideboard card${sideboardBoxCount === 1 ? "" : "s"} in this box.`];
  if (isCommander) {
    if (sideboardBoxCount > 0 || mainCounts.sideboard > 0) {
      sideboardBits.push("Commander sideboards are only treated as warnings right now.");
      sideboardTone = "warning";
    }
  } else if (sideboardBoxCount > 15) {
    sideboardBits.push("Most supported formats cap sideboards at 15 cards.");
    sideboardTone = "warning";
  } else if (sideboardBoxCount > 0) {
    sideboardBits.push("Sideboard size looks reasonable.");
    sideboardTone = "success";
  }
  setFieldMeta(sideboardMetaEl, sideboardBits.join(" "), sideboardTone);

  if (!isCommander) {
    setFieldMeta(commanderFieldMetaEl, "Commander input is ignored outside Commander format.", "muted");
    return;
  }

  if (commanderFieldCount) {
    const tone = commanderFieldCount <= 2 ? "success" : "warning";
    const suffix = commanderFieldCount <= 2 ? "" : " Only up to two commanders are supported right now.";
    setFieldMeta(commanderFieldMetaEl, `Using the commander field for ${commanderFieldCount} commander${commanderFieldCount === 1 ? "" : "s"}.${suffix}`, tone);
    return;
  }

  if (mainCounts.commanders) {
    const tone = mainCounts.commanders <= 2 ? "warning" : "danger";
    const suffix = mainCounts.commanders <= 2 ? "" : " That is more than the UI currently supports.";
    setFieldMeta(commanderFieldMetaEl, `No commander typed here — ${mainCounts.commanders} commander card${mainCounts.commanders === 1 ? "" : "s"} detected in the pasted decklist instead.${suffix}`, tone);
    return;
  }

  setFieldMeta(commanderFieldMetaEl, "No commander entered yet.", "warning");
}

export function formatPreviewSection(title, entries) {
  if (!entries.length) return `${title}:\n(none)`;
  return `${title}:\n${entries.map((entry) => `${entry.quantity} ${entry.name}`).join("\n")}`;
}

export function buildParserPreviewText() {
  const mainDetails = parseDeckInputClientDetailed(formFields.decklist.value || "");
  const sideDetails = parseDeckInputClientDetailed(formFields.sideboard.value || "");
  const commanderFieldRaw = formFields.commander.value || "";
  const commanderFieldEntries = commanderFieldRaw
    .replace(/\s+\/\/\s+/g, "\n")
    .replace(/\s+\/\s+/g, "\n")
    .replace(/;/g, "\n")
    .split(/\n+/)
    .map((entry) => parseCardLine(entry.trim()))
    .filter(Boolean);

  const previewSections = [
    formatPreviewSection("Commander field", commanderFieldEntries),
    formatPreviewSection("Detected commanders in pasted main deck", mainDetails.commanders),
    formatPreviewSection("Normalized main deck", mainDetails.mainboard),
    formatPreviewSection("Embedded sideboard inside main-deck box", mainDetails.sideboard),
    formatPreviewSection("Normalized sideboard box", [...sideDetails.mainboard, ...sideDetails.sideboard]),
  ];

  const ignoredLines = [...mainDetails.ignored, ...sideDetails.ignored];
  if (ignoredLines.length) {
    previewSections.push(`Ignored lines:\n${ignoredLines.map((entry) => `- ${entry.line} (${entry.reason})`).join("\n")}`);
  }

  return previewSections.join("\n\n");
}

export function refreshParserPreview() {
  if (!parserPreviewOutputEl) return;

  const mainDetails = parseDeckInputClientDetailed(formFields.decklist.value || "");
  const sideDetails = parseDeckInputClientDetailed(formFields.sideboard.value || "");
  const commanderFieldCount = parseCommanderFieldCount(formFields.commander.value || "");
  const totalVisibleCards = mainDetails.counts.mainboard
    + mainDetails.counts.sideboard
    + mainDetails.counts.commanders
    + sideDetails.counts.mainboard
    + sideDetails.counts.sideboard
    + sideDetails.counts.commanders
    + commanderFieldCount;
  const ignoredCount = mainDetails.ignored.length + sideDetails.ignored.length;

  parserPreviewCountEl.textContent = `${totalVisibleCards} card${totalVisibleCards === 1 ? "" : "s"}`;
  parserPreviewSummaryEl.textContent = `Previewing normalized commander/main/sideboard sections before submit.${ignoredCount ? ` ${ignoredCount} line${ignoredCount === 1 ? "" : "s"} ignored as helper noise.` : ""}`;
  parserPreviewStatusEl.textContent = "Updates as you type. Mirrors the browser-side pre-submit parsing.";
  parserPreviewOutputEl.textContent = buildParserPreviewText();
}

export function syncCommanderVisibility() {
  const isCommander = formatEl.value === "commander";
  commanderFieldGroupEl.classList.toggle("hidden", !isCommander);
  commanderValidationSectionEl?.classList.toggle("hidden", !isCommander);
  refreshDeckInputMeta();
  refreshParserPreview();
}

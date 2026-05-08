import {
  parseCardLine,
  parseDeckInputClientDetailed,
  parseCommanderFieldCount,
} from "./parser.js";

export function normalizeFormState(state = {}) {
  return {
    name: state.name || "",
    format: state.format || "commander",
    commander: state.commander || "",
    decklist: state.decklist || "",
    sideboard: state.sideboard || "",
  };
}

export function getDeckInputMetaModel(rawState = {}) {
  const state = normalizeFormState(rawState);
  const mainDetails = parseDeckInputClientDetailed(state.decklist);
  const sideDetails = parseDeckInputClientDetailed(state.sideboard);
  const mainCounts = mainDetails.counts;
  const sideCounts = sideDetails.counts;
  const commanderFieldCount = parseCommanderFieldCount(state.commander);
  const isCommander = state.format === "commander";
  const formatName = state.format;
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

  let commanderMessage = "No commander entered yet.";
  let commanderTone = "warning";
  if (!isCommander) {
    commanderMessage = "Commander input is ignored outside Commander format.";
    commanderTone = "muted";
  } else if (commanderFieldCount) {
    commanderTone = commanderFieldCount <= 2 ? "success" : "warning";
    const suffix = commanderFieldCount <= 2 ? "" : " Only up to two commanders are supported right now.";
    commanderMessage = `Using the commander field for ${commanderFieldCount} commander${commanderFieldCount === 1 ? "" : "s"}.${suffix}`;
  } else if (mainCounts.commanders) {
    commanderTone = mainCounts.commanders <= 2 ? "warning" : "danger";
    const suffix = mainCounts.commanders <= 2 ? "" : " That is more than the UI currently supports.";
    commanderMessage = `No commander typed here — ${mainCounts.commanders} commander card${mainCounts.commanders === 1 ? "" : "s"} detected in the pasted decklist instead.${suffix}`;
  }

  return {
    isCommander,
    decklist: { message: deckBits.join(" "), tone: deckTone },
    sideboard: { message: sideboardBits.join(" "), tone: sideboardTone },
    commander: { message: commanderMessage, tone: commanderTone },
  };
}

export function formatPreviewSection(title, entries) {
  if (!entries.length) return `${title}:\n(none)`;
  return `${title}:\n${entries.map((entry) => `${entry.quantity} ${entry.name}`).join("\n")}`;
}

export function buildParserPreviewText(rawState = {}) {
  const state = normalizeFormState(rawState);
  const mainDetails = parseDeckInputClientDetailed(state.decklist);
  const sideDetails = parseDeckInputClientDetailed(state.sideboard);
  const commanderFieldEntries = state.commander
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

export function getParserPreviewModel(rawState = {}) {
  const state = normalizeFormState(rawState);
  const mainDetails = parseDeckInputClientDetailed(state.decklist);
  const sideDetails = parseDeckInputClientDetailed(state.sideboard);
  const commanderFieldCount = parseCommanderFieldCount(state.commander);
  const totalVisibleCards = mainDetails.counts.mainboard
    + mainDetails.counts.sideboard
    + mainDetails.counts.commanders
    + sideDetails.counts.mainboard
    + sideDetails.counts.sideboard
    + sideDetails.counts.commanders
    + commanderFieldCount;
  const ignoredCount = mainDetails.ignored.length + sideDetails.ignored.length;

  return {
    countLabel: `${totalVisibleCards} card${totalVisibleCards === 1 ? "" : "s"}`,
    summary: `Previewing normalized commander/main/sideboard sections before submit.${ignoredCount ? ` ${ignoredCount} line${ignoredCount === 1 ? "" : "s"} ignored as helper noise.` : ""}`,
    status: "Updates as you type. Mirrors the browser-side pre-submit parsing.",
    output: buildParserPreviewText(state),
  };
}

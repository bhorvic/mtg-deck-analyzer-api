import {
  emptyStateEl,
  resultsEl,
} from "./dom.js";
import { appState } from "./state.js";
import {
  updateSectionEmphasis,
  renderKeyValueList,
  renderBarChart,
} from "./renderers.js";
import { updateResultsSummary } from "./results-summary-ui.js";

export function resetForSubmit(setStatus, setSubmitting = null) {
  appState.ui.highlightedSupportCards = [];
  appState.ui.selectedArchetypeName = "";
  setSubmitting?.(true);
  setStatus("Talking to Scryfall and crunching the deck…", "working");
}

export function finishSubmit(setSubmitting = null) {
  setSubmitting?.(false);
}

export function buildAnalysisPayload(formState) {
  return {
    name: formState.name,
    format: formState.format,
    commander: formState.format === "commander" ? (formState.commander || null) : null,
    decklist: formState.decklist,
    sideboard: formState.sideboard || null,
  };
}

export async function runDeckAnalysis({
  payload,
  setStatus,
  setDraftStatus,
  showToast,
  rerenderCardLists,
  renderArchetypeGuesses,
  updateResultsNavigator,
} = {}) {
  const response = await fetch("/deck/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const data = await response.json();
  appState.analysis = data;
  appState.cards.mainboard = data.parsed_cards || [];
  appState.cards.sideboard = data.parsed_sideboard || [];

  updateResultsSummary(data);
  updateResultsNavigator(data);
  updateSectionEmphasis(data);
  renderKeyValueList("mana-curve", data.mana_curve);
  renderKeyValueList("type-breakdown", data.type_breakdown);
  renderKeyValueList("classification-counts", data.classification_counts);
  renderBarChart("mana-curve-chart", data.mana_curve, "No mana curve data yet.");
  renderBarChart("type-breakdown-chart", data.type_breakdown, "No type breakdown data yet.");
  renderArchetypeGuesses(data.archetype_guesses, data.primary_archetype);

  rerenderCardLists();

  emptyStateEl?.classList.add("hidden");
  resultsEl?.classList.remove("hidden");
  setStatus(
    `Done. Found ${data.warnings?.length || 0} warning${data.warnings?.length === 1 ? "" : "s"}.`,
    data.warnings?.length ? "warning" : "success",
  );
  setDraftStatus("Draft saved locally and analysis is ready.", "success");
  showToast(`Analysis ready${data.primary_archetype ? `: ${data.primary_archetype}` : ""}.`, data.warnings?.length ? "warning" : "success");

  return data;
}

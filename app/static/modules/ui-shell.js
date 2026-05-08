import {
  statusEl,
  draftStatusEl,
  toastRegionEl,
  resultsNavRootEl,
} from "./dom.js";
import { appState, CARD_DENSITY_STORAGE_KEY } from "./state.js";
import { formatCountLabel } from "./renderers.js";
import { initResultsNavigator } from "../react/results-nav.js";

let statusWriter = (message, tone = "muted") => {
  if (!statusEl) return;
  statusEl.textContent = message;
  statusEl.dataset.tone = tone;
};

export function registerStatusWriter(writer) {
  statusWriter = writer || statusWriter;
}

export function setStatus(message, tone = "muted") {
  statusWriter(message, tone);
}

export function setDraftStatus(message, tone = "muted") {
  if (!draftStatusEl) return;
  draftStatusEl.textContent = message;
  draftStatusEl.dataset.tone = tone;
}

export function showToast(message, tone = "success") {
  if (!toastRegionEl || !message) return;

  const toast = document.createElement("div");
  toast.className = `toast ${tone}`;
  toast.textContent = message;
  toastRegionEl.appendChild(toast);

  window.requestAnimationFrame(() => {
    toast.classList.add("visible");
  });

  window.setTimeout(() => {
    toast.classList.remove("visible");
    window.setTimeout(() => toast.remove(), 220);
  }, 2200);
}

export function scrollToSection(targetId) {
  const target = document.getElementById(targetId);
  if (!target) return;
  target.scrollIntoView({ behavior: "smooth", block: "start" });
}

const resultsNavRenderer = resultsNavRootEl
  ? initResultsNavigator("results-nav-root", { onNavigate: scrollToSection })
  : null;

function buildResultsNavigatorModel(data = null) {
  if (!data) {
    return {
      statusLabel: "Waiting",
      statusTone: "neutral",
      counts: {
        overview: "-",
        visuals: "-",
        archetype: "-",
        feedback: "-",
        mainboard: "-",
        sideboard: "-",
      },
    };
  }

  const warningCount = data.warnings?.length || 0;
  const recommendationCount = data.recommendations?.length || 0;

  return {
    statusLabel: warningCount ? `${warningCount} warning${warningCount === 1 ? "" : "s"}` : "Ready",
    statusTone: warningCount ? "warning" : "success",
    counts: {
      overview: `${warningCount + recommendationCount} notes`,
      visuals: `${Object.keys(data.mana_curve || {}).length + Object.keys(data.type_breakdown || {}).length} stats`,
      archetype: data.primary_archetype || "Unknown",
      feedback: `${warningCount} / ${recommendationCount}`,
      mainboard: formatCountLabel(data.mainboard_count || 0, "card"),
      sideboard: formatCountLabel(data.sideboard_count || 0, "card"),
    },
  };
}

export function updateResultsNavigator(data = null) {
  resultsNavRenderer?.render(buildResultsNavigatorModel(data));
}

export function syncCardDensityUI() {}

export function toggleCardDensity(setStatusCallback = setStatus) {
  appState.ui.compactCardView = !appState.ui.compactCardView;
  window.localStorage.setItem(CARD_DENSITY_STORAGE_KEY, appState.ui.compactCardView ? "compact" : "expanded");
  syncCardDensityUI();
  setStatusCallback(`Switched to ${appState.ui.compactCardView ? "compact" : "expanded"} card view.`, "success");
}

export function setAllSectionsExpanded(open) {
  document.querySelectorAll("details.collapsible").forEach((section) => {
    section.open = open;
  });
}

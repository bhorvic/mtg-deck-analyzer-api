import {
  sampleDeckEl,
  loadSampleButtonEl,
  clearFormButtonEl,
  copyShareLinkButtonEl,
  restoreDraftButtonEl,
  clearDraftButtonEl,
} from "./modules/dom.js";
import {
  SAMPLE_DECKS,
  appState,
  DRAFT_STORAGE_KEY,
} from "./modules/state.js";
import { buildSummaryText } from "./modules/renderers.js";
import {
  resetForSubmit,
  finishSubmit,
  buildAnalysisPayload,
  runDeckAnalysis,
} from "./modules/analysis-controller.js";
import {
  getFormState,
  updateUrlFromState,
  persistDraftState,
  readDraftState,
  clearDraft,
  hydrateStateFromUrl,
} from "./modules/form-state.js";
import { copyToClipboard } from "./modules/clipboard.js";
import {
  setStatus,
  setDraftStatus,
  showToast,
  updateResultsNavigator,
  syncCardDensityUI,
  toggleCardDensity,
  setAllSectionsExpanded,
  registerStatusWriter,
} from "./modules/ui-shell.js";
import {
  selectArchetype as selectArchetypeView,
  setHighlightedSupportCards as setHighlightedSupportCardsView,
  renderArchetypeGuesses as renderArchetypeGuessesView,
} from "./modules/archetype-ui.js";
import {
  registerCardSurfaceCallbacks,
  renderCardSurface,
} from "./modules/card-surface-ui.js";
import { initDeckForm } from "./react/deck-form.js";

const DEFAULT_FORM_STATE = {
  name: "Test Deck",
  format: "commander",
  commander: "Baral, Chief of Compliance",
  decklist: `1 Sol Ring
1 Arcane Signet
1 Command Tower
1 Counterspell
1 Divination
95 Island`,
  sideboard: "",
};

let urlSyncTimer = null;
let draftSyncTimer = null;

function rerenderCardLists() {
  renderCardSurface();
}

function getArchetypeCallbacks() {
  return {
    setStatus,
    showToast,
    rerenderCardLists,
    selectArchetype,
    setHighlightedSupportCards,
    renderArchetypeGuesses,
  };
}

function selectArchetype(guess) {
  selectArchetypeView(guess, getArchetypeCallbacks());
}

function setHighlightedSupportCards(cardNames = [], label = "") {
  setHighlightedSupportCardsView(cardNames, label, getArchetypeCallbacks());
}

function renderArchetypeGuesses(guesses, primaryArchetype) {
  renderArchetypeGuessesView(guesses, primaryArchetype, getArchetypeCallbacks());
}

function scheduleUrlSync(state) {
  window.clearTimeout(urlSyncTimer);
  urlSyncTimer = window.setTimeout(() => {
    updateUrlFromState(state);
  }, 180);
}

function scheduleDraftSync(state) {
  window.clearTimeout(draftSyncTimer);
  draftSyncTimer = window.setTimeout(() => {
    persistDraftState(DRAFT_STORAGE_KEY, state, setDraftStatus);
  }, 320);
}

const initialState = hydrateStateFromUrl(DEFAULT_FORM_STATE) || getFormState(DEFAULT_FORM_STATE);
const deckForm = initDeckForm("deck-form-root", {
  initialState,
  onStateChange(state) {
    scheduleUrlSync(state);
    scheduleDraftSync(state);
  },
  async onSubmit(state) {
    updateUrlFromState(state);
    persistDraftState(DRAFT_STORAGE_KEY, state, setDraftStatus);
    resetForSubmit(setStatus, deckForm.setSubmitting);

    try {
      await runDeckAnalysis({
        payload: buildAnalysisPayload(state),
        setStatus,
        setDraftStatus,
        showToast,
        rerenderCardLists,
        renderArchetypeGuesses,
        updateResultsNavigator,
      });
    } catch (error) {
      console.error(error);
      updateResultsNavigator(appState.analysis);
      setStatus("Something went wrong. Check the API response or browser console.", "error");
      showToast("Analysis failed. Check the warning text or console.", "error");
    } finally {
      finishSubmit(deckForm.setSubmitting);
    }
  },
  async onCopyPreview(text) {
    await copyToClipboard(
      text,
      "Normalized parser preview copied to clipboard.",
      "Couldn't copy the parser preview automatically.",
      setStatus,
      showToast,
    );
  },
});

registerStatusWriter((message, tone) => deckForm.setStatus(message, tone));

if (hydrateStateFromUrl(DEFAULT_FORM_STATE)) {
  setStatus("Loaded deck state from the URL.", "success");
} else if (window.localStorage.getItem(DRAFT_STORAGE_KEY)) {
  setDraftStatus("Local draft available if you want to restore it.", "warning");
}

function applySampleDeck(sample) {
  deckForm.setState(sample);
  setStatus(`Loaded preset: ${sample.name}`, "success");
  showToast(`Loaded preset: ${sample.name}`, "success");
}

function clearFormState() {
  deckForm.setState({ name: "", format: "commander", commander: "", decklist: "", sideboard: "" });
  sampleDeckEl.value = "";
  appState.ui.cardFilter = "";
  renderCardSurface();
  setStatus("Form cleared.", "muted");
  showToast("Form cleared.", "success");
}

async function copyShareLink() {
  updateUrlFromState(deckForm.getState());
  await copyToClipboard(
    window.location.href,
    "Share link copied to clipboard.",
    "Couldn't copy the share link automatically. Copy the URL from your browser instead.",
    setStatus,
    showToast,
  );
}

function restoreDraftFromStorage() {
  const draft = readDraftState(DRAFT_STORAGE_KEY);
  if (!draft) {
    setDraftStatus("No local draft saved yet.", "warning");
    showToast("No saved draft to restore yet.", "warning");
    return;
  }

  deckForm.setState(draft);
  updateUrlFromState(draft);
  setDraftStatus(`Restored local draft from ${new Date(draft.savedAt).toLocaleString()}.`, "success");
  showToast("Draft restored.", "success");
}

function clearDraftFromStorage() {
  clearDraft(DRAFT_STORAGE_KEY, setDraftStatus, showToast);
}

registerCardSurfaceCallbacks({
  copySummary: async () => {
    if (!appState.analysis) {
      setStatus("Run an analysis first so there is something to copy.", "warning");
      return;
    }
    await copyToClipboard(
      buildSummaryText(appState.analysis),
      "Analysis summary copied to clipboard.",
      "Couldn't copy the summary automatically.",
      setStatus,
      showToast,
    );
  },
  copyJson: async () => {
    if (!appState.analysis) {
      setStatus("Run an analysis first so there is something to copy.", "warning");
      return;
    }
    await copyToClipboard(
      JSON.stringify(appState.analysis, null, 2),
      "Analysis JSON copied to clipboard.",
      "Couldn't copy the JSON automatically.",
      setStatus,
      showToast,
    );
  },
  toggleDensity: () => toggleCardDensity(setStatus),
  expandAll: () => setAllSectionsExpanded(true),
  collapseAll: () => setAllSectionsExpanded(false),
});

loadSampleButtonEl.addEventListener("click", () => {
  const selectedSample = SAMPLE_DECKS[sampleDeckEl.value];
  if (!selectedSample) {
    setStatus("Pick a preset first.", "warning");
    return;
  }
  applySampleDeck(selectedSample);
});
clearFormButtonEl.addEventListener("click", clearFormState);
copyShareLinkButtonEl.addEventListener("click", copyShareLink);
restoreDraftButtonEl.addEventListener("click", restoreDraftFromStorage);
clearDraftButtonEl.addEventListener("click", clearDraftFromStorage);
updateResultsNavigator();
syncCardDensityUI();
renderCardSurface();

import { appState } from "./state.js";
import { initArchetypePanel } from "../react/archetype-panel.js";
import { archetypePanelRootEl } from "./dom.js";

let callbacksRef = {
  setStatus() {},
  showToast() {},
  rerenderCardLists() {},
};

const archetypePanel = archetypePanelRootEl
  ? initArchetypePanel("archetype-panel-root", {
    onSelectArchetype(guess) {
      selectArchetype(guess, callbacksRef);
    },
    onHighlightSupportCards(guess) {
      appState.ui.selectedArchetypeName = guess.name || "";
      setHighlightedSupportCards(guess.support_cards || [], guess.name, callbacksRef);
      renderArchetypeGuesses(appState.analysis?.archetype_guesses || [], appState.analysis?.primary_archetype || null, callbacksRef);
      callbacksRef.showToast(`Highlighting ${guess.name} support cards.`, "success");
    },
    onClearHighlight() {
      setHighlightedSupportCards([], "", callbacksRef);
      renderArchetypeGuesses(appState.analysis?.archetype_guesses || [], appState.analysis?.primary_archetype || null, callbacksRef);
    },
    onPrimaryPillClick(guessName) {
      if (!guessName || !appState.analysis?.archetype_guesses?.length) return;
      const primaryGuess = appState.analysis.archetype_guesses.find((guess) => guess.name === guessName) || appState.analysis.archetype_guesses[0];
      if (!primaryGuess?.support_cards?.length) {
        callbacksRef.setStatus("This archetype guess doesn't have signature card highlighting yet.", "warning");
        return;
      }
      selectArchetype(primaryGuess, callbacksRef);
      callbacksRef.showToast(`Highlighting ${primaryGuess.name} support cards.`, "success");
    },
  })
  : { render() {} };

export function selectArchetype(guess, callbacks) {
  if (!guess) return;
  callbacksRef = callbacks || callbacksRef;
  appState.ui.selectedArchetypeName = guess.name || "";
  setHighlightedSupportCards(guess.support_cards || [], guess.name, callbacksRef);
  renderArchetypeGuesses(appState.analysis?.archetype_guesses || [], appState.analysis?.primary_archetype || null, callbacksRef);
}

export function setHighlightedSupportCards(cardNames = [], label = "", callbacks) {
  callbacksRef = callbacks || callbacksRef;
  appState.ui.highlightedSupportCards = [...new Set(cardNames.filter(Boolean))];
  callbacksRef.rerenderCardLists();

  if (!appState.ui.highlightedSupportCards.length) {
    callbacksRef.setStatus("Cleared archetype card highlight.", "muted");
    return;
  }

  callbacksRef.setStatus(
    `Highlighting ${appState.ui.highlightedSupportCards.length} support card${appState.ui.highlightedSupportCards.length === 1 ? "" : "s"} for ${label || "the selected archetype"}.`,
    "success",
  );
}

export function renderArchetypeGuesses(guesses, primaryArchetype, callbacks) {
  callbacksRef = callbacks || callbacksRef;

  if (!guesses?.length) {
    appState.ui.highlightedSupportCards = [];
    appState.ui.selectedArchetypeName = "";
  }

  archetypePanel.render(guesses || [], primaryArchetype || null);
}

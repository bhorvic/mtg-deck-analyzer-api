import { appState } from "./state.js";

export function buildArchetypePanelModel(guesses = [], primaryArchetype = null) {
  if (!guesses?.length) {
    return {
      hasGuesses: false,
      helperText: "Run an analysis to see likely archetype matches.",
      primaryPill: {
        label: primaryArchetype || "Unknown",
        disabled: true,
        clickable: false,
        active: false,
      },
      guesses: [],
    };
  }

  const primaryGuess = guesses.find((guess) => guess.name === primaryArchetype) || guesses[0];
  const selectedName = appState.ui.selectedArchetypeName && guesses.some((guess) => guess.name === appState.ui.selectedArchetypeName)
    ? appState.ui.selectedArchetypeName
    : primaryGuess.name;

  appState.ui.selectedArchetypeName = selectedName;

  return {
    hasGuesses: true,
    helperText: primaryGuess.support_cards?.length
      ? "Click the archetype pill or any support card below to highlight matching cards in the deck list."
      : "This read is heuristic for now — support-card highlighting appears when signature cards are available.",
    primaryPill: {
      label: primaryGuess.name,
      disabled: !primaryGuess.support_cards?.length,
      clickable: Boolean(primaryGuess.support_cards?.length),
      active: selectedName === primaryGuess.name,
      guessName: primaryGuess.name,
    },
    guesses: guesses.map((guess, index) => ({
      ...guess,
      rank: index + 1,
      selected: guess.name === selectedName,
      confidencePercent: Math.round((guess.confidence || 0) * 100),
      confidenceBarWidth: Math.max(8, Math.round((guess.confidence || 0) * 100)),
      reasons: guess.reasons?.length ? guess.reasons : ["No explanation available yet."],
      supportCards: guess.support_cards || [],
    })),
  };
}

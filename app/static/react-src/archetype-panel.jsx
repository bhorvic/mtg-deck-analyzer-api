import React from "react";
import { createRoot } from "react-dom/client";
import { buildArchetypePanelModel } from "../modules/archetype-model.js";

function ArchetypePanel({ model, actions }) {
  return (
    <section className="section-card archetype-card" id="archetype-section">
      <div className="section-heading static-heading archetype-heading">
        <div>
          <h3>Archetype read</h3>
          <p className="card-meta archetype-helper">{model.helperText}</p>
        </div>
        <button
          type="button"
          className={`pill success interactive-pill${model.primaryPill.clickable ? " is-clickable" : ""}${model.primaryPill.active ? " is-active" : ""}`}
          disabled={model.primaryPill.disabled}
          onClick={() => actions.onPrimaryPillClick(model.primaryPill.guessName)}
        >
          {model.primaryPill.label}
        </button>
      </div>

      {!model.hasGuesses ? (
        <div className="chart-empty">Run an analysis to see likely archetype matches.</div>
      ) : (
        <div className="archetype-guesses">
          {model.guesses.map((guess) => (
            <article key={guess.name} className={`archetype-guess${guess.selected ? " selected" : ""}`}>
              <button type="button" className="archetype-header archetype-header-button" onClick={() => actions.onSelectArchetype(guess)}>
                <div>
                  <h4>{guess.rank}. {guess.name}</h4>
                  <p className="card-meta">Confidence: {guess.confidencePercent}%</p>
                </div>
                <div className="confidence-track"><div className="confidence-bar" style={{ width: `${guess.confidenceBarWidth}%` }} /></div>
              </button>

              <ul className="archetype-reasons">
                {guess.reasons.map((reason, index) => <li key={`${guess.name}-reason-${index}`}>{reason}</li>)}
              </ul>

              {guess.supportCards.length > 0 && (
                <div className="archetype-support">
                  <p className="card-meta archetype-support-label">Support cards</p>
                  <div className="archetype-support-list">
                    {guess.supportCards.map((cardName) => (
                      <button
                        key={`${guess.name}-${cardName}`}
                        type="button"
                        className="support-card-pill"
                        onClick={() => actions.onHighlightSupportCards(guess)}
                      >
                        {cardName}
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="ghost-button small-button archetype-clear-button"
                    onClick={actions.onClearHighlight}
                  >
                    Clear highlight
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export function initArchetypePanel(rootId = "archetype-panel-root", actions = {}) {
  const mountEl = document.getElementById(rootId);
  if (!mountEl) {
    return { render() {} };
  }

  const root = createRoot(mountEl);

  const render = (guesses = [], primaryArchetype = null) => {
    root.render(<ArchetypePanel model={buildArchetypePanelModel(guesses, primaryArchetype)} actions={actions} />);
  };

  render();

  return { render };
}

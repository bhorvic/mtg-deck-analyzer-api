import React from "react";
import { createRoot } from "react-dom/client";

const NAV_ITEMS = [
  { key: "overview", label: "Overview", target: "overview-section" },
  { key: "visuals", label: "Visuals", target: "visuals-section" },
  { key: "archetype", label: "Archetype", target: "archetype-section" },
  { key: "feedback", label: "Feedback", target: "feedback-section" },
  { key: "mainboard", label: "Main deck", target: "mainboard-section" },
  { key: "sideboard", label: "Sideboard", target: "sideboard-section" },
];

function ResultsNavigator({ statusLabel, statusTone, counts, onNavigate }) {
  return (
    <>
      <div className="section-heading static-heading">
        <div className="section-heading-copy">
          <h3>Result navigator</h3>
          <p className="section-helper">Jump between the main analysis sections without hunting through the page.</p>
        </div>
        <span className={`pill ${statusTone}`}>{statusLabel}</span>
      </div>
      <div className="results-nav-grid">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.key}
            type="button"
            className="ghost-button nav-chip"
            onClick={() => onNavigate?.(item.target)}
          >
            {item.label} <span>{counts[item.key] ?? "-"}</span>
          </button>
        ))}
      </div>
    </>
  );
}

function createDefaultModel() {
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

let root = null;

export function initResultsNavigator(rootId = "results-nav-root", options = {}) {
  const mountEl = document.getElementById(rootId);
  if (!mountEl) {
    return {
      render() {},
      unmount() {},
    };
  }

  root = createRoot(mountEl);
  const render = (model = createDefaultModel()) => {
    root.render(
      <ResultsNavigator
        statusLabel={model.statusLabel}
        statusTone={model.statusTone}
        counts={model.counts}
        onNavigate={options.onNavigate}
      />,
    );
  };

  render();

  return {
    render,
    unmount() {
      root.unmount();
    },
  };
}

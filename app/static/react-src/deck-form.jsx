import React from "react";
import { createRoot } from "react-dom/client";
import { getFormState } from "../modules/form-state.js";
import { getDeckInputMetaModel, getParserPreviewModel, buildParserPreviewText } from "../modules/parser-preview-model.js";

const FORMAT_OPTIONS = ["commander", "standard", "pioneer", "modern", "pauper", "legacy", "vintage"];

function ToneText({ id, tone = "muted", className = "field-meta", children }) {
  return <p id={id} className={className} data-tone={tone}>{children}</p>;
}

function DeckFormApp({ model, onFieldChange, onSubmit, onCopyPreview }) {
  const meta = getDeckInputMetaModel(model.formState);
  const preview = getParserPreviewModel(model.formState);
  const isCommander = model.formState.format === "commander";

  return (
    <form id="deck-form" onSubmit={(event) => { event.preventDefault(); onSubmit?.(model.formState); }}>
      <label htmlFor="deck-name">Deck name</label>
      <input id="deck-name" name="name" type="text" value={model.formState.name} onChange={(event) => onFieldChange("name", event.target.value)} required />

      <label htmlFor="deck-format">Format</label>
      <select id="deck-format" name="format" value={model.formState.format} onChange={(event) => onFieldChange("format", event.target.value)}>
        {FORMAT_OPTIONS.map((format) => (
          <option key={format} value={format}>{format.charAt(0).toUpperCase() + format.slice(1)}</option>
        ))}
      </select>

      <div id="commander-field-group" className={isCommander ? "" : "hidden"}>
        <label htmlFor="commander">Commander</label>
        <input
          id="commander"
          name="commander"
          type="text"
          value={model.formState.commander}
          placeholder="Commander name(s); separate two with / or a new line"
          onChange={(event) => onFieldChange("commander", event.target.value)}
        />
        <ToneText id="commander-field-meta" tone={meta.commander.tone}>{meta.commander.message}</ToneText>
      </div>

      <div className="field-grid">
        <div>
          <label htmlFor="decklist">Main deck</label>
          <p className="field-helper">Paste a plain-text decklist. Most common exports and messy separators are cleaned up automatically.</p>
          <ToneText id="decklist-meta" tone={meta.decklist.tone}>{meta.decklist.message}</ToneText>
          <textarea id="decklist" className="deck-editor" name="decklist" rows="14" value={model.formState.decklist} onChange={(event) => onFieldChange("decklist", event.target.value)} required />
        </div>
        <div>
          <label htmlFor="sideboard">Sideboard</label>
          <p className="field-helper">Optional for 60-card formats.</p>
          <ToneText id="sideboard-meta" tone={meta.sideboard.tone}>{meta.sideboard.message}</ToneText>
          <textarea
            id="sideboard"
            className="deck-editor"
            name="sideboard"
            rows="14"
            placeholder="Optional for Standard/Pioneer/Modern/Pauper/Legacy/Vintage"
            value={model.formState.sideboard}
            onChange={(event) => onFieldChange("sideboard", event.target.value)}
          />
        </div>
      </div>

      <details className="section-card collapsible form-preview-card" id="parser-preview-section">
        <summary className="section-heading">
          <div className="section-heading-copy">
            <h3>Normalized parser preview</h3>
            <p id="parser-preview-summary" className="section-helper">{preview.summary}</p>
          </div>
          <span className="pill neutral" id="parser-preview-count">{preview.countLabel}</span>
        </summary>
        <div className="results-toolbar parser-preview-toolbar utility-strip">
          <div>
            <p className="toolbar-label">Preview</p>
            <p id="parser-preview-status" className="status">{preview.status}</p>
          </div>
          <div className="results-toolbar-actions">
            <button type="button" id="copy-parser-preview-button" className="secondary-button small-button" onClick={() => onCopyPreview?.(buildParserPreviewText(model.formState))}>Copy preview</button>
          </div>
        </div>
        <pre id="parser-preview-output" className="parser-preview-output">{preview.output}</pre>
      </details>

      <div className="actions">
        <button id="submit-button" type="submit" disabled={model.submitting}>{model.submitting ? "Analyzing…" : "Analyze deck"}</button>
        <span id="status" className="status" data-tone={model.statusTone} aria-live="polite">{model.statusMessage}</span>
      </div>
    </form>
  );
}

export function initDeckForm(rootId = "deck-form-root", options = {}) {
  const mountEl = document.getElementById(rootId);
  if (!mountEl) {
    return {
      getState: () => getFormState(options.initialState || {}),
      setState() {},
      setSubmitting() {},
      setStatus() {},
      getParserPreviewText: () => "",
    };
  }

  const root = createRoot(mountEl);
  const model = {
    formState: getFormState(options.initialState || {}),
    submitting: false,
    statusMessage: "",
    statusTone: "muted",
  };

  const render = () => {
    root.render(
      <DeckFormApp
        model={model}
        onFieldChange={(field, value) => {
          model.formState = getFormState({ ...model.formState, [field]: value });
          render();
          options.onStateChange?.(model.formState);
        }}
        onSubmit={options.onSubmit}
        onCopyPreview={options.onCopyPreview}
      />,
    );
  };

  render();

  return {
    getState() {
      return getFormState(model.formState);
    },
    setState(nextState, { silent = false } = {}) {
      model.formState = getFormState(nextState);
      render();
      if (!silent) {
        options.onStateChange?.(model.formState);
      }
    },
    setSubmitting(isSubmitting) {
      model.submitting = Boolean(isSubmitting);
      render();
    },
    setStatus(message, tone = "muted") {
      model.statusMessage = message;
      model.statusTone = tone;
      render();
    },
    getParserPreviewText() {
      return buildParserPreviewText(model.formState);
    },
  };
}

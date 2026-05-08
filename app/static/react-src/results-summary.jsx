import React from "react";
import { createRoot } from "react-dom/client";
import { buildResultsSummaryModel } from "../modules/results-summary-model.js";

function ColorIdentity({ colors = [] }) {
  if (!colors.length) {
    return <span className="colorless-label">Colorless</span>;
  }

  return (
    <span className="color-pip-row" aria-label={colors.join(", ")}>
      {colors.map((color) => (
        <img
          key={color}
          className="color-pip"
          src={`https://svgs.scryfall.io/card-symbols/${color}.svg`}
          alt={color}
        />
      ))}
    </span>
  );
}

function MessageList({ items, emptyMessage, variant, detailed = false }) {
  return (
    <ul className={`message-list ${variant === "danger" ? "warnings" : variant === "success" ? "recommendations" : "neutral-list"}`} data-variant={variant}>
      {!items.length ? (
        <li className="message-empty">{emptyMessage}</li>
      ) : items.map((item, index) => detailed ? (
        <li key={`${item.body}-${index}`} className="message-item">
          <div className="message-item-head">
            <span className={`message-badge message-badge-${item.tone || variant}`}>{item.label || "Note"}</span>
          </div>
          <div className="message-body">{item.body}</div>
        </li>
      ) : (
        <li key={`${item.body}-${index}`}>{item.body}</li>
      ))}
    </ul>
  );
}

function FeedbackCard({ id, title, section }) {
  const classNames = ["section-card", "collapsible"];
  if (section.hidden) classNames.push("section-soft-hidden");
  if (!section.hidden && section.quiet) classNames.push("section-quiet");
  if (!section.hidden && section.emphasis) classNames.push("section-emphasis");

  return (
    <details id={id} className={classNames.join(" ")} open={section.open}>
      <summary className="section-heading">
        <div className="section-heading-copy">
          <h3>{title}</h3>
          <p className="section-helper">{section.summary}</p>
        </div>
        <span className={`pill ${section.pillTone}`}>{section.count}</span>
      </summary>
      <MessageList
        items={section.items}
        emptyMessage={section.emptyMessage}
        variant={section.variant}
        detailed={section.detailed}
      />
    </details>
  );
}

function ResultsSummary({ model }) {
  return (
    <>
      <div className="results-header">
        <div>
          <p className="eyebrow">Analysis</p>
          <h2>{model.header.title}</h2>
        </div>
        <div className="chip-row" id="result-chips">
          <span className="chip">{model.header.format}</span>
          <span className="chip"><ColorIdentity colors={model.header.colors} /></span>
        </div>
      </div>

      <div className="grid stats-grid">
        {model.stats.map((stat) => (
          <div key={stat.label} className={`stat-card${stat.accent ? " accent-card" : ""}`}>
            <span>{stat.label}</span>
            <strong>{stat.isColors ? <ColorIdentity colors={stat.colors} /> : stat.value}</strong>
          </div>
        ))}
      </div>

      <section className="section-card overview-card" id="overview-section">
        <div className="section-heading static-heading overview-heading">
          <div className="section-heading-copy">
            <h3>Quick read</h3>
            <p className="section-helper">{model.overview.summary}</p>
          </div>
          <span className={`pill ${model.overview.pillTone}`}>{model.overview.pill}</span>
        </div>
        <div className="overview-grid">
          <article className="overview-stat overview-stat-danger">
            <span>Needs attention</span>
            <strong>{model.overview.dangerCount}</strong>
            <p className="card-meta">{model.overview.dangerLabel}</p>
          </article>
          <article className="overview-stat overview-stat-warning">
            <span>Watch list</span>
            <strong>{model.overview.warningCount}</strong>
            <p className="card-meta">{model.overview.warningLabel}</p>
          </article>
          <article className="overview-stat overview-stat-success">
            <span>Suggestions</span>
            <strong>{model.overview.recommendationCount}</strong>
            <p className="card-meta">{model.overview.recommendationLabel}</p>
          </article>
        </div>
      </section>

      <div className="grid feedback-grid" id="feedback-section">
        <FeedbackCard id="commander-validation-section" title="Commander validation" section={model.feedback.commanderValidation} />
        <FeedbackCard id="recommendations-section" title="Recommendations" section={model.feedback.recommendations} />
        <FeedbackCard id="warnings-section" title="Warnings" section={model.feedback.warnings} />
      </div>
    </>
  );
}

export function initResultsSummary(rootId = "results-summary-root") {
  const mountEl = document.getElementById(rootId);
  if (!mountEl) {
    return { render() {} };
  }

  const root = createRoot(mountEl);
  const render = (data = null) => {
    root.render(<ResultsSummary model={buildResultsSummaryModel(data)} />);
  };

  render();

  return { render };
}

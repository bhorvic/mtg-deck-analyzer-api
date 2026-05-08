import React from "react";
import { createRoot } from "react-dom/client";

function CardArticle({ entry }) {
  return (
    <article className={`${entry.highlighted ? "highlighted-support" : ""}${entry.matches ? "" : " hidden-by-filter"}`.trim()}>
      <div className="card-header">
        {entry.card?.image_small
          ? <img className="card-image" src={entry.card.image_small} alt={entry.name} />
          : <div className="card-image card-image-placeholder">No image</div>}
        <div>
          <h4>{entry.quantity}x {entry.name}</h4>
          <div className="tag-list">
            {entry.categories.length
              ? entry.categories.map((category) => <span key={`${entry.name}-${category}`} className="tag">{category}</span>)
              : <span className="tag tag-muted">uncategorized</span>}
          </div>
          <div className="card-type">{entry.card?.type_line || "Unknown type"}</div>
          <p className="card-meta">Mana cost: {entry.card?.mana_cost || "-"} · MV: {entry.card?.mana_value ?? "-"}</p>
        </div>
      </div>
      <p className="oracle-text">{entry.card?.oracle_text || "No oracle text available."}</p>
      {entry.card?.scryfall_uri ? <p><a href={entry.card.scryfall_uri} target="_blank" rel="noreferrer">View on Scryfall</a></p> : null}
    </article>
  );
}

function CardSection({ id, title, countLabel, items, compactCardView }) {
  return (
    <details className="section-card collapsible" id={id}>
      <summary className="section-heading">
        <h3>{title}</h3>
        <span className="pill neutral">{countLabel}</span>
      </summary>
      <div className={`cards${compactCardView ? " compact-cards" : ""}`}>
        {items.length ? items.map((entry) => <CardArticle key={`${entry.name}-${entry.quantity}`} entry={entry} />) : (
          <article className="empty-card"><h4>No cards</h4><p>Nothing to show in this section.</p></article>
        )}
      </div>
    </details>
  );
}

function CardSurface({ model, actions }) {
  return (
    <>
      <div className="results-toolbar section-card filter-toolbar">
        <div className="filter-toolbar-field">
          <label htmlFor="card-filter">Filter cards</label>
          <input
            id="card-filter"
            type="text"
            placeholder="Search by name, type, oracle text, or tag"
            value={model.toolbar.filter}
            onChange={(event) => actions.onFilterChange(event.target.value)}
          />
        </div>
        <div className="results-toolbar-actions filter-toolbar-actions">
          <span className="pill neutral" id="card-filter-count">{model.toolbar.filterCountLabel}</span>
          <div className="compact-select-group">
            <label className="sr-only" htmlFor="card-sort">Sort cards</label>
            <select id="card-sort" value={model.toolbar.sortKey} onChange={(event) => actions.onSortKeyChange(event.target.value)}>
              <option value="name">Sort: Name</option>
              <option value="manaValue">Sort: Mana value</option>
              <option value="quantity">Sort: Quantity</option>
              <option value="typeLine">Sort: Type</option>
            </select>
            <label className="sr-only" htmlFor="card-sort-direction">Sort direction</label>
            <select id="card-sort-direction" value={model.toolbar.sortDirection} onChange={(event) => actions.onSortDirectionChange(event.target.value)}>
              <option value="asc">Asc</option>
              <option value="desc">Desc</option>
            </select>
          </div>
          <button type="button" className="secondary-button small-button" onClick={actions.onCopySummary}>Copy summary</button>
          <button type="button" className="ghost-button small-button" onClick={actions.onCopyJson}>Copy JSON</button>
          <button type="button" className="ghost-button small-button" onClick={actions.onToggleDensity}>
            {model.toolbar.compactCardView ? "Expanded card view" : "Compact card view"}
          </button>
          <button type="button" className="secondary-button small-button" onClick={actions.onExpandAll}>Expand all</button>
          <button type="button" className="ghost-button small-button" onClick={actions.onCollapseAll}>Collapse all</button>
        </div>
      </div>

      <CardSection
        id="mainboard-section"
        title="Main deck cards"
        countLabel={model.sections.mainboard.countLabel}
        items={model.sections.mainboard.items}
        compactCardView={model.toolbar.compactCardView}
      />

      <CardSection
        id="sideboard-section"
        title="Sideboard cards"
        countLabel={model.sections.sideboard.countLabel}
        items={model.sections.sideboard.items}
        compactCardView={model.toolbar.compactCardView}
      />
    </>
  );
}

function createDefaultModel() {
  return {
    toolbar: {
      filter: "",
      sortKey: "name",
      sortDirection: "asc",
      filterCountLabel: "No rendered cards yet",
      compactCardView: false,
    },
    sections: {
      mainboard: {
        countLabel: "0 cards",
        items: [],
      },
      sideboard: {
        countLabel: "0 cards",
        items: [],
      },
    },
  };
}

export function initCardSurface(rootId = "card-surface-root", actions = {}) {
  const mountEl = document.getElementById(rootId);
  if (!mountEl) {
    return { render() {} };
  }

  const root = createRoot(mountEl);
  const render = (model = createDefaultModel()) => {
    root.render(<CardSurface model={model} actions={actions} />);
  };

  render();

  return { render };
}

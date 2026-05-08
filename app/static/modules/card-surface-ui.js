import { initCardSurface } from "../react/card-surface.js";
import { cardSurfaceRootEl } from "./dom.js";
import { appState } from "./state.js";
import { buildCardSurfaceModel } from "./card-surface-model.js";

let callbacksRef = {
  copySummary() {},
  copyJson() {},
  toggleDensity() {},
  expandAll() {},
  collapseAll() {},
};

const cardSurface = cardSurfaceRootEl
  ? initCardSurface("card-surface-root", {
    onFilterChange(value) {
      appState.ui.cardFilter = value;
      renderCardSurface();
    },
    onSortKeyChange(value) {
      appState.ui.cardSort = value;
      renderCardSurface();
    },
    onSortDirectionChange(value) {
      appState.ui.cardSortDirection = value;
      renderCardSurface();
    },
    onCopySummary() {
      callbacksRef.copySummary();
    },
    onCopyJson() {
      callbacksRef.copyJson();
    },
    onToggleDensity() {
      callbacksRef.toggleDensity();
      renderCardSurface();
    },
    onExpandAll() {
      callbacksRef.expandAll();
    },
    onCollapseAll() {
      callbacksRef.collapseAll();
    },
  })
  : { render() {} };

export function registerCardSurfaceCallbacks(callbacks = {}) {
  callbacksRef = { ...callbacksRef, ...callbacks };
}

export function renderCardSurface() {
  cardSurface.render(buildCardSurfaceModel());
}

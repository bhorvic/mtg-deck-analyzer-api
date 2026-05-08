import { appState } from "./state.js";
import { formatCountLabel } from "./renderers.js";

function buildCardSearchText(entry) {
  return [entry.name, entry.card?.type_line || "", entry.card?.oracle_text || "", ...(entry.categories || [])]
    .join(" ")
    .toLowerCase();
}

function getSortValue(entry, key) {
  if (key === "manaValue") return Number(entry.card?.mana_value ?? -1);
  if (key === "quantity") return Number(entry.quantity ?? 0);
  if (key === "typeLine") return (entry.card?.type_line || "").toLowerCase();
  return (entry.name || "").toLowerCase();
}

function sortCards(cards, key = "name", direction = "asc") {
  const sortDirection = direction === "desc" ? -1 : 1;

  return [...cards].sort((left, right) => {
    const leftValue = getSortValue(left, key);
    const rightValue = getSortValue(right, key);
    if (leftValue < rightValue) return -1 * sortDirection;
    if (leftValue > rightValue) return 1 * sortDirection;
    return left.name.localeCompare(right.name);
  });
}

function decorateCards(cards = [], query = "", sortKey = "name", sortDirection = "asc") {
  const normalizedQuery = query.trim().toLowerCase();
  const sortedCards = sortCards(cards, sortKey, sortDirection);
  let visibleCount = 0;

  const items = sortedCards.map((entry) => {
    const searchText = buildCardSearchText(entry);
    const matches = !normalizedQuery || searchText.includes(normalizedQuery);
    if (matches) visibleCount += 1;

    return {
      ...entry,
      matches,
      highlighted: appState.ui.highlightedSupportCards.includes(entry.name),
      categories: entry.categories || [],
    };
  });

  return {
    items,
    visibleCount,
    totalCount: sortedCards.length,
  };
}

export function buildCardSurfaceModel() {
  const query = appState.ui.cardFilter || "";
  const sortKey = appState.ui.cardSort || "name";
  const sortDirection = appState.ui.cardSortDirection || "asc";
  const mainboard = decorateCards(appState.cards.mainboard || [], query, sortKey, sortDirection);
  const sideboard = decorateCards(appState.cards.sideboard || [], query, sortKey, sortDirection);
  const totalRendered = mainboard.totalCount + sideboard.totalCount;
  const totalVisible = mainboard.visibleCount + sideboard.visibleCount;

  return {
    toolbar: {
      filter: query,
      sortKey,
      sortDirection,
      filterCountLabel: totalRendered
        ? (query ? `Showing ${totalVisible} of ${totalRendered} cards` : `Showing all ${totalRendered} cards`)
        : "No rendered cards yet",
      compactCardView: appState.ui.compactCardView,
    },
    sections: {
      mainboard: {
        countLabel: formatCountLabel(appState.cards.mainboard?.length || 0, "card"),
        items: mainboard.items,
      },
      sideboard: {
        countLabel: formatCountLabel(appState.cards.sideboard?.length || 0, "card"),
        items: sideboard.items,
      },
    },
  };
}

# Frontend React Migration Notes

This app started as plain browser JavaScript, and it has now begun an incremental React migration via a small bundled React island. The remaining frontend modules still map fairly cleanly to future React boundaries.

## Current module shape

- `app/static/app.js`
  - thin-ish orchestrator
  - event wiring
  - local UI helpers that still coordinate modules
- `app/static/modules/state.js`
  - shared app state
  - sample deck presets
  - storage keys / constants
- `app/static/modules/dom.js`
  - centralized DOM lookups
- `app/static/modules/parser.js`
  - browser-side deck parsing / normalization preview logic
- `app/static/modules/form-state.js`
  - form hydration
  - URL sync
  - local draft persistence
- `app/static/modules/renderers.js`
  - analysis result rendering
  - card list rendering / filtering / summary display
- `app/static/modules/parser-preview-ui.js`
  - parser preview output
  - deck input metadata hints
  - commander-field visibility sync
- `app/static/modules/ui-shell.js`
  - status/draft status/toasts
  - results navigator
  - card density toggle
  - section expand/collapse helpers
- `app/static/modules/archetype-ui.js`
  - archetype selection and support-card highlighting
- `app/static/modules/clipboard.js`
  - copy helpers
- `app/static/modules/analysis-controller.js`
  - submit state
  - payload building
  - API request + analysis result hydration
- `app/static/react-src/results-nav.jsx`
  - first React island source
  - owns the Results Navigator UI
- `app/static/react-src/deck-form.jsx`
  - React form island source
  - owns the deck input + parser preview workflow
- `app/static/react-src/results-summary.jsx`
  - React results-summary island source
  - owns the read-only top analysis summary surface
- `app/static/react-src/archetype-panel.jsx`
  - React archetype-panel island source
  - owns archetype selection and support-card highlight actions
- `app/static/react-src/card-surface.jsx`
  - React card-surface island source
  - owns filter/sort controls, copy actions, density toggle, and main/sideboard rendering
- `app/static/react/results-nav.js`
  - built browser bundle for the React navigator island
- `app/static/react/deck-form.js`
  - built browser bundle for the React form island
- `app/static/react/results-summary.js`
  - built browser bundle for the React results-summary island
- `app/static/react/archetype-panel.js`
  - built browser bundle for the React archetype-panel island
- `app/static/react/card-surface.js`
  - built browser bundle for the React card-surface island
- `app/static/modules/parser-preview-model.js`
  - pure parser-preview/meta derivation for React and non-React callers
- `app/static/modules/results-summary-model.js`
  - pure summary/feedback derivation for React-owned analysis panels
- `app/static/modules/results-summary-ui.js`
  - bridge from analysis flow into the React results-summary island
- `app/static/modules/archetype-model.js`
  - pure archetype panel derivation for React-owned archetype UI
- `app/static/modules/card-surface-model.js`
  - pure filter/sort/highlight derivation for the React-owned card surface
- `app/static/modules/card-surface-ui.js`
  - bridge from shared app state into the React card-surface island

## Likely React component boundaries

If this moves to React later, these are the most natural component seams:

### App shell
- owns top-level layout
- provides shared state/context
- coordinates form + results panes
- replaces most of the remaining `app.js` orchestration over time

### DeckForm
- deck name / format / commander / decklist / sideboard inputs
- parser preview panel
- already migrated to React as a form island

### ParserPreview
- normalized commander/main/sideboard preview
- ignored helper-line summary
- preview copy action
- already migrated together with DeckForm

### ResultsNavigator
- sticky quick-jump card
- overview/visual/archetype/feedback/main/sideboard badges
- already migrated to React as the first island

### ResultsHeader
- deck name
- format pill
- color identity display
- headline counts
- summary copy / JSON copy actions
- mostly migrated as part of the results-summary island

### AnalysisOverview
- analysis health pill
- warning / recommendation / commander validation summary blocks
- already migrated into the results-summary island

### ArchetypePanel
- primary archetype pill
- ranked archetype guesses
- reasons
- support-card highlighting interactions
- already migrated into a React island

### FeedbackPanels
- warnings
- recommendations
- commander color identity validation
- already migrated into the results-summary island

### SummaryStats
- mana curve
- type breakdown
- classification counts

### ChartPanels
- mana curve chart
- type breakdown chart

### CardSections
- mainboard list
- sideboard list
- card density toggle
- filter / sort controls
- already migrated into the React card-surface island

## State that likely belongs in React state/context

### Analysis state
- `analysis`
- `cards.mainboard`
- `cards.sideboard`

### UI state
- `highlightedSupportCards`
- `selectedArchetypeName`
- `compactCardView`
- current filter / sort selections
- draft status / submit status / toast queue

### Derived state worth memoizing later
- filtered/sorted card lists
- warning classification breakdown
- parser preview summary counts
- results navigator counts

## Good migration sequence

1. Keep the current island approach while leaving the backend/API contract unchanged.
2. Convert charts/stat lists and the remaining read-only result panels next.
3. Move shared state ownership into React once multiple islands need the same live state.
4. Delete the old DOM lookup layer only after all major screens are React-owned.

## Things to avoid during migration

- Don’t rewrite parser behavior at the same time as UI migration.
- Don’t change the API response shape unless the backend and frontend are updated together.
- Don’t mix React-owned DOM and manual DOM mutation in the same subtree longer than necessary.

## Practical next prep step

Now that the Results Navigator, DeckForm/ParserPreview, top results summary surface, archetype panel, and card surface are React-owned, the next useful migration step is migrating the remaining stat/chart panels and then consolidating more live state ownership inside React.

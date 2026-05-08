# MTG Deck Analyzer API

A FastAPI app and browser UI for analyzing Magic: The Gathering decklists.

It accepts pasted decklists, normalizes messy real-world input, looks up card data from Scryfall, and returns format-aware validation, deck statistics, role tags, and likely archetypes.

## Live app

Try it here: <https://mtg.bhorvicbot.com/>

## Highlights

- **Supports multiple formats**
  - Commander
  - Standard
  - Pioneer
  - Modern
  - Pauper
  - Legacy
  - Vintage
- **Format-aware validation** for deck size, card legality, duplicates, and other rules checks
- **Commander-specific rules support**
  - commander legality
  - commander color identity checks
  - commander-in-main-deck warnings
  - common two-commander patterns like Partner, Friends forever, Background, and Doctor's companion
- **Deck analysis output** including mana curve, type breakdown, color identity, unique-card counts, and lightweight role tagging
- **Archetype detection** using heuristics plus format-aware signature matching
- **Forgiving parser** for noisy exports and pasted lists from deck sites and text files
- **Built-in web UI** for interactive testing and exploration
- **Swagger docs** for API inspection and direct requests

## Why this project exists

Most deck tools are either very strict about input format or focused on a narrow slice of analysis. This project aims to be more practical:

- paste in messy decklists without hand-cleaning them first
- get fast feedback on legality and structure
- surface useful summary stats and warnings
- make the same logic available through both an API and a lightweight web app

## Tech stack

- **Backend:** FastAPI, Pydantic, httpx, Jinja2
- **Frontend:** vanilla JS with progressively introduced React islands
- **Tooling:** pytest, esbuild
- **Data source:** Scryfall

## Project structure

```text
app/
  api/routes/      # FastAPI route handlers
  core/            # app settings
  models/          # request/response models
  services/        # parser, analyzer, Scryfall client
  static/          # frontend JS, CSS, React bundles, client modules
  templates/       # Jinja templates
tests/             # parser, API, and Scryfall client coverage
```

## Run locally

### 1) Create a virtual environment and install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Install frontend dependencies

```bash
npm install
```

### 3) Build the React islands

```bash
npm run build:react
```

### 4) Start the app

```bash
uvicorn app.main:app --reload
```

Then open:

- App: <http://127.0.0.1:8000/>
- Swagger docs: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

## Example API request

```bash
curl -X POST http://127.0.0.1:8000/deck/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Sample Deck",
    "format": "commander",
    "commander": "Baral, Chief of Compliance",
    "decklist": "1 Sol Ring\n1 Arcane Signet\n97 Island"
  }'
```

## Frontend notes

The UI is intentionally being improved incrementally instead of rewritten all at once.

Current interface work includes things like:

- parser preview
- warnings and feedback cards
- result summaries
- archetype panel
- card surface/details
- filtering, sorting, copy/export helpers
- React-based UI islands layered into the existing app

Additional implementation notes live in [`FRONTEND_REACT_NOTES.md`](FRONTEND_REACT_NOTES.md).

## Parser tolerance

One of the main goals is accepting the kind of input people actually paste.

The parser currently handles things like:

- section headers such as `Commander`, `Sideboard`, `Creatures (12)`, and labeled groupings like `Interaction:`
- inline markers such as `Commander: 1x Baral` and `SB:1—Pongify`
- count/name separator variations like `4xLightning Bolt`, `2 - Mishra's Bauble`, `3 — Counterspell`, `1: Sol Ring`, and tab-delimited lines
- ignored helper noise like maybeboard sections, checklist bullets, comments, and title lines before real sections
- trailing metadata cleanup such as `(CMM)`, `[Commander]`, `{Promo}`, `(foil)`, and `*F*`

## Testing

Run the test suite with:

```bash
.venv/bin/pytest -q
```

## Notes and limitations

- This app was built entirely using an OpenClaw agentic agent workflow
- No API key is required for normal Scryfall usage
- Scryfall lookups use a simple in-process cache to reduce repeated card fetches
- Role tagging and archetype classification are heuristic, not oracle-perfect
- This project is designed as a practical analyzer and UI prototype, not a tournament rules engine

## Roadmap ideas

- broaden archetype coverage across more formats and commanders
- improve card-role classification depth
- continue React migration where it meaningfully improves maintainability
- add richer visualizations and deck comparison workflows

## License

This project is licensed under the [MIT License](LICENSE).

# mtg-deck-analyzer-api

FastAPI app for analyzing Magic: The Gathering decklists, with a small web UI and format-aware validation.

## What it does

- Parse pasted decklists and optional sideboards
- Look up card metadata from Scryfall
- Return deck statistics:
  - total cards
  - unique cards
  - mana curve
  - type breakdown
  - deck color identity
  - lightweight card role tags (ramp, draw, removal, boardwipe)
- Run format-specific checks for:
  - Commander
  - Standard
  - Pioneer
  - Modern
  - Pauper
  - Legacy
  - Vintage
- Return likely deck archetypes using a mix of heuristics and format-aware signature matching
  - current starter coverage includes shells like Burn, Tron, Hammer Time, Spirits, Phoenix, Rakdos Midrange, Shops, Stax, Artifacts, Lands, Enchantress, and more
- Support Commander validation for:
  - deck size
  - sideboard warnings
  - commander legality
  - commander color identity violations
  - common two-commander pairings (Partner, Friends forever, Background, Doctor's companion)
  - duplicate-count exceptions from oracle text
- Serve a browser UI plus Swagger docs

## Tech stack

- FastAPI
- Pydantic
- httpx
- Jinja2
- pytest

## Project layout

```text
app/
  api/routes/      # FastAPI route handlers
  core/            # app settings
  models/          # request/response models
  services/        # parser, analyzer, Scryfall client
  static/          # frontend JS + CSS
  templates/       # Jinja templates
tests/             # API and parser tests
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

- App: http://127.0.0.1:8000/
- Swagger docs: http://127.0.0.1:8000/docs

## Example request

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

## Test

```bash
.venv/bin/pytest -q
```

## Notes

- No API key is required for basic Scryfall usage.
- Scryfall lookups now use a simple in-process cache (default TTL: 1 hour) to avoid refetching the same cards repeatedly.
- This is a solid prototype, but card-role tagging is still heuristic rather than rules-perfect.

## Parser tolerance highlights

The deck parser is deliberately forgiving about a lot of real-world paste noise. Current cleanup/normalization includes things like:

- section headers such as `Commander`, `Sideboard`, `Creatures (12)`, and generic labels like `Interaction:`
- inline markers such as `Commander: 1x Baral` and `SB:1—Pongify`
- quantity/name separator variants like `4xLightning Bolt`, `2 - Mishra's Bauble`, `3 — Counterspell`, `1: Sol Ring`, and tab-delimited lines
- ignored helper noise like maybeboard sections, checklist bullets, comments, and deck-title lines before real sections
- trailing metadata cleanup for tags like `(CMM)`, `[Commander]`, `{Promo}`, `(foil)`, and `*F*`

The browser UI also exposes a normalized parser preview so you can see how the client-side preflight parser is interpreting a pasted list before you submit it.

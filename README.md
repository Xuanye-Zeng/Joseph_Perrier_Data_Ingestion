# Joseph Perrier Data Ingestion

> A data pipeline that scrapes the [Joseph Perrier](https://www.josephperrier.com/en/) champagne website and stores structured product, winery, and media data in a normalized SQLite database — designed to support product discovery and commerce.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for the web UI)

### Setup & Run

```bash
# Install Python dependencies
pip install -r requirements.txt
playwright install chromium

# Run the full pipeline (scrape → parse → translate → store)
python main.py

# Enrich product gallery images
python add_gallery_images.py

# Inspect the database
python inspect_db.py stats
python inspect_db.py products
python inspect_db.py product "Cuvée Royale Brut"

# Start the web UI (serves API + frontend on one port)
python api.py
# → Open http://localhost:8000
```

## Architecture

```
josephperrier.com → Playwright Scraper → BeautifulSoup Parser → Translator → SQLite DB → FastAPI → React UI
                    (age gate bypass)    (data extraction)       (FR → EN)    (11 tables)  (JSON API)  (explorer)
```

### Pipeline Steps

1. **Scrape** — Playwright handles age verification, crawls 55+ English pages, discovers product URLs dynamically with hardcoded fallback
2. **Parse** — Extracts structured data: products, tasting notes, technical specs, awards, food pairings, media URLs, team members, history events, blog articles
3. **Translate** — Post-processing French→English translation via Google Translate for content behind Weglot's client-side translation wall
4. **Store** — Normalized SQLite database with 11 tables, cascading inserts, and foreign key relationships
5. **Serve** — FastAPI REST API with product filtering (collection, price range, search) and theme color mapping
6. **Display** — React + Tailwind frontend styled to match the Joseph Perrier brand identity

## Database Schema

11 normalized tables designed to support product discovery and commerce queries:

| Table | Purpose | Records |
|---|---|---|
| `winery` | House-level info (name, location, founded year, vineyard, cellars) | 1 |
| `winery_history` | Timeline events (1825–2025) | 15 |
| `team_member` | Family & team (name, role, generation, bio, photo URL) | 4 |
| `product` | Champagne cuvées (name, collection, type, blend, price, vintage) | 10 |
| `tasting_note` | Structured notes (color, nose, palate, serving suggestion) | 10 |
| `food_pairing` | Pairing recommendations per product | 10 |
| `product_format` | Bottle sizes (375ml–6L) per product | 27 |
| `product_technical` | Aging months, dosage, serving temp, crus | 10 |
| `product_award` | Awards with scores (James Suckling 91pts, Decanter Silver, etc.) | 36 |
| `media` | Image/video URLs linked to product, winery, or article | 87 |
| `article` | Blog posts from Jojo Mag (title, summary, category, image) | 37 |

### Why This Schema?

Every table separation serves a specific product discovery or commerce query:

- **Separate `tasting_note`** → "Show me wines with citrus on the palate"
- **Normalized `food_pairing`** → "Which wines pair with seafood?"
- **`product_format` table** → "Show me all magnums" or "Available in half-bottle"
- **`product_technical`** → "Wines aged 60+ months" or "Zero dosage champagnes"
- **`product_award` with scores** → "Highest rated wines" or "Award-winning under €50"
- **`media` with context field** → Distinguish product photos from award badges from gallery images

## Key Technical Decisions

| Decision | Reasoning |
|---|---|
| Playwright over requests | Site requires JS rendering for age gate and dynamic content |
| SQLite over PostgreSQL | Zero-config for reviewer, single file, sufficient for this scale |
| Post-processing translation | Weglot's client-side JS translation doesn't execute in headless browsers |
| 11 tables (not 3) | Normalized schema enables real commerce queries, not just data storage |
| Fallback data tables | Elementor-generated HTML is unpredictable; hardcoded baselines ensure data quality |
| Curated gallery images | Hand-picked from the website to ensure visual relevance per product |
| E-shop product photos | Higher quality lifestyle shots vs transparent bottle cutouts |

## Web UI

The frontend is a brand-styled product explorer that demonstrates the schema supports real product discovery:

- **Product browsing** with collection filter pills, price range slider, and text search
- **Product detail modal** with tasting notes (4-column: eye, nose, mouth, pairing), technical specs (aging, dosage, temperature), award scores with logos, bottle formats in ml/L, and curated gallery
- **Winery overview** with key metrics (1825 / 200 years / 24 hectares / 5km cellars), cellar description, visit experiences
- **History timeline** with 15 events from founding to bicentenary
- **Family page** with current leadership across six generations
- **Articles** from the Jojo Mag blog with category tags and pagination

Design: warm cream palette, Playfair Display serif headings, Inter sans-serif body, gold accents — matching the Joseph Perrier brand.

## Project Structure

```
├── main.py                    # Pipeline orchestrator: scrape → parse → translate → store
├── api.py                     # FastAPI backend (8 endpoints + static SPA serving)
├── inspect_db.py              # CLI tool for database inspection
├── add_gallery_images.py      # Curated image enrichment script
├── requirements.txt           # Python dependencies
├── src/
│   ├── scraper.py             # Playwright async scraper with age gate handling
│   ├── parser.py              # BeautifulSoup extraction (products, awards, tech specs)
│   ├── database.py            # SQLite schema + full CRUD with cascading inserts
│   ├── models.py              # 11 Python dataclasses mirroring DB schema
│   └── translator.py          # French→English post-processing translation
├── data/
│   └── joseph_perrier.db      # Generated SQLite database
└── frontend/
    ├── src/
    │   ├── App.jsx            # Main app with tab navigation
    │   ├── api.js             # API client (fetch wrapper)
    │   └── components/        # ProductGrid, ProductDetail, WineryView, etc.
    ├── vite.config.js         # Vite + Tailwind + API proxy
    └── dist/                  # Production build (served by api.py)
```

## CLI Inspection

```bash
python inspect_db.py stats                           # Database summary
python inspect_db.py winery                          # Winery info
python inspect_db.py products                        # All products with prices
python inspect_db.py product "Cuvée Royale Brut"     # Full product detail
python inspect_db.py media --product "Joséphine"     # Media for a product
python inspect_db.py history                         # Timeline (1825–2025)
python inspect_db.py team                            # Family members
python inspect_db.py articles                        # Blog articles
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/stats` | Database summary with collection and media breakdowns |
| GET | `/api/winery` | Winery information with English description fallback |
| GET | `/api/products` | Products (filterable: `?collection=`, `?max_price=`, `?search=`) |
| GET | `/api/products/{id}` | Full product detail: tasting notes, awards, tech specs, formats, media |
| GET | `/api/history` | History timeline ordered by year |
| GET | `/api/team` | Family/team members |
| GET | `/api/media` | All media (filterable: `?product_id=`) |
| GET | `/api/articles` | Blog articles |

## Biggest Challenge: Weglot Translation Wall

The Joseph Perrier website uses [Weglot](https://weglot.com/) for client-side translation. All HTML is served in French (`lang="fr-FR"`) regardless of the `/en/` URL path. The English content is translated by Weglot's JavaScript at runtime — which does not execute in any automated environment (headless, headed, curl).

**Diagnosis**: Tested Playwright headless/headed, various cookies (`wglang=en`), URL params (`?wg-choose-original=false`), User-Agent spoofing — all returned French.

**Solution**: Built a `ContentTranslator` module using `deep-translator` (Google Translate) with French-language detection heuristic. Only translates text identified as French; English content passes through unchanged.

## Built With

- **Python 3.11** — Core pipeline
- **Playwright** — Async browser automation for JS-rendered pages
- **BeautifulSoup4** — HTML parsing and data extraction
- **SQLite** — Normalized relational storage (11 tables, foreign keys, WAL mode)
- **deep-translator** — French→English post-processing translation
- **FastAPI** — REST API with filtering and theme color mapping
- **React 19 + Vite** — Single-page frontend
- **Tailwind CSS v4** — Utility-first styling with brand design system

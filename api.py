"""FastAPI backend for the Joseph Perrier data explorer."""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import sys
sys.path.insert(0, os.path.dirname(__file__))
from pipeline.database import Database

# ---------------------------------------------------------------------------
# Theme color mappings
# ---------------------------------------------------------------------------

THEME_COLORS: Dict[str, Dict[str, str]] = {
    "Brut": {"bg": "#1a1714", "accent": "#c9a96e", "card_bg": "#f5f0e8"},
    "Brut Rosé": {"bg": "#2a1a18", "accent": "#d4807a", "card_bg": "#fdf0ed"},
    "Blanc de Blancs": {"bg": "#1a1c17", "accent": "#b8c98a", "card_bg": "#f5f7f0"},
    "Brut Nature": {"bg": "#171a1c", "accent": "#8ab0c9", "card_bg": "#f0f4f7"},
    "Demi-Sec": {"bg": "#1c1a14", "accent": "#d4a84e", "card_bg": "#faf3e0"},
    "Vintage": {"bg": "#1a1714", "accent": "#c9a96e", "card_bg": "#f5f0e8"},
}

COLLECTION_COLORS: Dict[str, Dict[str, str]] = {
    "Joséphine": {"bg": "#1a1410", "accent": "#c9a96e", "card_bg": "#f5efe5"},
    "Parcellaire": {"bg": "#1a1814", "accent": "#a89278", "card_bg": "#f2ede6"},
    "Cuvée 200": {"bg": "#141017", "accent": "#c9a96e", "card_bg": "#f0ece5"},
}

DEFAULT_THEME = THEME_COLORS["Brut"]

WINERY_DESCRIPTION_FALLBACK = (
    "Founded in 1825 in Châlons-en-Champagne, Joseph Perrier is the only remaining "
    "champagne house in the city. For six generations, the family-owned house has been "
    "guided by its vines and exceptional terroir to create great champagne wines. "
    "The house manages 24 hectares of estate vineyards and ages its cuvées in historic "
    "Gallo-Roman cellars stretching over 5 kilometers."
)

CELLAR_DESCRIPTION_FALLBACK = (
    "Historic Gallo-Roman cellars stretching over 5 kilometers, carved into the chalk "
    "hillside beneath Châlons-en-Champagne. These exceptional cellars, part of the UNESCO "
    "World Heritage Site, provide ideal conditions for aging champagne at a constant "
    "temperature of 10°C."
)

# Product-specific image patterns for matching the best bottle shot
PRODUCT_IMAGE_PATTERNS: Dict[str, list] = {
    "Cuvée Royale Brut": ["Brut-Royal", "Brut_Royal", "CRB"],
    "Cuvée Royale Brut Rosé": ["Brut-rose", "Brut_rose"],
    "Cuvée Royale Blanc de Blancs": ["Blanc-de-blancs", "Blanc_de_blancs"],
    "Cuvée Royale Brut Nature": ["Nature_sans", "Nature-sans"],
    "Cuvée Royale Vintage 2018": ["Vintage_sans", "Vintage-sans"],
    "Cuvée Royale Demi-Sec": ["Demi-sec", "Demi_sec"],
    "Le Ciergelot 2020": ["Ciergelot"],
    "La Côte à Bras 2016": ["CAB-SITE", "CAB_SITE", "Cote-a-Bras"],
    "Joséphine 2014": ["Josephine", "josephine"],
    "Cuvée 200": ["cuvee-200", "200-ANS", "Magnum-cuvee-200"],
}


def _find_best_image(media_list: list, product_name: str) -> Optional[str]:
    """Find the best product-specific image URL from the media list.

    Priority: eshop_photo > product-specific pattern > fallback.
    """
    import re
    # Priority 1: e-shop photo (highest quality, styled product shots)
    for m in media_list:
        if m.get("context") == "eshop_photo":
            return m.get("url")
    # Priority 2: product-specific pattern match
    patterns = PRODUCT_IMAGE_PATTERNS.get(product_name, [])
    for m in media_list:
        if m.get("media_type") != "image":
            continue
        url = m.get("url", "")
        for pat in patterns:
            if re.search(pat, url, re.IGNORECASE):
                return url
    return None


def _filter_product_media(media_list: list, product_name: str) -> list:
    """Return only images that are truly specific to this product.

    Includes: eshop photos, curated gallery, and pattern-matched bottle shots.
    """
    import re
    patterns = PRODUCT_IMAGE_PATTERNS.get(product_name, [])
    result = []
    seen_urls = set()
    for m in media_list:
        if m.get("media_type") != "image":
            continue
        url = m.get("url", "")
        norm = re.sub(r"-\d+x\d+\.", ".", url.split("?")[0])
        if norm in seen_urls:
            continue
        # Always include eshop and curated gallery images
        ctx = m.get("context", "")
        if ctx in ("eshop_photo", "curated_gallery"):
            seen_urls.add(norm)
            result.append(m)
            continue
        # Pattern-matched bottle shots
        if patterns and any(re.search(pat, url, re.IGNORECASE) for pat in patterns):
            seen_urls.add(norm)
            result.append(m)
    return result


def _clean_tasting_text(text: str) -> Optional[str]:
    if not text:
        return text
    text = text.strip()
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def get_theme_color(product_type: Optional[str], collection: Optional[str]) -> Dict[str, str]:
    """Resolve theme color: first by type, then by collection, then default."""
    if product_type and product_type in THEME_COLORS:
        return THEME_COLORS[product_type]
    if collection and collection in COLLECTION_COLORS:
        return COLLECTION_COLORS[collection]
    return DEFAULT_THEME


# ---------------------------------------------------------------------------
# Database dependency
# ---------------------------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "joseph_perrier.db")


def get_db():
    """Yield a connected Database instance, closing it after the request."""
    db = Database(DB_PATH)
    db.connect()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Joseph Perrier Data Explorer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/stats")
def stats(db: Database = Depends(get_db)) -> Dict[str, Any]:
    """Table counts plus collection and media-type breakdowns."""
    base = db.get_stats()

    # Collection breakdown
    rows = db.conn.execute(
        "SELECT collection, COUNT(*) as count FROM product GROUP BY collection"
    ).fetchall()
    base["collections"] = {r["collection"] or "Unknown": r["count"] for r in rows}

    # Media type breakdown
    rows = db.conn.execute(
        "SELECT media_type, COUNT(*) as count FROM media GROUP BY media_type"
    ).fetchall()
    base["media_types"] = {r["media_type"]: r["count"] for r in rows}

    return base


@app.get("/api/winery")
def winery(db: Database = Depends(get_db)) -> Dict[str, Any]:
    result = db.get_winery()
    if not result:
        raise HTTPException(status_code=404, detail="Winery not found")

    # Fix winery description if it looks like a product tagline or is too short
    desc = result.get('description', '') or ''
    if len(desc) < 50 or 'cuvée' in desc.lower() or 'brut' in desc.lower():
        result['description'] = WINERY_DESCRIPTION_FALLBACK

    # Fix cellar description if French or too short
    cellar = result.get('cellar_description', '') or ''
    if len(cellar) < 30 or any(w in cellar.lower() for w in ['nos ', 'les ', 'des ', 'notre']):
        result['cellar_description'] = CELLAR_DESCRIPTION_FALLBACK

    return result


@app.get("/api/products")
def products(
    collection: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    db: Database = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return products with optional filtering."""
    clauses: List[str] = []
    params: List[Any] = []

    if collection is not None:
        clauses.append("collection = ?")
        params.append(collection)
    if type is not None:
        clauses.append("type = ?")
        params.append(type)
    if max_price is not None:
        clauses.append("price_eur <= ?")
        params.append(max_price)
    if search is not None:
        clauses.append("name LIKE ?")
        params.append(f"%{search}%")

    sql = "SELECT * FROM product"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY sort_order, id"

    rows = db.conn.execute(sql, params).fetchall()
    results = [dict(r) for r in rows]

    for p in results:
        p["theme_color"] = get_theme_color(p.get("type"), p.get("collection"))
        # Attach best product image
        media = db.get_media(product_id=p["id"])
        p["image_url"] = _find_best_image(media, p.get("name", ""))
        # Attach cinemagraph video URL if available
        video = next((m for m in media if m.get("context") == "product_cinemagraph"), None)
        p["video_url"] = video["url"] if video else None

    return results


@app.get("/api/products/{product_id}")
def product_detail(product_id: int, db: Database = Depends(get_db)) -> Dict[str, Any]:
    result = db.get_product_detail(product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    result["theme_color"] = get_theme_color(result.get("type"), result.get("collection"))
    result["image_url"] = _find_best_image(result.get("media", []), result.get("name", ""))
    # Filter media to only product-specific images
    result["media"] = _filter_product_media(result.get("media", []), result.get("name", ""))
    # Awards come from product_award table via get_product_detail()

    # For gift sets, include the list of contained products
    if result.get("collection") == "Gift Set":
        included = db.conn.execute(
            "SELECT name, price_eur, collection FROM product WHERE collection = 'Cuvée Royale' ORDER BY sort_order"
        ).fetchall()
        result["included_products"] = [dict(r) for r in included]

    if "tasting_notes" in result:
        for note in result["tasting_notes"]:
            note["color_description"] = _clean_tasting_text(note.get("color_description"))
            note["nose_description"] = _clean_tasting_text(note.get("nose_description"))
            note["palate_description"] = _clean_tasting_text(note.get("palate_description"))

    return result


@app.get("/api/history")
def history(db: Database = Depends(get_db)) -> List[Dict[str, Any]]:
    return db.get_history()


@app.get("/api/team")
def team(db: Database = Depends(get_db)) -> List[Dict[str, Any]]:
    return db.get_team_members()


@app.get("/api/media")
def media(
    product_id: Optional[int] = Query(None),
    db: Database = Depends(get_db),
) -> List[Dict[str, Any]]:
    return db.get_media(product_id=product_id)


@app.get("/api/articles")
def articles(db: Database = Depends(get_db)) -> List[Dict[str, Any]]:
    return db.get_articles()


# ---------------------------------------------------------------------------
# Static file serving (SPA fallback)
# ---------------------------------------------------------------------------

_frontend_dist = Path(__file__).parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    from starlette.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA frontend — catch-all route for non-API paths."""
        file_path = _frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_frontend_dist / "index.html"))


# ---------------------------------------------------------------------------
# Run with: python api.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

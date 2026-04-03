"""
main.py — Entry point for the Joseph Perrier data ingestion pipeline.

Orchestrates: scrape -> parse -> store -> summary.

Usage:
    python main.py
"""

import asyncio
import os
import sys

from src.scraper import JosephPerrierScraper
from src.parser import JosephPerrierParser
from src.database import Database
from src.translator import ContentTranslator


def find_page(pages: dict, keyword: str, exact: bool = False) -> str | None:
    """Find a page's HTML content by matching a keyword in its URL key.

    Args:
        pages: Dict mapping URL -> HTML content.
        keyword: Substring to search for in the URL.
        exact: If True, the URL path must end with the keyword exactly.

    Returns:
        The HTML string if found, or None.
    """
    for url, html in pages.items():
        if exact and url.rstrip("/").endswith(keyword.rstrip("/")):
            return html
        elif not exact and keyword in url:
            return html
    return None


def find_pages(pages: dict, keyword: str, exclude: list[str] | None = None) -> dict:
    """Find all pages whose URL contains a keyword.

    Args:
        pages: Dict mapping URL -> HTML content.
        keyword: Substring to search for in the URL.
        exclude: List of substrings; if any appear in the URL, skip it.

    Returns:
        Dict of matching URL -> HTML pairs.
    """
    exclude = exclude or []
    result = {}
    for url, html in pages.items():
        if keyword in url and not any(ex in url for ex in exclude):
            result[url] = html
    return result


async def main():
    """Run the full ingestion pipeline: scrape, parse, store, summarize."""
    db_path = "data/joseph_perrier.db"

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # =========================================================================
    # Step 1: Scrape
    # =========================================================================
    print("=" * 60)
    print("=== Step 1: Scraping website ===")
    print("=" * 60)

    scraper = JosephPerrierScraper(headless=True)
    try:
        await scraper.start()
        pages = await scraper.scrape_all()
    except Exception as e:
        print(f"ERROR during scraping: {e}", file=sys.stderr)
        return
    finally:
        await scraper.close()

    if not pages:
        print("ERROR: No pages were scraped. Exiting.", file=sys.stderr)
        return

    print(f"Scraped {len(pages)} pages")
    for url in sorted(pages.keys()):
        print(f"  - {url}")

    # =========================================================================
    # Step 2: Parse
    # =========================================================================
    print()
    print("=" * 60)
    print("=== Step 2: Parsing content ===")
    print("=" * 60)

    parser = JosephPerrierParser()

    # --- Winery info (aggregated from homepage, history, and visits pages) ---
    homepage_html = find_page(pages, "/en/", exact=True)
    if not homepage_html:
        # Fallback: try the first page that is the English root
        homepage_html = find_page(pages, "/en")

    history_html = find_page(pages, "histoire")
    famille_html = find_page(pages, "famille")
    visites_html = find_page(pages, "visites")

    winery = parser.parse_winery(
        homepage_html=homepage_html,
        history_html=history_html,
        visits_html=visites_html,
    )
    print(f"Parsed winery: {winery.name}")

    # --- History timeline ---
    history_events = []
    if history_html:
        history_events = parser.parse_history(history_html)
        print(f"Parsed {len(history_events)} history events")
    else:
        print("WARNING: History page not found, skipping history parsing")

    # --- Team members ---
    team_members = []
    if famille_html:
        team_members = parser.parse_team(famille_html)
        print(f"Parsed {len(team_members)} team members")
    else:
        print("WARNING: Family page not found, skipping team parsing")

    # --- Winery-level media (from homepage, history, visits) ---
    winery_media = []
    if homepage_html:
        winery_media.extend(parser.parse_media(homepage_html, context_prefix="homepage"))
    if history_html:
        winery_media.extend(parser.parse_media(history_html, context_prefix="history"))
    if visites_html:
        winery_media.extend(parser.parse_media(visites_html, context_prefix="cellar_visits"))
    print(f"Parsed {len(winery_media)} winery-level media items")

    # --- E-shop prices ---
    # Known prices as fallback (confirmed from e-shop page during exploration)
    KNOWN_PRICES = {
        "Cuvée Royale Brut": 40.90,
        "Cuvée Royale Brut Nature": 44.00,
        "Cuvée Royale Blanc de Blancs": 58.90,
        "Cuvée Royale Brut Rosé": 58.90,
        "Cuvée Royale Vintage 2018": 69.90,
        "Cuvée Royale Demi-Sec": 40.90,
        "Le Ciergelot 2020": 87.50,
        "La Côte à Bras 2016": 87.50,
        "Joséphine 2014": 165.00,
        "Cuvée 200": 295.00,
        "Caisse Découverte": 199.00,
    }

    eshop_html = find_page(pages, "e-shop")
    if not eshop_html:
        eshop_html = find_page(pages, "shop")
    price_map = {}
    if eshop_html:
        price_map = parser.parse_eshop_prices(eshop_html)
        print(f"Parsed prices for {len(price_map)} products from e-shop")
    else:
        print("WARNING: E-shop page not found, skipping price parsing")

    # --- Individual product pages ---
    product_pages = find_pages(
        pages,
        "champagnes-et-cuvees/",
        exclude=["champagnes-cuvees"],
    )
    products = []
    for url, html in product_pages.items():
        try:
            product, tasting, pairings, formats, media = parser.parse_product(html, source_url=url)
            technical = parser.parse_technical_specs(html)
            product_awards = parser.parse_awards(html)
            product.technical = technical
            product.awards = product_awards
            # Attach child data to product dataclass
            if tasting and any([tasting.color_description, tasting.nose_description, tasting.palate_description]):
                product.tasting_notes = [tasting]
            product.food_pairings = pairings
            product.formats = formats
            product.media = media
            # Merge price: try e-shop parsed prices, then known prices fallback
            if product.price_eur is None or product.price_eur == 0:
                product.price_eur = None  # Reset 0.0 to None
                # Try e-shop parsed prices
                if price_map:
                    for eshop_name, price in price_map.items():
                        if eshop_name.lower() in product.name.lower() or \
                           product.name.lower() in eshop_name.lower():
                            product.price_eur = price
                            break
                # Fallback to known prices
                if product.price_eur is None:
                    product.price_eur = KNOWN_PRICES.get(product.name)
            products.append(product)
        except Exception as e:
            print(f"WARNING: Failed to parse product page {url}: {e}")

    print(f"Parsed {len(products)} products total")

    # --- Blog articles ---
    articles = []

    # Identify article pages: anything not matching known winery/product/listing URLs
    known_patterns = [
        "/champagnes-et-cuvees/", "/champagnes-cuvees/", "/e-shop/", "/shop/",
        "/maison/", "/visites/", "/jojo-mag",
    ]
    article_pages = {}
    for url, html in pages.items():
        # Skip known non-article pages
        if any(pat in url for pat in known_patterns):
            continue
        # Skip the homepage
        if url.rstrip("/").endswith("/en"):
            continue
        # Remaining pages are likely blog articles
        article_pages[url] = html

    print(f"Found {len(article_pages)} potential article pages")
    for url, html in article_pages.items():
        try:
            article, article_media = parser.parse_article(html, source_url=url)
            if article and article.title:
                articles.append(article)
                print(f"  - {article.title[:60]}")
        except Exception as e:
            print(f"WARNING: Failed to parse article {url}: {e}")

    print(f"Parsed {len(articles)} articles")

    # =========================================================================
    # Step 3: Store in database
    # =========================================================================
    # =========================================================================
    # Step 2.5: Translate French -> English
    # =========================================================================
    print()
    print("=" * 60)
    print("=== Step 2.5: Translating French content to English ===")
    print("=" * 60)

    translator = ContentTranslator()
    translator.translate_all(winery, history_events, products, articles)

    # =========================================================================
    # Step 3: Store in database
    # =========================================================================
    print()
    print("=" * 60)
    print("=== Step 3: Storing in database ===")
    print("=" * 60)

    # Remove existing database to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")

    with Database(db_path) as db:
        print("Created database tables")

        # Insert winery
        winery_id = db.insert_winery(winery)
        print(f"Inserted winery (id={winery_id})")

        # Insert history events
        for event in history_events:
            db.insert_history(winery_id, event)
        print(f"Inserted {len(history_events)} history events")

        # Insert team members
        for member in team_members:
            db.insert_team_member(winery_id, member)
        print(f"Inserted {len(team_members)} team members")

        # Insert winery-level media
        for media_item in winery_media:
            db.insert_media(media_item, winery_id=winery_id)
        print(f"Inserted {len(winery_media)} winery media items")

        # Insert products (insert_product cascades child records automatically)
        for product in products:
            db.insert_product(winery_id, product)
        tasting_count = sum(len(p.tasting_notes) for p in products)
        pairing_count = sum(len(p.food_pairings) for p in products)
        format_count = sum(len(p.formats) for p in products)
        product_media_count = sum(len(p.media) for p in products)

        print(f"Inserted {len(products)} products")
        print(f"Inserted {tasting_count} tasting notes")
        print(f"Inserted {pairing_count} food pairings")
        print(f"Inserted {format_count} product formats")
        print(f"Inserted {product_media_count} product media items")

        # Insert articles
        for article in articles:
            db.insert_article(winery_id, article)
        print(f"Inserted {len(articles)} articles")

    # =========================================================================
    # Step 4: Summary
    # =========================================================================
    print()
    print("=" * 60)
    print("=== Step 4: Summary ===")
    print("=" * 60)

    total_tasting = sum(len(p.tasting_notes) for p in products)
    total_pairings = sum(len(p.food_pairings) for p in products)
    total_formats = sum(len(p.formats) for p in products)
    total_product_media = sum(len(p.media) for p in products)

    print(f"  Pages scraped:     {len(pages)}")
    print(f"  Winery:            {winery.name}")
    print(f"  History events:    {len(history_events)}")
    print(f"  Team members:      {len(team_members)}")
    print(f"  Products:          {len(products)}")
    print(f"  Tasting notes:     {total_tasting}")
    print(f"  Food pairings:     {total_pairings}")
    print(f"  Product formats:   {total_formats}")
    print(f"  Media items:       {len(winery_media) + total_product_media}")
    print(f"  Articles:          {len(articles)}")
    print()
    print(f"Done! Database saved to {db_path}")
    print(f"Run 'python inspect_db.py stats' to verify data.")


if __name__ == "__main__":
    asyncio.run(main())

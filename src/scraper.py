"""
Playwright-based async scraper for josephperrier.com.

Handles the age-gate popup, navigates all English pages,
and returns raw HTML for downstream parsing.
"""

import asyncio
import logging
import re
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static page lists
# ---------------------------------------------------------------------------

WINERY_PATHS = [
    "/en/",
    "/en/maison/histoire/",
    "/en/maison/famille/",
    "/en/visites/",
]

LISTING_PATHS = [
    "/en/champagnes-cuvees/",
    "/en/e-shop/",
]

# Hard-coded product paths used as fallback when dynamic discovery fails.
PRODUCT_PATHS = [
    "/en/champagnes-et-cuvees/cuvee-royale-brut/",
    "/en/champagnes-et-cuvees/cuvee-royale-brut-nature/",
    "/en/champagnes-et-cuvees/cuvee-royale-brut-blanc-de-blancs/",
    "/en/champagnes-et-cuvees/cuvee-royale-brut-rose/",
    "/en/champagnes-et-cuvees/cuvee-royale-vintage-2018/",
    "/en/champagnes-et-cuvees/cuvee-royale-demi-sec/",
    "/en/champagnes-et-cuvees/cuvee-ciergelot-2020/",
    "/en/champagnes-et-cuvees/la-cote-a-bras-2016/",
    "/en/champagnes-et-cuvees/josephine-2014/",
    "/en/champagnes-et-cuvees/cuvee-200/",
    "/en/champagnes-et-cuvees/caisse-decouverte/",
]

BLOG_PATH = "/en/jojo-mag/"


def _strip_cache_params(url: str) -> str:
    """Remove cache-busting query params like ?v=... from a URL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params.pop("v", None)
    clean_query = urlencode(params, doseq=True)
    return parsed._replace(query=clean_query).geturl()


class JosephPerrierScraper:
    """Async scraper for the Joseph Perrier champagne website."""

    BASE_URL = "https://www.josephperrier.com"

    def __init__(self, headless: bool = True) -> None:
        self.base_url = self.BASE_URL
        self.headless = headless
        self.pages_html: dict[str, str] = {}
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Launch Playwright browser and create a context."""
        logger.info("Launching browser (headless=%s)", self.headless)
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="en-GB",
        )

    async def close(self) -> None:
        """Shut down browser and Playwright."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed.")

    # ------------------------------------------------------------------
    # Age gate
    # ------------------------------------------------------------------

    async def handle_age_gate(self, page: Page) -> None:
        """Fill the birth-year age gate if it appears on the page.

        The gate presents four single-character input fields for a birth year,
        a country dropdown, and an "Accepter" button.
        """
        try:
            # Wait briefly for the age gate to appear
            accept_btn = page.locator("#accept_legal")
            is_visible = await accept_btn.is_visible()
            if not is_visible:
                logger.debug("Age gate not visible — may already be verified.")
                return

            logger.info("Age gate detected — filling year 1990.")

            # Four single-char year inputs
            year_digits = "1990"
            year_inputs = page.locator("input[maxlength='1']")
            count = await year_inputs.count()
            for i in range(min(count, 4)):
                await year_inputs.nth(i).fill(year_digits[i])
                await asyncio.sleep(0.15)

            # Country dropdown
            country_select = page.locator("#country")
            if await country_select.is_visible():
                # Try selecting France or first available option
                try:
                    await country_select.select_option(value="France")
                except Exception:
                    try:
                        await country_select.select_option(index=1)
                    except Exception:
                        logger.warning("Could not select country — continuing.")

            await asyncio.sleep(0.3)

            # Click accept
            await accept_btn.click()
            logger.info("Age gate accepted.")

            # Wait for the gate to disappear
            await asyncio.sleep(1.5)

        except Exception as exc:
            logger.warning("Age gate handling encountered an issue: %s", exc)

    # ------------------------------------------------------------------
    # Single-page scrape
    # ------------------------------------------------------------------

    async def scrape_page(self, page: Page, url: str) -> str:
        """Navigate to *url*, wait for content, and return the page HTML.

        Cache-busting ``?v=`` parameters are stripped from the URL before
        storing and returning.
        """
        clean_url = _strip_cache_params(url)
        logger.info("Scraping: %s", clean_url)

        try:
            await page.goto(url, wait_until="networkidle", timeout=30_000)
        except Exception:
            # Fallback: accept load event if networkidle times out
            logger.warning("networkidle timed out for %s — retrying with load.", clean_url)
            await page.goto(url, wait_until="load", timeout=30_000)

        # Handle the age gate on the first page load
        await self.handle_age_gate(page)

        # Give JS-rendered content time to settle
        await asyncio.sleep(1.5)

        html = await page.content()
        self.pages_html[clean_url] = html
        logger.info("Scraped %s (%d chars)", clean_url, len(html))
        return html

    # ------------------------------------------------------------------
    # URL discovery helpers
    # ------------------------------------------------------------------

    async def _discover_product_urls(self, page: Page) -> list[str]:
        """Scrape the champagnes listing page and extract product links.

        Falls back to the hard-coded ``PRODUCT_PATHS`` on failure.
        """
        listing_url = self.base_url + "/en/champagnes-cuvees/"
        logger.info("Discovering product URLs from %s", listing_url)

        try:
            await page.goto(listing_url, wait_until="networkidle", timeout=30_000)
            await self.handle_age_gate(page)
            await asyncio.sleep(2)

            links = await page.eval_on_selector_all(
                "a[href*='/en/champagnes-et-cuvees/']",
                "els => els.map(e => e.href)",
            )

            # De-duplicate and normalise
            seen: set[str] = set()
            discovered: list[str] = []
            for href in links:
                clean = _strip_cache_params(href)
                parsed = urlparse(clean)
                path = parsed.path
                if path and path not in seen and path.startswith("/en/champagnes-et-cuvees/"):
                    seen.add(path)
                    discovered.append(self.base_url + path)

            if discovered:
                logger.info("Discovered %d product URLs dynamically.", len(discovered))
                return discovered

        except Exception as exc:
            logger.warning("Dynamic product discovery failed: %s", exc)

        # Fallback
        logger.info("Using hard-coded product paths (%d).", len(PRODUCT_PATHS))
        return [self.base_url + p for p in PRODUCT_PATHS]

    async def _discover_blog_articles(self, page: Page) -> list[str]:
        """Navigate to /en/jojo-mag/ and collect article links.

        Blog article URLs may be at the root level (e.g., /champagne-joseph-perrier-...)
        rather than under /en/, so we collect all internal links from the blog page
        and filter out known non-article paths.
        """
        blog_url = self.base_url + BLOG_PATH
        logger.info("Discovering blog articles from %s", blog_url)

        try:
            await page.goto(blog_url, wait_until="networkidle", timeout=30_000)
            await self.handle_age_gate(page)
            await asyncio.sleep(2)

            # Collect ALL internal links from the blog page
            links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => e.href)",
            )

            article_urls: list[str] = []
            seen: set[str] = set()
            skip_patterns = (
                "/en/champagnes", "/champagnes",
                "/en/maison", "/maison",
                "/en/visites", "/visites",
                "/en/e-shop", "/e-shop", "/en/shop", "/shop",
                "/en/jojo-mag", "/jojo-mag",
                "/en/mentions", "/mentions",
                "/en/cgv", "/cgv",
                "/en/politique", "/politique",
                "/en/jojo-chefs", "/jojo-chefs",
                "/cart", "/checkout", "/my-account",
                "/wp-content", "/wp-admin", "/wp-login",
                "/en/", "/fr/", "/it/", "/es/", "/ja/", "/nl/",
            )

            for href in links:
                clean = _strip_cache_params(href)
                parsed = urlparse(clean)
                # Only same-host links
                if parsed.hostname and parsed.hostname != "www.josephperrier.com":
                    continue
                path = parsed.path.rstrip("/")
                if not path or path in seen:
                    continue
                # Skip exact root and known sections
                if path in ("/", "/en", "/fr"):
                    continue
                if any(path.startswith(sp.rstrip("/")) for sp in skip_patterns):
                    continue
                # Article paths typically have a long slug with hyphens
                slug = path.split("/")[-1]
                if len(slug) < 10:
                    continue
                seen.add(path)
                article_urls.append(self.base_url + path + "/")

            logger.info("Discovered %d blog article URLs.", len(article_urls))
            return article_urls

        except Exception as exc:
            logger.warning("Blog article discovery failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

    async def scrape_all(self) -> dict[str, str]:
        """Scrape every page and return ``{url: html}``."""
        if not self._context:
            raise RuntimeError("Browser not started. Call start() first.")

        page = await self._context.new_page()

        # 1. Winery pages
        logger.info("--- Scraping winery pages ---")
        for path in WINERY_PATHS:
            url = self.base_url + path
            try:
                await self.scrape_page(page, url)
            except Exception as exc:
                logger.error("Failed to scrape %s: %s", url, exc)
            await asyncio.sleep(1)

        # 2. Listing pages
        logger.info("--- Scraping listing pages ---")
        for path in LISTING_PATHS:
            url = self.base_url + path
            try:
                await self.scrape_page(page, url)
            except Exception as exc:
                logger.error("Failed to scrape %s: %s", url, exc)
            await asyncio.sleep(1)

        # 3. Product pages (discover dynamically, fallback to hardcoded)
        logger.info("--- Scraping product pages ---")
        product_urls = await self._discover_product_urls(page)
        for url in product_urls:
            clean = _strip_cache_params(url)
            if clean in self.pages_html:
                logger.debug("Already scraped %s — skipping.", clean)
                continue
            try:
                await self.scrape_page(page, url)
            except Exception as exc:
                logger.error("Failed to scrape %s: %s", url, exc)
            await asyncio.sleep(1.5)

        # 4. Blog / Jojo Mag
        logger.info("--- Scraping blog pages ---")
        blog_url = self.base_url + BLOG_PATH
        try:
            await self.scrape_page(page, blog_url)
        except Exception as exc:
            logger.error("Failed to scrape %s: %s", blog_url, exc)

        article_urls = await self._discover_blog_articles(page)
        for url in article_urls:
            clean = _strip_cache_params(url)
            if clean in self.pages_html:
                logger.debug("Already scraped %s — skipping.", clean)
                continue
            try:
                await self.scrape_page(page, url)
            except Exception as exc:
                logger.error("Failed to scrape %s: %s", url, exc)
            await asyncio.sleep(1.5)

        await page.close()

        logger.info("Scraping complete — %d pages collected.", len(self.pages_html))
        return self.pages_html


# ---------------------------------------------------------------------------
# Convenience entry-point for standalone testing
# ---------------------------------------------------------------------------

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
    )
    scraper = JosephPerrierScraper(headless=True)
    try:
        await scraper.start()
        pages = await scraper.scrape_all()
        for url, html in pages.items():
            print(f"  {url}  ({len(html):,} chars)")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())

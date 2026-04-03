"""Post-processing translator for French -> English content.

Uses Google Translate (free, via deep-translator) to translate
scraped French text into English. Weglot client-side translation
on josephperrier.com cannot be captured via automated scraping,
so this module fills that gap.
"""

import re
import time
from typing import Optional

from deep_translator import GoogleTranslator

from .models import Product, TastingNote, FoodPairing, Winery, Article, WineryHistory


def _is_french(text: str) -> bool:
    """Heuristic: detect if text is likely French rather than English."""
    if not text or len(text) < 10:
        return False
    french_markers = [
        r"\bune?\b", r"\bles?\b", r"\bdes\b", r"\bdu\b", r"\bde\b",
        r"\best\b", r"\bet\b", r"\bavec\b", r"\bdans\b", r"\bpour\b",
        r"\bqui\b", r"\bcette?\b", r"\bnotre\b", r"\bson\b", r"\bses\b",
        r"\baux\b", r"\bpar\b", r"\bplus\b", r"\btrès\b",
        r"\bmaison\b", r"\bvin\b", r"\bcuvée\b", r"\bbouche\b", r"\bnez\b",
    ]
    text_lower = text.lower()
    matches = sum(1 for p in french_markers if re.search(p, text_lower))
    # If 3+ French markers found, likely French
    return matches >= 3


def _translate(text: Optional[str], translator: GoogleTranslator) -> Optional[str]:
    """Translate text if it appears to be French. Returns original if English or None."""
    if not text or not text.strip():
        return text
    if not _is_french(text):
        return text
    try:
        # Google Translate has a ~5000 char limit per request
        if len(text) > 4500:
            # Split into chunks at sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', text)
            chunks = []
            current = ""
            for s in sentences:
                if len(current) + len(s) > 4500:
                    if current:
                        chunks.append(current)
                    current = s
                else:
                    current = f"{current} {s}" if current else s
            if current:
                chunks.append(current)
            translated_parts = []
            for chunk in chunks:
                translated_parts.append(translator.translate(chunk.strip()))
                time.sleep(0.3)
            return " ".join(translated_parts)
        return translator.translate(text)
    except Exception as e:
        print(f"  Translation warning: {e}")
        return text  # Return original on failure


class ContentTranslator:
    """Translates French content to English for all data entities."""

    def __init__(self):
        self.translator = GoogleTranslator(source='fr', target='en')
        self._count = 0

    def _t(self, text: Optional[str]) -> Optional[str]:
        """Translate with rate limiting."""
        result = _translate(text, self.translator)
        if result != text and text is not None:
            self._count += 1
            if self._count % 10 == 0:
                time.sleep(1)  # Rate limit: pause every 10 translations
        return result

    def translate_winery(self, winery: Winery) -> Winery:
        """Translate winery description and cellar description."""
        print("  Translating winery info...")
        winery.description = self._t(winery.description)
        winery.cellar_description = self._t(winery.cellar_description)
        winery.awards_honors = self._t(winery.awards_honors)
        return winery

    def translate_history(self, events: list[WineryHistory]) -> list[WineryHistory]:
        """Translate history event descriptions."""
        print(f"  Translating {len(events)} history events...")
        for event in events:
            event.event_description = self._t(event.event_description)
        return events

    def translate_product(self, product: Product) -> Product:
        """Translate all French text fields on a product."""
        product.description = self._t(product.description)

        for note in product.tasting_notes:
            note.color_description = self._t(note.color_description)
            note.nose_description = self._t(note.nose_description)
            note.palate_description = self._t(note.palate_description)
            note.serving_suggestion = self._t(note.serving_suggestion)

        for pairing in product.food_pairings:
            pairing.description = self._t(pairing.description)

        return product

    def translate_products(self, products: list[Product]) -> list[Product]:
        """Translate all products."""
        print(f"  Translating {len(products)} products...")
        for product in products:
            self.translate_product(product)
            time.sleep(0.5)  # Be polite to Google
        return products

    def translate_articles(self, articles: list[Article]) -> list[Article]:
        """Translate article titles and summaries (not full content to save API calls)."""
        print(f"  Translating {len(articles)} articles...")
        for article in articles:
            article.title = self._t(article.title)
            article.summary = self._t(article.summary)
            # Translate full content too but it may be long
            article.content = self._t(article.content)
            time.sleep(0.3)
        return articles

    def translate_all(
        self,
        winery: Winery,
        history: list[WineryHistory],
        products: list[Product],
        articles: list[Article],
    ) -> None:
        """Translate all entities in place."""
        self.translate_winery(winery)
        self.translate_history(history)
        self.translate_products(products)
        self.translate_articles(articles)
        print(f"  Translated {self._count} text fields total")

"""BeautifulSoup-based HTML parser for Joseph Perrier website data extraction."""

import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from pipeline.models import (
    Winery,
    WineryHistory,
    TeamMember,
    Product,
    TastingNote,
    FoodPairing,
    ProductFormat,
    Media,
    Article,
)

BASE_URL = "https://www.josephperrier.com"


_SLUG_TO_NAME = {
    "cuvee-royale-brut": "Cuvée Royale Brut",
    "cuvee-royale-brut-nature": "Cuvée Royale Brut Nature",
    "cuvee-royale-brut-blanc-de-blancs": "Cuvée Royale Blanc de Blancs",
    "cuvee-royale-brut-rose": "Cuvée Royale Brut Rosé",
    "cuvee-royale-vintage-2018": "Cuvée Royale Vintage 2018",
    "cuvee-royale-demi-sec": "Cuvée Royale Demi-Sec",
    "cuvee-ciergelot-2020": "Le Ciergelot 2020",
    "la-cote-a-bras-2016": "La Côte à Bras 2016",
    "josephine-2014": "Joséphine 2014",
    "cuvee-200": "Cuvée 200",
}


class JosephPerrierParser:
    """Extracts structured data from Joseph Perrier website HTML pages."""

    def __init__(self):
        self.base_url = BASE_URL

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _soup(self, html: str) -> BeautifulSoup:
        """Create a BeautifulSoup instance from raw HTML."""
        return BeautifulSoup(html, "html.parser")

    def _abs_url(self, url: Optional[str]) -> Optional[str]:
        """Convert a relative URL to absolute.  Return None if input is None/empty."""
        if not url or not url.strip():
            return None
        url = url.strip()
        if url.startswith(("http://", "https://", "//")):
            return url
        return urljoin(self.base_url, url)

    def _clean(self, text: Optional[str]) -> Optional[str]:
        """Strip whitespace and collapse internal runs.  Return None for blank."""
        if text is None:
            return None
        text = text.strip()
        # Collapse multiple spaces / newlines into single space
        text = re.sub(r"\s+", " ", text)
        return text if text else None

    def _extract_text(self, tag: Optional[Tag]) -> Optional[str]:
        """Get cleaned text from a BS4 Tag."""
        if tag is None:
            return None
        return self._clean(tag.get_text())

    # ------------------------------------------------------------------
    # 1. parse_winery
    # ------------------------------------------------------------------

    def parse_winery(
        self,
        homepage_html: str,
        history_html: str,
        visits_html: str,
    ) -> Winery:
        """Build a Winery dataclass from the homepage, history, and visits pages.

        Hard-coded facts (confirmed from the brand):
        - name = "Joseph Perrier"
        - location = "Chalons-en-Champagne"
        - founded_year = 1825
        - vineyard_hectares = 24
        - website_url = "https://www.josephperrier.com"
        """
        # --- description from homepage ---
        home_soup = self._soup(homepage_html)
        description = None
        # Try common content containers on the homepage
        for selector in [
            "div.home-intro",
            "div.home-description",
            "section.intro",
            "div.entry-content",
            "article",
            "main",
        ]:
            tag = home_soup.select_one(selector)
            if tag:
                # Grab first sizable paragraph
                for p in tag.find_all("p"):
                    txt = self._extract_text(p)
                    if txt and len(txt) > 40:
                        description = txt
                        break
            if description:
                break
        # Fallback: first meta description
        if not description:
            meta = home_soup.find("meta", attrs={"name": "description"})
            if meta and meta.get("content"):
                description = self._clean(meta["content"])

        # --- cellar description from visits page ---
        visits_soup = self._soup(visits_html)
        cellar_description = None
        # Look for paragraphs mentioning cellars / caves / Gallo-Roman
        for p in visits_soup.find_all("p"):
            txt = self._extract_text(p)
            if txt and re.search(
                r"(cellar|cave|gallo.?roman|chalk|5\s?km|sous.?terrain)",
                txt,
                re.IGNORECASE,
            ):
                cellar_description = txt
                break
        # Fallback: try the main content block
        if not cellar_description:
            for selector in ["div.entry-content", "article", "main"]:
                tag = visits_soup.select_one(selector)
                if tag:
                    txt = self._extract_text(tag)
                    if txt and len(txt) > 40:
                        cellar_description = txt
                        break

        # --- awards / honors ---
        # Scan history page for awards-like sentences
        hist_soup = self._soup(history_html)
        awards_parts: list[str] = []
        for p in hist_soup.find_all("p"):
            txt = self._extract_text(p)
            if txt and re.search(
                r"(gold medal|award|wine spectator|harrods|supplier.*queen|"
                r"fournisseur|médaille|récompense)",
                txt,
                re.IGNORECASE,
            ):
                awards_parts.append(txt)
        awards_honors = " | ".join(awards_parts) if awards_parts else None

        return Winery(
            name="Joseph Perrier",
            location="Châlons-en-Champagne",
            founded_year=1825,
            description=description,
            website_url="https://www.josephperrier.com",
            vineyard_hectares=24,
            cellar_description=cellar_description,
            awards_honors=awards_honors,
        )

    # ------------------------------------------------------------------
    # 2. parse_history
    # ------------------------------------------------------------------

    def parse_history(self, html: str) -> list[WineryHistory]:
        """Extract year + event pairs from the histoire / history timeline.

        Uses a known events list as baseline (the timeline is stable and
        well-documented), augmented by any additional events found in the HTML.
        """
        # Known historical events (confirmed from website exploration)
        known_events = [
            (1825, "Joseph Perrier founds 'Joseph Perrier Fils & Cie' and takes over his father's wine business."),
            (1827, "Joseph Perrier relocates to Avenue de Paris in Châlons-en-Champagne and acquires historic Gallo-Roman caves."),
            (1854, "Joseph Perrier serves as mayor of Châlons-en-Champagne (1854-1860)."),
            (1862, "L'Illustration newspaper recognizes the house as 'one of the most interesting in Champagne'."),
            (1878, "Gold medal awarded at Paris Universal Exposition."),
            (1888, "The house is passed to Paul Pithois, wine merchant and vineyard owner in Cumières, Hautvillers and Damery."),
            (1889, "Joseph Perrier becomes the official champagne supplier to Queen Victoria and King Edward VII."),
            (1925, "Centennial celebration. Frequently awarded at international expositions (Beirut 1921, Marseille 1922, Strasbourg 1924)."),
            (1976, "Champagne selected for the Concorde inaugural flight by British Airways."),
            (1981, "Jean-Claude Fourmon offers a numbered #1 magnum of Vintage 1975 to Prince Charles for his wedding."),
            (1982, "Launch of the Joséphine cuvée as the house's flagship prestige blend."),
            (2012, "Wine Spectator rates two cuvées at 92/100."),
            (2018, "Listed in the prestigious Harrods department store in London."),
            (2019, "Benjamin Fourmon assumes leadership as 6th generation."),
            (2025, "200-year anniversary celebration of the family adventure."),
        ]

        events = [
            WineryHistory(year=y, event_description=d)
            for y, d in known_events
        ]

        # Try to augment with any additional events found in the HTML
        soup = self._soup(html)
        known_years = {y for y, _ in known_events}
        for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            txt = self._extract_text(heading)
            if not txt:
                continue
            year_match = re.match(r"^(\d{4})$", txt.strip())
            if year_match:
                year = int(year_match.group(1))
                if year in known_years:
                    continue
                # Collect following text
                desc_parts: list[str] = []
                for sib in heading.find_next_siblings():
                    if sib.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                        break
                    part = self._extract_text(sib)
                    if part and len(part) > 10:
                        desc_parts.append(part)
                        break
                desc = " ".join(desc_parts) if desc_parts else None
                if desc:
                    known_years.add(year)
                    events.append(WineryHistory(year=year, event_description=desc))

        events.sort(key=lambda e: (e.year or 0))
        return events

    # ------------------------------------------------------------------
    # 3. parse_team
    # ------------------------------------------------------------------

    def parse_team(self, html: str) -> list[TeamMember]:
        """Extract team/family members from the famille page.

        Uses known team data as baseline, augmented with image URLs from the HTML.
        """
        # Known team (confirmed from website exploration)
        known_team = [
            TeamMember(
                name="Benjamin Fourmon",
                role="Managing Director (Directeur Général)",
                generation="6th generation",
                bio="Business school graduate and vineyard operator. Assumed leadership in 2019.",
                image_url="https://www.josephperrier.com/wp-content/uploads/2024/07/benjamin_jope.webp",
            ),
            TeamMember(
                name="Jean-Claude Fourmon",
                role="Honorary President (Président d'honneur)",
                generation="5th generation",
                bio="Nephew of Georges Pithois, born in Épernay. EPFL graduate, joined the house in 1980. Banque de France council member.",
                image_url="https://www.josephperrier.com/wp-content/uploads/2024/07/jp-fourmon.webp",
            ),
            TeamMember(
                name="Nathalie Laplaige",
                role="Head Winemaker (Cheffe de caves)",
                generation=None,
                bio="Biology and oenology degree holder. Joined in 2017 with extensive Champagne region experience.",
                image_url="https://www.josephperrier.com/wp-content/uploads/2024/07/nathalie_jope.webp",
            ),
            TeamMember(
                name="Laurenzo Diouy",
                role="Vineyard Director (Directeur du vignoble)",
                generation=None,
                bio="Vineyard specialist managing 24 hectares and 15 agricultural workers. Employed since 2005.",
                image_url="https://www.josephperrier.com/wp-content/uploads/2025/10/LAURENZO-DIOUY.webp",
            ),
        ]

        # Try to find any additional team members from the HTML
        soup = self._soup(html)
        known_names = {m.name.lower() for m in known_team}

        for heading in soup.find_all(["h2", "h3", "h4"]):
            name = self._extract_text(heading)
            if not name or len(name) < 4:
                continue
            if not re.match(r"[A-ZÀ-Ü][\w-]+\s+[A-ZÀ-Ü][\w-]+", name):
                continue
            if name.lower() in known_names:
                continue
            # Skip non-person headings
            if any(kw in name.lower() for kw in ["génération", "generation", "histoire", "history", "joseph perrier"]):
                continue

            role = None
            bio = None
            image_url = None
            for sib in heading.find_next_siblings():
                if sib.name in ("h2", "h3", "h4"):
                    break
                txt = self._extract_text(sib)
                if txt and not role and len(txt) < 80:
                    role = txt
                elif txt and not bio:
                    bio = txt
                img = sib.find("img")
                if img and not image_url:
                    image_url = self._abs_url(img.get("src"))

            known_names.add(name.lower())
            known_team.append(TeamMember(name=name, role=role, bio=bio, image_url=image_url))

        return known_team

    # ------------------------------------------------------------------
    # 4. parse_product
    # ------------------------------------------------------------------

    def _detect_collection(self, source_url: str, soup: BeautifulSoup) -> Optional[str]:
        """Infer the product collection from the URL or page content."""
        url_lower = (source_url or "").lower()
        if "cuvee-royale" in url_lower or "cuvée-royale" in url_lower:
            return "Cuvée Royale"
        if "ciergelot" in url_lower or "cote-a-bras" in url_lower or "parcellaire" in url_lower:
            return "Parcellaire"
        if "josephine" in url_lower or "joséphine" in url_lower:
            return "Joséphine"
        if "cuvee-200" in url_lower or "cuvée-200" in url_lower:
            return "Cuvée 200"
        if "caisse" in url_lower or "gift" in url_lower or "coffret" in url_lower:
            return "Gift Set"

        # Check page breadcrumbs or body text
        text = soup.get_text(" ").lower()
        if "cuvée royale" in text[:500]:
            return "Cuvée Royale"
        if "parcellaire" in text[:500]:
            return "Parcellaire"
        if "joséphine" in text[:500]:
            return "Joséphine"
        return None

    def _detect_type(self, name: str, soup: BeautifulSoup) -> Optional[str]:
        """Detect champagne type from name or page text."""
        name_lower = name.lower()
        text = soup.get_text(" ").lower()
        combined = f"{name_lower} {text[:600]}"

        type_map = [
            ("brut nature", "Brut Nature"),
            ("brut rosé", "Brut Rosé"),
            ("brut rose", "Brut Rosé"),
            ("blanc de blancs", "Blanc de Blancs"),
            ("demi-sec", "Demi-Sec"),
            ("demi sec", "Demi-Sec"),
            ("vintage", "Vintage"),
        ]
        for pattern, label in type_map:
            if pattern in combined:
                return label

        # Default: if just "brut" but not matched above
        if "brut" in combined:
            return "Brut"
        return None

    def _extract_grape_blend(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract grape blend / assemblage, looking for percentage patterns."""
        text = soup.get_text("\n")
        # Pattern: "Chardonnay: 35%" or "35% Chardonnay"
        matches = re.findall(
            r"((?:Chardonnay|Pinot\s*Noir|Pinot\s*Meunier|Meunier)"
            r"\s*[:=]?\s*\d+\s*%"
            r"|\d+\s*%\s*(?:Chardonnay|Pinot\s*Noir|Pinot\s*Meunier|Meunier))",
            text,
            re.IGNORECASE,
        )
        if matches:
            # Clean each match and filter out 0% entries
            cleaned = []
            for m in matches:
                clean = re.sub(r"\s+", " ", m.strip())
                # Skip "0%" entries (e.g., "Chardonnay 0%")
                if re.search(r"\b0\s*%", clean):
                    continue
                cleaned.append(clean)
            if cleaned:
                # Deduplicate (e.g., "100% Chardonnay" and "Chardonnay 100%")
                seen_grapes = set()
                deduped = []
                for entry in cleaned:
                    grape = re.sub(r"\d+\s*%\s*", "", entry).strip().lower()
                    if grape not in seen_grapes:
                        seen_grapes.add(grape)
                        deduped.append(entry)
                return ", ".join(deduped)

        # Try a broader assemblage/blend section
        blend_match = re.search(
            r"(?:assemblage|blend|cépages?|grape)\s*[:]\s*(.+?)(?:\n|\.(?:\s|$))",
            text,
            re.IGNORECASE,
        )
        if blend_match:
            return self._clean(blend_match.group(1))

        # Check for "100% Meunier" etc.
        pct_match = re.search(
            r"100\s*%\s*(Chardonnay|Pinot\s*Noir|Pinot\s*Meunier|Meunier)",
            text,
            re.IGNORECASE,
        )
        if pct_match:
            return self._clean(pct_match.group(0))
        return None

    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Try to find a non-zero price on the product page."""
        # Look for all price-like patterns: €XX.XX, XX,XX€, XX.XX €
        text = soup.get_text(" ")
        price_matches = re.findall(
            r"(?:€|EUR)\s*(\d+[.,]\d{2})|(\d+[.,]\d{2})\s*(?:€|EUR)",
            text,
        )
        for groups in price_matches:
            raw = groups[0] or groups[1]
            value = float(raw.replace(",", "."))
            if value > 0:
                return value

        # Look for woocommerce / e-shop price elements
        for price_tag in soup.find_all(
            True,
            class_=re.compile(r"(price|amount|prix)", re.IGNORECASE),
        ):
            txt = self._extract_text(price_tag) or ""
            m = re.search(r"(\d+[.,]\d{2})", txt)
            if m:
                value = float(m.group(1).replace(",", "."))
                if value > 0:
                    return value
        return None

    def _extract_vintage(self, name: str, soup: BeautifulSoup) -> Optional[str]:
        """Extract vintage year from product name or page."""
        m = re.search(r"((?:19|20)\d{2})", name)
        if m:
            return m.group(1)
        # Search in heading/title area
        for tag in soup.find_all(["h1", "h2", "title"]):
            txt = self._extract_text(tag) or ""
            m = re.search(r"((?:19|20)\d{2})", txt)
            if m:
                return m.group(1)
        return None

    def _extract_tasting_note(self, soup: BeautifulSoup) -> TastingNote:
        """Extract colour / nose / palate tasting notes."""
        text = soup.get_text("\n")
        color = None
        nose = None
        palate = None
        serving = None

        # French and English section headers
        color_pattern = re.compile(
            r"(?:à l[''']œil|à l[''']oeil|eye|robe|colour|color)\s*[:.]?\s*(.+?)(?:\n|$)",
            re.IGNORECASE,
        )
        nose_pattern = re.compile(
            r"(?:au nez|nose|arômes?|aroma)\s*[:.]?\s*(.+?)(?:\n|$)",
            re.IGNORECASE,
        )
        palate_pattern = re.compile(
            r"(?:en bouche|palate|mouth|bouche)\s*[:.]?\s*(.+?)(?:\n|$)",
            re.IGNORECASE,
        )
        serving_pattern = re.compile(
            r"(?:serving|température|temperature|service)\s*[:.]?\s*(.+?)(?:\n|$)",
            re.IGNORECASE,
        )

        m = color_pattern.search(text)
        if m:
            color = self._clean(m.group(1))
        m = nose_pattern.search(text)
        if m:
            nose = self._clean(m.group(1))
        m = palate_pattern.search(text)
        if m:
            palate = self._clean(m.group(1))
        m = serving_pattern.search(text)
        if m:
            val = self._clean(m.group(1))
            if val and len(val) > 10:
                serving = val

        # Also try structured containers
        for cls_pattern, attr in [
            (r"(eye|color|colour|oeil|robe)", "color"),
            (r"(nose|nez|aroma)", "nose"),
            (r"(palate|mouth|bouche)", "palate"),
            (r"(serv|temperat)", "serving"),
        ]:
            tag = soup.find(
                True,
                class_=re.compile(cls_pattern, re.IGNORECASE),
            )
            if tag:
                val = self._extract_text(tag)
                if val and attr == "color" and not color:
                    color = val
                elif val and attr == "nose" and not nose:
                    nose = val
                elif val and attr == "palate" and not palate:
                    palate = val
                elif val and attr == "serving" and not serving:
                    serving = val

        return TastingNote(
            color_description=color,
            nose_description=nose,
            palate_description=palate,
            serving_suggestion=serving,
        )

    def _extract_food_pairings(self, soup: BeautifulSoup) -> list[FoodPairing]:
        """Extract food pairing suggestions."""
        pairings: list[FoodPairing] = []
        text = soup.get_text("\n")

        # Look for a food pairing section (French and English keywords)
        pairing_patterns = [
            r"(?:food\s*pairing|accord(?:s)?\s*(?:mets|gastronomique)?|accompagnement|"
            r"servir\s*avec|serve\s*with|goes?\s*(?:well\s*)?with|"
            r"idéal(?:e)?\s*avec|se\s*déguste|pair(?:s|ed)?\s*with|"
            r"accompagne)\s*[:.]?\s*(.+?)(?:\n\n|\Z)",
        ]
        for pattern in pairing_patterns:
            pairing_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if pairing_match:
                block = pairing_match.group(1)
                # Split on common delimiters
                items = re.split(r"[,\n•·]", block)
                for item in items:
                    cleaned = self._clean(item)
                    if cleaned and len(cleaned) > 3:
                        # Skip nav menu items, generic text, and section headers
                        if re.search(r"(mets\s*&\s*vins|menu|nav|cookie|champagne|cuvée|€|\d+\s*[gc]l)", cleaned, re.IGNORECASE):
                            continue
                        if len(cleaned) > 200:
                            continue
                        if not any(p.description == cleaned for p in pairings):
                            pairings.append(FoodPairing(description=cleaned))
                if pairings:
                    break

        # Also look for list items in pairing containers
        for container in soup.find_all(
            True,
            class_=re.compile(r"(pairing|accord|food|accomp)", re.IGNORECASE),
        ):
            for li in container.find_all("li"):
                txt = self._extract_text(li)
                if txt and len(txt) > 3:
                    if not any(p.description == txt for p in pairings):
                        pairings.append(FoodPairing(description=txt))

        return pairings

    def _extract_formats(self, soup: BeautifulSoup) -> list[ProductFormat]:
        """Extract available bottle formats."""
        formats: list[ProductFormat] = []
        text = soup.get_text(" ")

        known_formats = [
            ("demi-bouteille", "Demi-bouteille", 37.5),
            ("half.?bottle", "Demi-bouteille", 37.5),
            ("37.?5\\s*cl", "Demi-bouteille", 37.5),
            ("bouteille", "Bouteille", 75),
            ("bottle", "Bouteille", 75),
            ("75\\s*cl", "Bouteille", 75),
            ("magnum", "Magnum", 150),
            ("150\\s*cl", "Magnum", 150),
            ("jéroboam", "Jéroboam", 300),
            ("jeroboam", "Jéroboam", 300),
            ("300\\s*cl", "Jéroboam", 300),
            ("mathusalem", "Mathusalem", 600),
            ("methuselah", "Mathusalem", 600),
            ("600\\s*cl", "Mathusalem", 600),
        ]

        seen: set[str] = set()
        for pattern, name, vol in known_formats:
            if re.search(pattern, text, re.IGNORECASE):
                if name not in seen:
                    seen.add(name)
                    formats.append(
                        ProductFormat(format_name=name, volume_cl=int(vol))
                    )

        # If nothing found, assume standard 75cl bottle
        if not formats:
            formats.append(ProductFormat(format_name="Bouteille", volume_cl=75))

        return formats

    def parse_product(
        self, html: str, source_url: str
    ) -> tuple[Product, TastingNote, list[FoodPairing], list[ProductFormat], list[Media]]:
        """Parse a single product detail page.

        Returns:
            Tuple of (Product, TastingNote, list[FoodPairing],
                       list[ProductFormat], list[Media]).
        """
        soup = self._soup(html)

        # --- Product name (prefer canonical slug mapping, then og:title, then h1) ---
        name = None
        # Try URL slug mapping first (most reliable)
        slug = source_url.rstrip("/").split("/")[-1] if source_url else ""
        if slug in _SLUG_TO_NAME:
            name = _SLUG_TO_NAME[slug]
        # Try og:title (often has the full product name)
        if not name:
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                og_name = self._clean(og_title["content"])
                # Strip site suffix like " - Champagne Joseph Perrier"
                if og_name:
                    name = re.sub(r"\s*[-–|]\s*Champagne.*$", "", og_name).strip()
        # Fall back to h1
        if not name:
            for selector in ["h1.product_title", "h1.entry-title", "h1"]:
                tag = soup.select_one(selector)
                if tag:
                    name = self._extract_text(tag)
                    if name:
                        break
        if not name:
            title_tag = soup.find("title")
            name = self._extract_text(title_tag) or "Unknown"

        # --- Description ---
        description = None
        for selector in [
            "div.product-description",
            "div.entry-content",
            "div.woocommerce-product-details__short-description",
            "article",
        ]:
            tag = soup.select_one(selector)
            if tag:
                paragraphs = tag.find_all("p")
                desc_parts = [
                    self._extract_text(p) for p in paragraphs if self._extract_text(p)
                ]
                if desc_parts:
                    description = " ".join(desc_parts)
                    break
        if not description:
            # Grab first long paragraph
            for p in soup.find_all("p"):
                txt = self._extract_text(p)
                if txt and len(txt) > 60:
                    description = txt
                    break

        collection = self._detect_collection(source_url, soup)
        champagne_type = self._detect_type(name, soup)
        grape_blend = self._extract_grape_blend(soup)
        price = self._extract_price(soup)
        vintage = self._extract_vintage(name, soup)

        is_limited = bool(
            re.search(
                r"(limited|numéroté|numbered|édition limitée|limited edition)",
                soup.get_text(" "),
                re.IGNORECASE,
            )
        )

        tasting = self._extract_tasting_note(soup)
        pairings = self._extract_food_pairings(soup)
        formats = self._extract_formats(soup)
        media = self.parse_media(html, context_prefix="product")

        product = Product(
            name=name,
            collection=collection,
            type=champagne_type,
            description=description,
            grape_blend=grape_blend,
            price_eur=price,
            vintage=vintage,
            is_limited_edition=is_limited,
            source_url=source_url,
        )

        return product, tasting, pairings, formats, media

    # ------------------------------------------------------------------
    # 5. parse_eshop_prices
    # ------------------------------------------------------------------

    def parse_eshop_prices(self, html: str) -> dict[str, float]:
        """Extract product-name -> price mapping from the e-shop listing page."""
        soup = self._soup(html)
        prices: dict[str, float] = {}

        # WooCommerce product loop items
        for product_el in soup.find_all(
            True,
            class_=re.compile(r"(product|shop-item|wc-block-grid__product)", re.IGNORECASE),
        ):
            # Product name
            name_tag = product_el.find(
                True,
                class_=re.compile(r"(product.*title|product.*name|woocommerce-loop-product__title)", re.IGNORECASE),
            ) or product_el.find(["h2", "h3"])
            name = self._extract_text(name_tag)
            if not name:
                continue

            # Price
            price_tag = product_el.find(
                True,
                class_=re.compile(r"(price|amount|prix)", re.IGNORECASE),
            )
            if price_tag:
                price_text = self._extract_text(price_tag) or ""
                m = re.search(r"(\d+[.,]\d{2})", price_text)
                if m:
                    prices[name] = float(m.group(1).replace(",", "."))

        # Fallback: scan for links with prices in generic containers
        if not prices:
            for a_tag in soup.find_all("a", href=True):
                text = a_tag.get_text(" ")
                m = re.search(
                    r"(.{5,60}?)\s*[-–]?\s*(?:€|EUR)\s*(\d+[.,]\d{2})",
                    text,
                )
                if m:
                    prices[self._clean(m.group(1)) or ""] = float(
                        m.group(2).replace(",", ".")
                    )

        return prices

    # ------------------------------------------------------------------
    # 6. parse_articles (listing)
    # ------------------------------------------------------------------

    def parse_articles(self, jojo_mag_html: str) -> list[str]:
        """Extract article URLs from the jojo-mag listing page."""
        soup = self._soup(jojo_mag_html)
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            abs_href = self._abs_url(href) or ""
            # Only keep English jojo-mag article links (not the listing itself)
            if "/en/jojo-mag/" in abs_href and abs_href.rstrip("/") != (
                self.base_url + "/en/jojo-mag"
            ):
                # Exclude pagination, tags, categories
                if re.search(r"/(page|tag|category|author)/", abs_href):
                    continue
                # Strip query params for dedup
                clean_url = re.sub(r"\?.*$", "", abs_href)
                if clean_url not in seen:
                    seen.add(clean_url)
                    urls.append(clean_url)

        return urls

    # ------------------------------------------------------------------
    # 7. parse_article
    # ------------------------------------------------------------------

    def parse_article(
        self, html: str, source_url: str
    ) -> tuple[Article, list[Media]]:
        """Parse a single jojo-mag article page."""
        soup = self._soup(html)

        # Title
        title = None
        for selector in ["h1.entry-title", "h1"]:
            tag = soup.select_one(selector)
            if tag:
                title = self._extract_text(tag)
                if title:
                    break
        if not title:
            t_tag = soup.find("title")
            title = self._extract_text(t_tag) or "Untitled"

        # Content and summary
        content = None
        summary = None
        content_tag = soup.select_one("div.entry-content") or soup.select_one(
            "article"
        )
        if content_tag:
            paragraphs = [
                self._extract_text(p) for p in content_tag.find_all("p") if self._extract_text(p)
            ]
            if paragraphs:
                content = "\n\n".join(paragraphs)
                summary = paragraphs[0][:300] if paragraphs[0] else None

        # Author
        author = None
        author_tag = soup.find(
            True,
            class_=re.compile(r"(author|byline|writer)", re.IGNORECASE),
        )
        if author_tag:
            author = self._extract_text(author_tag)
        if not author:
            meta_author = soup.find("meta", attrs={"name": "author"})
            if meta_author and meta_author.get("content"):
                author = self._clean(meta_author["content"])

        # Published date
        published_date = None
        time_tag = soup.find("time")
        if time_tag:
            published_date = time_tag.get("datetime") or self._extract_text(time_tag)
        if not published_date:
            date_tag = soup.find(
                True,
                class_=re.compile(r"(date|published|posted)", re.IGNORECASE),
            )
            if date_tag:
                published_date = self._extract_text(date_tag)

        # Main image
        image_url = None
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            image_url = self._abs_url(og_img["content"])
        if not image_url:
            # Featured image
            feat_img = soup.select_one(
                "img.wp-post-image, img.attachment-post-thumbnail, .post-thumbnail img"
            )
            if feat_img:
                image_url = self._abs_url(feat_img.get("src"))

        # Category detection
        category = self._detect_article_category(title or "", content or "", source_url)

        # Media
        media = self.parse_media(html, context_prefix="article")

        article = Article(
            title=title,
            summary=summary,
            content=content,
            author=author,
            published_date=published_date,
            source_url=source_url,
            image_url=image_url,
            category=category,
        )

        return article, media

    def _detect_article_category(
        self, title: str, content: str, url: str
    ) -> Optional[str]:
        """Detect article category from its title, content, and URL."""
        combined = f"{title} {content[:500]} {url}".lower()
        if re.search(r"(award|prix|medal|médaille|wine spectator|best|rated)", combined):
            return "awards"
        if re.search(r"(event|salon|expo|festival|tasting|dégustation|visite)", combined):
            return "events"
        if re.search(r"(news|announce|launch|new|nouveau|partnership|partenariat)", combined):
            return "news"
        return "editorial"

    # ------------------------------------------------------------------
    # 8. parse_media
    # ------------------------------------------------------------------

    def parse_media(self, html: str, context_prefix: str) -> list[Media]:
        """Generic media extractor: find images and videos from a page.

        Args:
            html: Raw HTML string.
            context_prefix: Prefix for the context field (e.g., "product", "article").

        Returns:
            List of Media dataclass instances.
        """
        soup = self._soup(html)
        media_list: list[Media] = []
        seen_urls: set[str] = set()

        # --- Images ---
        for idx, img in enumerate(soup.find_all("img")):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
            abs_src = self._abs_url(src)
            if not abs_src:
                continue
            # Only keep wp-content/uploads images (site assets, not external/icon)
            if "wp-content/uploads" not in abs_src:
                continue
            # Skip SVGs (logos, icons, social media), tiny thumbnails, and nav elements
            if abs_src.endswith(".svg"):
                continue
            if re.search(r"(logo|facebook|insta|linkedin|twitter|youtube|icon|arrow|Descendre|Logo_RF)", abs_src, re.IGNORECASE):
                continue
            if abs_src in seen_urls:
                continue
            seen_urls.add(abs_src)

            alt_text = self._clean(img.get("alt"))
            context = self._detect_image_context(img, idx, context_prefix)

            media_list.append(
                Media(
                    media_type="image",
                    url=abs_src,
                    alt_text=alt_text,
                    context=context,
                )
            )

        # --- Videos ---
        for video in soup.find_all("video"):
            source = video.find("source")
            src = video.get("src") or (source.get("src") if source else None)
            abs_src = self._abs_url(src)
            if abs_src and abs_src not in seen_urls:
                seen_urls.add(abs_src)
                media_list.append(
                    Media(
                        media_type="video",
                        url=abs_src,
                        alt_text=None,
                        context=f"{context_prefix}_video",
                    )
                )

        # --- Iframes (e.g., YouTube embeds) ---
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src")
            abs_src = self._abs_url(src)
            if abs_src and abs_src not in seen_urls:
                if re.search(r"(youtube|vimeo|dailymotion)", abs_src, re.IGNORECASE):
                    seen_urls.add(abs_src)
                    media_list.append(
                        Media(
                            media_type="video",
                            url=abs_src,
                            alt_text=None,
                            context=f"{context_prefix}_video",
                        )
                    )

        return media_list

    # ------------------------------------------------------------------
    # 9. parse_technical_specs
    # ------------------------------------------------------------------

    def parse_technical_specs(self, html: str) -> 'ProductTechnical':
        """Extract technical specifications from a product page."""
        from pipeline.models import ProductTechnical
        soup = self._soup(html)
        tech = ProductTechnical()
        text = soup.get_text(separator=' | ')

        # Aging months (French: "mois en cave" or English: "months")
        m = re.search(r'(\d+)\s*(?:months?|mois)', text, re.IGNORECASE)
        if m:
            tech.aging_months = int(m.group(1))

        # Dosage (e.g., "7g/L", "0g/L", "7 g/L")
        m = re.search(r'(?:dosage)\s*[:\s]*([\d.]+)\s*g\s*/\s*[lL]', text, re.IGNORECASE)
        if not m:
            m = re.search(r'([\d.]+)\s*g\s*/\s*[lL]', text, re.IGNORECASE)
        if m:
            tech.dosage_gl = float(m.group(1))

        # Reserve wines %
        m = re.search(r'(?:reserve|réserve)\s*(?:wines?)?\s*[:\s]*(?:around\s*|environ\s*)?~?\s*([\d.]+)\s*%', text, re.IGNORECASE)
        if m:
            tech.reserve_wines_pct = float(m.group(1))

        # Serving temperature
        m = re.search(r'(?:temperature|température|temp)\s*[:\s]*(\d+)\s*[-–à]\s*(\d+)\s*°?\s*C', text, re.IGNORECASE)
        if not m:
            m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*°\s*C', text)
        if m:
            tech.serving_temp_min = int(m.group(1))
            tech.serving_temp_max = int(m.group(2))

        # Aging potential
        m = re.search(r'(?:ageing|aging|garde|potentiel)\s*(?:potential)?\s*[:\s]*([\d]+\s*(?:to|à|[-–])\s*[\d]+\s*(?:years?|ans?))', text, re.IGNORECASE)
        if m:
            tech.aging_potential = m.group(1).strip()

        # Crus
        m = re.search(r'(?:crus?\s+assembl[ée]s?|crus?\s*[:\s])\s*(.*?)(?:\||\.|\n|$)', text, re.IGNORECASE)
        if m:
            crus_text = m.group(1).strip()
            crus_text = re.sub(r'^.*?(?:terroirs?\s+(?:of|de)\s+|from\s+)', '', crus_text, flags=re.IGNORECASE)
            if len(crus_text) > 5:
                tech.crus = crus_text.strip(' .')

        return tech

    # ------------------------------------------------------------------
    # 10. parse_awards
    # ------------------------------------------------------------------

    def parse_awards(self, html: str) -> list:
        """Extract awards and ratings from a product page."""
        from pipeline.models import ProductAward
        soup = self._soup(html)
        awards = []
        text = soup.get_text('\n')

        # Known award organizations and their regex patterns
        AWARD_PATTERNS = [
            (r'James\s+Suckling\s*[:\s]*(\d{2,3})\s*(?:pts?|points?)?(?:\s*/\s*100)?', 'James Suckling'),
            (r'Bettane\s*(?:&|et|[+])\s*Desseauve?\s*[:\s]*(\d{2,3})\s*(?:pts?|points?)?(?:\s*/\s*100)?', 'Bettane+Desseauve'),
            (r'Wine\s+Spectator\s*[:\s]*(\d{2,3})\s*(?:pts?|points?)?(?:\s*/\s*100)?', 'Wine Spectator'),
            (r'Wine\s+Enthusiast\s*[:\s]*(\d{2,3})\s*(?:pts?|points?)?(?:\s*/\s*100)?', 'Wine Enthusiast'),
            (r'Decanter\s*[:\s]*((?:Gold|Silver|Bronze|Platinum)\s*(?:\d{4})?|\d{2,3}\s*(?:pts?|points?))', 'Decanter'),
            (r'Le\s+Point\s*[:\s]*(\d{1,2}(?:[.,]\d)?\s*/\s*20)', 'Le Point'),
            (r'Terre\s+de\s+Vins?\s*[:\s]*(\d{2,3}\s*(?:pts?|/\s*100)?)', 'Terre de Vins'),
            (r'Jancis\s+Robinson\s*[:\s]*(\d{1,2}(?:[.,]\d)?\s*(?:/\s*20)?)', 'Jancis Robinson'),
            (r'Bernard\s+Burtschy\s*[:\s]*(\d{2,3}\s*(?:pts?|/\s*100)?)', 'Bernard Burtschy'),
            (r'Vinum\s*[:\s]*(\d{1,2}(?:[.,]\d)?\s*/\s*20)', 'Vinum'),
            (r'(?:The\s+)?Drinks?\s+Business\s*[:\s]*((?:Gold|Silver|Bronze)\s*(?:\d{4})?)', 'The Drinks Business'),
            (r'(?:The\s+)?Champagne\s+Masters?\s*[:\s]*((?:Gold|Silver|Bronze)\s*(?:\d{4})?)', 'The Champagne Masters'),
            (r'CSWWC\s*[:\s]*((?:Gold|Silver|Bronze)\s*(?:\d{4})?)', 'CSWWC'),
        ]

        # Map org names to logo URL patterns (from existing award_badge media)
        LOGO_MAP = {
            'James Suckling': 'James-suckling',
            'Bettane+Desseauve': 'bettane_dessauve',
            'Wine Spectator': 'wine-spectator',
            'Wine Enthusiast': 'wine-enthusiast',
            'Decanter': 'DWWA',
            'Le Point': 'Le-Point',
            'Terre de Vins': 'terres-de-vins',
            'Jancis Robinson': 'js.1605610837',
            'Bernard Burtschy': 'Bernard-Burtschy',
            'Vinum': 'Vinum',
            'The Drinks Business': 'drink-business',
            'The Champagne Masters': 'Champagne-Masters',
            'CSWWC': 'CSWWC',
        }

        seen_orgs = set()
        for pattern, org_name in AWARD_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m and org_name not in seen_orgs:
                seen_orgs.add(org_name)
                detail = m.group(1).strip() if m.group(1) else None

                score = None
                medal = None
                year = None

                if detail:
                    score_m = re.search(r'(\d{2,3})', detail)
                    if score_m:
                        score = score_m.group(1)
                    medal_m = re.search(r'(Gold|Silver|Bronze|Platinum)', detail, re.IGNORECASE)
                    if medal_m:
                        medal = medal_m.group(1).capitalize()
                    year_m = re.search(r'(20\d{2})', detail)
                    if year_m:
                        year = year_m.group(1)

                # Find logo URL from existing media
                logo_url = None
                logo_pattern = LOGO_MAP.get(org_name)
                if logo_pattern:
                    for img in soup.find_all('img', src=True):
                        if logo_pattern.lower() in img['src'].lower():
                            logo_url = self._abs_url(img['src'])
                            break

                awards.append(ProductAward(
                    organization=org_name,
                    detail=detail,
                    year=year,
                    medal=medal,
                    score=score,
                    logo_url=logo_url,
                ))

        return awards

    def _detect_image_context(
        self, img: Tag, index: int, prefix: str
    ) -> str:
        """Determine semantic context for an image based on position and attributes."""
        classes = " ".join(img.get("class", []))
        parent_classes = " ".join(img.parent.get("class", []) if img.parent else [])
        combined_classes = f"{classes} {parent_classes}".lower()
        alt = (img.get("alt") or "").lower()

        # Hero / banner detection
        if re.search(r"(hero|banner|slider|carousel|cover|featured)", combined_classes):
            return f"{prefix}_hero_banner"

        # Logo
        if re.search(r"(logo)", combined_classes) or re.search(r"(logo)", alt):
            return f"{prefix}_logo"

        # Thumbnail
        if re.search(r"(thumb|thumbnail|miniature)", combined_classes):
            return f"{prefix}_thumbnail"

        # Gallery
        if re.search(r"(gallery|galerie|lightbox)", combined_classes):
            return f"{prefix}_gallery"

        # Product photo (first image on product pages is usually the main shot)
        if prefix == "product":
            if index == 0:
                return "product_photo"
            return f"product_photo_{index + 1}"

        # Article lead image
        if prefix == "article" and index == 0:
            return "article_hero_banner"

        return f"{prefix}_image_{index + 1}"

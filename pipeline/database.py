"""SQLite database manager for the Joseph Perrier data ingestion project."""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

from .models import (
    Winery, WineryHistory, TeamMember, Product,
    TastingNote, FoodPairing, ProductFormat, Media, Article,
)


class Database:
    """Context-managed SQLite database with full CRUD for all entities."""

    def __init__(self, db_path: str = "data/joseph_perrier.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Open connection, enable WAL mode and foreign keys."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.create_tables()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def create_tables(self):
        """Create all nine tables if they do not exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS winery (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                location        TEXT,
                founded_year    INTEGER,
                description     TEXT,
                website_url     TEXT,
                vineyard_hectares REAL,
                cellar_description TEXT,
                awards_honors   TEXT
            );

            CREATE TABLE IF NOT EXISTS winery_history (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                winery_id        INTEGER NOT NULL,
                year             INTEGER,
                event_description TEXT,
                FOREIGN KEY (winery_id) REFERENCES winery(id)
            );

            CREATE TABLE IF NOT EXISTS team_member (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                winery_id   INTEGER NOT NULL,
                name        TEXT NOT NULL,
                role        TEXT,
                generation  TEXT,
                bio         TEXT,
                image_url   TEXT,
                FOREIGN KEY (winery_id) REFERENCES winery(id)
            );

            CREATE TABLE IF NOT EXISTS product (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                winery_id         INTEGER NOT NULL,
                name              TEXT NOT NULL,
                collection        TEXT,
                type              TEXT,
                description       TEXT,
                grape_blend       TEXT,
                price_eur         REAL,
                vintage           TEXT,
                is_limited_edition INTEGER DEFAULT 0,
                source_url        TEXT,
                FOREIGN KEY (winery_id) REFERENCES winery(id)
            );

            CREATE TABLE IF NOT EXISTS tasting_note (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id          INTEGER NOT NULL,
                color_description   TEXT,
                nose_description    TEXT,
                palate_description  TEXT,
                serving_suggestion  TEXT,
                FOREIGN KEY (product_id) REFERENCES product(id)
            );

            CREATE TABLE IF NOT EXISTS food_pairing (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id  INTEGER NOT NULL,
                description TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES product(id)
            );

            CREATE TABLE IF NOT EXISTS product_format (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id  INTEGER NOT NULL,
                format_name TEXT NOT NULL,
                volume_cl   INTEGER,
                FOREIGN KEY (product_id) REFERENCES product(id)
            );

            CREATE TABLE IF NOT EXISTS article (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                winery_id       INTEGER NOT NULL,
                title           TEXT NOT NULL,
                summary         TEXT,
                content         TEXT,
                author          TEXT,
                published_date  TEXT,
                source_url      TEXT,
                image_url       TEXT,
                category        TEXT,
                FOREIGN KEY (winery_id) REFERENCES winery(id)
            );

            CREATE TABLE IF NOT EXISTS product_technical (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id      INTEGER NOT NULL,
                aging_months    INTEGER,
                dosage_gl       REAL,
                reserve_wines_pct REAL,
                serving_temp_min INTEGER,
                serving_temp_max INTEGER,
                aging_potential  TEXT,
                crus            TEXT,
                FOREIGN KEY (product_id) REFERENCES product(id)
            );

            CREATE TABLE IF NOT EXISTS product_award (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id      INTEGER NOT NULL,
                organization    TEXT NOT NULL,
                detail          TEXT,
                year            TEXT,
                medal           TEXT,
                score           TEXT,
                logo_url        TEXT,
                FOREIGN KEY (product_id) REFERENCES product(id)
            );

            CREATE TABLE IF NOT EXISTS media (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id  INTEGER,
                winery_id   INTEGER,
                article_id  INTEGER,
                media_type  TEXT NOT NULL,
                url         TEXT NOT NULL,
                alt_text    TEXT,
                context     TEXT,
                FOREIGN KEY (product_id) REFERENCES product(id),
                FOREIGN KEY (winery_id)  REFERENCES winery(id),
                FOREIGN KEY (article_id) REFERENCES article(id)
            );
        """)
        self.conn.commit()

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a sqlite3.Row to a plain dict."""
        return dict(row) if row else {}

    def _rows_to_dicts(self, rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Winery CRUD
    # ------------------------------------------------------------------

    def insert_winery(self, winery: Winery) -> int:
        """Insert a winery and return its id."""
        cur = self.conn.execute(
            """INSERT INTO winery
               (name, location, founded_year, description, website_url,
                vineyard_hectares, cellar_description, awards_honors)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (winery.name, winery.location, winery.founded_year,
             winery.description, winery.website_url,
             winery.vineyard_hectares, winery.cellar_description,
             winery.awards_honors),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_winery(self, winery_id: int = 1) -> Optional[Dict[str, Any]]:
        """Fetch a winery by id (defaults to 1 — the single Joseph Perrier row)."""
        row = self.conn.execute(
            "SELECT * FROM winery WHERE id = ?", (winery_id,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def update_winery(self, winery_id: int, **fields) -> None:
        """Update specific fields on a winery row."""
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [winery_id]
        self.conn.execute(
            f"UPDATE winery SET {set_clause} WHERE id = ?", values
        )
        self.conn.commit()

    def delete_winery(self, winery_id: int) -> None:
        self.conn.execute("DELETE FROM winery WHERE id = ?", (winery_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Winery History CRUD
    # ------------------------------------------------------------------

    def insert_history(self, winery_id: int, event: WineryHistory) -> int:
        cur = self.conn.execute(
            """INSERT INTO winery_history (winery_id, year, event_description)
               VALUES (?, ?, ?)""",
            (winery_id, event.year, event.event_description),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_history(self, winery_id: int = 1) -> List[Dict[str, Any]]:
        """Return all history events for a winery, ordered by year."""
        rows = self.conn.execute(
            "SELECT * FROM winery_history WHERE winery_id = ? ORDER BY year",
            (winery_id,),
        ).fetchall()
        return self._rows_to_dicts(rows)

    def delete_history(self, history_id: int) -> None:
        self.conn.execute(
            "DELETE FROM winery_history WHERE id = ?", (history_id,)
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Team Member CRUD
    # ------------------------------------------------------------------

    def insert_team_member(self, winery_id: int, member: TeamMember) -> int:
        cur = self.conn.execute(
            """INSERT INTO team_member
               (winery_id, name, role, generation, bio, image_url)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (winery_id, member.name, member.role, member.generation,
             member.bio, member.image_url),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_team_members(self, winery_id: int = 1) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM team_member WHERE winery_id = ?", (winery_id,)
        ).fetchall()
        return self._rows_to_dicts(rows)

    def get_team_member(self, member_id: int) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM team_member WHERE id = ?", (member_id,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def update_team_member(self, member_id: int, **fields) -> None:
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [member_id]
        self.conn.execute(
            f"UPDATE team_member SET {set_clause} WHERE id = ?", values
        )
        self.conn.commit()

    def delete_team_member(self, member_id: int) -> None:
        self.conn.execute("DELETE FROM team_member WHERE id = ?", (member_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Product CRUD
    # ------------------------------------------------------------------

    def insert_product(self, winery_id: int, product: Product) -> int:
        """Insert a product and all its child records (tasting notes, pairings, formats, media)."""
        cur = self.conn.execute(
            """INSERT INTO product
               (winery_id, name, collection, type, description, grape_blend,
                price_eur, vintage, is_limited_edition, source_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (winery_id, product.name, product.collection, product.type,
             product.description, product.grape_blend, product.price_eur,
             product.vintage, int(product.is_limited_edition),
             product.source_url),
        )
        product_id = cur.lastrowid

        # Child records
        for tn in product.tasting_notes:
            self.insert_tasting_note(product_id, tn)
        for fp in product.food_pairings:
            self.insert_food_pairing(product_id, fp)
        for fmt in product.formats:
            self.insert_product_format(product_id, fmt)
        for m in product.media:
            self.insert_media(m, product_id=product_id)

        if product.technical and any([
            product.technical.aging_months, product.technical.dosage_gl,
            product.technical.reserve_wines_pct, product.technical.serving_temp_min,
            product.technical.aging_potential, product.technical.crus
        ]):
            self.insert_product_technical(product_id, product.technical)

        for award in product.awards:
            self.insert_product_award(product_id, award)

        self.conn.commit()
        return product_id

    def get_products(self, winery_id: int = 1) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM product WHERE winery_id = ?", (winery_id,)
        ).fetchall()
        return self._rows_to_dicts(rows)

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM product WHERE id = ?", (product_id,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def get_product_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM product WHERE name = ?", (name,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def update_product(self, product_id: int, **fields) -> None:
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [product_id]
        self.conn.execute(
            f"UPDATE product SET {set_clause} WHERE id = ?", values
        )
        self.conn.commit()

    def delete_product(self, product_id: int) -> None:
        """Delete a product and all associated child rows."""
        self.conn.execute("DELETE FROM tasting_note WHERE product_id = ?", (product_id,))
        self.conn.execute("DELETE FROM food_pairing WHERE product_id = ?", (product_id,))
        self.conn.execute("DELETE FROM product_format WHERE product_id = ?", (product_id,))
        self.conn.execute("DELETE FROM product_technical WHERE product_id = ?", (product_id,))
        self.conn.execute("DELETE FROM product_award WHERE product_id = ?", (product_id,))
        self.conn.execute("DELETE FROM media WHERE product_id = ?", (product_id,))
        self.conn.execute("DELETE FROM product WHERE id = ?", (product_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Tasting Note CRUD
    # ------------------------------------------------------------------

    def insert_tasting_note(self, product_id: int, note: TastingNote) -> int:
        cur = self.conn.execute(
            """INSERT INTO tasting_note
               (product_id, color_description, nose_description,
                palate_description, serving_suggestion)
               VALUES (?, ?, ?, ?, ?)""",
            (product_id, note.color_description, note.nose_description,
             note.palate_description, note.serving_suggestion),
        )
        return cur.lastrowid

    def get_tasting_notes(self, product_id: int) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM tasting_note WHERE product_id = ?", (product_id,)
        ).fetchall()
        return self._rows_to_dicts(rows)

    def delete_tasting_note(self, note_id: int) -> None:
        self.conn.execute("DELETE FROM tasting_note WHERE id = ?", (note_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Food Pairing CRUD
    # ------------------------------------------------------------------

    def insert_food_pairing(self, product_id: int, pairing: FoodPairing) -> int:
        cur = self.conn.execute(
            "INSERT INTO food_pairing (product_id, description) VALUES (?, ?)",
            (product_id, pairing.description),
        )
        return cur.lastrowid

    def get_food_pairings(self, product_id: int) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM food_pairing WHERE product_id = ?", (product_id,)
        ).fetchall()
        return self._rows_to_dicts(rows)

    def delete_food_pairing(self, pairing_id: int) -> None:
        self.conn.execute(
            "DELETE FROM food_pairing WHERE id = ?", (pairing_id,)
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Product Format CRUD
    # ------------------------------------------------------------------

    def insert_product_format(self, product_id: int, fmt: ProductFormat) -> int:
        cur = self.conn.execute(
            """INSERT INTO product_format (product_id, format_name, volume_cl)
               VALUES (?, ?, ?)""",
            (product_id, fmt.format_name, fmt.volume_cl),
        )
        return cur.lastrowid

    def get_product_formats(self, product_id: int) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM product_format WHERE product_id = ?", (product_id,)
        ).fetchall()
        return self._rows_to_dicts(rows)

    def delete_product_format(self, format_id: int) -> None:
        self.conn.execute(
            "DELETE FROM product_format WHERE id = ?", (format_id,)
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Article CRUD
    # ------------------------------------------------------------------

    def insert_article(self, winery_id: int, article: Article) -> int:
        cur = self.conn.execute(
            """INSERT INTO article
               (winery_id, title, summary, content, author,
                published_date, source_url, image_url, category)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (winery_id, article.title, article.summary, article.content,
             article.author, article.published_date, article.source_url,
             article.image_url, article.category),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_articles(self, winery_id: int = 1) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM article WHERE winery_id = ?", (winery_id,)
        ).fetchall()
        return self._rows_to_dicts(rows)

    def get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM article WHERE id = ?", (article_id,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def update_article(self, article_id: int, **fields) -> None:
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [article_id]
        self.conn.execute(
            f"UPDATE article SET {set_clause} WHERE id = ?", values
        )
        self.conn.commit()

    def delete_article(self, article_id: int) -> None:
        self.conn.execute("DELETE FROM media WHERE article_id = ?", (article_id,))
        self.conn.execute("DELETE FROM article WHERE id = ?", (article_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Media CRUD
    # ------------------------------------------------------------------

    def insert_media(
        self,
        media: Media,
        product_id: Optional[int] = None,
        winery_id: Optional[int] = None,
        article_id: Optional[int] = None,
    ) -> int:
        cur = self.conn.execute(
            """INSERT INTO media
               (product_id, winery_id, article_id, media_type, url, alt_text, context)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (product_id, winery_id, article_id,
             media.media_type, media.url, media.alt_text, media.context),
        )
        return cur.lastrowid

    def get_media(
        self,
        product_id: Optional[int] = None,
        winery_id: Optional[int] = None,
        article_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve media filtered by optional FK, or all media if no filter."""
        if product_id is not None:
            rows = self.conn.execute(
                "SELECT * FROM media WHERE product_id = ?", (product_id,)
            ).fetchall()
        elif winery_id is not None:
            rows = self.conn.execute(
                "SELECT * FROM media WHERE winery_id = ?", (winery_id,)
            ).fetchall()
        elif article_id is not None:
            rows = self.conn.execute(
                "SELECT * FROM media WHERE article_id = ?", (article_id,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM media").fetchall()
        return self._rows_to_dicts(rows)

    def delete_media(self, media_id: int) -> None:
        self.conn.execute("DELETE FROM media WHERE id = ?", (media_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Product Technical CRUD
    # ------------------------------------------------------------------

    def insert_product_technical(self, product_id: int, tech) -> int:
        cur = self.conn.execute(
            """INSERT INTO product_technical
               (product_id, aging_months, dosage_gl, reserve_wines_pct,
                serving_temp_min, serving_temp_max, aging_potential, crus)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (product_id, tech.aging_months, tech.dosage_gl, tech.reserve_wines_pct,
             tech.serving_temp_min, tech.serving_temp_max, tech.aging_potential, tech.crus),
        )
        return cur.lastrowid

    def insert_product_award(self, product_id: int, award) -> int:
        cur = self.conn.execute(
            """INSERT INTO product_award
               (product_id, organization, detail, year, medal, score, logo_url)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (product_id, award.organization, award.detail, award.year,
             award.medal, award.score, award.logo_url),
        )
        return cur.lastrowid

    def get_product_technical(self, product_id: int):
        row = self.conn.execute(
            "SELECT * FROM product_technical WHERE product_id = ?", (product_id,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def get_product_awards(self, product_id: int):
        rows = self.conn.execute(
            "SELECT * FROM product_award WHERE product_id = ?", (product_id,)
        ).fetchall()
        return self._rows_to_dicts(rows)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, int]:
        """Return row counts for every table."""
        tables = [
            "winery", "winery_history", "team_member", "product",
            "tasting_note", "food_pairing", "product_format",
            "product_technical", "product_award", "media", "article",
        ]
        stats = {}
        for table in tables:
            count = self.conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            stats[table] = count
        return stats

    # ------------------------------------------------------------------
    # Convenience: full product detail
    # ------------------------------------------------------------------

    def get_product_detail(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a product with its tasting notes, pairings, formats, and media."""
        product = self.get_product(product_id)
        if not product:
            return None
        product["tasting_notes"] = self.get_tasting_notes(product_id)
        product["food_pairings"] = self.get_food_pairings(product_id)
        product["formats"] = self.get_product_formats(product_id)
        product["media"] = self.get_media(product_id=product_id)
        product["technical"] = self.get_product_technical(product_id)
        product["awards"] = self.get_product_awards(product_id)
        return product

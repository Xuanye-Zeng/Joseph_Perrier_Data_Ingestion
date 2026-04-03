"""
CLI tool to inspect the Joseph Perrier SQLite database.

Usage:
    python scripts/inspect_db.py winery                     # Winery info
    python inspect_db.py products                   # List all products
    python inspect_db.py product "Cuvée Royale"     # Product details
    python inspect_db.py media                      # All media
    python inspect_db.py media --product "Name"     # Media for product
    python inspect_db.py history                    # Timeline
    python inspect_db.py team                       # Team members
    python inspect_db.py articles                   # Blog articles
    python inspect_db.py stats                      # Summary statistics
"""

import argparse
import sqlite3
import sys
import os

from tabulate import tabulate


DEFAULT_DB_PATH = "data/joseph_perrier.db"


def get_connection(db_path: str) -> sqlite3.Connection:
    """Open a read-only SQLite connection. Exit if file does not exist."""
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        print("Run 'python main.py' first to create the database.")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def cmd_winery(conn: sqlite3.Connection):
    """Display winery information as key-value pairs."""
    row = conn.execute("SELECT * FROM winery LIMIT 1").fetchone()
    if not row:
        print("No winery data found.")
        return

    fields = [
        ("ID", "id"),
        ("Name", "name"),
        ("Location", "location"),
        ("Founded", "founded_year"),
        ("Website", "website_url"),
        ("Vineyard (ha)", "vineyard_hectares"),
        ("Description", "description"),
        ("Cellar", "cellar_description"),
        ("Awards/Honors", "awards_honors"),
    ]

    data = []
    for label, key in fields:
        value = row[key]
        if value is not None:
            # Truncate long text for display
            value_str = str(value)
            if len(value_str) > 120:
                value_str = value_str[:117] + "..."
            data.append([label, value_str])

    print("\n=== Winery Info ===\n")
    print(tabulate(data, headers=["Field", "Value"], tablefmt="grid"))


def cmd_products(conn: sqlite3.Connection):
    """Display all products in a table."""
    rows = conn.execute(
        """SELECT name, collection, type, vintage, price_eur, is_limited_edition
           FROM product ORDER BY collection, name"""
    ).fetchall()

    if not rows:
        print("No products found.")
        return

    data = []
    for r in rows:
        price = f"EUR {r['price_eur']:.2f}" if r["price_eur"] else "-"
        limited = "Yes" if r["is_limited_edition"] else ""
        data.append([
            r["name"],
            r["collection"] or "-",
            r["type"] or "-",
            r["vintage"] or "-",
            price,
            limited,
        ])

    print(f"\n=== Products ({len(rows)}) ===\n")
    print(tabulate(
        data,
        headers=["Name", "Collection", "Type", "Vintage", "Price", "Limited"],
        tablefmt="grid",
    ))


def cmd_product_detail(conn: sqlite3.Connection, name: str):
    """Display detailed information for a single product."""
    row = conn.execute(
        "SELECT * FROM product WHERE name LIKE ?", (f"%{name}%",)
    ).fetchone()

    if not row:
        print(f"No product found matching '{name}'.")
        # Show available products to help the user
        all_products = conn.execute("SELECT name FROM product ORDER BY name").fetchall()
        if all_products:
            print("\nAvailable products:")
            for p in all_products:
                print(f"  - {p['name']}")
        return

    product_id = row["id"]

    # Basic info
    print(f"\n=== Product: {row['name']} ===\n")
    info = [
        ["Collection", row["collection"] or "-"],
        ["Type", row["type"] or "-"],
        ["Vintage", row["vintage"] or "-"],
        ["Price", f"EUR {row['price_eur']:.2f}" if row["price_eur"] else "-"],
        ["Limited Edition", "Yes" if row["is_limited_edition"] else "No"],
        ["Grape Blend", row["grape_blend"] or "-"],
        ["Source URL", row["source_url"] or "-"],
    ]
    print(tabulate(info, headers=["Field", "Value"], tablefmt="grid"))

    # Description
    if row["description"]:
        print(f"\nDescription:\n  {row['description']}")

    # Tasting notes
    notes = conn.execute(
        "SELECT * FROM tasting_note WHERE product_id = ?", (product_id,)
    ).fetchall()
    if notes:
        print("\n--- Tasting Notes ---")
        for n in notes:
            note_data = []
            if n["color_description"]:
                note_data.append(["Color", n["color_description"]])
            if n["nose_description"]:
                note_data.append(["Nose", n["nose_description"]])
            if n["palate_description"]:
                note_data.append(["Palate", n["palate_description"]])
            if n["serving_suggestion"]:
                note_data.append(["Serving", n["serving_suggestion"]])
            if note_data:
                print(tabulate(note_data, tablefmt="grid"))

    # Food pairings
    pairings = conn.execute(
        "SELECT description FROM food_pairing WHERE product_id = ?", (product_id,)
    ).fetchall()
    if pairings:
        print("\n--- Food Pairings ---")
        for p in pairings:
            print(f"  - {p['description']}")

    # Formats
    formats = conn.execute(
        "SELECT format_name, volume_cl FROM product_format WHERE product_id = ?",
        (product_id,),
    ).fetchall()
    if formats:
        print("\n--- Available Formats ---")
        fmt_data = [[f["format_name"], f"{f['volume_cl']} cl" if f["volume_cl"] else "-"]
                     for f in formats]
        print(tabulate(fmt_data, headers=["Format", "Volume"], tablefmt="grid"))

    # Media
    media = conn.execute(
        "SELECT media_type, url, alt_text, context FROM media WHERE product_id = ?",
        (product_id,),
    ).fetchall()
    if media:
        print("\n--- Media ---")
        media_data = [[m["media_type"], m["url"][:80], m["context"] or "-"]
                       for m in media]
        print(tabulate(media_data, headers=["Type", "URL", "Context"], tablefmt="grid"))


def cmd_media(conn: sqlite3.Connection, product_name: str | None = None):
    """Display media items, optionally filtered by product name."""
    if product_name:
        rows = conn.execute(
            """SELECT m.media_type, m.url, m.alt_text, m.context,
                      p.name AS product_name, w.name AS winery_name
               FROM media m
               LEFT JOIN product p ON m.product_id = p.id
               LEFT JOIN winery w ON m.winery_id = w.id
               WHERE p.name LIKE ?
               ORDER BY m.media_type""",
            (f"%{product_name}%",),
        ).fetchall()
        title = f"Media for '{product_name}'"
    else:
        rows = conn.execute(
            """SELECT m.media_type, m.url, m.alt_text, m.context,
                      p.name AS product_name, w.name AS winery_name,
                      a.title AS article_title
               FROM media m
               LEFT JOIN product p ON m.product_id = p.id
               LEFT JOIN winery w ON m.winery_id = w.id
               LEFT JOIN article a ON m.article_id = a.id
               ORDER BY m.media_type"""
        ).fetchall()
        title = "All Media"

    if not rows:
        print("No media found.")
        return

    data = []
    for r in rows:
        associated = r["product_name"] or r["winery_name"] or \
                     (r["article_title"] if "article_title" in r.keys() else None) or "-"
        url_display = r["url"]
        if len(url_display) > 70:
            url_display = url_display[:67] + "..."
        data.append([
            r["media_type"],
            url_display,
            r["context"] or "-",
            associated,
        ])

    print(f"\n=== {title} ({len(rows)}) ===\n")
    print(tabulate(
        data,
        headers=["Type", "URL", "Context", "Associated With"],
        tablefmt="grid",
    ))


def cmd_history(conn: sqlite3.Connection):
    """Display the winery history timeline."""
    rows = conn.execute(
        """SELECT h.year, h.event_description
           FROM winery_history h
           ORDER BY h.year"""
    ).fetchall()

    if not rows:
        print("No history events found.")
        return

    data = [[r["year"] or "?", r["event_description"]] for r in rows]

    print(f"\n=== History Timeline ({len(rows)} events) ===\n")
    print(tabulate(data, headers=["Year", "Event"], tablefmt="grid"))


def cmd_team(conn: sqlite3.Connection):
    """Display team members."""
    rows = conn.execute(
        """SELECT t.name, t.role, t.generation, t.bio
           FROM team_member t
           ORDER BY t.name"""
    ).fetchall()

    if not rows:
        print("No team members found.")
        return

    data = []
    for r in rows:
        bio = r["bio"] or "-"
        if len(bio) > 80:
            bio = bio[:77] + "..."
        data.append([r["name"], r["role"] or "-", r["generation"] or "-", bio])

    print(f"\n=== Team Members ({len(rows)}) ===\n")
    print(tabulate(
        data,
        headers=["Name", "Role", "Generation", "Bio"],
        tablefmt="grid",
    ))


def cmd_articles(conn: sqlite3.Connection):
    """Display blog articles."""
    rows = conn.execute(
        """SELECT title, category, author, published_date, source_url
           FROM article
           ORDER BY published_date DESC"""
    ).fetchall()

    if not rows:
        print("No articles found.")
        return

    data = []
    for r in rows:
        data.append([
            r["title"] or "-",
            r["category"] or "-",
            r["author"] or "-",
            r["published_date"] or "-",
        ])

    print(f"\n=== Articles ({len(rows)}) ===\n")
    print(tabulate(
        data,
        headers=["Title", "Category", "Author", "Date"],
        tablefmt="grid",
    ))


def cmd_stats(conn: sqlite3.Connection):
    """Display summary statistics for the database."""
    tables = [
        ("winery", "Wineries"),
        ("winery_history", "History Events"),
        ("team_member", "Team Members"),
        ("product", "Products"),
        ("tasting_note", "Tasting Notes"),
        ("food_pairing", "Food Pairings"),
        ("product_format", "Product Formats"),
        ("media", "Media Items"),
        ("article", "Articles"),
    ]

    data = []
    total = 0
    for table_name, label in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        except sqlite3.OperationalError:
            count = "TABLE MISSING"
        data.append([label, count])
        if isinstance(count, int):
            total += count

    # Additional breakdowns
    try:
        collections = conn.execute(
            "SELECT collection, COUNT(*) as cnt FROM product GROUP BY collection ORDER BY cnt DESC"
        ).fetchall()
        if collections:
            data.append(["", ""])
            data.append(["--- Product Collections ---", ""])
            for c in collections:
                data.append([f"  {c['collection'] or 'Uncategorized'}", c["cnt"]])
    except sqlite3.OperationalError:
        pass

    try:
        media_types = conn.execute(
            "SELECT media_type, COUNT(*) as cnt FROM media GROUP BY media_type ORDER BY cnt DESC"
        ).fetchall()
        if media_types:
            data.append(["", ""])
            data.append(["--- Media Types ---", ""])
            for m in media_types:
                data.append([f"  {m['media_type']}", m["cnt"]])
    except sqlite3.OperationalError:
        pass

    print("\n=== Database Statistics ===\n")
    print(tabulate(data, headers=["Category", "Count"], tablefmt="grid"))
    print(f"\nTotal records: {total}")


def main():
    """Parse arguments and dispatch to the appropriate command handler."""
    parser = argparse.ArgumentParser(
        description="Inspect the Joseph Perrier champagne database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python inspect_db.py winery
  python inspect_db.py products
  python inspect_db.py product "Cuvée Royale Brut"
  python inspect_db.py media --product "Joséphine"
  python inspect_db.py history
  python inspect_db.py team
  python inspect_db.py articles
  python inspect_db.py stats
        """,
    )

    parser.add_argument(
        "command",
        choices=["winery", "products", "product", "media", "history", "team",
                 "articles", "stats"],
        help="The inspection command to run.",
    )
    parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Product name (for 'product' command).",
    )
    parser.add_argument(
        "--product",
        default=None,
        help="Filter media by product name (for 'media' command).",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH}).",
    )

    args = parser.parse_args()
    conn = get_connection(args.db)

    try:
        if args.command == "winery":
            cmd_winery(conn)
        elif args.command == "products":
            cmd_products(conn)
        elif args.command == "product":
            if not args.name:
                print("ERROR: 'product' command requires a product name.")
                print("Usage: python inspect_db.py product \"Product Name\"")
                sys.exit(1)
            cmd_product_detail(conn, args.name)
        elif args.command == "media":
            cmd_media(conn, product_name=args.product)
        elif args.command == "history":
            cmd_history(conn)
        elif args.command == "team":
            cmd_team(conn)
        elif args.command == "articles":
            cmd_articles(conn)
        elif args.command == "stats":
            cmd_stats(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

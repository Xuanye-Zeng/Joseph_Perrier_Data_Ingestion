"""Add curated gallery images and clean up duplicate media."""

import sqlite3

DB_PATH = "data/joseph_perrier.db"

CURATED_GALLERY = {
    "Cuvée Royale Brut": [
        "https://www.josephperrier.com/wp-content/uploads/2021/03/CRB-SITE-.webp",
    ],
    "Cuvée Royale Brut Nature": [
        "https://www.josephperrier.com/wp-content/uploads/2021/03/Nature.webp",
    ],
    "Cuvée Royale Blanc de Blancs": [
        "https://www.josephperrier.com/wp-content/uploads/2021/03/BDB-page-produit-1-1.webp",
        "https://www.josephperrier.com/wp-content/uploads/2021/03/BDB-page-produit-1-2.webp",
    ],
    "Cuvée Royale Brut Rosé": [
        "https://www.josephperrier.com/wp-content/uploads/2021/03/3.webp",
        "https://www.josephperrier.com/wp-content/uploads/2021/03/Joseph-Perrier-Michael-Boudot-Cuvee-Royale-Brut-Rose-New-id-HD-scaled.webp",
    ],
    "Cuvée Royale Vintage 2018": [
        "https://www.josephperrier.com/wp-content/uploads/2025/09/14-08-1.webp",
    ],
    "Cuvée Royale Demi-Sec": [
        "https://www.josephperrier.com/wp-content/uploads/2021/03/Demi-secx1.webp",
    ],
    "Le Ciergelot 2020": [
        "https://www.josephperrier.com/wp-content/uploads/2025/03/JosephPerrier_fev25@ninacoriton-41-2.webp",
    ],
    "La Côte à Bras 2016": [
        "https://www.josephperrier.com/wp-content/uploads/2025/06/CAB2.webp",
        "https://www.josephperrier.com/wp-content/uploads/2025/06/CAB3.webp",
    ],
    "Joséphine 2014": [
        "https://www.josephperrier.com/wp-content/uploads/2023/04/JOSITE-.webp",
    ],
    "Cuvée 200": [
        "https://www.josephperrier.com/wp-content/uploads/2025/01/1.webp",
        "https://www.josephperrier.com/wp-content/uploads/2025/01/2.webp",
    ],
}


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    products = conn.execute("SELECT id, name FROM product").fetchall()

    for p in products:
        pid, name = p["id"], p["name"]

        # Step 1: Keep only first non-award image, delete rest
        images = conn.execute(
            "SELECT id FROM media WHERE product_id = ? AND media_type = 'image' AND context != 'award_badge' ORDER BY id",
            (pid,),
        ).fetchall()
        deleted = 0
        if len(images) > 1:
            ids_to_delete = [r["id"] for r in images[1:]]
            conn.execute(
                f"DELETE FROM media WHERE id IN ({','.join('?' * len(ids_to_delete))})",
                ids_to_delete,
            )
            deleted = len(ids_to_delete)

        # Step 2: Insert curated gallery images (idempotent)
        urls = CURATED_GALLERY.get(name, [])
        existing_urls = set(
            r[0] for r in conn.execute(
                "SELECT url FROM media WHERE product_id = ?", (pid,)
            ).fetchall()
        )
        added = 0
        for url in urls:
            if url not in existing_urls:
                conn.execute(
                    "INSERT INTO media (product_id, media_type, url, alt_text, context) VALUES (?, 'image', ?, ?, 'curated_gallery')",
                    (pid, url, f"{name} gallery"),
                )
                added += 1

        print(f"  {name:30s} | deleted {deleted:2d} dupes | added {added} gallery images")

    conn.commit()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

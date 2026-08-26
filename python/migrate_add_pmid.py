"""One-off migration: add pmid/mesh_terms columns to review.db and populate
them for source='NLM' rows by title-matching against a PubMed .nbib file.

Run once: python migrate_add_pmid.py
"""
import re
import sqlite3
from pathlib import Path

from bib_reader import BibParser

DB_PATH = Path(__file__).parent / "review.db"
NBIB_PATH = Path(__file__).parent / "bibs" / "pubmed-StudentsMe-set.nbib"


def norm_title(title):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", (title or "").lower())).strip()


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cols = {row[1] for row in cur.execute("PRAGMA table_info(papers)").fetchall()}
    if "pmid" not in cols:
        cur.execute("ALTER TABLE papers ADD COLUMN pmid TEXT")
    if "mesh_terms" not in cols:
        cur.execute("ALTER TABLE papers ADD COLUMN mesh_terms TEXT")
    conn.commit()

    records = BibParser().parse(str(NBIB_PATH))
    by_title = {}
    for rec in records:
        by_title.setdefault(norm_title(rec.get("TI", "")), rec)

    rows = cur.execute(
        "SELECT id, title FROM papers WHERE source='NLM'"
    ).fetchall()

    matched, unmatched = 0, []
    for id_, title in rows:
        rec = by_title.get(norm_title(title))
        if rec is None:
            unmatched.append((id_, title))
            continue
        pmid = rec.get("PMID")
        mesh = rec.get("MH")
        mesh_str = "; ".join(mesh) if isinstance(mesh, list) else (mesh or "")
        cur.execute(
            "UPDATE papers SET pmid = ?, mesh_terms = ? WHERE id = ?",
            (pmid, mesh_str, id_),
        )
        matched += 1

    conn.commit()
    conn.close()

    print(f"Matched {matched}/{len(rows)} NLM rows to PMIDs.")
    if unmatched:
        print(f"Unmatched ({len(unmatched)}):")
        for id_, title in unmatched:
            print(f"  id={id_}: {title!r}")


if __name__ == "__main__":
    main()

"""SQLite access for the labeled PubMed article set in review.db.

Schema (papers table, relevant columns):
    id INTEGER, title TEXT, abstract TEXT, decision TEXT, source TEXT,
    user_decision TEXT, pmid TEXT, mesh_terms TEXT (added by migrate_add_pmid.py)

Relevance label: user_decision if set, else decision ('INCLUDE'/'EXCLUDE'/
'UNCERTAIN'). Rows with an effective label of 'UNCERTAIN' are excluded from
the labeled set used for query optimization.
"""
import random
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent / "review.db"


def _effective_label(decision, user_decision):
    label = user_decision if user_decision else decision
    if label not in ("INCLUDE", "EXCLUDE"):
        return None
    return label


def get_labeled_articles(db_path=DEFAULT_DB_PATH, source="NLM"):
    """Return list of dicts: pmid, title, abstract, mesh_terms, label ('relevant'/'irrelevant').

    Only rows with a non-null pmid and a resolved INCLUDE/EXCLUDE label are returned.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, pmid, title, abstract, mesh_terms, decision, user_decision "
            "FROM papers WHERE source = ? AND pmid IS NOT NULL",
            (source,),
        ).fetchall()
    finally:
        conn.close()

    articles = []
    for row in rows:
        label = _effective_label(row["decision"], row["user_decision"])
        if label is None:
            continue
        articles.append(
            {
                "id": row["id"],
                "pmid": str(row["pmid"]),
                "title": row["title"],
                "abstract": row["abstract"],
                "mesh_terms": row["mesh_terms"] or "",
                "label": "relevant" if label == "INCLUDE" else "irrelevant",
            }
        )
    return articles


def stratified_split(articles, train_frac=0.7, seed=42):
    """Stratified split by label, preserving class balance. Returns (train, holdout)."""
    rng = random.Random(seed)
    by_label = {}
    for art in articles:
        by_label.setdefault(art["label"], []).append(art)

    train, holdout = [], []
    for label, group in by_label.items():
        group = list(group)
        rng.shuffle(group)
        n_train = round(len(group) * train_frac)
        train.extend(group[:n_train])
        holdout.extend(group[n_train:])

    rng.shuffle(train)
    rng.shuffle(holdout)
    return train, holdout


def update_metadata_cache(pmid_to_fields, db_path=DEFAULT_DB_PATH):
    """Write fetched (abstract, mesh_terms) back into review.db for rows matching pmid.

    pmid_to_fields: dict pmid -> {"abstract": str, "mesh_terms": str, "title": str}
    """
    conn = sqlite3.connect(db_path)
    try:
        for pmid, fields in pmid_to_fields.items():
            conn.execute(
                "UPDATE papers SET abstract = COALESCE(NULLIF(?, ''), abstract), "
                "mesh_terms = COALESCE(NULLIF(?, ''), mesh_terms) WHERE pmid = ?",
                (fields.get("abstract", ""), fields.get("mesh_terms", ""), pmid),
            )
        conn.commit()
    finally:
        conn.close()

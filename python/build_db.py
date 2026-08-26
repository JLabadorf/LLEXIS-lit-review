"""Load reasoning_results.csv into a SQLite database for the review UI."""
import csv
import sqlite3
from pathlib import Path

CSV_PATH = Path(__file__).parent / "reasoning_results.csv"
DB_PATH = Path(__file__).parent / "review.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    abstract TEXT,
    decision TEXT,
    reasoning TEXT,
    source TEXT,
    review TEXT,
    qa_decision TEXT,
    user_decision TEXT,
    user_notes TEXT,
    reviewed_at TEXT
);
"""


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)

    existing = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    if existing > 0:
        print(f"papers table already has {existing} rows; skipping import.")
        conn.close()
        return

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                row["title"],
                row["abstract"],
                row["decision"],
                row["reasoning"],
                row["source"],
                row["review"],
                row["qa_decision"],
            )
            for row in reader
        ]

    conn.executemany(
        """INSERT INTO papers
           (title, abstract, decision, reasoning, source, review, qa_decision)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    print(f"Imported {len(rows)} rows into {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()

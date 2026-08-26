"""Flask UI for reviewing LLM screening results item-by-item.

Run with:  python flask_app.py
Then open http://localhost:5000

Keyboard shortcuts:
    d       -> mark INCLUDE and go to next item
    a       -> mark EXCLUDE and go to next item
    w       -> mark MAYBE and go to next item
    s       -> clear your decision for this item
    space   -> next item (no change)
    p       -> previous item
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request

DB_PATH = Path(__file__).parent / "review.db"

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_ids(classification=None, graded=None, disagreement=None):
    """classification: 'INCLUDE' / 'EXCLUDE' / None (any).
    graded: 'yes' (has user_decision) / 'no' (does not) / None (any).
    disagreement: 'yes' (user_decision set and differs from decision) / None (any).
    """
    db = get_db()
    clauses = []
    params = []
    if classification:
        clauses.append("decision = ?")
        params.append(classification)
    if graded == "yes":
        clauses.append("user_decision IS NOT NULL")
    elif graded == "no":
        clauses.append("user_decision IS NULL")
    if disagreement == "yes":
        clauses.append("user_decision IS NOT NULL AND user_decision != decision")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = db.execute(f"SELECT id FROM papers {where} ORDER BY id", params)
    return [r["id"] for r in rows]


def get_classifications():
    db = get_db()
    rows = db.execute(
        "SELECT DISTINCT decision FROM papers WHERE decision IS NOT NULL ORDER BY decision"
    )
    return [r["decision"] for r in rows]


def parse_filters(req):
    classification = req.args.get("classification") or None
    graded = req.args.get("graded") or None
    disagreement = req.args.get("disagreement") or None
    return classification, graded, disagreement


def get_paper(paper_id):
    db = get_db()
    return db.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()


def get_filtered_reviewed_count(classification=None, disagreement=None):
    """Count of reviewed items within a classification/disagreement filter (ignoring graded filter)."""
    return len(get_ids(classification, "yes", disagreement))


def paper_to_dict(paper, ids, classification=None, disagreement=None):
    idx = ids.index(paper["id"]) if paper["id"] in ids else -1
    return {
        "id": paper["id"],
        "idx": idx,
        "total": len(ids),
        "title": paper["title"],
        "abstract": paper["abstract"],
        "decision": paper["decision"],
        "reasoning": paper["reasoning"],
        "source": paper["source"],
        "qa_decision": paper["qa_decision"],
        "user_decision": paper["user_decision"],
        "filtered_reviewed_count": get_filtered_reviewed_count(classification, disagreement),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/meta")
def api_meta():
    return jsonify({"classifications": get_classifications()})


@app.route("/api/paper/<int:idx>")
def api_paper(idx):
    classification, graded, disagreement = parse_filters(request)
    ids = get_ids(classification, graded, disagreement)
    if not ids:
        return jsonify({"empty": True, "total": 0})
    idx = max(0, min(idx, len(ids) - 1))
    paper = get_paper(ids[idx])
    return jsonify(paper_to_dict(paper, ids, classification, disagreement))


@app.route("/api/decide", methods=["POST"])
def api_decide():
    data = request.get_json(force=True)
    paper_id = data["id"]
    decision = data.get("decision")  # INCLUDE / EXCLUDE / MAYBE / None
    classification = data.get("classification") or None
    graded = data.get("graded") or None
    disagreement = data.get("disagreement") or None
    db = get_db()
    db.execute(
        "UPDATE papers SET user_decision = ?, reviewed_at = ? WHERE id = ?",
        (decision, datetime.now(timezone.utc).isoformat(), paper_id),
    )
    db.commit()
    ids = get_ids(classification, graded, disagreement)
    paper = get_paper(paper_id)
    return jsonify(paper_to_dict(paper, ids, classification, disagreement))


if __name__ == "__main__":
    # The reloader's default watcher walks the whole project dir, including
    # .venv, which churns endlessly (and can crash the process) whenever
    # packages there change. Disable auto-reload; restart manually after
    # editing flask_app.py or templates/index.html.
    app.run(debug=True, port=5000, use_reloader=False)

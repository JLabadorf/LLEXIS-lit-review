"""Streamlit UI for reviewing LLM screening results item-by-item.

Run with:  streamlit run review_app.py

Keyboard shortcuts (click anywhere on the page first so it has focus):
    d       -> mark INCLUDE and go to next item
    a       -> mark EXCLUDE and go to next item
    w       -> mark MAYBE and go to next item
    s       -> clear your decision for this item
    space   -> next item (no change)
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

DB_PATH = Path(__file__).parent / "review.db"

st.set_page_config(page_title="Lit Review QA", layout="centered")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


conn = get_conn()


@st.cache_data(ttl=1)
def load_ids():
    rows = conn.execute("SELECT id FROM papers ORDER BY id").fetchall()
    return [r["id"] for r in rows]


def get_paper(paper_id):
    return conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()


def set_decision(paper_id, decision):
    conn.execute(
        "UPDATE papers SET user_decision = ?, reviewed_at = ? WHERE id = ?",
        (decision, datetime.now(timezone.utc).isoformat(), paper_id),
    )
    conn.commit()
    st.cache_data.clear()


ids = load_ids()
total = len(ids)

if "idx" not in st.session_state:
    st.session_state.idx = 0

st.session_state.idx = max(0, min(st.session_state.idx, total - 1))
paper = get_paper(ids[st.session_state.idx])

reviewed_count = conn.execute(
    "SELECT COUNT(*) c FROM papers WHERE user_decision IS NOT NULL"
).fetchone()["c"]

st.progress(reviewed_count / total if total else 0)
st.caption(
    f"Item {st.session_state.idx + 1} of {total}  |  "
    f"{reviewed_count} reviewed  |  paper id {paper['id']}"
)

st.markdown(f"### {paper['title']}")

col1, col2, col3 = st.columns(3)
col1.metric("AI decision", paper["decision"] or "—")
col2.metric("QA agreement", paper["qa_decision"] or "—")
col3.metric("Your decision", paper["user_decision"] or "—")

st.markdown("**Abstract**")
st.write(paper["abstract"])

with st.expander("AI reasoning / source"):
    st.write(f"**Source:** {paper['source']}")
    st.write(f"**Reasoning:** {paper['reasoning']}")

st.divider()

BTN_EXCLUDE = "❌ Exclude (a)"
BTN_MAYBE = "❓ Maybe (w)"
BTN_CLEAR = "Clear (s)"
BTN_INCLUDE = "✅ Include (d)"
BTN_NEXT = "Next ➡ (space)"
BTN_PREV = "⬅ Prev (p)"

nav1, nav2, nav3, nav4, nav5 = st.columns(5)
if nav1.button(BTN_EXCLUDE):
    set_decision(paper["id"], "EXCLUDE")
    st.session_state.idx = min(st.session_state.idx + 1, total - 1)
    st.rerun()
if nav2.button(BTN_MAYBE):
    set_decision(paper["id"], "MAYBE")
    st.session_state.idx = min(st.session_state.idx + 1, total - 1)
    st.rerun()
if nav3.button(BTN_CLEAR):
    set_decision(paper["id"], None)
    st.rerun()
if nav4.button(BTN_INCLUDE):
    set_decision(paper["id"], "INCLUDE")
    st.session_state.idx = min(st.session_state.idx + 1, total - 1)
    st.rerun()
if nav5.button(BTN_NEXT):
    st.session_state.idx = min(st.session_state.idx + 1, total - 1)
    st.rerun()

if st.button(BTN_PREV):
    st.session_state.idx = max(st.session_state.idx - 1, 0)
    st.rerun()

st.caption("Shortcuts: a=exclude, w=maybe, s=clear, d=include, space=next, p=prev "
           "(click the page once so it has keyboard focus)")

# JS listener: on keydown, find the matching Streamlit button in the parent
# document (by its unique label) and click it directly. This avoids
# navigating/reloading the page, which the sandboxed component iframe blocks.
components.html(
    """
    <script>
    const doc = window.parent.document;
    if (!doc._shortcutsBound) {
        doc._shortcutsBound = true;
        const keyToLabel = {
            'a': 'Exclude (a)',
            'w': 'Maybe (w)',
            's': 'Clear (s)',
            'd': 'Include (d)',
            ' ': 'Next ➡ (space)',
            'p': 'Prev (p)',
        };
        function clickByLabel(labelFragment) {
            const buttons = doc.querySelectorAll('button');
            for (const btn of buttons) {
                if (btn.innerText && btn.innerText.indexOf(labelFragment) !== -1) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }
        doc.addEventListener('keydown', function(e) {
            const tag = (e.target && e.target.tagName) || '';
            if (tag === 'INPUT' || tag === 'TEXTAREA') return;
            const labelFragment = keyToLabel[e.key];
            if (!labelFragment) return;
            e.preventDefault();
            clickByLabel(labelFragment);
        }, true);
    }
    </script>
    """,
    height=0,
)

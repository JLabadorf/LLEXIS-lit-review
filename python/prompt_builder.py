"""Builds the query-edit prompt and calls the LLM proxy (llm.py) to get one
structured edit proposal per iteration."""
import json
import re

PROMPT_TEMPLATE = """You are refining a PubMed (PICO-style) boolean search query for a \
systematic review, so that it retrieves more of the known-relevant articles and \
fewer of the known-irrelevant ones.

CURRENT QUERY:
{query}

CURRENT PERFORMANCE (on a held-out-from-you training sample):
Precision: {precision:.3f}  Recall: {recall:.3f}  F{beta:g}: {f_beta:.3f}
True positives: {tp}  False negatives (missed relevant): {fn}  False positives (wrongly retrieved): {fp}

ARTICLES THE QUERY IS MISSING (false negatives - should be retrieved but are not):
{false_negatives}

ARTICLES THE QUERY WRONGLY RETRIEVES (false positives - retrieved but irrelevant):
{false_positives}

MeSH TERMS SEEN ONLY IN MISSED RELEVANT ARTICLES (a signal, not an exhaustive list):
{fn_only_mesh}

MeSH TERMS SEEN ONLY IN WRONGLY-RETRIEVED ARTICLES (a signal, not an exhaustive list):
{fp_only_mesh}

INSTRUCTIONS:
Rewrite the query however you judge will best improve it. You are not limited
to picking a term from the lists above - use your own judgment about wording,
synonyms, MeSH terms, field tags, and boolean structure, drawing on the
titles/abstracts/MeSH terms shown above as evidence. Make exactly ONE
meaningful, targeted change per iteration (do not rewrite the whole query from
scratch) so its effect can be measured, and prefer the smallest change that
plausibly fixes the pattern you observe. After making your edit, classify it
as one of: add_mesh_term, remove_mesh_term, add_synonym, remove_synonym,
change_boolean_operator, add_field_tag, remove_field_tag, other.

Return ONLY a JSON object, no other text:

```json
{{"new_query": "<the full revised query string>",
"edit_type": "<one of the edit types above>",
"justification": "<one sentence explaining the edit>"}}
```
"""


def _format_articles(articles, limit=5):
    if not articles:
        return "(none)"
    lines = []
    for art in articles[:limit]:
        lines.append(
            f"- PMID {art['pmid']}\n"
            f"  Title: {art['title']}\n"
            f"  Abstract: {(art['abstract'] or '')[:500]}\n"
            f"  MeSH: {art['mesh_terms'] or '(none)'}"
        )
    return "\n".join(lines)


def _mesh_terms_of(article):
    return {t.strip() for t in (article["mesh_terms"] or "").split(";") if t.strip()}


def _differentiated_mesh_terms(articles, other_articles):
    terms = set()
    for art in articles:
        terms |= _mesh_terms_of(art)
    other_terms = set()
    for art in other_articles:
        other_terms |= _mesh_terms_of(art)
    only_terms = sorted(terms - other_terms)
    return ", ".join(only_terms) if only_terms else "(none)"


def build_prompt(query, score_result, false_negative_articles, false_positive_articles, beta):
    return PROMPT_TEMPLATE.format(
        query=query,
        precision=score_result["precision"],
        recall=score_result["recall"],
        beta=beta,
        f_beta=score_result["f_beta"],
        tp=score_result["tp"],
        fn=score_result["fn"],
        fp=score_result["fp"],
        false_negatives=_format_articles(false_negative_articles),
        false_positives=_format_articles(false_positive_articles),
        fn_only_mesh=_differentiated_mesh_terms(false_negative_articles, false_positive_articles),
        fp_only_mesh=_differentiated_mesh_terms(false_positive_articles, false_negative_articles),
    )


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text.strip()).strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM response: {text!r}")
    return json.loads(match.group(0))


def propose_edit(client, query, score_result, false_negative_articles, false_positive_articles, beta):
    """Call the LLM (via llm.py's Client) to propose one query edit.

    Returns dict: new_query, edit_type, justification.
    Raises ValueError if the response cannot be parsed.
    """
    prompt = build_prompt(query, score_result, false_negative_articles, false_positive_articles, beta)
    raw = client.send(prompt)
    response_text = raw["response"] if isinstance(raw, dict) and "response" in raw else raw
    parsed = _extract_json(response_text)

    for key in ("new_query", "edit_type", "justification"):
        if key not in parsed:
            raise ValueError(f"LLM response missing required key '{key}': {parsed!r}")
    return parsed

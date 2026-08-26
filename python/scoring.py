"""Precision / recall / F-beta scoring of a retrieved PMID set against labels."""


def score(retrieved_pmids, labeled_articles, beta=2.0):
    """Compare a retrieved PMID set against a labeled set (train or holdout).

    labeled_articles: list of dicts with "pmid" and "label" ('relevant'/'irrelevant').

    Returns dict with precision, recall, f_beta, and the PMID sets for
    true positives, false negatives (missed relevant), false positives
    (wrongly retrieved irrelevant).
    """
    relevant = {a["pmid"] for a in labeled_articles if a["label"] == "relevant"}
    irrelevant = {a["pmid"] for a in labeled_articles if a["label"] == "irrelevant"}

    true_positives = retrieved_pmids & relevant
    false_negatives = relevant - retrieved_pmids
    false_positives = retrieved_pmids & irrelevant

    tp, fn, fp = len(true_positives), len(false_negatives), len(false_positives)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    beta_sq = beta * beta
    denom = (beta_sq * precision) + recall
    f_beta = (1 + beta_sq) * precision * recall / denom if denom > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f_beta": f_beta,
        "beta": beta,
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "true_positives": true_positives,
        "false_negatives": false_negatives,
        "false_positives": false_positives,
    }

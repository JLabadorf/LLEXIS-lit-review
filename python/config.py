"""Configuration for the query optimizer, via CLI args."""
import argparse

DEFAULT_QUERY = (
    '("Large Language Models"[Mesh] OR "ChatGPT"[tiab] OR "LLM"[tiab] OR '
    '"generative artificial intelligence"[tiab]) AND '
    '("feedback"[tiab] OR "formative feedback"[tiab]) AND '
    '("writing"[tiab] OR "scientific writing"[tiab]) AND '
    '("medical education"[Mesh] OR "medical students"[tiab] OR "nursing students"[tiab])'
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Iteratively optimize a PubMed search query with an LLM.")
    parser.add_argument("--db-path", default="review.db", help="Path to the SQLite database.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Starting PubMed query.")
    parser.add_argument("--model", default="anthropic.claude-opus-5", help="Model id passed to llm.Client.")
    parser.add_argument("--beta", type=float, default=2.0, help="Beta for F-beta scoring.")
    parser.add_argument("--max-iterations", type=int, default=30, help="Maximum optimization iterations.")
    parser.add_argument("--patience", type=int, default=8, help="Stop after this many consecutive non-improving iterations.")
    parser.add_argument("--train-frac", type=float, default=0.7, help="Fraction of labeled data used for training.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for the train/holdout split.")
    parser.add_argument("--holdout-every", type=int, default=5, help="Score against holdout every N iterations.")
    parser.add_argument("--sample-size", type=int, default=5, help="Max false negatives/positives sampled per iteration.")
    parser.add_argument("--entrez-email", default=None, help="Contact email required by NCBI Entrez.")
    parser.add_argument("--entrez-api-key", default=None, help="Optional NCBI API key (raises rate limit to 10 req/sec).")
    parser.add_argument("--log-path", default="optimizer_log.jsonl", help="Path to the JSONL iteration log.")
    parser.add_argument("--cache-path", default="entrez_cache.json", help="Local JSON cache for fetched metadata.")
    return parser.parse_args(argv)

"""Main loop: iteratively refine a PubMed query using an LLM as the editor,
scored against a labeled train/holdout split. See config.py for CLI args."""
import json
import random
import time
from pathlib import Path

import bedrock_client
import db_client
import entrez_client
import prompt_builder
import scoring
from config import parse_args
from llm import Client as ProxyClient


def _load_cache(cache_path):
    path = Path(cache_path)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache_path, cache):
    Path(cache_path).write_text(json.dumps(cache, indent=2), encoding="utf-8")


def ensure_metadata(articles, cache_path, entrez_email, entrez_api_key, db_path):
    """Fill in missing title/abstract/mesh_terms via Entrez, caching results
    to both a local JSON file and back into the database."""
    missing = [a for a in articles if not a["abstract"]]
    if not missing:
        return articles

    cache = _load_cache(cache_path)
    still_missing = [a for a in missing if a["pmid"] not in cache]

    if still_missing:
        if not entrez_email:
            raise ValueError(
                f"{len(still_missing)} articles are missing abstracts and no "
                "--entrez-email was provided to fetch them from NCBI."
            )
        entrez_client.configure(entrez_email, entrez_api_key)
        fetched = entrez_client.fetch_metadata(
            [a["pmid"] for a in still_missing], api_key=entrez_api_key
        )
        cache.update(fetched)
        _save_cache(cache_path, cache)
        db_client.update_metadata_cache(fetched, db_path=db_path)

    for art in missing:
        cached = cache.get(art["pmid"])
        if cached:
            art["abstract"] = art["abstract"] or cached.get("abstract", "")
            art["mesh_terms"] = art["mesh_terms"] or cached.get("mesh_terms", "")

    return articles


def sample_misses(score_result, labeled_by_pmid, sample_size, seed_rng):
    """Draw a fresh random sample of up to sample_size false negatives/positives.

    Uses rng.sample (without replacement, freshly drawn each call) rather than
    shuffle+slice, so each iteration sees a different subset of the miss pool
    instead of repeatedly showing the same articles/MeSH terms to the LLM.
    """
    fn_pmids = list(score_result["false_negatives"])
    fp_pmids = list(score_result["false_positives"])
    fn_sample = seed_rng.sample(fn_pmids, min(sample_size, len(fn_pmids)))
    fp_sample = seed_rng.sample(fp_pmids, min(sample_size, len(fp_pmids)))
    fn_articles = [labeled_by_pmid[p] for p in fn_sample]
    fp_articles = [labeled_by_pmid[p] for p in fp_sample]
    return fn_articles, fp_articles


def run(args):
    articles = db_client.get_labeled_articles(db_path=args.db_path)
    if not articles:
        raise ValueError("No labeled NLM articles with a pmid found in the database.")

    articles = ensure_metadata(
        articles, args.cache_path, args.entrez_email, args.entrez_api_key, args.db_path
    )

    train, holdout = db_client.stratified_split(articles, train_frac=args.train_frac, seed=args.seed)
    train_by_pmid = {a["pmid"]: a for a in train}
    print(
        f"Train: {len(train)} ({sum(1 for a in train if a['label']=='relevant')} relevant), "
        f"Holdout: {len(holdout)} ({sum(1 for a in holdout if a['label']=='relevant')} relevant)"
    )

    if args.model.startswith("anthropic.claude-opus-5"):
        # The local proxy sends a `temperature` param that Opus 5 rejects
        # ("temperature is deprecated for this model"), so call Bedrock directly.
        client = bedrock_client.Client(model=args.model)
    else:
        client = ProxyClient(model=args.model)
    rng = random.Random(args.seed)

    best_query = args.query
    retrieved = entrez_client.run_query(best_query, api_key=args.entrez_api_key)
    best_score = scoring.score(retrieved, train, beta=args.beta)
    print(f"Initial train F{args.beta:g}: {best_score['f_beta']:.3f} "
          f"(P={best_score['precision']:.3f}, R={best_score['recall']:.3f})")

    log_records = []
    no_improve_count = 0

    for iteration in range(1, args.max_iterations + 1):
        fn_articles, fp_articles = sample_misses(best_score, train_by_pmid, args.sample_size, rng)

        record = {
            "iteration": iteration,
            "query": None,
            "train_precision": None,
            "train_recall": None,
            "train_f_beta": None,
            "holdout_f_beta": None,
            "edit_type": None,
            "justification": None,
            "accepted": None,
            "llm_latency_sec": None,
        }

        try:
            llm_start = time.monotonic()
            edit = prompt_builder.propose_edit(
                client, best_query, best_score, fn_articles, fp_articles, args.beta
            )
            llm_latency = time.monotonic() - llm_start
            record["llm_latency_sec"] = round(llm_latency, 2)
            print(f"[iter {iteration}] LLM call took {llm_latency:.2f}s")
        except Exception as exc:
            print(f"[iter {iteration}] LLM proposal failed: {exc}")
            record.update({"query": best_query, "edit_type": "ERROR", "justification": str(exc), "accepted": False})
            log_records.append(record)
            no_improve_count += 1
            if no_improve_count >= args.patience:
                print(f"Stopping: no improvement for {args.patience} consecutive iterations.")
                break
            continue

        new_query = edit["new_query"]
        try:
            retrieved = entrez_client.run_query(new_query, api_key=args.entrez_api_key)
        except Exception as exc:
            print(f"[iter {iteration}] Query execution failed: {exc}")
            record.update({
                "query": new_query, "edit_type": edit.get("edit_type"),
                "justification": edit.get("justification"), "accepted": False,
            })
            log_records.append(record)
            no_improve_count += 1
            if no_improve_count >= args.patience:
                print(f"Stopping: no improvement for {args.patience} consecutive iterations.")
                break
            continue

        new_score = scoring.score(retrieved, train, beta=args.beta)

        record.update({
            "query": new_query,
            "train_precision": new_score["precision"],
            "train_recall": new_score["recall"],
            "train_f_beta": new_score["f_beta"],
            "edit_type": edit.get("edit_type"),
            "justification": edit.get("justification"),
        })

        if new_score["f_beta"] > best_score["f_beta"]:
            best_query, best_score = new_query, new_score
            record["accepted"] = True
            no_improve_count = 0
            print(f"[iter {iteration}] ACCEPTED ({edit.get('edit_type')}): "
                  f"F{args.beta:g}={new_score['f_beta']:.3f} "
                  f"(P={new_score['precision']:.3f}, R={new_score['recall']:.3f})")
        else:
            record["accepted"] = False
            no_improve_count += 1
            print(f"[iter {iteration}] rejected ({edit.get('edit_type')}): "
                  f"F{args.beta:g}={new_score['f_beta']:.3f} <= best {best_score['f_beta']:.3f}")

        if iteration % args.holdout_every == 0:
            holdout_retrieved = entrez_client.run_query(best_query, api_key=args.entrez_api_key)
            holdout_score = scoring.score(holdout_retrieved, holdout, beta=args.beta)
            record["holdout_f_beta"] = holdout_score["f_beta"]
            print(f"[iter {iteration}] holdout F{args.beta:g}: {holdout_score['f_beta']:.3f} "
                  f"(P={holdout_score['precision']:.3f}, R={holdout_score['recall']:.3f})")

        log_records.append(record)

        if no_improve_count >= args.patience:
            print(f"Stopping: no improvement for {args.patience} consecutive iterations.")
            break

    with open(args.log_path, "w", encoding="utf-8") as f:
        for rec in log_records:
            f.write(json.dumps(rec) + "\n")

    final_holdout_retrieved = entrez_client.run_query(best_query, api_key=args.entrez_api_key)
    final_holdout_score = scoring.score(final_holdout_retrieved, holdout, beta=args.beta)

    print("\n" + "=" * 60)
    print("BEST QUERY:")
    print(best_query)
    print(f"\nTrain:   F{args.beta:g}={best_score['f_beta']:.3f}  "
          f"P={best_score['precision']:.3f}  R={best_score['recall']:.3f}  "
          f"TP={best_score['tp']} FN={best_score['fn']} FP={best_score['fp']}")
    print(f"Holdout: F{args.beta:g}={final_holdout_score['f_beta']:.3f}  "
          f"P={final_holdout_score['precision']:.3f}  R={final_holdout_score['recall']:.3f}  "
          f"TP={final_holdout_score['tp']} FN={final_holdout_score['fn']} FP={final_holdout_score['fp']}")

    holdout_points = [(r["iteration"], r["holdout_f_beta"]) for r in log_records if r["holdout_f_beta"] is not None]
    train_points = [(r["iteration"], r["train_f_beta"]) for r in log_records if r["accepted"]]
    print("\nTrain vs holdout F-beta over accepted iterations (overfitting check):")
    print("  iter | train F-beta | holdout F-beta")
    holdout_by_iter = dict(holdout_points)
    for it, train_f in train_points:
        ho = holdout_by_iter.get(it)
        print(f"  {it:4d} | {train_f:.3f}       | {ho if ho is None else f'{ho:.3f}'}")

    if len(holdout_points) >= 2:
        train_delta = train_points[-1][1] - train_points[0][1] if len(train_points) >= 2 else 0
        holdout_delta = holdout_points[-1][1] - holdout_points[0][1]
        if train_delta > 0 and holdout_delta < 0:
            print("\nWARNING: train F-beta improved while holdout F-beta declined — possible overfitting to train misses.")

    print(f"\nFull iteration log written to {args.log_path}")


if __name__ == "__main__":
    run(parse_args())

"""NCBI Entrez access: run PubMed ESearch queries and fetch missing metadata.

Rate limits (per NCBI E-utilities policy): 3 req/sec without an API key,
10 req/sec with one. Pass api_key to raise the limit.
"""
import time

from Bio import Entrez

_last_request_time = [0.0]


def _rate_limit(api_key):
    min_interval = 1.0 / 10 if api_key else 1.0 / 3
    elapsed = time.monotonic() - _last_request_time[0]
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _last_request_time[0] = time.monotonic()


def configure(email, api_key=None):
    """Set the contact email NCBI requires, and optionally an API key."""
    Entrez.email = email
    if api_key:
        Entrez.api_key = api_key


def run_query(query, api_key=None, retmax=10000):
    """Run a PubMed ESearch query, return the set of retrieved PMIDs (as strings)."""
    _rate_limit(api_key)
    handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax)
    try:
        record = Entrez.read(handle)
    finally:
        handle.close()
    return set(record.get("IdList", []))


def fetch_metadata(pmids, api_key=None, batch_size=200):
    """Fetch title/abstract/MeSH terms for a list of PMIDs via EFetch.

    Returns dict: pmid -> {"title": str, "abstract": str, "mesh_terms": str}.
    """
    results = {}
    pmids = list(pmids)
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i : i + batch_size]
        _rate_limit(api_key)
        handle = Entrez.efetch(db="pubmed", id=",".join(batch), rettype="medline", retmode="xml")
        try:
            data = Entrez.read(handle)
        finally:
            handle.close()

        for article in data.get("PubmedArticle", []):
            medline = article["MedlineCitation"]
            pmid = str(medline["PMID"])
            article_data = medline["Article"]
            title = str(article_data.get("ArticleTitle", ""))

            abstract_parts = article_data.get("Abstract", {}).get("AbstractText", [])
            abstract = " ".join(str(part) for part in abstract_parts)

            mesh_headings = medline.get("MeshHeadingList", [])
            mesh_terms = "; ".join(
                str(heading["DescriptorName"]) for heading in mesh_headings
            )

            results[pmid] = {
                "title": title,
                "abstract": abstract,
                "mesh_terms": mesh_terms,
            }
    return results

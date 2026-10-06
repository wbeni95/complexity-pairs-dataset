"""Literature check for the mutation pilot (2026-10-06d).

1. Verifies every DOI in mutations/literature.py against Crossref (DataCite fallback): title match via
   tools/check_sources.title_matches and year within 1. Output: mutations/records/2026-10-06d/literature.jsonl.
2. For references whose recalled DOI did not match, one Crossref bibliographic query each (query.bibliographic,
   rows=3) to find the correct DOI. Output printed and appended to literature_queries.jsonl.

Etiquette: one connection, sequential, >= 1.05 s between Crossref/DataCite requests, >= 3.05 s between arXiv requests,
User-Agent identifies the project (mutations/literature.py).

First run (2026-10-06): 30 DOI OK, 2 MISMATCH (vassilevska-williams-yuster2009: Crossref record without the cited
title; duan-pettie2009: the recalled DOI belongs to another SODA 2009 paper), 7 without identifier.
"""
import json
import sys
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from mutations import literature  # noqa: E402

OUT = REPO / "mutations" / "records" / "2026-10-06d"

QUERIES = {
    "vassilevska-williams-yuster2009": "All pairs bottleneck paths and max-min matrix products in truly subcubic time "
                                       "Vassilevska Williams Yuster Theory of Computing",
    "duan-pettie2009": "Fast algorithms for (max, min)-matrix multiplication and bottleneck shortest paths Duan Pettie",
}


def query(text):
    raw = literature._get("https://api.crossref.org/works?rows=3&query.bibliographic=" + urllib.parse.quote(text),
                          "crossref")
    items = json.loads(raw)["message"]["items"]
    out = []
    for it in items:
        year = None
        for key in ("published-print", "published-online", "issued"):
            parts = it.get(key, {}).get("date-parts")
            if parts and parts[0] and parts[0][0]:
                year = parts[0][0]
                break
        out.append({"doi": it.get("DOI"), "title": " ".join(it.get("title") or []), "year": year,
                    "container": " ".join(it.get("container-title") or [])})
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--queries-only" not in sys.argv:
        rows = literature.verify_all()
        with open(OUT / "literature.jsonl", "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    res = []
    for key, text in QUERIES.items():
        hits = query(text)
        res.append({"key": key, "query": text, "hits": hits})
        for h in hits:
            print(f"{key}: {h['doi']} | {h['year']} | {h['title'][:100]} | {h['container'][:60]}")
    with open(OUT / "literature_queries.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in res:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

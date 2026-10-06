#!/usr/bin/env python3
"""Find DOIs for sources whose guessed DOI failed in experiments/2026-10-07_doi_checks.py.

Question: experiments/2026-10-07_doi_checks.py found that three guessed DOIs belong to OTHER papers
(10.1109/SFCS.1991.185345 is Chazelle's convex-hull paper, 10.1109/SFFCS.1999.814598 is "Long-lived adaptive
collect", 10.1007/BF02241984 is "Formal languages of labelled graphs") and that one DOI (10.4086/toc.2008.v004a008)
has no title in Crossref. What are the correct records?

Method: Crossref bibliographic search (api.crossref.org/works?query.bibliographic=...), top 3 hits per query,
printed with DOI, year, title and container. For the empty-title record, print the Crossref fields (volume,
page, year, container) so they can be compared field by field, as in RESEARCH_LOG RL-017. Deterministic in its
inputs; the output depends on the live Crossref index (external provenance).

Outcome (run 2026-10-07): the top hit of each query is the intended paper:
  Papadimitriou 1991 'On selecting a satisfying truth assignment' -> 10.1109/sfcs.1991.185365 (no issued year);
  Blaser 1999 'A 5/2n^2-lower bound for the rank of n x n-matrix multiplication over arbitrary fields'
    -> 10.1109/sffcs.1999.814576 (no issued year);
  Mehlhorn & Galil 'Monotone switching circuits and boolean matrix product' -> 10.1007/bf02241983 (Computing 1976);
  the third hit of that query, Paterson 1975 'Complexity of monotone networks for Boolean matrix product',
    10.1016/0304-3975(75)90009-2, was added to the report.
Records: 10.4086/toc.2008.v004a008 has an empty title, year 2008, volume 4, issue 1, pages 169-190;
10.1007/BFb0038202 has the expected title, no year, pages 359-370.
All found DOIs were then re-checked with experiments/2026-10-07_doi_checks.py (see its docstring). A DOI found
here is cited only after that check; otherwise the source is cited without a DOI and marked unverified.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from check_sources import _get, crossref_record  # noqa: E402

QUERIES = [
    "Papadimitriou On selecting a satisfying truth assignment FOCS 1991",
    "Blaser lower bound for the rank of n x n matrix multiplication over arbitrary fields 1999",
    "Mehlhorn Galil Monotone switching circuits and Boolean matrix product Computing 1976",
]
RECORDS = ["10.4086/toc.2008.v004a008", "10.1007/BFb0038202"]


def search(q: str, rows: int = 3):
    url = ("https://api.crossref.org/works?rows=%d&select=DOI,title,issued,container-title&query.bibliographic=%s"
           % (rows, urllib.parse.quote(q)))
    raw = _get(url)
    items = json.loads(raw)["message"]["items"] if raw else []
    for it in items:
        year = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
        print(f"    {it.get('DOI')}  {year}  {(it.get('title') or [''])[0]!r}  in {(it.get('container-title') or [''])[0]!r}")


def main() -> int:
    for q in QUERIES:
        print(f"query: {q}")
        search(q)
        time.sleep(1.0)
    for doi in RECORDS:
        rec = crossref_record(doi)
        print(f"record {doi}: {rec}")
        time.sleep(1.0)
    return 0


if __name__ == "__main__":
    sys.exit(main())

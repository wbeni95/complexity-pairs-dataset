#!/usr/bin/env python3
"""Crossref title/year check of the DOIs cited in research/2026-10-06d_rule_mining.md.

One connection, one request at a time, at least 1.2 s apart (project rule RL-073: at most 1 request per second
for Crossref), User-Agent identifying the project. Prints, for each DOI, the registered title, the first
author's family name and the year, or the HTTP error. The report labels a DOI [DOI OK] only if this script
printed a matching title and year.

Usage: python experiments/2026-10-06d_rules_doi_checks.py
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

UA = "complexity-pairs-dataset research agent (https://github.com/wbeni95/complexity-pairs-dataset)"
DOIS = [
    "10.1007/BF00264289",          # Knuth 1971, Optimum binary search trees
    "10.1145/800141.804691",       # Yao 1980, quadrangle inequalities
    "10.1145/1644015.1644032",     # Bein-Golin-Larmore-Zhang 2009, Knuth-Yao speedup and total monotonicity
    "10.1007/BF01584082",          # Edmonds 1971, Matroids and the greedy algorithm
    "10.1112/plms/s3-7.1.300",     # Rado 1957, Note on independence functions
    "10.1016/S0167-5060(08)70322-4",  # Korte-Hausmann 1978, greedy heuristic for independence systems
    "10.1145/321812.321823",       # Horowitz-Sahni 1974, computing partitions (knapsack MITM)
    "10.1007/BF02165411",          # Strassen 1969
    "10.1090/S0025-5718-1965-0178586-1",  # Cooley-Tukey 1965
    "10.1006/jcta.2001.3201",      # Pemantle-Wilson 2002, asymptotics of multivariate sequences I
]


def main() -> int:
    last = 0.0
    for doi in DOIS:
        wait = 1.2 - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        last = time.monotonic()
        req = urllib.request.Request(f"https://api.crossref.org/works/{doi}", headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                msg = json.load(r)["message"]
            title = (msg.get("title") or ["?"])[0]
            year = None
            for k in ("published-print", "published-online", "issued"):
                parts = msg.get(k, {}).get("date-parts")
                if parts and parts[0] and parts[0][0]:
                    year = parts[0][0]
                    break
            fam = (msg.get("author") or [{}])[0].get("family", "?")
            print(f"{doi} | {fam} | {year} | {title}")
        except urllib.error.HTTPError as e:
            print(f"{doi} | HTTP {e.code}")
        except Exception as e:  # network errors are reported, not hidden
            print(f"{doi} | ERROR {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

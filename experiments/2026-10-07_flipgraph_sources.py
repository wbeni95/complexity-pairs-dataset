"""Experiment (research/2026-10-07_search_flipgraph.md, section "Sources"): the identifiers cited in the flip-graph
report, checked against Crossref / DataCite (DOIs) and, only with --arxiv, the arXiv API.

The arXiv part was run once on 2026-10-06/07 (four API calls in total, including two searches: one for
'ti:"flip graph" AND ti:matrix' to find the Arai et al. id, and one for claims of 22-multiplication 3x3 schemes);
it is opt-in here to respect the arXiv rate limits. Two DOIs guessed from memory were WRONG or absent and are
listed as negative controls: 10.1145/3666000.3669715 resolves to a different paper ("Computing Krylov iterates
in the time of matrix multiplication"), and 10.1145/3610377.3610381 does not exist in Crossref or DataCite.

Run from the repository root:  python experiments/2026-10-07_flipgraph_sources.py [--arxiv]
"""
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_sources import ATOM, _get, crossref_record, lookup_doi, title_matches  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOIS = [
    ("10.1145/3597066.3597120", "Flip Graphs for Matrix Multiplication", 2023),
    ("10.1038/s41586-022-05172-4", "Discovering faster matrix multiplication algorithms with reinforcement learning", 2022),
    ("10.1007/BF02165411", "Gaussian elimination is not optimal", 1969),
    ("10.1090/S0002-9904-1976-13988-2", "A noncommutative algorithm for multiplying 3x3 matrices using 23 multiplications", 1976),
    ("10.1137/0120004", "On Minimizing the Number of Multiplications Necessary for Matrix Multiplication", 1971),
    ("10.1016/0024-3795(71)90009-7", "On multiplication of 2 x 2 matrices", 1971),
    ("10.1016/0304-3975(78)90045-2", "On varieties of optimal algorithms for the computation of bilinear mappings II. "
     "Optimal algorithms for 2x2-matrix multiplication", 1978),
    ("10.1016/j.jsc.2020.10.003", "New ways to multiply 3 x 3-matrices", 2021),
    ("10.1016/S0885-064X(02)00007-9", "On the complexity of the multiplication of matrices of small formats", 2003),
    ("10.1109/ICTAI.2014.36", "Twenty-Five Comparators Is Optimal When Sorting Nine Inputs (and Twenty-Nine for Ten)", 2014),
]
NEGATIVE = [
    ("10.1145/3666000.3669715", "Adaptive Flip Graph Algorithm for Matrix Multiplication"),
    ("10.1145/3610377.3610381", "The FBHHRBNRSSSHK-Algorithm for Multiplication in Z_2^{5x5} is still not the end of the story"),
]
ARXIV = [
    ("2212.01175", "Flip Graphs for Matrix Multiplication"),
    ("2210.04045", "The FBHHRBNRSSSHK-Algorithm for Multiplication in Z_2^{5x5} is still not the end of the story"),
    ("2312.16960", "Adaptive Flip Graph Algorithm for Matrix Multiplication"),
    ("1905.10192", "New ways to multiply 3 x 3-matrices"),
    ("2502.04514", "Flip Graphs with Symmetry and New Matrix Multiplication Schemes"),
    ("2610.01639", "Lower Bound of 22 for 3x3 Matrix Multiplication over the Integers"),
]

problems = 0
for doi, title, year in DOIS:
    rec = crossref_record(doi)
    if rec is None:
        found = lookup_doi(doi)
        ok = found is not None and title_matches(title, found[0]) and found[1] == year
        print(f"{'OK ' if ok else 'BAD'} {doi}: DataCite {found}")
    else:
        ok = title_matches(title, rec["title"]) and rec["year"] == year
        print(f"{'OK ' if ok else 'BAD'} {doi}: '{rec['title']}' ({rec['year']}), vol {rec['volume']}, "
              f"issue {rec['issue']}, pages {rec['page']}")
    problems += not ok
    time.sleep(0.3)
for doi, title in NEGATIVE:
    found = lookup_doi(doi)
    matches = found is not None and title_matches(title, found[0])
    print(f"negative control {doi}: found {found}; matches the paper we wanted: {matches}")
    problems += matches   # a negative control that suddenly matches would mean our record above is stale
if "--arxiv" in sys.argv:
    raw = _get("https://export.arxiv.org/api/query?max_results=20&id_list=" + ",".join(a for a, _ in ARXIV))
    got = {}
    for e in ET.fromstring(raw).findall(f"{ATOM}entry"):
        aid = e.findtext(f"{ATOM}id", "").rsplit("/abs/", 1)[-1].split("v")[0]
        got[aid] = " ".join(e.findtext(f"{ATOM}title", "").split())
    for aid, title in ARXIV:
        ok = aid in got and title_matches(title, got[aid])
        problems += not ok
        print(f"{'OK ' if ok else 'BAD'} arXiv:{aid}: {got.get(aid)}")
else:
    print("arXiv ids (checked once, not re-queried; pass --arxiv to re-check): " + ", ".join(a for a, _ in ARXIV))
print(f"problems: {problems}")

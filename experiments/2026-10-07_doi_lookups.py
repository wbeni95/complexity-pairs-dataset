"""Source check (network, Crossref/DataCite only; no arXiv queries): every DOI looked up while writing the eight
entries added on 2026-10-07, both cited and considered-but-not-cited, with the title and venue details
Crossref returns. The cited ones are also covered by `python tools/check_sources.py <entry folders>`, which on
2026-10-07 reported 25 identifiers checked (25 also on volume/issue/pages), 0 problems, and 2 sources without
DOI (Knuth TAOCP by ISBN, Dinic 1970).

Outcome (2026-10-07): every DOI below resolved, and every title matched the work intended.
Not cited, and why:
  * 10.1137/0220041 (Yao 1991): Crossref title "Lower Bounds for Algebraic Computation Trees of Functions with
    Finite Domains". It was considered for the integer-input version of the element-distinctness lower bound.
    The paper's content could not be checked, so it is not cited.
  * 10.1137/0204043 (Even & Tarjan 1975, "Network Flow and Testing Graph Connectivity"): considered for the
    O(E sqrt V) bound of Dinic's algorithm on unit-capacity bipartite networks. The content was not checked, so
    the remark was dropped from the matching entry.
  * 10.1145/2591796.2591811 (Williams, STOC 2014): the journal version 10.1137/15M1024524 is cited instead.
  * 10.1145/1250790.1250801 ("Fourier meets Möbius: fast subset convolution", 2007 per Crossref): looked up as a
    possible related source for the chromatic entry; not needed.

Run from the repository root (needs network):  python experiments/2026-10-07_doi_lookups.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_sources import crossref_record, lookup_doi  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CITED = [
    "10.1145/367766.368168", "10.1145/321105.321107", "10.1090/qam/102435", "10.1145/321992.321993",
    "10.1137/15M1024524", "10.1145/3186893",                                        # APSP
    "10.1145/321892.321896", "10.1016/0304-3975(94)00083-U",                        # palindromes
    "10.1145/800061.808735", "10.1016/0022-0000(79)90044-8",                        # element distinctness
    "10.1016/0020-0190(76)90065-X", "10.1137/070683933", "10.1007/BF02760024",
    "10.7155/jgaa.00064", "10.1007/978-1-4684-2001-2_9",                            # chromatic number
    "10.1007/10719839_9", "10.1137/090779759",                                      # RMQ
    "10.1137/0202019", "10.1073/pnas.43.9.842", "10.1002/nav.3800020109",           # bipartite matching
    "10.1145/321694.321699", "10.4153/CJM-1956-045-5", "10.1145/321679.321693",     # max flow
    "10.1109/SFFCS.1999.814612", "10.1145/800157.805047",                           # 3-SAT
]
NOT_CITED = ["10.1137/0220041", "10.1137/0204043", "10.1145/2591796.2591811", "10.1145/1250790.1250801"]

for label, dois in (("cited", CITED), ("looked up, not cited", NOT_CITED)):
    print(f"== {label}")
    for doi in dois:
        rec = crossref_record(doi)
        if rec is None:
            print(f"  {doi}: not in Crossref; DataCite: {lookup_doi(doi)}")
        else:
            print(f"  {doi}: {rec['title']!r} ({rec['year']}) vol {rec['volume']} issue {rec['issue']} pages {rec['page']}")

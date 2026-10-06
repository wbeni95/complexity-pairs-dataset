#!/usr/bin/env python3
"""DOI checks for the sources cited in research/2026-10-07_patterns.md.

Question: does every DOI that the pattern-mining report (research/2026-10-07_patterns.md) cites resolve, and do
the registered title and year match what the report says?

Method: for each (doi, year, title) below, call tools/check_sources.lookup_doi (Crossref first, DataCite as
fallback) and compare the registered title with tools/check_sources.title_matches (>= 70 % word overlap) and the
registered year with the cited year. Sources are queried one at a time with a 1 s pause (Crossref etiquette).
Only the DOIs listed here are queried; tools/check_sources.py is NOT run on the repository.

Deterministic in its inputs (a fixed list, no randomness). The output depends on the public Crossref /
DataCite registries at run time, so it is "external" provenance in the RESEARCH_LOG sense.

Outcome (first full run 2026-10-07, 74 DOIs): 69 OK. Three guessed DOIs belonged to OTHER papers and were
replaced by the records found with experiments/2026-10-07_doi_search.py (Papadimitriou 1991 -> .185365,
Blaser 1999 -> .814576, Mehlhorn-Galil 1976 -> BF02241983; Paterson 1975 added). Rechecked with this script:
Mehlhorn-Galil and Paterson OK; Papadimitriou (.185365) and Blaser (.814576) match the title but Crossref
registers no year (the proceedings names, "32nd ... FOCS" [1991] and "40th ... FOCS", give the year).
Two further records have incomplete metadata: 10.1007/BFb0038202 (Welzl 1991) matches the title but Crossref
registers no year;
10.4086/toc.2008.v004a008 (Farhi-Goldstone-Gutmann) has no title in Crossref, only year 2008, volume 4,
issue 1, pages 169-190. The report states both limitations. The report cites a DOI only if its line is OK or
the limitation is stated next to the citation.

Usage (repository root):  PYTHONIOENCODING=utf-8 ./.venv/Scripts/python experiments/2026-10-07_doi_checks.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from check_sources import lookup_doi, title_matches  # noqa: E402

# (doi, cited year, cited title) -- exactly as the report intends to cite them.
SOURCES = [
    # transforms on the Boolean cube
    ("10.1145/1250790.1250801", 2007, "Fourier meets Möbius: fast subset convolution"),
    ("10.1109/TC.1976.1674569", 1976, "Unified Matrix Treatment of the Fast Walsh-Hadamard Transform"),
    # strings / automata
    ("10.1145/360825.360855", 1975, "Efficient string matching: an aid to bibliographic search"),
    ("10.1145/363347.363387", 1968, "Programming Techniques: Regular expression search algorithm"),
    ("10.1016/0304-3975(85)90157-4", 1985, "The smallest automaton recognizing the subwords of a text"),
    ("10.1145/359581.359603", 1977, "A fast algorithm for computing longest common subsequences"),
    ("10.1016/S0019-9958(85)80046-2", 1985, "Algorithms for approximate string matching"),
    ("10.1137/0222058", 1993, "Suffix Arrays: A New Method for On-Line String Searches"),
    ("10.1007/3-540-48194-X_17", 2001, "Linear-Time Longest-Common-Prefix Computation in Suffix Arrays and Its Applications"),
    ("10.1147/rd.312.0249", 1987, "Efficient randomized pattern-matching algorithms"),
    ("10.1016/S0019-9958(67)80007-X", 1967, "Recognition and parsing of context-free languages in time n^3"),
    # graphs
    ("10.1145/263867.263872", 1997, "A simple min-cut algorithm"),
    ("10.1145/234533.234534", 1996, "A new approach to the minimum cut problem"),
    ("10.1016/0020-0190(79)90002-4", 1979, "A linear-time algorithm for testing the truth of certain quantified boolean formulas"),
    ("10.1109/SFCS.1991.185365", 1991, "On selecting a satisfying truth assignment"),  # corrected, see doi_search
    ("10.1137/0201010", 1972, "Depth-First Search and Linear Graph Algorithms"),
    ("10.4153/CJM-1965-045-4", 1965, "Paths, Trees, and Flowers"),
    ("10.1016/0012-365X(78)90011-0", 1978, "A characterization of the minimum cycle mean in a digraph"),
    ("10.1137/0214017", 1985, "Arboricity and Subgraph Listing Algorithms"),
    ("10.1007/BF01442866", 1873, "Ueber die Möglichkeit, einen Linienzug ohne Wiederholung und ohne Unterbrechung zu umfahren"),
    ("10.1016/0166-218X(89)90031-0", 1989, "Linear time algorithms for NP-hard problems restricted to partial k-trees"),
    ("10.1002/andp.18471481202", 1847, "Ueber die Auflösung der Gleichungen, auf welche man bei der Untersuchung der linearen Vertheilung galvanischer Ströme geführt wird"),
    ("10.1016/0031-8914(61)90063-5", 1961, "The statistics of dimers on a lattice"),
    # DP speed-ups
    ("10.1007/BF00264289", 1971, "Optimum binary search trees"),
    ("10.1145/800141.804691", 1980, "Efficient dynamic programming using quadrangle inequalities"),
    ("10.1007/BF01840359", 1987, "Geometric applications of a matrix-searching algorithm"),
    ("10.1137/0216043", 1987, "The Least Weight Subsequence Problem"),
    # algebra / linear algebra
    ("10.1137/0214007", 1985, "An Efficient Formula for Linear Recurrences"),
    ("10.1109/TIT.1969.1054260", 1969, "Shift-register synthesis and BCH decoding"),
    ("10.1109/TIT.1986.1057137", 1986, "Solving sparse linear equations over finite fields"),
    ("10.1002/sapm1946251261", 1946, "The Wiener (Root Mean Square) Error Criterion in Filter Design and Prediction"),
    ("10.1016/0020-0190(84)90018-8", 1984, "On computing the determinant in small parallel time using a small number of processors"),
    ("10.1109/TIT.1967.1054010", 1967, "Error bounds for convolutional codes and an asymptotically optimum decoding algorithm"),
    # geometry
    ("10.1016/0020-0190(72)90045-2", 1972, "An efficient algorithm for determining the convex hull of a finite planar set"),
    ("10.1007/BFb0038202", 1991, "Smallest enclosing disks (balls and ellipsoids)"),
    ("10.1007/BF02574699", 1991, "Small-dimensional linear programming and convex hulls made easy"),
    # data structures / selection
    ("10.1002/spe.4380240306", 1994, "A new data structure for cumulative frequency tables"),
    ("10.1145/321879.321884", 1975, "Efficiency of a Good But Not Linear Set Union Algorithm"),
    ("10.1016/S0022-0000(73)80033-9", 1973, "Time bounds for selection"),
    ("10.1145/366622.366647", 1961, "Algorithm 65: find"),
    # exact exponential / parameterized
    ("10.1137/0206038", 1977, "Finding a Maximum Independent Set"),
    ("10.1016/j.ic.2017.06.001", 2017, "Exact algorithms for maximum independent set"),
    ("10.1016/j.tcs.2010.06.026", 2010, "Improved upper bounds for vertex cover"),
    ("10.1007/s00453-004-1090-5", 2004, "Automated Generation of Search Tree Algorithms for Hard Graph Modification Problems"),
    ("10.1007/978-3-642-16533-7", 2010, "Exact Exponential Algorithms"),
    ("10.1016/j.tcs.2005.09.023", 2005, "A new algorithm for optimal 2-constraint satisfaction and its implications"),
    ("10.1137/0210033", 1981, "A T=O(2^{n/2}), S=O(2^{n/4}) Algorithm for Certain NP-Complete Problems"),
    ("10.1137/110839229", 2014, "Determinant Sums for Undirected Hamiltonicity"),
    ("10.1016/0167-6377(82)90044-X", 1982, "Dynamic programming meets the principle of inclusion and exclusion"),
    ("10.1137/070683933", 2009, "Set Partitioning via Inclusion-Exclusion"),
    # query complexity / quantum
    ("10.1109/SFCS.1986.44", 1986, "Probabilistic Boolean decision trees and the complexity of evaluating game trees"),
    ("10.4086/toc.2008.v004a008", 2008, "A Quantum Algorithm for the Hamiltonian NAND Tree"),
    ("10.1016/j.ic.2004.04.001", 2004, "The query complexity of order-finding"),
    ("10.1145/780542.780552", 2003, "Exponential algorithmic speedup by a quantum walk"),
    ("10.1090/conm/305/05215", 2002, "Quantum amplitude amplification and estimation"),
    ("10.1145/301250.301349", 1999, "The quantum query complexity of approximating the median and related statistics"),
    ("10.1145/502090.502097", 2001, "Quantum lower bounds by polynomials"),
    ("10.1145/3106234", 2017, "Separations in Query Complexity Based on Pointer Functions"),
    # scheduling
    ("10.1002/nav.3800010110", 1954, "Optimal two- and three-stage production schedules with setup times included"),
    ("10.1002/nav.3800030106", 1956, "Various optimizers for single-stage production"),
    ("10.1287/mnsc.15.1.102", 1968, "An n Job, One Machine Sequencing Algorithm for Minimizing the Number of Late Jobs"),
    ("10.1109/JRPROC.1952.273898", 1952, "A Method for the Construction of Minimum-Redundancy Codes"),
    # number theory
    ("10.1090/S0025-5718-1974-0340163-2", 1974, "Factoring large integers"),
    ("10.1090/S0025-5718-1985-0777285-5", 1985, "Computing π(x): the Meissel-Lehmer method"),
    ("10.1007/978-1-4757-5579-4", 1976, "Introduction to Analytic Number Theory"),
    ("10.1017/CBO9780511608650", 1984, "The Theory of Partitions"),
    # matrix multiplication: small formats, lower bounds, search
    ("10.1090/S0002-9904-1976-13988-2", 1976, "A noncommutative algorithm for multiplying 3×3 matrices using 23 multiplications"),
    ("10.1016/S0885-064X(02)00007-9", 2003, "On the complexity of the multiplication of matrices of small formats"),
    ("10.1016/0024-3795(71)90009-7", 1971, "On multiplication of 2 × 2 matrices"),
    ("10.1137/0120004", 1971, "On Minimizing the Number of Multiplications Necessary for Matrix Multiplication"),
    ("10.1109/SFFCS.1999.814576", 1999, "A 5/2 n^2-lower bound for the rank of n×n-matrix multiplication over arbitrary fields"),  # corrected
    ("10.1145/3597066.3597120", 2023, "Flip Graphs for Matrix Multiplication"),
    ("10.1007/BF02241983", 1976, "Monotone switching circuits and Boolean matrix product"),  # corrected
    ("10.1016/0304-3975(75)90009-2", 1975, "Complexity of monotone networks for Boolean matrix product"),
    # randomized algorithms textbook
    ("10.1017/CBO9780511814075", 1995, "Randomized Algorithms"),
]


def main(argv: list[str]) -> int:
    """With DOIs as arguments, check only those (they must be in SOURCES)."""
    todo = [s for s in SOURCES if not argv or s[0] in argv]
    ok = 0
    for doi, year, title in todo:
        try:
            res = lookup_doi(doi)
        except RuntimeError as e:  # network unreachable after retries
            print(f"UNREACHABLE  {doi}  ({e})")
            continue
        if res is None:
            print(f"MISSING      {doi}  cited: {year} {title!r}")
        else:
            found_title, found_year = res
            t_ok = title_matches(title, found_title)
            y_ok = found_year == year
            status = "OK" if (t_ok and y_ok) else ("TITLE?" if not t_ok else "YEAR?")
            ok += status == "OK"
            print(f"{status:<12} {doi}  cited: {year} | registered: {found_year} {found_title!r}")
        time.sleep(1.0)
    print(f"\n{ok}/{len(todo)} OK (title and year both match)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

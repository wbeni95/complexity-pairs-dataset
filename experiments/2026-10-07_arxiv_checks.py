#!/usr/bin/env python3
"""arXiv id checks for arXiv-only sources considered in research/2026-10-07_patterns.md.

Question: do these arXiv ids exist, and what titles and first-submission years are registered for them?
The ids were recalled from memory, so any of them may be wrong; the report cites an id only if the registered
title says what the report attributes to it.

Method: ONE call of tools/check_sources.arxiv_batch (one HTTP request to export.arxiv.org for all ids, respecting
the project's arXiv rate-limit etiquette). Deterministic in its inputs; the output depends on the live arXiv API
(external provenance).

Outcome (run 2026-10-07, one request): all four ids exist and their registered titles and years match the
expected papers: 1206.3369 'A Successive Approximation Algorithm for Computing the Divisor Summatory Function'
(2012); 2212.01175 'Flip Graphs for Matrix Multiplication' (2022); 2502.04514 'Flip Graphs with Symmetry and New
Matrix Multiplication Schemes' (2025); 2506.13131 'AlphaEvolve: A coding agent for scientific and algorithmic
discovery' (2025). Only titles and years were checked: the specific numbers attributed to these papers in the
report (ranks, exponents) were NOT checked against the paper texts, and the report says so where it uses them.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from check_sources import arxiv_batch  # noqa: E402

IDS = {
    "1206.3369": "Sladkey: successive approximation algorithm for the divisor summatory function (O(x^(1/3)) claim)",
    "2502.04514": "Moosbauer & Poole: flip graphs with symmetry, new matrix multiplication schemes (5x5, 6x6 ranks)",
    "2506.13131": "Novikov et al.: AlphaEvolve (4x4 complex matrix multiplication with 48 multiplications claim)",
    "2212.01175": "Kauers & Moosbauer: flip graphs for matrix multiplication (arXiv version of the ISSAC 2023 paper)",
}


def main() -> int:
    found = arxiv_batch(sorted(IDS))
    for aid in sorted(IDS):
        print(f"{aid}: expected [{IDS[aid]}]")
        print(f"    registered: {found.get(aid)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

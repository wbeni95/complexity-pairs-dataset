# Edit distance: plain recursion vs Wagner–Fischer DP

**Type:** T2 (naive-exp → poly) · **Verification:** V2

| Algorithm | Time (two length-n strings) | Implementation |
|---|---|---|
| Plain recursion | Θ((3+2√2)ⁿ/√n) ≈ Θ(5.83ⁿ/√n) | [brute_force.py](implementations/brute_force.py) |
| Wagner–Fischer DP | Θ(n²) | [wagner_fischer.py](implementations/wagner_fischer.py) |

**Why it's a pair.** There are only (n+1)² distinct subproblems. The recursion recomputes them
exponentially often, and the DP solves each one once.

**Beyond the pair.** Masek–Paterson give O(n²/log n). Backurs–Indyk show that no O(n^(2−ε)) algorithm
exists unless SETH fails.

**Sources.** Wagner & Fischer 1974 (J. ACM). Levenshtein 1966. Masek & Paterson 1980 (JCSS).
Backurs & Indyk, STOC 2015 (arXiv:1412.0348).

# Edit distance: plain recursion vs Wagner–Fischer DP

**Type:** T2 (naive-exp → poly) · **Verification:** V2

| Algorithm | Time (two length-n strings) | Implementation |
|---|---|---|
| Plain recursion | Θ((3+2√2)ⁿ/√n), with 3+2√2 ≈ 5.83 | [brute_force.py](implementations/brute_force.py) |
| Wagner–Fischer DP | Θ(n²) | [wagner_fischer.py](implementations/wagner_fischer.py) |

**Why it's a pair.** There are only (n+1)² distinct subproblems. The recursion recomputes them
exponentially often, and the DP solves each one once.

**Background (cited, not claims of this entry).** Masek–Paterson, *A faster algorithm computing string edit distances*
(title only; its bound is not restated here).
Backurs–Indyk show that an O(n^(2−δ)) algorithm would yield a SAT algorithm violating SETH; so, under SETH, no such
algorithm exists.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: both algorithms are correct (edit scripts and
alignments have the same minimum cost), the recursion makes exactly (3 D(n, n) − 1)/2 calls with
3·10⁻⁴ ≤ D(n, n)√n/(3+2√2)ⁿ ≤ 6 for n ≥ 1, its depth is 2n, and the DP does exactly |a|·|b| inner iterations with
two rows. For general lengths the DP takes Θ((|a|+1)(|b|+1)), i.e. Θ(|a|·|b|) when both strings are non-empty.
[tests/test_proofs_editdist.py](../../tests/test_proofs_editdist.py) checks the computable facts, including both
outputs against an independent edit-script search.

**Sources.** Wagner & Fischer 1974 (J. ACM). Levenshtein 1966. Masek & Paterson 1980 (JCSS).
Backurs & Indyk, STOC 2015 (arXiv:1412.0348).

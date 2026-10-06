# Boundary note: 2-SAT vs 3-SAT

**Not a pair.** These are two *different* problems. The note records a structural complexity boundary,
not a same-problem speedup (START_HERE section 4, "cautionary entries").

| Problem | Best known | Status |
|---|---|---|
| 2-SAT (≤ 2 literals per clause) | O(n + m): implication graph + strongly connected components | in P |
| 3-SAT (≤ 3 literals per clause) | O(1.307ⁿ) randomized (biased-PPSZ) | NP-complete |

Allowing a third literal per clause moves the problem from linear time to NP-complete.

- 2-SAT in linear time: Aspvall, Plass, Tarjan (1979), *A linear-time algorithm for testing the truth of certain
  quantified boolean formulas*, Information Processing Letters 8(3), 121–123.
  [doi:10.1016/0020-0190(79)90002-4](https://doi.org/10.1016/0020-0190(79)90002-4)
- 3-SAT NP-complete: Cook (1971); Karp (1972).

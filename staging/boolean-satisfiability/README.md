<!-- generated from entry.json by tools/build_index.py; edit entry.json, not this file -->
# 3-SAT: brute force vs Schöning vs PPSZ

**Type:** T6, T8 (open / unpaired) · **Verification:** V0

**Problem.** Given a Boolean formula in conjunctive normal form with at most 3 literals per clause, decide whether some assignment satisfies it.

**Input.** n = number of variables (m clauses). Size: O(m log n) bits.

| Algorithm | Model | Time | Space |
|---|---|---|---|
| brute force | classical-deterministic | O(2^n m) | O(n + m) |
| Schöning's random walk | classical-randomized | O((4/3)^n poly(n)) expected | poly(n) |
| PPSZ / biased-PPSZ | classical-randomized | O(1.308^n) (PPSZ; Hertli 2014 in general); O(1.307^n) (biased-PPSZ, Hansen et al. 2019) | poly(n) |

**Relationship.** 2^n -> (4/3)^n -> 1.307^n: exponential to better exponential. 3-SAT is NP-complete (Cook 1971), so a polynomial algorithm would prove P = NP. The Exponential Time Hypothesis conjectures that some base > 1 is unavoidable.

**Caveats.** 2-SAT is solvable in linear time; see notes/boundary-2sat-vs-3sat.md. That is a boundary between problems, not a same-problem pair.

**Notes.** Brute force vs Schöning is a separate V1 entry (pairs/3sat-brute-force-vs-schoening); this staging entry also cites PPSZ, which is not implemented.

**Verification.** Cited from the literature.

**Sources.**

- Cook, S. A. (1971). *The complexity of theorem-proving procedures*. STOC 1971, 151-158. [doi:10.1145/800157.805047](https://doi.org/10.1145/800157.805047)
- Schöning, U. (1999). *A probabilistic algorithm for k-SAT and constraint satisfaction problems*. FOCS 1999, 410-414. [doi:10.1109/SFFCS.1999.814612](https://doi.org/10.1109/SFFCS.1999.814612)
- Paturi, R.; Pudlák, P.; Saks, M. E.; Zane, F. (2005). *An improved exponential-time algorithm for k-SAT*. Journal of the ACM 52(3), 337-364. [doi:10.1145/1066100.1066101](https://doi.org/10.1145/1066100.1066101)
- Hertli, T. (2014). *3-SAT Faster and Simpler - Unique-SAT Bounds for PPSZ Hold in General*. SIAM Journal on Computing 43(2), 718-729. [doi:10.1137/120868177](https://doi.org/10.1137/120868177)
- Hansen, T. D.; Kaplan, H.; Zamir, O.; Zwick, U. (2019). *Faster k-SAT algorithms using biased-PPSZ*. STOC 2019. [doi:10.1145/3313276.3316359](https://doi.org/10.1145/3313276.3316359)

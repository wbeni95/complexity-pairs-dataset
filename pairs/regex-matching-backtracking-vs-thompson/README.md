# Regular-expression matching: backtracking vs memoised backtracking vs Thompson's NFA

**Type:** T2 (naive exponential → polynomial) · **Verification:** V2 (exact comparison counts with rivals)

**Dialect (defined in the entry).** Atoms are a letter a–z or `.`, each optionally followed by `?` or `*`. There
are no groups, alternation, classes, anchors or backreferences, and the whole text must match (`re.fullmatch`
semantics). Size parameter n: at most 2n atoms and 2n text characters. Worst-case family:
P_n = `(a?)ⁿ aⁿ` against `aⁿ`.

| Algorithm | Comparisons on P_n (counted, exact, proved) | General bound | Implementation |
|---|---|---|---|
| Backtracking (consume first) | (n + 2)·2ⁿ⁻¹ − 1 = Θ(n·2ⁿ) | O(2^(m+\|t\|)) | [backtracking.py](implementations/backtracking.py) |
| Memoised backtracking | n(n + 1) = Θ(n²) | O(m·\|t\|) | [memoized.py](implementations/memoized.py) |
| Thompson's NFA simulation | n(n + 1) = Θ(n²) | O(m·\|t\|) | [thompson.py](implementations/thompson.py) |

**Why it's here.** It is the classic "catastrophic backtracking" case. Depth-first search re-explores the same
subproblem (atom i, position j) along exponentially many branches. Memoising (i, j) already gives a polynomial
algorithm, which makes this a clean example of the memoisation pattern in RESEARCH_LOG RL-039. Thompson (1968)
reaches the same bound by advancing the set of all NFA states in lock step, with no table and one left-to-right
pass. On P_n the memoised matcher and the simulation make exactly the same number of comparisons.

**Verification.** V1: all three agree with Python's `re.fullmatch`, used only as the oracle, on random patterns
and texts for n ≤ 24; about a quarter of the instances for n ≤ 12 are P_n. A larger battery found 0
disagreements in 3300 instances. V2: an instrumented text character counts every symbol–character comparison of
the unchanged matchers.
- Backtracking: α = 0.974 against n·2ⁿ at tolerance 0.035. The deviation 0.026 is fixed by the exact
  lower-order terms. Rivals rejected: 2ⁿ (1.131), n²·2ⁿ (0.854), n² (3.386).
- Memoised backtracking and Thompson: α = 0.981 against n², tolerance 0.05. Rivals rejected: n (1.962),
  n³ (0.654).

See `experiments/2026-10-07b_regex_counts.py`.

**Sources.** Thompson, CACM 11(6), 1968.

# Matrix-chain ordering: plain recursion vs DP

**Type:** T2 (naive-exp → poly) · **Verification:** V2

| Algorithm | Time (n matrices) | Implementation |
|---|---|---|
| Plain recursion (no memo) | Θ(3ⁿ) | [recursion.py](implementations/recursion.py) |
| Bottom-up DP | Θ(n³) | [dp.py](implementations/dp.py) |

**Why it's a pair.** There are Θ(n²) distinct subchains. The recursion recomputes them, and the DP
solves each one once.

**Note on the exponent.** The recurrence gives T(n) = 3T(n−1) + Θ(1), which is Θ(3ⁿ): exactly 3ⁿ⁻¹ calls
(n ≥ 1). That is the cost the V2 fit uses. (There are Θ(4ⁿ/n^1.5) parenthesisations, more than the recursion makes
calls, from n = 18 on.)

**Published faster algorithm (background; not verified here).** Hu & Shing (1982/84) published an O(n log n) algorithm; it is
not implemented in this entry. Schwartz & Weiss (2019) report that its original correctness proof is wrong; their abstract says they present an alternative proof for the correctness
of "the first two algorithms" they discuss.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: both algorithms are correct, the
recursion makes exactly 3ⁿ⁻¹ calls and (3ⁿ⁻¹ − 1)/2 split evaluations, the DP exactly (n³ − n)/6, and there are
C(2n−2, n−1)/n = Θ(4ⁿ/n^1.5) parenthesisations. [tests/test_proofs_matchain.py](../../tests/test_proofs_matchain.py)
checks the computable facts, including both outputs against an explicit enumeration of all parenthesisations.

**Sources.** CLRS (3rd ed.). Hu & Shing, SIAM J. Comput. 1982, 1984. Schwartz & Weiss, SIAM J. Comput. 48(5), 2019.

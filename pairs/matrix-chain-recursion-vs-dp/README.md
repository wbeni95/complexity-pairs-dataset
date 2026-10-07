# Matrix-chain ordering: plain recursion vs DP

**Type:** T2 (naive-exp → poly) · **Verification:** V2

| Algorithm | Time (n matrices) | Implementation |
|---|---|---|
| Plain recursion (no memo) | Θ(3ⁿ) | [recursion.py](implementations/recursion.py) |
| Bottom-up DP | Θ(n³) | [dp.py](implementations/dp.py) |

**Why it's a pair.** There are Θ(n²) distinct subchains. The recursion recomputes them, and the DP
solves each one once.

**Note on the exponent.** CLRS proves Ω(2ⁿ) for the recursion. The recurrence actually gives
T(n) = 3T(n−1) + Θ(1), which is Θ(3ⁿ), and that is the cost the V2 fit uses.

**Faster known algorithm.** Hu & Shing (1982/84) give an O(n log n) algorithm. Schwartz & Weiss (2019) show that
its original correctness proof is wrong; their abstract says they present an alternative proof for the correctness
of "the first two algorithms" they discuss.

**Sources.** CLRS §15.2–15.3. Hu & Shing, SIAM J. Comput. 1982, 1984. Schwartz & Weiss, SIAM J. Comput. 48(5), 2019.

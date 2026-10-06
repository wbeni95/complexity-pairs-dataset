# Longest common subsequence: enumeration vs DP

**Type:** T2 (naive-exp → poly) · **Verification:** V2

| Algorithm | Time (two length-n strings) | Implementation |
|---|---|---|
| Enumerate subsequences of a | Θ(2ⁿ·n) | [brute_force.py](implementations/brute_force.py) |
| Dynamic programming | Θ(n²) | [dp.py](implementations/dp.py) |

**Why it's a pair.** Enumerating candidate answers is exponential. The prefix-pair subproblems are
only quadratic in number.

**Beyond the pair.** No O(n^(2−ε)) algorithm exists unless SETH fails (Abboud–Backurs–Vassilevska Williams 2015).

**Sources.** CLRS §15.4. Wagner & Fischer 1974. arXiv:1501.07053.

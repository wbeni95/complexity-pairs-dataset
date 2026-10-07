# Longest common subsequence: enumeration vs DP

**Type:** T2 (naive-exp → poly) · **Verification:** V2

| Algorithm | Time (two length-n strings) | Implementation |
|---|---|---|
| Enumerate subsequences of a | Θ(2ⁿ·n) | [brute_force.py](implementations/brute_force.py) |
| Dynamic programming | Θ(n²) | [dp.py](implementations/dp.py) |

**Why it's a pair.** Enumerating candidate answers is exponential. The prefix-pair subproblems are
only quadratic in number.

**Background (cited, not a claim of this entry).** No O(n^(2−ε)) algorithm exists unless SETH fails
(Abboud–Backurs–Vassilevska Williams 2015).

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: the greedy scan decides the subsequence
relation, both algorithms are correct, every mask of the enumeration costs between n and 2n steps (so Θ(2ⁿ·n); the
upper bound assumes that `str.find` scans forward to the first match, a machine-model assumption in background), and
the DP does exactly |a|·|b| inner iterations with two rows (Θ(|a|·|b|) for non-empty strings).
[tests/test_proofs_lcs.py](../../tests/test_proofs_lcs.py) checks the computable facts.

**Sources.** CLRS (3rd ed.). Wagner & Fischer 1974. arXiv:1501.07053.

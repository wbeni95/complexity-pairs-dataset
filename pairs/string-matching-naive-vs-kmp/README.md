# Exact string matching: naive scan vs Knuth–Morris–Pratt

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Count the (possibly overlapping) occurrences of a pattern P (length m ≥ 1) in a text T (length n).

| Algorithm | Time | Implementation |
|---|---|---|
| Naive matching | Θ((n − m + 1)·m) worst case (m ≤ n), so Θ(nm) for m ≤ cn, c < 1 | [naive.py](implementations/naive.py) |
| Knuth–Morris–Pratt | Θ(n + m) always | [kmp.py](implementations/kmp.py) |

**Why it's a pair.** After a mismatch the naive matcher slides P one place and re-reads text it has already
matched. KMP's failure function says exactly how far P can shift, so the text pointer never moves backwards.

**Scaling instances.** V2 uses T = aⁿ and P = a^(m−1)b with m = n // 2. Then m = Θ(n), the naive matcher does
(n − m + 1)·m ≈ n²/4 comparisons, and KMP does Θ(n). So the measured costs are n² versus n. On uniformly random
text over σ ≥ 2 letters the naive matcher makes at most 2 comparisons per alignment on average, far fewer than in
its worst case.

**Verification.** V1: agreement with each other and with a `str.find` loop (oracle only) on small-alphabet and
periodic texts with frequent overlapping matches. V2 counts **character comparisons exactly** on the instances
above. A str's characters cannot be instrumented, so the harness passes the same characters as tuples of an
instrumented character type (`CountingChar`); the implementations are unchanged and give the same answers.
The naive matcher makes exactly (n − m + 1)·m with m = n // 2 (α = 0.998 against n², n = 200..3200), and KMP
exactly 3n + 2m − 6, which is 4n − 6 at these even n and 4n − 7 at odd n ≥ 7 (α = 1.000 against n,
n = 3000..300000). With tolerance 0.03 every declared rival is rejected:
n (α = 1.997) and n² log n (0.928) for the naive matcher; n log n (0.910) and n² (0.500) for KMP. Details:
`experiments/2026-10-07b_count_v2_apsp_strings.py` and `research/2026-10-07b_count_based_v2.md`.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: the exact comparison counts for all sizes of
their domains, the correctness of both matchers (the KMP failure function and scan), the naive worst case, KMP's
Θ(n + m) on every input, the optimality caveat and the naive average on random text. It names the checks: the
count-check scripts and [tests/test_proofs_kmp.py](../../tests/test_proofs_kmp.py).

**Sources.** Knuth, Morris & Pratt, "Fast pattern matching in strings", SIAM J. Comput. 6(2), 1977.
CLRS (3rd ed.).

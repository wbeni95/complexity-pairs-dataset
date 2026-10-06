# Exact string matching: naive scan vs Knuth–Morris–Pratt

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Count the (possibly overlapping) occurrences of a pattern P (length m ≥ 1) in a text T (length n).

| Algorithm | Time | Implementation |
|---|---|---|
| Naive matching | Θ(nm) worst case | [naive.py](implementations/naive.py) |
| Knuth–Morris–Pratt | Θ(n + m) always | [kmp.py](implementations/kmp.py) |

**Why it's a pair.** After a mismatch the naive matcher slides P one place and re-reads text it has already
matched. KMP's failure function says exactly how far P can shift, so the text pointer never moves backwards.

**Scaling instances.** V2 uses T = aⁿ and P = a^(m−1)b with m = n // 2. Then m = Θ(n), the naive matcher does
(n − m + 1)·m ≈ n²/4 comparisons, and KMP does Θ(n). So the measured costs are n² versus n. On random text the
naive matcher is much faster than its worst case.

**Verification.** V1: agreement with each other and with a `str.find` loop (oracle only) on small-alphabet and
periodic texts with frequent overlapping matches. V2: runtimes fit n² (naive) and n (KMP) on the instances above.

**Sources.** Knuth, Morris & Pratt, "Fast pattern matching in strings", SIAM J. Comput. 6(2), 1977.
CLRS (3rd ed.), §32.1 and §32.4.

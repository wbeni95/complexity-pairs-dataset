# Closest pair of points: brute force vs divide and conquer

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Given n ≥ 2 points with integer coordinates, return the minimum squared Euclidean distance
between two of them. Integers keep the answer exact.

| Algorithm | Time (n points) | Implementation |
|---|---|---|
| All pairs | Θ(n²) | [brute_force.py](implementations/brute_force.py) |
| Shamos–Hoey divide and conquer | Θ(n log n) | [divide_conquer.py](implementations/divide_conquer.py) |

**Why it's a pair.** After solving both halves, only points within δ of the dividing line can form a
closer pair, and in y order each one needs only a constant number of comparisons. The y-sorted lists are
merged on the way up rather than re-sorted, so the cost is n log n and not n log² n.

**Optimality.** Ω(n log n) in the algebraic computation-tree model (Ben-Or 1983, via element uniqueness).
Randomized grid hashing with the floor function gets expected O(n) (Rabin 1976; Khuller & Matias 1995).

**Verification.** V1: both agree with each other and with an independent plane-sweep oracle, including
duplicate points and points that all lie on one vertical line. V2 counts **multiplications exactly** (a
squaring counts as one) with an instrumented integer type (`CountingInt`) around every coordinate; the
implementations are unchanged and give the same answers. All pairs makes exactly n(n − 1) (α = 1.001 against
n², n = 125..2000). Divide and conquer makes 1.406–1.457 · n log₂ n, 61.5–66.5% of it in the strip filter
(one squaring per point per recursion level), α = 0.993 against n log n (n = 1000..64000). With tolerance 0.03
every declared rival is rejected: n log n (α = 1.721) and n² log n (0.926) for all pairs; n (1.105), n log² n
(0.902) and n² (0.553) for divide and conquer. So the log factor is resolved. Comparisons are not counted:
those inside CPython's `sorted()` and `min()` differ between Python 3.12 and 3.14 (measured), while the
multiplication counts are identical. Details:
`experiments/2026-10-07b_count_v2_closest_pair.py` and `research/2026-10-07b_count_based_v2.md`.

**Sources.** Shamos & Hoey 1975 (FOCS). Bentley & Shamos 1976 (STOC). Ben-Or 1983. Rabin 1976. Khuller & Matias 1995.

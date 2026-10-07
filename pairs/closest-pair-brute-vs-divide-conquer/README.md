# Closest pair of points: brute force vs divide and conquer

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Given n ≥ 2 points with integer coordinates, return the minimum squared Euclidean distance
between two of them. Integers keep the answer exact.

| Algorithm | Time (n points) | Implementation |
|---|---|---|
| All pairs | Θ(n²) | [brute_force.py](implementations/brute_force.py) |
| Shamos–Hoey divide and conquer | Θ(n log n), assuming the built-in sort runs in O(n log n) (see Background) | [divide_conquer.py](implementations/divide_conquer.py) |

**Why it's a pair.** After solving both halves, only points within δ of the dividing line can form a
closer pair, and in y order each one needs only a constant number of comparisons (at most 7 full distance
computations per strip point, by a packing argument). The y-sorted lists are
merged on the way up rather than re-sorted, so the cost is n log n and not n log² n.

**Optimality (conditional).** The answer is 0 exactly when two points coincide, so element distinctness reduces to
closest pair. If Ben-Or's Ω(n log n) lower bound for element distinctness in the algebraic computation tree model on
real-valued inputs holds (cited, see Background), closest pair needs Ω(n log n) in that model, and divide and conquer
matches it up to a constant factor under the sort assumption; the theorem does not by itself cover the integer
coordinates used here.

**Background** (cited; not claims of this entry). Machine-model assumption: the built-in sort runs in O(n log n)
time with O(n) extra space on n items, and `min()` over k values in O(k). It is used by the initial sort of the n
points and by the sort of at most 3 points in every leaf of the recursion (1 + #leaves calls, 489 at n = 1000), and
`min()` is called 2·#leaves − 1 times (975 at n = 1000), on at most 3 values. Its
basis: the current CPython list sort orders its merges by the powersort rule (`Objects/listsort.txt`), for which
Munro & Wild (2018, Theorem 6) bound the comparisons of a plain merge by n log₂ n + 3n; CPython's galloping merges
are not covered by that theorem, so the assumption is not proved in this repository. Ben-Or (1983, Theorem 1):
element distinctness needs Ω(n log n) operations in the algebraic computation tree model. Randomized closest-pair
algorithms: Rabin 1976; Khuller & Matias 1995. Divide and conquer in multidimensional space: Bentley & Shamos 1976.

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

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry from the code: the exact operation counts for
all sizes of their domains, the correctness of both algorithms, the packing lemma, the time and space bounds (for divide
and conquer under the assumption on the built-in sort), and the reduction from element distinctness. It names the scripts and tests (among them `tests/test_proofs_closest_pair.py`) and the sizes that
check each statement.

**Sources.** Shamos & Hoey 1975 (FOCS). Bentley & Shamos 1976 (STOC). Ben-Or 1983. Rabin 1976. Khuller & Matias 1995.
Munro & Wild 2018 (ESA). CPython `Objects/listsort.txt`.

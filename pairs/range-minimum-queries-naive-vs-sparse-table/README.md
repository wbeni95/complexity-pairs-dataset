# Range minimum queries: scanning vs a sparse table

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Given n numbers and q = n queries (l, r), return min(a[l..r]) for each query.

| Algorithm | Time (q = n long queries) | Implementation |
|---|---|---|
| Scan each range | Θ(n²) (Θ(q + Σ lengths) in general) | [naive_scan.py](implementations/naive_scan.py) |
| Sparse table | Θ(n log n) preprocessing + O(1) per query | [sparse_table.py](implementations/sparse_table.py) |

**Why it's a pair.** Every range is the union of two, possibly overlapping, ranges of the same power-of-two
length. The minimum is idempotent, so precomputing the minima of all power-of-two ranges (log n levels,
each from the previous one) makes every query two lookups.

**Worst case.** Scanning is quadratic only when the queries are long. The scaling family uses n ranges, each
longer than n/2; the expected total scanned length is exactly n(3n/4 + 1) when 4 divides n, and the seeded instances
measure 0.75·n² within 0.5%. For short queries scanning is linear, so the pair is stated for long queries.

**Verification.** V1: both agree with each other and with an independent segment-tree oracle on random
values (with many ties) and mixed query kinds. V2 uses exact comparison counts. The scaling values are
wrapped in a counting type, and the implementations are unchanged. CPython's two-argument `min()` calls
`__lt__` once, so the table build's comparisons are counted too. Because these comparisons happen inside a
CPython built-in, the count is an implementation property, not a language guarantee (RL-069); it was identical
under CPython 3.12.10 and 3.14.2 (RL-069).
- Scan: the count equals Σ(r − l) over the queries. α = 1.001 against n², and the rivals n log n, n² log n
  and n³ are rejected.
- Sparse table: the count equals Σ_{j=1..⌊log₂n⌋}(n − 2^j + 1) + n, i.e. n log₂n − n + log₂n + 2 on powers of
  two. α = 1.007 against n log n, and the rivals n (α 1.113), n log² n (0.920) and n² are rejected.

Tolerance is 0.03. The log factor is now resolved; the earlier timing fit could not tell n log n from n
(α = 0.989 vs 1.100 in the probe).

**Beyond (background, cited; not proved here).** See Bender & Farach-Colton (2000), *The LCA problem revisited*, and
Fischer & Heun (2011), who give space-efficient preprocessing schemes for range minimum queries on static arrays
(title).

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry from the code: the correctness of both
algorithms, the time and space bounds, the properties of the scaling family, the exact counts for all sizes of their
domains, and the remark on other idempotent operations. It names the scripts and tests that check each one
(`tests/test_proofs_rmq.py` among them).

**Sources.** Bender & Farach-Colton, LATIN 2000. Fischer & Heun, SIAM J. Comput. 40(2), 2011.

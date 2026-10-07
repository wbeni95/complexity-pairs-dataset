# OR convolution (covering product): all index pairs vs zeta and Möbius transforms

**Type:** T3 (poly → faster poly) · **Verification:** V2 (exact operation counts with rivals)

h[S] = Σ over A ∪ B = S of f[A]·g[B], for two integer set functions on an n-element ground set (N = 2ⁿ values each).

| Algorithm | Ring operations (counted, exact) | Time | Implementation |
|---|---|---|---|
| All index pairs | 2·4ⁿ | Θ(4ⁿ) = Θ(N²) | [naive.py](implementations/naive.py) |
| Zeta transforms, pointwise product, Möbius transform | (3n + 2)·2ⁿ⁻¹ | Θ(n·2ⁿ) = Θ(N log N) | [zeta_mobius.py](implementations/zeta_mobius.py) |

**Why it is here.** The zeta transform (sums over subsets) diagonalises the OR convolution: ζ(h) = ζ(f)·ζ(g)
pointwise, because A ∪ B ⊆ S exactly when A ⊆ S and B ⊆ S. Two fast zeta transforms (Yates' passes), a pointwise
product and one Möbius transform (the inverse) give h (see Björklund, Husfeldt, Kaski & Koivisto 2007). It is the
subset-lattice analogue of
[xor-convolution-naive-vs-walsh-hadamard](../xor-convolution-naive-vs-walsh-hadamard/), with ζ in the role of the
Walsh–Hadamard transform. The zeta transform alone is
[subset-sum-zeta-transform-naive-vs-yates](../subset-sum-zeta-transform-naive-vs-yates/). The AND convolution is the
same problem with every index complemented (A ∩ B = S iff ∁A ∪ ∁B = ∁S). The experiment checks this mirror, which is a
reindexing, not a separate pair.

**Verification.**
- *V1:* both implementations agree for n = 0..8 and 10 (zeta–Möbius also at 11). The independent `check` verifies
  ζ(h)[S] = ζ(f)[S]·ζ(g)[S] for **every** S, with each ζ computed by submask enumeration (Θ(3ⁿ), not Yates' passes).
  ζ is invertible, so this check is complete at every n. For n ≤ 10 it also evaluates the definition at 6 seeded sets.
- *Oracle control* ([experiment](../../experiments/2026-10-06f_entries_or_convolution.py)): 86 correct outputs
  accepted. All 383 wrong ones were rejected: single entries off by one, the AND and XOR convolutions, the result
  without the Möbius step, wrong lengths. A first version of `check` sampled 48 sets for n > 8 and missed 4 of the 86
  off-by-one errors, because only supersets of the changed set see it; it was replaced by the complete check.
- *V2:* an instrumented integer counts every +, − and × of the unchanged implementations. The counts are exactly 2·4ⁿ
  (n = 0..10) and (3n + 2)·2ⁿ⁻¹ (n = 1..16).

| Fit (tolerance 0.02) | α | Rivals (must not fit) |
|---|---|---|
| naive vs 4ⁿ, n = 3..8 | 1.000 | n·2ⁿ: 1.562, 3ⁿ: 1.262, n·4ⁿ: 0.877 |
| zeta–Möbius vs (3n + 2)·2ⁿ, n = 4..16 | 1.000 | 2ⁿ: 1.149, n²·2ⁿ: 0.868, 3ⁿ: 0.725 |

**Caveats.** Only additions, subtractions and multiplications on O(n)-bit integers are counted; index arithmetic is
not. The input has N = 2ⁿ entries, so both costs are polynomial in the input size (T3, not an exponential pair).

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry from the code: the correctness of both
algorithms, the completeness of the V1 check, the time and space bounds, the exact counts for all sizes of their
domains, the value sizes and the AND mirror. It names the scripts and tests that check each one
(`tests/test_proofs_or_convolution.py` among them).

**Background (cited, not proved here).** Björklund, Husfeldt, Kaski & Koivisto (2007; abstract, arXiv:cs/0611101)
evaluate the subset convolution (Σ over T ⊆ S of f(T)·g(S ∖ T)) in O(n²·2ⁿ) additions and multiplications, via Möbius
transform and inversion.

**Sources.** Björklund, Husfeldt, Kaski & Koivisto, STOC 2007, 67–74. Kennes, IEEE Trans. SMC 22(2), 1992.

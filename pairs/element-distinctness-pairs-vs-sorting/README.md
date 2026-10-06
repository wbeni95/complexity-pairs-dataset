# Element distinctness: all pairs vs sorting

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Decide whether n integers are pairwise distinct.

| Algorithm | Time | Implementation |
|---|---|---|
| All pairs | Θ(n²) worst case (exactly n(n−1)/2 comparisons on yes-instances) | [all_pairs.py](implementations/all_pairs.py) |
| Merge sort, then compare neighbours | Θ(n log n) | [sort_adjacent.py](implementations/sort_adjacent.py) |

**Why it's a pair.** Sorting puts equal values next to each other, so n − 1 neighbour comparisons replace
all n(n−1)/2 pairs.

**Lower bound.** In the algebraic computation tree model over the reals, deciding distinctness needs
Ω(n log n) operations (Ben-Or 1983). The yes-set has n! connected components, one per ordering. Sorting
is therefore optimal in that model. The bound concerns real-valued inputs. On a word RAM, universal
hashing (Carter & Wegman 1979) decides distinctness of integers in O(n) *expected* time. That method is
randomized, outside the model and not implemented here.

**Verification.** V1: both agree with each other and with a hash-set oracle on distinct inputs, inputs
with one planted duplicate, inputs with many duplicates, and inputs with huge values of both signs. V2: on
distinct inputs (the all-pairs worst case), the harness counts **comparisons between input values exactly**
with an instrumented value type (`CountingKey`); the implementations are unchanged. All pairs makes exactly
n(n−1)/2 (α = 1.000 against n², n = 500..4000). Sorting plus the neighbour scan makes n log₂ n − c·n with
c = 0.24–0.26 (α = 1.002 against n log n, n = 1000..128000). With tolerance 0.03, every declared rival is
rejected: n log n (α = 1.757) and n² log n (0.936) for all pairs; n (1.111), n log² n (0.912) and n² (0.556)
for sorting. So the log factor is resolved. The earlier timing fit could not tell n log n from n (α = 1.001 vs
1.125 in the probe). Details: `experiments/2026-10-07b_count_v2_element_distinctness.py` and
`research/2026-10-07b_count_based_v2.md`.

**Sources.** Ben-Or, STOC 1983. Carter & Wegman, JCSS 18(2), 1979. Knuth, TAOCP Vol. 3, §5.2.4.

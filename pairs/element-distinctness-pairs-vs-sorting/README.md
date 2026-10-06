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
distinct inputs (the all-pairs worst case), runtimes fit n² and n log n. As for every n log n entry, the fit
cannot tell n log n from n (α = 1.001 vs 1.125 in the probe), but it rules out n² (α = 0.558).

**Sources.** Ben-Or, STOC 1983. Carter & Wegman, JCSS 18(2), 1979. Knuth, TAOCP Vol. 3, §5.2.4.

# 3SUM: all triples vs sort + two pointers

**Type:** T3 (poly → faster poly) · **Verification:** V2

| Algorithm | Time | Implementation |
|---|---|---|
| All triples | Θ(n³) worst case (exactly C(n, 3) tests on every no-instance) | [brute_force.py](implementations/brute_force.py) |
| Sort + two pointers | Θ(n²) worst case, assuming the built-in sort runs in O(n log n) (exactly (n − 1)(n − 2)/2 pointer steps on every no-instance, n ≥ 1) | [sort_two_pointers.py](implementations/sort_two_pointers.py) |

**Why it's a pair.** On the sorted array, for a fixed first element the pair sums a[j] + a[k] are monotone in j and
k, so two pointers moving toward each other never skip a solution, and each step discards one candidate pair.

**Background** (cited; not claims of this entry). Gajentaan & Overmars (1995) showed that a large class of problems
in computational geometry is "3SUM-hard": there is no hope of o(n²) algorithms for them unless 3SUM can be solved
faster. The conjecture that 3SUM needs Ω(n²) time was refuted by Grønlund & Pettie (2014; J. ACM 2018), who shaved
polylogarithmic factors off n² and showed decision-tree complexity O(n^(3/2) √log n); for integer inputs it is
conjectured that 3SUM needs n^(2−o(1)) time, i.e. that no O(n^(2−ε)) algorithm exists. Linear decision trees need only
O(n log² n) linear queries, which are comparisons of sums of two k-subsets (Kane, Lovett & Moran 2019), so no quadratic
lower bound can be proved in that model. Machine-model assumption: the built-in sort, called once by the quadratic
algorithm, runs in O(n log n) time with O(n) extra space; its basis is the powersort merge order of the current CPython
list sort (`Objects/listsort.txt`), for which Munro & Wild (2018, Theorem 6) bound the comparisons of a plain merge by
n log₂ n + 3n; the galloping merges are not covered by that theorem, so the assumption is not proved in this
repository. This entry proves no lower bound for 3SUM.

**Verification.** V1 against an independent hash-based oracle. V2 on worst-case (no-solution) inputs: all values are
positive, so neither algorithm stops early (timing fits, measured).

**Proofs.** [PROOFS.md](PROOFS.md) proves the correctness, the exact step counts on no-instances, the worst-case
bounds and the space of both algorithms, and that the timing instances have no solution;
`tests/test_proofs_three_sum.py` checks them on stated ranges. The quadratic algorithm's upper bounds hold under the
machine-model assumption on the built-in sort (background).

**Sources.** Gajentaan & Overmars 1995. Grønlund & Pettie, J. ACM 2018. Kane, Lovett & Moran, J. ACM 2019. Munro &
Wild, ESA 2018. CPython `Objects/listsort.txt`.

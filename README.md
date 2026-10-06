# Complexity Pairs Dataset

An open, machine-readable, **verified** dataset of *complexity pairs*: computational problems for which
we record two or more correct algorithms with **different asymptotic cost**, for example an
exponential-time and a polynomial-time method for the same problem.

The goal is training and benchmark data for algorithm-discovery systems (the AlphaTensor / AlphaDev /
FunSearch family) and a reference map for anyone studying where efficient algorithms exist and where
they are not known. Every entry carries an explicit verification level, and the validator enforces
that level. Nothing is counted as validated just because a paper says so.

> Status: v0, bootstrapping. See [START_HERE.txt](START_HERE.txt) for the full charter.

## What counts as a pair

A pair is a property of a **problem family** (defined for every input size n), not of a single number or
expression. One entry records a problem with an explicit size parameter and at least two provably
correct algorithms whose costs differ asymptotically.

These are **not** pairs: a constant written two ways (`4 = 2^2`), a single instance with no family over n,
or a cosmetic rewrite with the same cost. In this project, "exponential" always means a cost that
grows like 2^n or faster in the input size. It never means a formula that happens to contain a power.

| Tag | Meaning |
|---|---|
| T1 | exp → poly, same problem (rare) |
| T2 | naive-exp → poly (the naive method was wasteful: DP, memoisation, a better idea) |
| T3 | poly → faster poly |
| T4 | randomized ↔ deterministic |
| T5 | quantum → classical (dequantization) |
| T6 | open / unpaired: only high-cost algorithms known (e.g. factoring classically) |
| T7 | synthetic / bloated: deliberately wasteful rewrites. Low signal, stored separately, never counted |
| T8 | super-poly → faster super-poly (n! → 2ⁿ, 2ⁿ → 1.307ⁿ): real improvements that stay exponential |
| T9 | proven quantum advantage in a query / oracle / black-box model (needs a cited classical lower bound) |

The primary tag is T6 whenever polynomial time is open for the problem; the improvement then goes in
`secondary_tags` (e.g. TSP: T6 + T8). An entry counts as a **validated pair** if it is V1+ in `pairs/` and
carries any of T1–T5, T8, T9.

| Level | Meaning | Enforced by `tools/validate.py` |
|---|---|---|
| V0 | claimed: cited, not independently checked | folder `staging/` |
| V1 | correct: ≥ 2 implementations agree with each other (and an oracle) on a test battery | runs every implementation |
| V2 | scaling: measured growth matches the claimed cost | fits log(time), or log(reported operation count, e.g. oracle queries), against log(cost(n)); slope must be 1 ± tolerance |
| V3 | proven: complexity proof cited | requires `verification.proofs` |

## The dataset

<!-- PAIRS-TABLE:START -->
**28 validated pairs** (V1+, tagged T1–T5, T8 or T9) · 9 open problems (T6) · 4 proven quantum advantages (T9) · 8 staged (V0) · 6 with a quantum algorithm (⚛)

### Verified (`pairs/`, V1+)

| Entry | Type | Level | Algorithms (time) |
|---|---|---|---|
| [Primality testing: trial division vs AKS](pairs/primality-trial-vs-aks) | T1 | V1 | trial division: Theta(sqrt(N)) = Theta(2^(n/2)) divisions in the worst case<br>AKS: Õ(n^(21/2)) as proven in AKS 2004 |
| [Assignment problem: permutation enumeration vs the Hungarian method](pairs/assignment-brute-vs-hungarian) | T2 | V2 | permutation enumeration: Theta(n * n!)<br>Hungarian method (shortest augmenting paths with potentials): O(n^3) worst case |
| [Determinant over GF(p): cofactor expansion vs Gaussian elimination](pairs/determinant-cofactor-vs-gaussian) | T2 | V2 | Laplace (cofactor) expansion: Theta(n!) field operations<br>Gaussian elimination mod p: Theta(n^3) field operations on non-singular input |
| [Edit (Levenshtein) distance: plain recursion vs Wagner-Fischer DP](pairs/edit-distance-brute-vs-dp) | T2 | V2 | plain recursion: Theta(D(n, n)) = Theta((3 + 2 sqrt 2)^n / sqrt(n)) ~ Theta(5.83^n / sqrt(n))<br>Wagner-Fischer dynamic programming: Theta(n^2) |
| [Fibonacci numbers: naive recursion vs dynamic programming vs fast doubling](pairs/fibonacci-naive-vs-dp) | T2 | V2 | naive recursion: Theta(phi^n)<br>bottom-up dynamic programming: Theta(n) word operations<br>fast doubling (matrix power): Theta(log n) word operations |
| [Greatest common divisor: trial divisors vs Euclid's algorithm](pairs/gcd-trial-vs-euclid) | T2 | V2 | trial divisors: Theta(2^n) iterations in the worst case<br>Euclid's algorithm: O(n) division steps |
| [Longest common subsequence: subsequence enumeration vs dynamic programming](pairs/lcs-brute-vs-dp) | T2 | V2 | subsequence enumeration: Theta(2^n n)<br>dynamic programming: Theta(n^2) |
| [Longest increasing subsequence: subset enumeration vs quadratic DP vs patience sorting](pairs/longest-increasing-subsequence) | T2+T3 | V2 | subset enumeration: Theta(2^n n) on every input<br>quadratic dynamic programming: Theta(n^2) on every input<br>patience sorting with binary search: O(n log L) <= O(n log n) |
| [Matrix-chain ordering: plain recursion vs dynamic programming](pairs/matrix-chain-recursion-vs-dp) | T2 | V2 | plain recursion: Theta(3^n)<br>bottom-up dynamic programming: Theta(n^3) |
| [Minimum spanning tree: edge-subset enumeration vs Kruskal (and Prim)](pairs/minimum-spanning-tree-brute-vs-kruskal) | T2 | V2 | enumeration of all (n-1)-edge subsets: Theta(n * C(n(n-1)/2, n-1)) = 2^Theta(n log n)<br>Kruskal with union-find: O(m log m) = O(n^2 log n) on K_n<br>Prim, array version: Theta(n^2) on K_n |
| [Modular exponentiation: repeated multiplication vs square-and-multiply](pairs/modular-exponentiation-repeated-vs-square-multiply) | T2 | V2 | repeated multiplication: Theta(e) = Theta(2^n) multiplications mod m<br>left-to-right square-and-multiply (binary method): Theta(n) multiplications mod m |
| [Single-pair shortest path: simple-path enumeration vs Dijkstra](pairs/shortest-path-enumeration-vs-dijkstra) | T2 | V2 | simple-path enumeration: Theta(n (n-2)!) on the complete digraph<br>Dijkstra (array version): Theta(n^2) with an array |
| [Closest pair of points: brute force vs divide and conquer](pairs/closest-pair-brute-vs-divide-conquer) | T3 | V2 | all pairs: Theta(n^2)<br>Shamos-Hoey divide and conquer: Theta(n log n) on every input |
| [Integer multiplication: schoolbook vs Karatsuba](pairs/integer-multiplication-schoolbook-vs-karatsuba) | T3 | V2 | schoolbook (long) multiplication: Theta(n^2) digit operations<br>Karatsuba: Theta(n^log2(3)) ~ Theta(n^1.585) digit operations |
| [Counting inversions: all pairs vs merge sort](pairs/inversion-counting-quadratic-vs-merge) | T3 | V2 | all pairs: Theta(n^2)<br>merge-sort counting: Theta(n log n) |
| [Matrix multiplication: schoolbook vs Strassen](pairs/matrix-multiplication-naive-vs-strassen) | T3 | V1 | schoolbook: Theta(n^3)<br>Strassen: Theta(n^(log2 7)) ~ Theta(n^2.807) |
| [Maximum subarray sum: brute force vs running sums vs Kadane's scan](pairs/maximum-subarray) | T3 | V2 | brute force (sum every subarray): Theta(n^3) on every input<br>running sums: Theta(n^2) on every input<br>Kadane's algorithm (linear scan): Theta(n) |
| [Polynomial multiplication over Z_p: schoolbook vs number-theoretic transform (FFT)](pairs/polynomial-multiplication-naive-vs-ntt) | T3 | V2 | schoolbook convolution: Theta(n^2)<br>number-theoretic transform (Cooley-Tukey over Z_p): Theta(n log n) |
| [Comparison sorting: insertion sort vs merge sort](pairs/sorting-insertion-vs-merge) | T3 | V2 | insertion sort: Theta(n + I) where I is the number of inversions<br>merge sort: Theta(n log n) on every input |
| [Exact string matching: naive scan vs Knuth-Morris-Pratt](pairs/string-matching-naive-vs-kmp) | T3 | V2 | naive matching: Theta(n m) character comparisons in the worst case<br>Knuth-Morris-Pratt: Theta(n + m) on every input |
| [3SUM: all triples vs sorting with two pointers](pairs/three-sum-cubic-vs-quadratic) | T3 | V2 | all triples: Theta(n^3) worst case<br>sort + two pointers: Theta(n^2) |
| [Primality testing: Miller-Rabin (randomized) vs AKS (deterministic)](pairs/primality-miller-rabin-vs-aks) | T4 | V1 | Miller-Rabin: O(k n^3) bit operations for k rounds with schoolbook multiplication<br>AKS: Õ(n^(21/2)) as proven in AKS 2004 |
| [0/1 knapsack: subset enumeration vs meet in the middle vs pseudo-polynomial DP](pairs/knapsack-01-brute-vs-dp) | T6+T8 | V2 | subset enumeration: Theta(2^n n)<br>meet in the middle (Horowitz-Sahni): Theta(2^(n/2) n)<br>capacity DP (Bellman): Theta(n W) |
| [Permanent: sum over permutations vs Ryser's formula](pairs/permanent-naive-vs-ryser) | T6+T8 | V2 | sum over all permutations: Theta(n * n!) arithmetic operations<br>Ryser's formula with Gray-code ordering: Theta(n 2^n) arithmetic operations |
| [Travelling salesman: permutation enumeration vs Held-Karp DP](pairs/tsp-brute-vs-held-karp) | T6+T8 | V2 | permutation enumeration: Theta(n!)<br>Held-Karp dynamic programming: Theta(n^2 2^n) |
| [Bernstein-Vazirani: n classical queries vs 1 quantum query](pairs/bernstein-vazirani-classical-vs-quantum) | T9 | V2 | classical: query the unit vectors: n queries<br>Bernstein-Vazirani quantum algorithm: 1 query ⚛ |
| [Unstructured search: Theta(N) classical queries vs Theta(sqrt N) quantum queries (Grover)](pairs/grover-search-classical-vs-quantum) | T9 | V2 | classical random-order search: (N + 1) / 2 queries expected = Theta(2^n)<br>Grover's algorithm: (pi/4) sqrt(N) + O(1) queries = Theta(2^(n/2)) ⚛ |
| [Simon's problem: Theta(2^(n/2)) classical queries vs O(n) quantum queries](pairs/simon-classical-vs-quantum) | T9 | V2 | classical collision search: Theta(2^(n/2)) queries expected<br>Simon's quantum algorithm: O(n) queries ⚛ |

### Staging (`staging/`, V0: cited, not yet independently checked)

| Entry | Type | Level | Algorithms (time) |
|---|---|---|---|
| [Linear programming: simplex vs ellipsoid / interior-point methods](staging/linear-programming-simplex-vs-interior-point) | T1+T6 | V0 | simplex method (Dantzig's pivot rule): exponential in the worst case<br>ellipsoid method: polynomial in n and L<br>interior-point method (Karmarkar): O(n^3.5 L) arithmetic operations |
| [Maximum flow: Edmonds-Karp vs push-relabel vs almost-linear time](staging/max-flow-edmonds-karp-vs-almost-linear) | T3 | V0 | Edmonds-Karp: O(n m^2)<br>push-relabel (Goldberg-Tarjan): O(n m log(n^2 / m)) with dynamic trees<br>almost-linear-time max flow (Chen et al.): m^(1+o(1)) |
| [Recommendation systems: Kerenidis-Prakash quantum algorithm vs Tang's dequantization](staging/recommendation-systems-dequantization) | T5 | V0 | Kerenidis-Prakash quantum recommendation algorithm: poly(k) polylog(mn) ⚛<br>Tang's quantum-inspired classical algorithm: poly(k, 1/eps) polylog(mn) |
| [3-SAT: brute force vs Schöning vs PPSZ](staging/boolean-satisfiability) | T6+T8 | V0 | brute force: O(2^n m)<br>Schöning's random walk: O((4/3)^n poly(n)) expected<br>PPSZ / biased-PPSZ: O(1.308^n) |
| [Discrete logarithm: generic and index-calculus algorithms vs Shor's quantum algorithm](staging/discrete-logarithm) | T6+T9 | V0 | baby-step giant-step: O(sqrt(p)) = O(2^(n/2)) group operations<br>Pollard rho for logarithms: O(sqrt(p)) group operations<br>number field sieve for discrete logs in GF(q): L_q[1/3, (64/9)^(1/3)]<br>Shor's algorithm: polynomial in n ⚛ |
| [Graph isomorphism: moderately exponential vs quasi-polynomial](staging/graph-isomorphism) | T6+T8 | V0 | brute force over permutations: O(n! n^2)<br>Babai-Luks canonical labeling: exp(O(sqrt(n log n)))<br>Babai's quasi-polynomial algorithm: exp((log n)^O(1)) |
| [Integer factoring: classical algorithms vs Shor's quantum algorithm](staging/integer-factoring) | T6+T8 | V0 | trial division: O(2^(n/2))<br>Pollard rho: O(N^(1/4)) = O(2^(n/4)) heuristically<br>general number field sieve (GNFS): exp(((64/9)^(1/3) + o(1)) (ln N)^(1/3) (ln ln N)^(2/3))<br>Shor's algorithm: O(n^3) quantum gates with schoolbook modular arithmetic ⚛ |
| [Polynomial identity testing: randomized polynomial vs deterministic (open)](staging/polynomial-identity-testing) | T6+T4 | V0 | expand into monomials: exponential in s in general<br>Schwartz-Zippel random evaluation: poly(s) |

### Synthetic (`synthetic/`, T7: not counted)

| Entry | Type | Level | Algorithms (time) |
|---|---|---|---|
| [Synthetic: linear recurrence a(n) = 1 a(n-1) + 1 a(n-3) (mod 2^64), naive vs DP vs matrix power](synthetic/linear-recurrence-c1-0-1) | T7 | V2 | naive recursion (deliberately wasteful): Theta(lambda^n) calls<br>bottom-up dynamic programming: Theta(k n) word operations<br>companion-matrix power: Theta(k^3 log n) word operations |
| [Synthetic: linear recurrence a(n) = 1 a(n-1) + 1 a(n-2) + 1 a(n-3) (mod 2^64), naive vs DP vs matrix power](synthetic/linear-recurrence-c1-1-1) | T7 | V2 | naive recursion (deliberately wasteful): Theta(lambda^n) calls<br>bottom-up dynamic programming: Theta(k n) word operations<br>companion-matrix power: Theta(k^3 log n) word operations |
| [Synthetic: linear recurrence a(n) = 1 a(n-1) + 1 a(n-2) + 1 a(n-3) + 1 a(n-4) (mod 2^64), naive vs DP vs matrix power](synthetic/linear-recurrence-c1-1-1-1) | T7 | V2 | naive recursion (deliberately wasteful): Theta(lambda^n) calls<br>bottom-up dynamic programming: Theta(k n) word operations<br>companion-matrix power: Theta(k^3 log n) word operations |
| [Synthetic: linear recurrence a(n) = 2 a(n-1) + 3 a(n-2) (mod 2^64), naive vs DP vs matrix power](synthetic/linear-recurrence-c2-3) | T7 | V2 | naive recursion (deliberately wasteful): Theta(lambda^n) calls<br>bottom-up dynamic programming: Theta(k n) word operations<br>companion-matrix power: Theta(k^3 log n) word operations |
<!-- PAIRS-TABLE:END -->

## Classical vs quantum

Every algorithm records its computational model (`classical-deterministic`, `classical-randomized`, or
`quantum`), so you can query the dataset for the classical/quantum frontier. T5 entries record cases where
a claimed exponential quantum speedup was **dequantized**. T6 entries such as factoring and discrete
logarithm record cases where it was **not**. The dataset collects evidence on this question; it does not
settle it. An unconditional proof that quantum computers are more powerful (BQP ≠ BPP) would imply
P ≠ PSPACE, which is far beyond the reach of any catalogue.

## Research log and evidence

Every result is recorded, including refutations, corrections and inconclusive tests:

- [RESEARCH_LOG.md](RESEARCH_LOG.md) is the dated lab notebook: what was tested, what held, what failed, what was corrected,
  with exact numbers and their provenance.
- [ledger/runs/](ledger/runs/) holds machine-recorded validation runs (`tools/validate.py --record`): the environment,
  the git state and every measured value.
- [experiments/](experiments/) holds the deterministic scripts behind ad-hoc checks cited in the log.

## Quick start

```bash
pip install -r requirements.txt
python tools/check_all.py                # everything below in one go (--record, --sources, --quick)
python tools/validate.py                 # schema, folder rules, V1 correctness runs
python tools/validate.py --scaling -v    # also re-measure every V2 scaling claim
python tools/validate.py --probe         # report entries that pass a higher level than claimed
python tools/validate.py --scaling --record   # same, and store all results in ledger/runs/
python tools/check_sources.py            # resolve every DOI / arXiv id and compare titles (network)
python tools/build_index.py              # regenerate index.json and the table above
python -m unittest discover -s tests     # the validator must reject wrong claims
```

## Layout

```
schema/entry.schema.json     the entry format (JSON Schema 2020-12)
pairs/<id>/                  V1+ entries: entry.json, README.md, harness.py, implementations/
staging/<id>/                V0 entries (cited, awaiting implementation)
synthetic/<id>/              T7 entries (never counted as validated)
notes/                       research notes and material that is not a pair
lib/                         shared code (qsim.py: exact state-vector simulator for T9 entries)
tools/                       validate.py, build_index.py, check_sources.py
experiments/                 deterministic scripts behind RESEARCH_LOG entries
ledger/runs/                 recorded validation runs (evidence)
RESEARCH_LOG.md              the lab notebook
index.json                   generated registry of all entries
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: add `pairs/<id>/` or `staging/<id>/`, run the validator, and
open a PR. CI re-runs everything.

## Scope

This is not a cryptanalysis tool. Factoring and discrete logarithm are catalogued as open (T6), and
we do not target them operationally. We make no claim about P vs NP. We reject cosmetic rewrites and
number-notation tricks.

## License

Free for **personal, educational and non-commercial research use**. **Commercial use requires a paid license**,
and the fees fund the research. See [COMMERCIAL.md](COMMERCIAL.md).

- Data (entries, READMEs, notes, index, the compilation): [CC BY-NC 4.0](LICENSE)
- Code (tools, lib, harnesses, implementations, tests): [PolyForm Noncommercial 1.0.0](LICENSE-CODE)

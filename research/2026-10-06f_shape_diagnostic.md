# Exact shape diagnostic for exact-count V2 (round 2026-10-06f)

Author: delegated research agent (Claude), for the maintainer. Date: 2026-10-06. Environment: Windows 11 Pro
10.0.26200, CPython 3.14.2, jsonschema 4.26.0 (the project venv, unchanged).

## How to read the labels

- **[console]** seen in a run made during this round, not machine-recorded (per-entry validator runs; their
  exact counts do not depend on machine load).
- **[exp: name]** a deterministic script `experiments/2026-10-06f_shape_<name>.py`; rerunning it reproduces the
  numbers.
- **[test]** asserted by a unit test in `tests/test_shape.py` or `tests/test_shape_validator.py`.
- **[ledger]** `ledger/runs/20261006T143136Z.json`, read only.

No ledger file was written in this round. The recorded run is left to the maintainer.

---

## Summary

- **What was built.** An exact shape diagnostic for V2 claims measured with exact counts (`measure: "reported"`).
  It is informational in this round. It guesses a recurrence for the counts on a regular grid, accepting the guess
  only if it is overdetermined, has a one-dimensional solution space and reproduces held-out terms. It reads the
  growth off the recurrence exactly (base as an algebraic number with its minimal polynomial, polynomial power, log
  power), and compares that with the claimed cost, which is parsed exactly. Every run ends in one of four categories
  (MATCH, MISMATCH, UNDETERMINED, SKIPPED) with one of 20 machine-readable reasons.
- **Where.** The engine is a new pure module, `methods/shape.py`. The integration in `tools/validate.py` adds a
  printed line with `-v` and a `shape` field per V2 measurement with `--record`. `schema/entry.schema.json` gains an
  optional `harness.scaling.shape` block. V2 pass/fail and all existing output lines are unchanged (proof in
  section 4).
- **Applied.** 46 shape blocks were added to 23 existing entries (insertion only, verified against git HEAD
  [exp: blocks]). Over all **59 exact-count series** of the last recorded run [exp: survey]:
  **40 MATCH, 0 MISMATCH, 19 UNDETERMINED** (6 instance-dependent counts with a block; without a block,
  10 randomised, 2 harnesses outside both grid kinds, 1 too few terms). All 40 MATCHes have the claimed base, power
  and log power exactly, including n^log₂7 for Strassen (root 7), n^log₂3 for Karatsuba (root 3) and n·log n for the
  NTT, the sparse table and patience sorting (doubling root 2 of multiplicity 2).
- **No MISMATCH occurred**, so no entry claim is in question. Three automatic first grids gave UNDETERMINED
  (Strassen, Karatsuba, KMP). In each case the grid started before the count's regular regime (schoolbook cutoffs,
  a degenerate pattern for n ≤ 5), so this was a limit of the grid choice, not of the claim. With the grid starting
  at the regular regime, all three are MATCH.
  *Correction (2026-10-07): "no entry claim is in question" says too much. A MATCH is evidence, not a proof (§2
  of this report), and side finding (1) below shows a count statement (RL-057's KMP 4n − 6) that was wrong. What
  holds is that no V2 cost expression's shape was contradicted by its exact counts on the declared grids.*
- **Side findings.** (1) The KMP count is 4n − 6 for even n and 4n − 7 for odd n (n = 6..60); RL-057 quoted 4n − 6
  from its even-n V2 grid [exp: closed_forms]. (2) The RMQ sparse-table count includes comparisons inside
  two-argument `min()`. RL-069 reports these counts identical under CPython 3.12.10 and 3.14.2 (agent report), and
  the entry does not declare version dependence. (3) Why the fit cannot replace the diagnostic, on the dataset's own
  grids with perfect data: n^2.8 passes for Strassen's n^log₂7 counts (α = 1.0026 at tolerance 0.02), and the
  edit-distance claim without its 1/√n passes on the entry's V2 grid (α = 0.9585 at 0.25) [exp: fit_limits].
- **Tests.** 42 new tests (30 engine, 12 integration and regression). Full suite on the final state: 266 tests OK,
  1 skipped, in 79 s (other agents added tests in parallel) [console]. With `CPAIRS_FULL_REGRESSION=1`, all 59 exact-count V2 series equal the ledger in verdict and in
  value (same Python version as the ledger), 155 s [console].

---

## 1. Design and decision log

| Decision | Alternatives considered | Evidence that settled it |
|---|---|---|
| The block lives in `harness.scaling.shape` (per scaling claim) | per algorithm (`harness.shape`); per entry | The diagnostic checks the scaling claim: it needs `cost`, `measure`, `samples` and V2's values, all in `harness.scaling`. One schema addition in `$defs/scaling` (additionalProperties stays false) |
| The grid is declared as `sequence` + `n_range` (+ `step` for consecutive grids) | an explicit list of n | The method needs a regular grid. A range cannot be irregular and is shorter. `step` covers harnesses that need a stride; no current block needs it |
| The claimed shape is derived from `cost` by an exact parser, with `expect` as the override | numeric evaluation of `cost` plus LLL guessing of constants; always explicit `expect` | Exactness: 58 of the 59 exact-count cost expressions (97 of all 108 V2 costs) parse exactly; the exceptions are factorial-type costs and the 4 synthetic decimal bases [console, script in section 8]. LLL would reintroduce a guess on the claim side |
| The shape model is C·bⁿ·n^p·(log n)^q; a consecutive grid sees (b, p), a doubling grid sees (p, q) | one model per grid; free-form | One vocabulary for readers. MISMATCH components map one to one: `base`, `polynomial_factor`, `log_power` |
| Constants are exact objects: rationals, a + b√d, c^(1/v) with v ≤ 12, roots of given polynomials | floats | Covers every base and power in the dataset's costs: φ, 3+2√2, (1+√33)/4, 2^(1/3), log₂7, log₂3, 5/2 [test: CostParsing]. A decimal *base* (`1.4655712319**n`) is refused (`cost_not_parseable`) rather than treated as an exact rational, because that would report a misleading MISMATCH |
| Acceptance rule: RL-082 defaults (constant coefficients: 2L + 2 training terms and 4 held out; polynomial coefficients: 4 equations beyond the unknowns and 3 held out); `holdout` may be lowered to 2, never below | a fixed rule only; holdout 1 | Strassen's regular regime starts at n = 16, and n = 1024 costs about 7 times n = 512. With holdout 2, n = 16..512 gives 6 terms (4 training + 2 held out): MATCH [console]. The holdout used is recorded with every result |
| Precedence: block, randomised, count failure, instance dependence, non-integer, declared version dependence, identification, claim | claim problems first | A claim cannot be compared with a shape that was never identified; data problems are more basic. The found shape is recorded in every case |
| Instance-dependence probe: 3 smallest grid n ≥ 3, 2 other seeds each (instance and `random`), run before the full grid | no probe (rely on "no recurrence"); probe every n | 6 series flagged at n = 4 or 5 in about 0.0 s each [console]. Without the probe their reason would be an uninformative "no recurrence". Running the probe first makes a block on such a series nearly free |
| Python-version dependence is declared (`python_version_dependent`), not detected | detect by running two Pythons | Only one Python is available to the validator. The rule follows RL-069 |
| Dominance: per-factor Schur bounds plus an exact same-modulus test (a factor whose roots all have modulus λ, with lower multiplicity, is dominated); floating-point checks never certify | `exactalg.dominance_certificate` as is | On the KMP, naive-matching and floor(n/2) characteristic polynomials (x+1)(x−1)², (x+1)(x−1)³ and (x+1)(x−1)², the old test returns `fails` and the new one `certified` [console, script in section 8]; without it two dataset MATCHes would be `dominance_not_certified` |
| For polynomial-coefficient guesses, the exact θ must agree with a numeric slope within 0.15 | no guard | The Birkhoff–Trjitzinsky formula assumes that the counts follow the dominant formal solution. The guard can only turn a result into UNDETERMINED. Edit distance: numeric −0.4950 against exact −1/2 (RL-082) |
| Integration: the diagnostic runs after the V2 loop of an entry, only with `-v` or `--record`, reuses V2 values at shared n, and catches every exception | inline in the V2 loop; always on | Running after the loop means it cannot influence V2 measurements. Gating keeps plain `--scaling` (CI) unchanged in time and output. A test caught my first gating bug (section 6) |
| Engine in `methods/shape.py`, imported lazily by `validate.py` | everything in `validate.py` | Pure, unit-testable functions. The validator does not depend on `methods/` unless the diagnostic runs |
| Blocks on deterministic series and on instance-dependent series; none on randomised series, the two matching series or MST enumeration; none on entries created in this round | blocks everywhere; MATCH-only | Instance-dependent blocks cost about 0 s and record *why* the diagnostic cannot decide. Randomised blocks could only ever say `randomised_counts`. Matching harnesses accept only n = 4k² + k. MST enumeration has 7 terms for n ≤ 8 (n = 8 alone took about 4 s) and a factorial-type cost |
| Default regression scope: 46 exact-count series with samples = 1 outside the Strassen entry; everything with `CPAIRS_FULL_REGRESSION=1` | always full (+155 s) | The default regression test takes about 48 s (54.5 s for the 12 tests of the file, 6.2 s without it); the full run was made once and passed [console] |

---

## 2. Category definitions

A **guess** is accepted only if (a) it is found on the training terms (all but the held-out ones) and is
overdetermined there: for constant coefficients, the Berlekamp–Massey length L satisfies 2L + 2 ≤ #training terms;
for polynomial coefficients, #equations ≥ #unknowns − 1 + 4; (b) its solution space is one-dimensional (for
Berlekamp–Massey this follows from 2L < #terms); (c) it reproduces every held-out term exactly. Constant
coefficients are tried first. Polynomial coefficients are searched by increasing order + degree, with order ≤
`max_order` (6) and degree ≤ `max_degree` (4).

**Found shape.** Constant coefficients: λ is the dominant real root of the characteristic polynomial, with its exact
minimal polynomial (Kronecker factorisation) and multiplicity m, and θ = m − 1. The recurrence is minimal, so every
root appears with full multiplicity. Polynomial coefficients: λ comes from the leading-coefficient polynomial, and
θ from the exact balance formula in Q(λ) (simple root only).

| Category | Reason | Exact condition |
|---|---|---|
| MATCH | `exact_shape_agrees` | accepted guess, dominance certified, λ_found and λ_claimed have the same primitive minimal polynomial **and** are the same real root of it, and θ_found = θ_claimed (rationals) |
| MISMATCH | `differs` | accepted guess, dominance certified, claim available, and λ or θ differs. `differs` ⊆ {base, polynomial_factor} (consecutive) or {polynomial_factor, log_power} (doubling); `found` and `claimed` give both sides |
| UNDETERMINED | `invalid_shape_block` | grid or `expect` inconsistent (doubling endpoints not powers of two, step not dividing lo, more than 64 points, holdout < 2, unparsable `expect`) |
| | `randomised_counts` | `samples > 1` |
| | `count_failed` | the harness or implementation raised at a grid n |
| | `instance_dependent_counts` | some probe count ≠ the V2-seeded count at the same n |
| | `non_integer_counts` | a count is not an integer (or is a float ≥ 2^53) |
| | `python_version_dependent` | the block declares it |
| | `too_few_terms` | fewer than 2 + 2 + holdout terms; or the Berlekamp–Massey length L ≤ `max_order` but 2L + 2 > #training terms (the record gives the minimum needed, a lower bound) and no polynomial-coefficient candidate is overdetermined |
| | `holdout_not_reproduced` | some candidate fitted the training terms but failed a held-out term |
| | `solution_space_not_one_dimensional` | some polynomial-coefficient system had a nullspace of dimension > 1 and no candidate was accepted |
| | `no_recurrence_within_limits` | otherwise, when no candidate was accepted |
| | `factorial_type_growth` | accepted polynomial-coefficient guess whose p₀ has lower degree than the maximum degree |
| | `dominance_not_certified` | the exact test fails (the floating-point verdict is recorded as `numeric` or `fails`) |
| | `asymptotics_not_determined` | no real root; a repeated dominant root with polynomial coefficients; or a θ guard failure |
| | `cost_not_parseable` | the cost is outside the grammar and there is no `expect` |
| | `cost_outside_grid_family` | the claim has q ≠ 0 or an irrational p on a consecutive grid, or b ≠ 1 on a doubling grid |
| | `internal_error` | any exception in the diagnostic |
| SKIPPED | `timing_measure` | `measure` is `time` |
| | `no_shape_block` | no block |

A MATCH is strong evidence, not a proof: the recurrence is a conjecture verified on finitely many terms.

---

## 3. Implementation notes

**`methods/shape.py` (new, about 900 lines).** Exact constants (`("q", F)`, `("s", a, b, d)`, `("r", c, v)`,
`("p", poly, approx)`, inexact `("f", x)`) with arithmetic, minimal polynomials (radicals normalised so that
x^v − c is irreducible by Capelli's criterion, so no factoring is needed) and root identity. `parse_cost` and
`parse_expect` produce a `Shape(base, 2^p, q, coef)`; `expected_on_grid` maps it to (λ, θ) or raises
`OutsideGridFamily`; `grid_from_block` builds the grid; `identify` runs the guessers (Berlekamp–Massey from
`methods/recurrences.py`, my own polynomial-coefficient search that records per-candidate statuses), the dominance
test and the θ rule; `run` applies the precedence; `summary_line` formats the verbose line. `REASONS` is the single
table of reasons and categories, and `outcome()` asserts that each reason is used with its category.

**`tools/validate.py` (+116/−2 lines).**
1. Module docstring: a `shape` paragraph and a `--no-shape` usage line.
2. `run_v2(..., shape=True)`: each measurement dict is queued. After the loop, if `shape and (verbose or rec is not
   None)`, `run_shape` runs for each queued measurement, stores `m["shape"]`, and prints one line with `-v`. Nothing
   inside the loop changed, and `errors`/`ok` are not touched.
3. New `run_shape` (never raises): SKIPPED for timing measures or missing blocks; lazy import of `methods.shape`;
   probe first, then the grid counts (V2 values reused where n coincides, V2 seeding otherwise); all exceptions are
   mapped to `count_failed` or `internal_error`.
4. New `shape_line` for the verbose line.
5. `validate_entry`: `want_shape = not args.no_shape and (args.verbose or recorder is not None)` is passed to
   `run_v2` (`getattr` keeps old callers working).
6. `run_metadata` gains `shape_diagnostic` (version 1, the default limits, `informational: true`).
7. CLI: `--no-shape`.

**`schema/entry.schema.json` (+111 lines).** `$defs/scaling.properties.shape` → `$defs/shape` with `sequence`,
`n_range` (required), `step`, `max_order`, `max_degree`, `holdout`, `python_version_dependent`, `expect` (`base` as
a string or `{minpoly, approx}`, `polynomial_factor`, `log_power`) and `note`; additionalProperties false.

**Proof that pass/fail is unchanged.**
1. *Code:* the V2 loop body is unchanged except for one `append` of the measurement to a local queue. The
   diagnostic runs after the loop, writes only `m["shape"]` and verbose lines, and catches all exceptions.
   `validate_entry` only gates it.
2. *Tests:* a crash injected into `methods.shape.run` leaves the entry passing [test]; a wrong `expect` gives
   MISMATCH and the entry still passes [test]; a wrong `cost` still fails V2 [test]; verbose output with the
   diagnostic, minus the new `shape` lines, equals the output with `--no-shape` (elapsed seconds normalised) [test];
   with neither `-v` nor `--record`, `run_shape` is never called (patched to raise) [test]; every old ledger
   measurement key is still present and `shape` is the only new key [test].
3. *Regression against ledger 20261006T143136Z:* all 59 exact-count series (`CPAIRS_FULL_REGRESSION=1`) and the 46
   default series give identical `passed` flags, `n_values` and exact `values` (same CPython 3.14.2) [test, 155 s].
4. *Real runs:* `tools/validate.py --scaling -v` on the 23 modified entries: 23/23 OK [console];
   `tools/validate.py`: 69/69 OK and `tools/validate.py --static`: 69/69 OK on the final state, including the
   entries other agents added in parallel [console].

Timing measures are SKIPPED without executing anything [test], so the 49 wall-clock fits cannot be affected.

---

## 4. Results per series

Source: `experiments/2026-10-06f_shape_survey.py` on the final state [exp: survey]. Series with an entry block use
it; the others use an automatic grid that is not stored anywhere. "found/claimed" are written as the components the
grid can see. "terms used/checked" counts the training terms and all terms.

| # | Entry / algorithm | cost | grid | category (reason) | found | claimed | characteristic polynomial; terms used/checked |
|---|---|---|---|---|---|---|---|
| 1 | all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall / Bellman-Ford from every source | `n**2 * (n-1)**2` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^4, base 1 | n^4, base 1 | (x - 1)^5; 16/20 |
| 2 | all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall / Floyd-Warshall | `n**3` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^3, base 1 | n^3, base 1 | (x - 1)^4; 16/20 |
| 3 | bernstein-vazirani-classical-vs-quantum / classical: query the unit vectors | `n` | consecutive 1..16 | MATCH (exact_shape_agrees) | n^1, base 1 | n^1, base 1 | (x - 1)^2; 12/16 |
| 4 | bernstein-vazirani-classical-vs-quantum / Bernstein-Vazirani quantum algorithm | `1` | consecutive 1..10 | MATCH (exact_shape_agrees) | n^0, base 1 | n^0, base 1 | (x - 1); 6/10 |
| 5 | bipartite-matching-kuhn-vs-hopcroft-karp / Kuhn's augmenting paths (one DFS per left ... | `n**3` | no block | UNDETERMINED (count_failed): harness accepts only n = 4k^2 + k | - | - | - |
| 6 | bipartite-matching-kuhn-vs-hopcroft-karp / Hopcroft-Karp | `n**2.5` | no block | UNDETERMINED (count_failed): harness accepts only n = 4k^2 + k | - | - | - |
| 7 | closest-pair-brute-vs-divide-conquer / all pairs | `n**2` | consecutive 2..20 | MATCH (exact_shape_agrees) | n^2, base 1 | n^2, base 1 | (x - 1)^3; 15/19 |
| 8 | closest-pair-brute-vs-divide-conquer / Shamos-Hoey divide and conquer | `n * log(n)` | doubling 2..4096 | UNDETERMINED (instance_dependent_counts): n=4: 8 (V2 seed) vs 12 (probe seed 1) | - | - | - |
| 9 | collision-problem-classical-vs-quantum / classical birthday search | `2**(n/2)` | no block (samples = 100) | UNDETERMINED (randomised_counts) | - | - | - |
| 10 | collision-problem-classical-vs-quantum / Brassard-Hoyer-Tapp, known number of marke... | `2**(n/3)` | no block (samples = 40) | UNDETERMINED (randomised_counts) | - | - | - |
| 11 | collision-problem-classical-vs-quantum / Brassard-Hoyer-Tapp with BBHT exponential ... | `2**(n/3)` | no block (samples = 100) | UNDETERMINED (randomised_counts) | - | - | - |
| 12 | deutsch-jozsa-classical-vs-quantum / classical deterministic: scan until a diff... | `2**(n-1) + 1` | consecutive 1..16 | MATCH (exact_shape_agrees) | n^0, base 2 | n^0, base 2 | (x - 1) (x - 2); 12/16 |
| 13 | deutsch-jozsa-classical-vs-quantum / classical randomized, one-sided bounded er... | `1` | consecutive 1..12 | MATCH (exact_shape_agrees) | n^0, base 1 | n^0, base 1 | (x - 1); 8/12 |
| 14 | deutsch-jozsa-classical-vs-quantum / Deutsch-Jozsa quantum algorithm (one-query... | `1` | consecutive 1..10 | MATCH (exact_shape_agrees) | n^0, base 1 | n^0, base 1 | (x - 1); 6/10 |
| 15 | element-distinctness-pairs-vs-sorting / all pairs | `n**2` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^2, base 1 | n^2, base 1 | (x - 1)^3; 16/20 |
| 16 | element-distinctness-pairs-vs-sorting / sort, then compare neighbours | `n*log(n)` | doubling 2..4096 | UNDETERMINED (instance_dependent_counts): n=4: 8 (V2 seed) vs 7 (probe seed 2) | - | - | - |
| 17 | global-min-cut-brute-vs-stoer-wagner / brute force | `n**2 * 2**n` | consecutive 2..17 | MATCH (exact_shape_agrees) | n^2, base 2 | n^2, base 2 | (x - 1) (x - 2)^3; 12/16 |
| 18 | global-min-cut-brute-vs-stoer-wagner / Stoer-Wagner (array) | `n**3` | consecutive 2..21 | MATCH (exact_shape_agrees) | n^3, base 1 | n^3, base 1 | (x - 1)^4; 16/20 |
| 19 | grover-search-classical-vs-quantum / classical random-order search | `2**n` | no block (samples = 40) | UNDETERMINED (randomised_counts) | - | - | - |
| 20 | grover-search-classical-vs-quantum / Grover's algorithm | `2**(n/2)` | no block (samples = 5) | UNDETERMINED (randomised_counts) | - | - | - |
| 21 | integer-multiplication-schoolbook-vs-karatsuba / schoolbook (long) multiplication | `n**2` | consecutive 1..16 | MATCH (exact_shape_agrees) | n^2, base 1 | n^2, base 1 | (x - 1)^3; 12/16 |
| 22 | integer-multiplication-schoolbook-vs-karatsuba / Karatsuba | `n**log2(3)` | doubling 32..4096 | MATCH (exact_shape_agrees) | n^log2(3) = n^1.584963, (log n)^0 | n^log2(3) = n^1.584963, (log n)^0 | (x - 3); 4/8 |
| 23 | inversion-counting-quadratic-vs-merge / all pairs | `n**2` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^2, base 1 | n^2, base 1 | (x - 1)^3; 16/20 |
| 24 | inversion-counting-quadratic-vs-merge / merge-sort counting | `n * log(n)` | doubling 2..4096 | UNDETERMINED (instance_dependent_counts): n=4: 5 (V2 seed) vs 4 (probe seed 2) | - | - | - |
| 25 | longest-increasing-subsequence / subset enumeration | `2**n * n` | consecutive 1..18 | MATCH (exact_shape_agrees) | n^1, base 2 | n^1, base 2 | (x - 1) (x - 2)^2; 14/18 |
| 26 | longest-increasing-subsequence / quadratic dynamic programming | `n**2` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^2, base 1 | n^2, base 1 | (x - 1)^3; 16/20 |
| 27 | longest-increasing-subsequence / patience sorting with binary search | `n*log(n)` | doubling 2..65536 | MATCH (exact_shape_agrees) | n^1, (log n)^1 | n^1, (log n)^1 | (x - 1)^2 (x - 2)^2; 12/16 |
| 28 | matrix-multiplication-naive-vs-strassen / schoolbook | `n**3` | consecutive 1..18 | MATCH (exact_shape_agrees) | n^3, base 1 | n^3, base 1 | (x - 1)^4; 14/18 |
| 29 | matrix-multiplication-naive-vs-strassen / Strassen | `n**log2(7)` | doubling 16..512 | MATCH (exact_shape_agrees) | n^log2(7) = n^2.807355, (log n)^0 | n^log2(7) = n^2.807355, (log n)^0 | (x - 7); 4/6 |
| 30 | minimum-finding-classical-vs-quantum / classical scan | `2**n` | consecutive 1..14 | MATCH (exact_shape_agrees) | n^0, base 2 | n^0, base 2 | (x - 2); 10/14 |
| 31 | minimum-finding-classical-vs-quantum / Durr-Hoyer quantum minimum finding | `2**(n/2)` | no block (samples = 5) | UNDETERMINED (randomised_counts) | - | - | - |
| 32 | minimum-spanning-tree-brute-vs-kruskal / enumeration of all (n-1)-edge subsets | `n * factorial(n*(n-1)/2) / (factorial(n-1) * factorial(n*(n-1)/2 - n + 1))` | no block; auto consecutive 1..8 | UNDETERMINED (too_few_terms): shortest C-finite recurrence of the training terms has order 2; confirming it needs at lea | - | not parseable | - |
| 33 | minimum-spanning-tree-brute-vs-kruskal / Kruskal with union-find | `n**2 * log(n)` | doubling 2..2048 | UNDETERMINED (instance_dependent_counts): n=4: 33 (V2 seed) vs 34 (probe seed 1) | - | - | - |
| 34 | minimum-spanning-tree-brute-vs-kruskal / Prim, array version | `n**2` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^2, base 1 | n^2, base 1 | (x - 1)^3; 16/20 |
| 35 | nand-tree-evaluation-deterministic-vs-randomized / deterministic left-first evaluation | `2**n` | consecutive 1..14 | MATCH (exact_shape_agrees) | n^0, base 2 | n^0, base 2 | (x - 2); 10/14 |
| 36 | nand-tree-evaluation-deterministic-vs-randomized / randomized random-order evaluation | `((1 + sqrt(33)) / 4)**n` | no block (samples = 200) | UNDETERMINED (randomised_counts) | - | - | - |
| 37 | optimal-bst-recursion-vs-dp-vs-knuth / plain recursion | `3**n` | consecutive 1..12 | MATCH (exact_shape_agrees) | n^0, base 3 | n^0, base 3 | (x - 1) (x - 3); 8/12 |
| 38 | optimal-bst-recursion-vs-dp-vs-knuth / cubic interval DP (every root) | `n**3` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^3, base 1 | n^3, base 1 | (x - 1)^4; 16/20 |
| 39 | optimal-bst-recursion-vs-dp-vs-knuth / Knuth's speed-up (monotone roots) | `n**2` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^2, base 1 | n^2, base 1 | (x - 1)^3; 16/20 |
| 40 | polynomial-multiplication-naive-vs-ntt / schoolbook convolution | `n**2` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^2, base 1 | n^2, base 1 | (x - 1)^3; 16/20 |
| 41 | polynomial-multiplication-naive-vs-ntt / number-theoretic transform (Cooley-Tukey o... | `n*(3*log2(n) + 5)` | doubling 2..16384 | MATCH (exact_shape_agrees) | n^1, (log n)^1 | n^1, (log n)^1 | (x - 2)^2; 10/14 |
| 42 | range-minimum-queries-naive-vs-sparse-table / scan each range | `n**2` | consecutive 1..20 | UNDETERMINED (instance_dependent_counts): n=5: 15 (V2 seed) vs 17 (probe seed 1) | - | - | - |
| 43 | range-minimum-queries-naive-vs-sparse-table / sparse table | `n*log(n)` | doubling 2..65536 | MATCH (exact_shape_agrees) | n^1, (log n)^1 | n^1, (log n)^1 | (x - 1)^2 (x - 2)^2; 12/16 |
| 44 | regex-matching-backtracking-vs-thompson / backtracking (consume first) | `n * 2**n` | consecutive 1..16 | MATCH (exact_shape_agrees) | n^1, base 2 | n^1, base 2 | (x - 1) (x - 2)^2; 12/16 |
| 45 | regex-matching-backtracking-vs-thompson / memoised backtracking | `n**2` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^2, base 1 | n^2, base 1 | (x - 1)^3; 16/20 |
| 46 | regex-matching-backtracking-vs-thompson / Thompson's NFA simulation | `n**2` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^2, base 1 | n^2, base 1 | (x - 1)^3; 16/20 |
| 47 | simon-classical-vs-quantum / classical collision search | `2**(n/2)` | no block (samples = 40) | UNDETERMINED (randomised_counts) | - | - | - |
| 48 | simon-classical-vs-quantum / Simon's quantum algorithm | `n` | no block (samples = 100) | UNDETERMINED (randomised_counts) | - | - | - |
| 49 | sorting-insertion-vs-merge / insertion sort | `n**2` | no block (samples = 3) | UNDETERMINED (randomised_counts) | - | - | - |
| 50 | sorting-insertion-vs-merge / merge sort | `n*log(n)` | doubling 2..4096 | UNDETERMINED (instance_dependent_counts): n=4: 4 (V2 seed) vs 5 (probe seed 1) | - | - | - |
| 51 | spanning-tree-count-enumeration-vs-kirchhoff / Kirchhoff's matrix-tree theorem with Barei... | `(n-1)**3` | consecutive 1..20 | MATCH (exact_shape_agrees) | n^3, base 1 | n^3, base 1 | (x - 1)^4; 16/20 |
| 52 | string-matching-naive-vs-kmp / naive matching | `n**2` | consecutive 2..24 | MATCH (exact_shape_agrees) | n^2, base 1 | n^2, base 1 | (x + 1) (x - 1)^3; 19/23 |
| 53 | string-matching-naive-vs-kmp / Knuth-Morris-Pratt | `n` | consecutive 6..30 | MATCH (exact_shape_agrees) | n^1, base 1 | n^1, base 1 | (x + 1) (x - 1)^2; 21/25 |
| 54 | subset-sum-zeta-transform-naive-vs-yates / submask enumeration (naive) | `3**n` | consecutive 1..12 | MATCH (exact_shape_agrees) | n^0, base 3 | n^0, base 3 | (x - 3); 8/12 |
| 55 | subset-sum-zeta-transform-naive-vs-yates / Yates' method (fast zeta transform) | `n * 2**n` | consecutive 1..16 | MATCH (exact_shape_agrees) | n^1, base 2 | n^1, base 2 | (x - 2)^2; 12/16 |
| 56 | two-sat-brute-force-vs-scc / brute force over all assignments | `(n + 7) * 2**n` | consecutive 3..16 | MATCH (exact_shape_agrees) | n^1, base 2 | n^1, base 2 | (x - 1) (x - 2)^2; 10/14 |
| 57 | two-sat-brute-force-vs-scc / Aspvall-Plass-Tarjan (implication graph + ... | `n` | consecutive 3..20 | MATCH (exact_shape_agrees) | n^1, base 1 | n^1, base 1 | (x - 1)^2; 14/18 |
| 58 | xor-convolution-naive-vs-walsh-hadamard / all index pairs (naive) | `4**n` | consecutive 1..10 | MATCH (exact_shape_agrees) | n^0, base 4 | n^0, base 4 | (x - 4); 6/10 |
| 59 | xor-convolution-naive-vs-walsh-hadamard / fast Walsh-Hadamard transform (FWHT) | `n * 2**n` | consecutive 1..14 | MATCH (exact_shape_agrees) | n^1, base 2 | n^1, base 2 | (x - 2)^2; 10/14 |

**Totals:** 59 series; 40 MATCH (all with an entry block); 0 MISMATCH; 19 UNDETERMINED: 6
`instance_dependent_counts` (entry block), 10 `randomised_counts`, 2 `count_failed`, 1 `too_few_terms` (no block).

**MISMATCH investigation.** None occurred with the final grids, so no entry claim is questioned (*correction
2026-10-07: see the note in the Summary; a MATCH does not establish an entry claim*). Before the grids
were tuned, the automatic first pass [console] gave 37 MATCH and 22 UNDETERMINED. The cases that changed:

- *Strassen*, doubling n = 2..256: `holdout_not_reproduced` (the guess x − 7 failed at index 4). For n ≤ 16 the
  implementation uses schoolbook multiplication (CUTOFF = 16), so the counts there are n³. From n = 16:
  4096·7^(k−4), MATCH. **Cause: grid before the regular regime (limit of the grid choice).**
- *Karatsuba*, doubling n = 2..4096: `too_few_terms` (order 5). CUTOFF = 32 digits; from n = 32 the counts are
  exactly 1024·3^(k−5) (1024, 3072, …, 2239488), MATCH. **Same cause.**
- *KMP*, consecutive n = 1..22: `no_recurrence_within_limits` (order 8). The counts for n = 1..5 are 1, 2, 3, 8, 10,
  while 4n−6 (even) / 4n−7 (odd) would give −3, 2, 5, 10, 13. From n = 6 the guess is (x+1)(x−1)², MATCH.
  **Cause: degenerate tiny patterns (m = n//2 ≤ 2).**

Neither a wrong claim nor an incomplete count was involved. Partial counts (RL-068: the NTT counts only
multiplications on input-derived values) still MATCH their own exact formulas, which is the expected behaviour:
the diagnostic checks the counts as they are, not the completeness of the count.

**Other observations.**
- *Global min cut, brute force*: from n = 1 the minimal recurrence has an extra root 0 (order 5, the n = 1 count is
  special); from n = 2 it is (x−1)(x−2)³ = n²·2ⁿ, as RL-082 found.
- *2-SAT*: the harness accepts n ≥ 3 (the automatic start moved to 3).
- *Kruskal*: the probe flags instance dependence (33 vs 34 comparisons at n = 4) before the declared Python-version
  dependence is reached in the precedence order.
- *RMQ sparse table*: MATCH n·log n, (x−1)²(x−2)². Its count includes comparisons inside `min(a, b)` (one `__lt__`
  per call, RL-068). Under RL-069's rule that is a built-in comparison; RL-069 reports the series identical under
  CPython 3.12.10 and 3.14.2 (agent report). The block does not declare version dependence; this is left to the
  maintainer.
- Exact lower-order structure is visible in the characteristic polynomials: the NTT's (x−2)² means n log n + n with
  no constant (3n log₂n + 5n); patience sorting and the sparse table have (x−1)²(x−2)², i.e. n log n, n, log n and
  constant terms.

---

## 5. Edge cases and how they are handled

| Edge case | Handling | Why |
|---|---|---|
| Too few terms | `too_few_terms` with the minimum needed (a lower bound: Berlekamp–Massey sees at most half the prefix's order) | A test caught my first wording, which presented the bound as exact (section 6) |
| No recurrence within limits | `no_recurrence_within_limits`, with the list of (order/degree) candidates actually tested and the limits | Says what was tried, not just that it failed |
| Solution space > 1 dimension | `solution_space_not_one_dimensional` | A non-unique guess is not identification (RL-082 rule) |
| Held-out terms not reproduced | `holdout_not_reproduced`, with the failing index for constant coefficients | Typical of regime changes (cutoffs); Strassen on n = 2..256 |
| Dominance not certified | exact Schur + same-modulus tests; floating point is recorded but never certifies | 3·2ⁿ + (−2)ⁿ gives `fails` [test]; parity terms with lower multiplicity are certified [test] |
| Factorial-type growth | `factorial_type_growth` | n! + 1 [test]; the bⁿn^p(log n)^q model does not apply |
| Randomised counts (expected values) | `randomised_counts` for `samples > 1`, decided without computing anything | A sample mean is not an exact sequence |
| Non-integer counts | `non_integer_counts` | Exact methods need integers |
| Instance-dependent counts | probe first; `instance_dependent_counts` with the first differing count | 6 dataset series |
| Python-version-dependent counts | declared flag → `python_version_dependent`; found shape still recorded | RL-069; exact equality across versions is not guaranteed |
| Cost not parseable without `expect` | `cost_not_parseable` with the grammar reason; `expect` with a minimal polynomial resolves it | Decimal bases and factorials [test] |
| Claim component invisible on the grid | `cost_outside_grid_family` naming the component and the grid to use | n log n on a consecutive grid, 2ⁿ on a doubling grid [test] |
| Conjugate roots | same minimal polynomial *and* same root required | (3−2√2)ⁿ claimed for an edit-distance count → MISMATCH base [test] |
| Subdominant solution of a polynomial-coefficient recurrence | θ guard → `asymptotics_not_determined` | tested by patching the numeric slope [test] |
| Timing measures, missing block | SKIPPED, nothing executed | [test] |
| Diagnostic crash | `internal_error`, V2 unaffected | [test] |

---

## 6. My failures, bugs and near-misses (all fixed before the final runs)

1. **Gating bug (would have changed CI runtime).** I gated the diagnostic on `verbose or rec is not None` inside
   `run_v2`, but `validate_entry` always passes a `rec` dict. So every plain `--scaling` run would have computed
   all shape grids (about +40 s for Strassen alone; no verdict change, since exceptions are caught).
   `test_not_computed_without_verbose_or_record` failed and exposed it. The gate moved to `validate_entry`.
2. **Wrong test expectation.** I expected `needed = 16` for n⁴ + 1 on 12 terms; the code gave 14, which is correct
   because 8 training terms show order 4 at most. The test now asserts 14, documents the lower bound, and checks
   that 16 terms give MATCH. The message now says "at least".
3. **`expect` root selection too strict.** The approx had to lie within 1e-6 of the root, so 1.4656 for
   1.46557… failed. The rule is now: nearest real root, unambiguous (less than half the distance to the next root).
4. **`powq(x, 1)` degraded a root object to a float**, so an `expect` minpoly base became "inexact". Exponent 1 now
   returns the constant unchanged.
5. **Block inserter.** The first `--apply` stopped at the first entry because I had not handled one-line
   `"scaling": { ... }` objects; nothing was written. My first `--check` then reported 31 false differences (a wrong
   line-count formula). It was replaced by a difflib opcode check.
6. **Shell here-documents collapsed escapes twice** (a `\n` in an f-string, a backslash continuation in
   `validate.py`). Both were redone with the Edit tool. No result was affected; the same tooling issue was noted in
   round 2026-10-06d.
7. **Hand-written labels.** My first fit-limits table had hand-written "shape diagnostic" labels, one of them wrong
   (I wrote "no recurrence" for an n^1.1 claim; `n**1.1` parses exactly, 2^1.1 has minimal polynomial x¹⁰ − 2¹¹,
   and the result is MISMATCH). The column is now computed by the script.
8. A smoke-test lambda of mine was malformed (no effect on any file).

---

## 7. Drafted texts for the maintainer (DRAFT)

**README.md, footnote to the V2 row (DRAFT):**

> For exact counts, an informational *shape diagnostic* also runs (with `-v` or `--record`). It guesses an exact
> recurrence for the counts, checks it on held-out terms, and compares the growth it implies (exponential base as an
> algebraic number, polynomial power, log power) with the claimed cost, with no tolerance. It reports MATCH,
> MISMATCH, UNDETERMINED (with the reason) or SKIPPED and does not change V2 verdicts. See
> [notes/v2-shape-diagnostic.md](notes/v2-shape-diagnostic.md).

**CONTRIBUTING.md paragraph, after the `harness.scaling` paragraph (DRAFT):**

> For `"measure": "reported"` claims you may add an optional `shape` block to `harness.scaling`, e.g.
> `"shape": {"sequence": "doubling", "n_range": [2, 16384]}`. Use `doubling` (n = 2^k) for costs with a log factor
> or an irrational power of n, and `consecutive` otherwise. Start the range where the count is regular, for example
> above a schoolbook cutoff. The validator then identifies the exact growth of your counts and compares it with
> `cost` (`python tools/validate.py <entry> --scaling -v`). The result is informational and does not affect V2. If
> your count includes comparisons inside CPython built-ins, set `"python_version_dependent": true` (RL-069). If
> `cost` cannot be parsed exactly (e.g. a decimal base), give `expect`. Details:
> [notes/v2-shape-diagnostic.md](notes/v2-shape-diagnostic.md).

**RESEARCH_LOG entry (DRAFT, to number):**

> **RL-0xx · DECISION and VERIFIED · Exact shape diagnostic for exact-count V2 (informational)**
> **Decision** (by the owner; follows RL-082): exact counts get an additional, informational
> check. A recurrence guessed from the counts on a regular grid (overdetermined, one-dimensional solution space,
> held-out terms reproduced) gives the growth exactly, and it is compared with the claimed cost. The check never
> changes a V2 verdict. Entries declare it with an optional `harness.scaling.shape` block. Every run ends in MATCH,
> MISMATCH, UNDETERMINED or SKIPPED with a machine-readable reason (20 reasons; notes/v2-shape-diagnostic.md).
> Code: `methods/shape.py`, wired into `tools/validate.py` (printed with `-v`, a `shape` field per V2 measurement
> with `--record`, `--no-shape` to skip); schema extended.
> **Applied:** 46 blocks on 23 existing entries. Over the 59 exact-count series: 40 MATCH, 0 MISMATCH, 19
> UNDETERMINED (6 instance-dependent counts; 10 randomised, 2 matching harnesses defined only on n = 4k² + k and 1
> MST enumeration with too few terms, all without a block). Examples: Strassen root 7 → n^log₂7 (n = 16..512),
> Karatsuba root 3 (n = 32..4096), NTT, sparse table and patience sorting (x−2)² → n log n, edit-distance-type
> θ = −1/2 recovered exactly in the unit tests.
> **Unchanged verdicts:** all 59 exact-count series equal ledger 20261006T143136Z in verdict and value; 23/23
> modified entries pass `--scaling -v`. Unit tests: 266 OK (42 new).
> **Side findings:** KMP's count is 4n − 6 for even and 4n − 7 for odd n ≥ 6 (RL-057 quoted 4n − 6); the RMQ
> sparse-table count includes comparisons inside two-argument `min()`.
> Provenance: agent report; experiments `2026-10-06f_shape_{survey,blocks,fit_limits,closed_forms}.py`;
> research/2026-10-06f_shape_diagnostic.md.

---

## 8. Reproduction

From the repository root, with `PYTHONIOENCODING=utf-8` and `.venv/Scripts/python.exe`:

```
python experiments/2026-10-06f_shape_survey.py [--json out.json]      # the table of section 4 (~3 min; Strassen n = 512)
python experiments/2026-10-06f_shape_blocks.py --check                 # the 46 blocks are insertion-only vs git HEAD
python experiments/2026-10-06f_shape_fit_limits.py                     # the "why refine" table (< 1 s)
python experiments/2026-10-06f_shape_closed_forms.py                   # KMP 4n-6 / 4n-7 and naive (n-m+1)m (< 1 s)
python tools/validate.py --scaling -v pairs/<entry>                    # per-entry shape lines
python -m unittest discover -s tests                                   # 266 tests on the final state
CPAIRS_FULL_REGRESSION=1 python -m unittest tests.test_shape_validator # adds randomised series and Strassen
```

Two console checks in the decision log were one-off inline scripts. Their outputs: "all V2 costs: 97/108 parse;
exact-count costs: 58/59 parse", and the dominance comparison "old `fails` / new `certified`" for (x+1)(x−1)²,
(x+1)(x−1)³ and the floor(n/2) case. Both follow from `methods.shape.parse_cost` over the ledger's cost strings
and from `methods.shape._dominance` vs `methods.recurrences.growth_from_charpoly`.

---

## 9. Files created or changed

Created:
- `methods/shape.py` (engine)
- `tests/test_shape.py` (30 tests), `tests/test_shape_validator.py` (12 tests)
- `notes/v2-shape-diagnostic.md` (for readers)
- `research/2026-10-06f_shape_diagnostic.md` (this report)
- `experiments/2026-10-06f_shape_survey.py`, `experiments/2026-10-06f_shape_blocks.py`,
  `experiments/2026-10-06f_shape_fit_limits.py`, `experiments/2026-10-06f_shape_closed_forms.py`

Changed:
- `tools/validate.py` (+116/−2), `schema/entry.schema.json` (+111)
- `entry.json` of 23 entries, adding a `shape` block to `harness.scaling` only (46 blocks):
  all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall, bernstein-vazirani-classical-vs-quantum,
  closest-pair-brute-vs-divide-conquer, deutsch-jozsa-classical-vs-quantum, element-distinctness-pairs-vs-sorting,
  global-min-cut-brute-vs-stoer-wagner, integer-multiplication-schoolbook-vs-karatsuba,
  inversion-counting-quadratic-vs-merge, longest-increasing-subsequence, matrix-multiplication-naive-vs-strassen,
  minimum-finding-classical-vs-quantum, minimum-spanning-tree-brute-vs-kruskal,
  nand-tree-evaluation-deterministic-vs-randomized, optimal-bst-recursion-vs-dp-vs-knuth,
  polynomial-multiplication-naive-vs-ntt, range-minimum-queries-naive-vs-sparse-table,
  regex-matching-backtracking-vs-thompson, sorting-insertion-vs-merge, spanning-tree-count-enumeration-vs-kirchhoff,
  string-matching-naive-vs-kmp, subset-sum-zeta-transform-naive-vs-yates, two-sat-brute-force-vs-scc,
  xor-convolution-naive-vs-walsh-hadamard

Not touched: RESEARCH_LOG.md (its working-tree change is not mine), README.md, CONTRIBUTING.md, index.json,
tools/build_index.py, lib/, implementations and harnesses, `search/`, and the entries created in this round.

---


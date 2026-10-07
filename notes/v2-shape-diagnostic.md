# The V2 shape diagnostic: exact growth shapes from exact counts

**Not an entry.** A guide for readers and contributors, written 2026-10-06 (round 2026-10-06f) by a delegated research
agent (Claude). Code: [methods/shape.py](../methods/shape.py), wired into [tools/validate.py](../tools/validate.py).
Evidence and design log: [research/2026-10-06f_shape_diagnostic.md](../research/2026-10-06f_shape_diagnostic.md).

**Status: informational.** The diagnostic adds information to the validator's output and to the recorded runs.
It does not change which entries pass or fail V2, and no level depends on it.

## In one paragraph

V2 checks a claimed cost by fitting a straight line through log(measured) against log(claimed cost) at a few sizes n
and accepting a slope of 1 ± a tolerance. For claims checked with **exact operation counts** (`measure: "reported"`)
we can do more: guess an exact recurrence that the counts satisfy, check it on terms it was not fitted to, and read
the growth off the recurrence **exactly**, including the exponential base as an algebraic number, the polynomial
exponent, and the power of log n. The diagnostic compares that shape with the claimed cost and reports one of four
outcomes (MATCH, MISMATCH, UNDETERMINED, SKIPPED) with a machine-readable reason.

## Why refine V2

The slope fit has four limits. The numbers below are computed with **perfect, noise-free data** on the entries'
own grids ([experiments/2026-10-06f_shape_fit_limits.py](../experiments/2026-10-06f_shape_fit_limits.py)), so they
are limits of the fit itself, not of measurement noise.

| Limit | Example from this dataset | Fit slope α (tolerance) | Fit accepts? | Shape diagnostic on an exact count of the true shape |
|---|---|---|---|---|
| Confirms only approximately | Strassen counts grow as n^log₂7 (exactly 7^k·16³ on n = 16·2^k); claim n^2.8 instead | 1.0026 (0.02) | yes | MISMATCH (polynomial_factor) |
| Cannot see constants in the base | edit distance grows like (3+2√2)ⁿ/√n, base 5.8284…; claim 5.8ⁿ/√n | 1.0029 (0.03) | yes | MISMATCH (base), with the claim given exactly |
| Cannot see polynomial corrections | the same count, claim (3+2√2)ⁿ without the 1/√n, on the entry's V2 grid n = 5..9 | 0.9585 (0.25) | yes | MISMATCH (polynomial_factor) |
| Rejects only declared rivals | Fibonacci's naive recursion is Θ(φⁿ); claim 1.7ⁿ | 0.9069 (0.25) | yes | MISMATCH (base) |
| Log factors | the NTT count is n(3 log₂n + 5) for n a power of two, n ≥ 2; claim n, on the entry's V2 grid | 1.1107 (0.25) | yes | MISMATCH (log_power) |

The NTT row is rejected at the entry's actual tolerance of 0.03; the V2 fit then says only "the slope is off",
not what is wrong. Earlier rounds measured the log-factor limit for the whole dataset: none of the 69 timing fits
with a computable diagnostic resolved a log factor (RL-048, which gives the number as 77; that figure also counts 8
exact-count fits), and with perfect data none of the 44 timing grids could have done so at ±0.25 (RL-082).

## What changes, and what does not

- **Unchanged:** every V2 verdict, every existing line of validator output, and every existing field of the ledger
  records. Entries without a shape block behave exactly as before.
- **New:** an optional `shape` block inside `harness.scaling`. When the validator runs with `-v` or `--record`, each
  V2 measurement gets a shape result: one extra output line with `-v`, and a `shape` field in the ledger record.
  `--no-shape` turns it off.
- The diagnostic runs after all V2 measurements of an entry, so it cannot influence them. It never adds an error.
  A crash inside it is recorded as `internal_error`, and the V2 verdict stands.

## How it works, in plain terms

A cost is described by three components: **C · bⁿ · n^p · (log n)^q** (exponential base b, polynomial power p, log
power q; the constant C is ignored).

1. **Counts on a regular grid.** The validator computes the exact count at every n of the grid declared in the shape
   block. It reuses the V2 values where n coincides and computes the others with the same seeds.
2. **Guess a recurrence.** First a recurrence with constant coefficients (Berlekamp–Massey), else one with polynomial
   coefficients (holonomic guessing), all in exact rational arithmetic.
3. **Accept the guess only if it is solid.** It must be overdetermined (more equations than unknowns, by a margin),
   its solution space must be one-dimensional (only one recurrence of that size fits), and it must reproduce
   held-out terms that were not used to find it.
4. **Read off the shape.** The dominant root of the recurrence's characteristic polynomial, with its exact minimal
   polynomial and multiplicity, gives the growth. For polynomial coefficients, the exponent comes from an exact
   formula (Birkhoff–Trjitzinsky).
5. **Compare with the claim.** The claimed cost is parsed exactly: `phi` becomes (1+√5)/2 with minimal polynomial
   x²−x−1, and `n**log2(7)` becomes the root 7 on a doubling grid. The diagnostic compares minimal polynomials and
   exponents for **equality**. There is no tolerance.

What a grid can see:

| Grid | n values | Recurrence variable | It identifies | It cannot see |
|---|---|---|---|---|
| `consecutive` | lo, lo+step, … | t = n/step | base b (as the root b^step) and power p | log factors: a count with a (log n)^q factor satisfies no such recurrence |
| `doubling` | lo, 2lo, 4lo, … (powers of two) | k = log₂ n | power p (root 2^p) and log power q (multiplicity − 1) | exponential factors |

Examples: `n*log2(n)` on a doubling grid predicts the root 2 with multiplicity 2, i.e. n¹(log n)¹. `n**log2(7)` on
a doubling grid predicts the root 7, i.e. n^log₂7. `2**n * n` on a consecutive grid predicts the root 2 with
multiplicity 2, i.e. 2ⁿ·n¹. `((3+2*sqrt(2))**n)/sqrt(n)` on a consecutive grid predicts the root of x²−6x+1 and the
exponent −1/2.

## Declaring the check

```json
"scaling": {
  "cost": "n*(3*log2(n) + 5)", "n_values": [512, 1024, 2048, 4096, 8192, 16384],
  "measure": "reported", "tolerance": 0.03,
  "shape": {"sequence": "doubling", "n_range": [2, 16384]}
}
```

| Field | Meaning |
|---|---|
| `sequence` | `consecutive` or `doubling` (required) |
| `n_range` | `[lo, hi]`, inclusive (required). At most 64 grid points. Doubling grids need powers of two |
| `step` | consecutive only: spacing of n (must divide lo) |
| `max_order`, `max_degree` | search limits (defaults 6 and 4) |
| `holdout` | held-out terms (defaults 4 for constant coefficients, 3 for polynomial coefficients; never below 2) |
| `python_version_dependent` | `true` if the count includes work inside CPython built-ins (RL-069) |
| `expect` | the claimed shape, given explicitly when `cost` cannot be parsed exactly: `{"base": "phi" or {"minpoly": [1, -1, 0, -1], "approx": 1.4656}, "polynomial_factor": "-1/2", "log_power": 1}` |
| `note` | free text, e.g. why the grid starts where it does |

**Choosing the grid.** Use doubling for costs with a log factor or an irrational power of n (n log n, n^log₂3), and
consecutive for everything else. Start where the count becomes regular: Karatsuba and Strassen switch to schoolbook
multiplication below 32 digits and 16 rows, so their grids start there. A recurrence of order L needs at least
2L + 2 + holdout terms.

## Outcome categories and reasons

Every run ends in **exactly one** category with **one** reason.

| Category | Reason | When |
|---|---|---|
| MATCH | `exact_shape_agrees` | the dominant root (same minimal polynomial *and* the same root of it) and the exponent equal the claim |
| MISMATCH | `differs` | a solid recurrence was found and at least one visible component differs; `differs` lists `base`, `polynomial_factor` and/or `log_power`, and the record states found vs claimed |
| UNDETERMINED | `invalid_shape_block` | the block is inconsistent (e.g. a doubling grid not on powers of two, more than 64 points, a bad `expect`) |
| | `randomised_counts` | `samples > 1`: V2 averages a random count; a sample mean is not an exact sequence |
| | `count_failed` | the harness or implementation raised an exception at some n of the grid |
| | `instance_dependent_counts` | re-drawing the instance (and the internal randomness) at a few small n changed the count |
| | `non_integer_counts` | a reported count is not an integer |
| | `python_version_dependent` | declared in the block (RL-069); what was found is still recorded |
| | `too_few_terms` | a candidate recurrence exists, but there are not enough terms to overdetermine and check it (the record says how many are needed at least) |
| | `holdout_not_reproduced` | a recurrence fitted the training terms but failed a held-out term (often a change of regime, e.g. a cutoff) |
| | `solution_space_not_one_dimensional` | several independent recurrences fit, so none is singled out |
| | `no_recurrence_within_limits` | no recurrence up to `max_order`/`max_degree` fits |
| | `factorial_type_growth` | the recurrence implies super-exponential growth (n!-like); the bⁿ n^p (log n)^q shape does not apply |
| | `dominance_not_certified` | no exact certificate that the chosen root dominates all other roots (e.g. 2ⁿ and (−2)ⁿ of equal weight) |
| | `asymptotics_not_determined` | the recurrence does not fix the exponent: a repeated root with polynomial coefficients, or the counts follow a smaller solution |
| | `cost_not_parseable` | the cost is outside the exact grammar (factorials, eⁿ, decimal bases such as `1.4655712319**n`) and no `expect` is given |
| | `cost_outside_grid_family` | the claim has a component this grid cannot see (a log factor on a consecutive grid, an exponential on a doubling grid) |
| | `internal_error` | the diagnostic itself failed; the V2 verdict is unaffected |
| SKIPPED | `timing_measure` | wall-clock timings are not exact counts |
| | `no_shape_block` | the claim declares no shape block |

When several reasons apply, the earliest in this order is reported: block, randomised, count failure,
instance dependence, non-integer counts, declared version dependence, identification of the recurrence, the claim.
Problems with the data come before problems with the claim, because a claim cannot be compared with a shape that
was never identified. Whatever was found is recorded in every case.

## Edge cases, and why they are handled this way

- **Lower-order terms and parity effects.** Exact counts carry terms such as −n or (−1)ⁿ (for n ≥ 6, KMP with
  m = n//2 counts 4n − 6 for even n and 4n − 7 for odd n). A root with the same modulus as the dominant root but a *lower*
  multiplicity does not change the growth, and the dominance certificate accepts it exactly (cyclotomic test). Equal
  multiplicity (2ⁿ + (−2)ⁿ) is not accepted.
- **Small-n irregularities and cutoffs.** A count that changes regime (a schoolbook cutoff, a degenerate pattern for
  tiny n) gives either a longer recurrence with a harmless root 0, or `holdout_not_reproduced`. The remedy is to start
  the grid at the regular regime, and the block's `note` says why.
- **Conjugate roots.** 3 − 2√2 and 3 + 2√2 share the minimal polynomial x²−6x+1. The comparison also checks that it
  is the same root.
- **Decimal constants.** `1.4655712319**n` is an approximation of the root of x³−x²−1. The diagnostic refuses to
  treat it as exact (`cost_not_parseable`) rather than report a misleading MISMATCH; `expect` can state the exact
  base.
- **Randomised algorithms.** With `samples > 1` the V2 value is a sample mean, so the diagnostic does not try. With
  `samples = 1` and internal randomness, the instance probe re-seeds both the instance and `random`.
- **Instance-dependent counts.** Comparison counts of merge sort, Timsort or random queries depend on the drawn input.
  The probe catches this at small n before the full grid is computed. A block on such a series is still useful: the
  record then says *why* the diagnostic cannot decide.
- **Python-version dependence.** RL-069 found that counts including comparisons inside CPython built-ins can differ
  between Python versions. Because the diagnostic rests on exact equalities, such a count can at best give a
  version-specific answer, so it is UNDETERMINED by declaration.
- **Polynomial-coefficient recurrences.** Their exponent formula needs a simple dominant root. As a guard against
  counts that follow a smaller solution, the exact exponent must agree with a numeric slope within 0.15. The guard
  can only turn a result into UNDETERMINED, never into a MATCH.
- **Numeric fallbacks are never certificates.** If the exact dominance test fails, a floating-point root check is
  recorded for information, but the result is `dominance_not_certified`.

## What a MATCH does and does not prove

A MATCH is **strong evidence, not a proof.** It means: on the declared grid, the exact counts satisfy a
recurrence that was overdetermined, unique at its size, and confirmed on held-out terms, and that recurrence implies
exactly the claimed base, power and log power. It does **not** prove that the recurrence continues to hold for all
n (that needs an argument from the program text or a proof), that the count measures the right operations (a
partial count, such as the NTT's multiplications only, RL-068, can match its own formula and still miss work), or
anything about worst-case inputs the harness does not generate. A MISMATCH is a precise statement about *these
counts*: it can come from a wrong claim, an incomplete count, or a grid that starts before the regular regime, and it
must be investigated. UNDETERMINED is never evidence for or against the claim.

## Where the results appear

Validator output with `-v`, one line per V2 measurement after the V2 lines of the entry:

```
      shape number-theoretic transform (Cooley-Tukey over Z_p): [doubling n=2..16384, 14 terms] MATCH  n^1, (log n)^1  (C-finite order 2, ...)
      shape merge sort: [doubling n=2..4096, 12 terms] UNDETERMINED (instance_dependent_counts): n=4: 4 (V2 seed) vs 5 (probe seed 1)
      shape fast doubling (matrix power): SKIPPED (timing_measure)
```

In a recorded run (`--record`), each V2 measurement gains a `shape` object: `category`, `reason`, `detail`,
`sequence`, `n_values`, `values` (the exact counts), `found` and `claimed` (base, polynomial_factor, log_power),
`differs` (MISMATCH only), `found_recurrence` (kind, order, the recurrence, characteristic polynomial and factors,
minimal polynomial of the root, multiplicity, dominance certificate, terms used and checked), `instance_probe`,
`limits`, `search` (what was tried) and `seconds`. The run metadata gains `shape_diagnostic` (version and default
limits). Older ledger files have no `shape` field; readers should use `measurement.get("shape")`.

## Current results (round 2026-10-06f)

Of the 59 exact-count V2 series in the last recorded run, 46 now declare a shape block: **40 MATCH, 0 MISMATCH and
6 UNDETERMINED** (instance-dependent counts). The other 13 have no block: 10 are randomised (`samples > 1`), 2
(bipartite matching) use a harness defined only for n = 4k² + k, which is neither grid kind, and 1 (MST enumeration)
grows too fast for enough terms and has a factorial-type cost. Details:
[research/2026-10-06f_shape_diagnostic.md](../research/2026-10-06f_shape_diagnostic.md).

## Limitations of the current implementation

- Only two grid kinds exist: consecutive (with a step) and doubling with ratio 2. Harnesses defined only on other
  size families (bipartite matching: n = 4k² + k) cannot declare a block.
- The exact cost grammar covers bases that are rationals, quadratic surds a + b√d and radicals c^(1/v) (v ≤ 12),
  powers of n that are rational or rational + log₂ of such a constant, and integer or rational log powers. Factorials,
  eⁿ, log log n and products of surds with different radicands need `expect` or are outside the diagnostic.
- Minimal polynomials are computed by Kronecker factorisation, which is exact but slow above degree about 8.
- The instance probe checks a few small n only. A count that is fixed at small n but varies at larger n passes the
  probe and then usually ends as `no_recurrence_within_limits` or `holdout_not_reproduced`.

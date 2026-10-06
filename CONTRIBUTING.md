# Contributing

Thanks for helping. The dataset is useful only if every claim in it is honest, so most of this page
is about verification.

## Workflow

1. Create `staging/<id>/` (cited only, V0) or `pairs/<id>/` (implemented, V1+). The `<id>` is a lowercase slug
   and must equal the `id` field.
2. Write `entry.json` following [schema/entry.schema.json](schema/entry.schema.json). A README.md is generated
   from it by `tools/build_index.py`. You can write your own README.md instead, and it will be left alone.
3. For V1+, add `harness.py` and `implementations/` (see below).
4. Run:
   ```bash
   python tools/validate.py <your entry folder> --scaling -v
   python tools/check_sources.py <your entry folder>
   python tools/build_index.py
   ```
5. Open a PR. CI re-runs the validator, the scaling checks, the unit tests and the index freshness check.

Reviewers check three things. Is it a real pair (START_HERE section 1)? Is the tag correct? Is the level honest?

## Harness and implementations (V1+)

`harness.py` must define:

- `generate(n, rng)`: returns one instance of size n, using only the given `random.Random` instance.
- Optional `check(instance, output)`: an oracle **independent of the implementations under test**. It
  returns True/False, or None if it cannot judge that instance.
- Optional `equal(a, b)`: output comparison (default `==`).
- Optional `generate_scaling(n, rng)`: worst-case instances for V2 timing, e.g. primes for trial division.

Each algorithm's `implementation` is `relative/path.py:function`. The function takes one instance and returns
the answer. It **must not mutate its input**; the validator checks this. Keep implementations
self-contained and readable, because they are reference code as much as test subjects.

For query-model entries (T9), make the implementation return `(answer, queries)` and add `reported_cost(output)` and
`equal(a, b)` to the harness. Then set `"measure": "reported"` (plus `"samples"` for randomized algorithms) in
`harness.scaling`. Shared simulation code lives in `lib/` (e.g. `lib/qsim.py`, a small state-vector simulator).

Per algorithm, `harness.v1_max_n` caps the sizes a slow algorithm is run on. `harness.scaling` declares the
claimed cost as an expression in `n` (`"n**2"`, `"phi**n"`, `"n * factorial(n - 2)"`) together with n values
spanning at least a factor of 8 in cost. Choose n values so that the runtimes land roughly between 0.1 ms and 300 ms.

## Research log (required)

This is research, so every change to what the dataset claims leaves a trace. Add a dated entry to
[RESEARCH_LOG.md](RESEARCH_LOG.md) whenever you:

- add an entry or raise or lower a level (VERIFIED / INCONCLUSIVE);
- find that a claim, tag, citation or implementation was wrong (REFUTED / CORRECTED, recording the old state);
- change methodology (DECISION);
- run a search that finds nothing (NULL, with the exact scope searched);
- get close but not all the way (NEAR-MISS, with the numbers), or have an untested hypothesis worth keeping (IDEA).

Keep every script that produced or attempted a result, failed ones included, and say in its docstring what
happened. Scripts that manufacture candidate pairs belong in `generators/` (see generators/README.md).

Give exact numbers and their provenance. For a run that changes a claim, attach a recorded run
(`python tools/validate.py <entries> --scaling --record`) and commit the file it writes in `ledger/runs/`. Put any
ad-hoc check you cite in `experiments/` as a deterministic script. Never delete or rewrite old log entries;
supersede them with new ones.

## Long runs and compiled code

- **Long runs go in the background, with a time budget.** Validation with `--scaling`, recorded runs, searches and long
  experiments are started detached, with an explicit budget (e.g. `--max-seconds`), and signal completion. Nobody sits
  watching them, and the maintainer stays available while they run. Timing-sensitive runs (V2, `--record`) must not
  overlap with CPU-heavy jobs.
- **Compiled kernels (C/C++) are allowed only if they build in seconds.** They must come as small single-file programs
  without heavy dependencies and run as separate processes; no shared memory with Python. They must also be treated
  as untrusted for memory safety:
  - bounds-checked array access in test builds, compiled with all warnings as errors;
  - differential tests against the Python reference implementation (identical seeds give identical results on small runs);
  - every result a compiled kernel produces is re-verified by the exact Python verifier before it is saved, logged or
    claimed, so a memory error can at worst waste time, never create a false result.

## Honesty rules

- Do not inflate levels. V2 means every implemented algorithm's scaling was measured and passed. If one
  cannot be measured, the entry stays at V1 and the reason goes in `verification.method`.
- Pseudo-polynomial is not polynomial. State what n is and how input size is measured.
- T7 (deliberately bloated) entries go in `synthetic/` and never count toward the headline.
- A V1 check of a randomized algorithm is itself probabilistic. Say so in `caveats`.
- Prefer removing an unverifiable detail (page numbers, attributions, "no better algorithm is known") over keeping it.
- No secrets, credentials or private material in any commit.

## Tagging decisions (2026-10)

1. **Exp → better exp gets its own tag, T8** (super-poly → faster super-poly). If polynomial time is open for the
   problem, T6 stays primary and T8 goes in `secondary_tags` (TSP, 3-SAT, permanent, graph isomorphism,
   factoring). T8 counts toward validated pairs.
2. **Constant-factor / fixed-size improvements are out of scope as entries**, because section 1 requires an asymptotic
   difference. AlphaDev-style results are kept as methodology notes in `notes/`, since they matter for the
   search pipeline. A fixed-size scheme that yields an asymptotic bound when applied recursively (e.g. an
   AlphaTensor rank) is in scope through that bound.
3. **Proven quantum separations in query / oracle / black-box models get tag T9.** The validator requires a quantum
   algorithm *and* a classical lower bound in `lower_bounds`. For T9, the cost that matters is queries, not
   simulation time, so V2 uses `"measure": "reported"` with the harness's `reported_cost(output)`. T9 shows
   separations *relative to an oracle*. It does not prove BQP ≠ BPP.

## License of contributions

The project is free for non-commercial use and licensed commercially to fund the research (see
[COMMERCIAL.md](COMMERCIAL.md)). By submitting a contribution, you agree that:

- it is your own work, or you have the right to submit it;
- it is licensed to everyone under the repository's licenses (CC BY-NC 4.0 for data, PolyForm Noncommercial 1.0.0
  for code); and
- you grant the maintainer a perpetual, worldwide, non-exclusive, royalty-free right to also license it under other
  terms, including commercial licenses.

You keep your copyright. Add `Signed-off-by: Your Name <email>` to your commits to confirm these terms.

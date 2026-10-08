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

For `"measure": "reported"` claims you may add an optional `shape` block to `harness.scaling`, e.g.
`"shape": {"sequence": "doubling", "n_range": [2, 16384]}`. Use `doubling` (n = 2^k) for costs with a log factor or
an irrational power of n, and `consecutive` otherwise. Start the range where the count is regular, for example above
a schoolbook cutoff. The validator then identifies the exact growth of the counts and compares it with `cost`
(`python tools/validate.py <entry> --scaling -v`). The result is informational and does not affect V2. If the count
includes comparisons inside CPython built-ins, say so in the entry (RL-069), and set `"python_version_dependent": true`
when the count is not known to be identical across Python versions. If `cost` cannot be parsed exactly (e.g. a
decimal base), give `expect`. Details: [notes/v2-shape-diagnostic.md](notes/v2-shape-diagnostic.md).

## Research log (required)

This is research, so every change to what the dataset claims leaves a trace. Add a dated entry to
[RESEARCH_LOG.md](RESEARCH_LOG.md) whenever you:

- add an entry or raise or lower a level (VERIFIED / INCONCLUSIVE);
- find that a claim, tag, citation or implementation was wrong (REFUTED / CORRECTED, recording the old state);
- change methodology (DECISION);
- run a search that finds nothing (NULL, with the exact scope searched);
- get close but not all the way (NEAR-MISS, with the numbers).

Keep every script that produced or attempted a result, failed ones included, and say in its docstring what
happened. Scripts that manufacture candidate pairs belong in `generators/` (see generators/README.md).

Give exact numbers and their provenance. For a run that changes a claim, attach a recorded run
(`python tools/validate.py <entries> --scaling --record`) and commit the file it writes in `ledger/runs/`. Put any
ad-hoc check you cite in `experiments/` as a deterministic script. Never delete or rewrite old log entries;
supersede them with new ones.

## Long runs and compiled code

- **Long runs go in the background, with a time budget.** Validation with `--scaling`, recorded runs, searches and long
  experiments are started detached, with an explicit budget (e.g. `--max-seconds`), and signal completion. Nobody sits
  watching them, so whoever started them, a person or an AI assistant, stays free for other work. Timing-sensitive runs (V2, `--record`) must not
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

## Provenance labels (whose result it is)

Every entry, and every note under `theorems/`, says whose result it is, in the optional `provenance` field
(absent means `literature`):

- **`literature`**: the result is in the cited literature; this project re-proved or re-checked it (staging
  entries, at V0, are cited only). No label.
- **`own-extension`**: a generalization or sharpening of a cited base result that is not itself in the
  literature. It must name the base(s) in `bases`. Shown with the orange label **🟠 Own extension**.
- **`own`**: no prior literature was found after a documented search. Shown with the orange label **🟠 Own result**.
- **`undetermined`**: probably our own result, but a source that might already contain it could not be read.
  Shown as **🟡⏳ Undetermined (may be our own result)**: the yellow dot means probably our own finding, the
  hourglass means a source could not be read. It needs `pending: true`, a `pending_note` and a non-empty
  `missing_sources` list. Its text says what it proves beyond the sources that were read, that it may be our own
  result, and that this could not be checked.
- **`pending: true`**: a source that could not be read (or identified) might already cover the result; `pending_note` names it.
  Shown as **⏳ Pending** (on an `undetermined` item the hourglass is part of its label). A pending result is
  published as `literature` when the result itself is in the literature and only a detail could not be verified,
  or as `undetermined` when it may be our own result but a source that might contain it could not be read. It is
  never published with an own label (`own`, `own-extension`).
- **`missing_sources`**: the sources that could not be read, listed exactly. Each item has `authors`, `year`,
  `title`, `venue`, a `doi` or a `url` (or both), `status` (why it could not be read, for example "no open-access
  copy found") and `needed_for` (what reading it would decide). Required for `undetermined`; allowed only with
  `pending: true`. The README lists every such source under "Sources we could not read".

The orange labels mark the project's own results so that readers can see at once what is new here; the yellow label
marks a probable own result whose literature check could not be finished. If prior literature turns up later, the
label is corrected in a new RESEARCH_LOG entry; the old entry is not deleted.
Every labelled result ships with a complete proof and a deterministic check (`verify.py` or a test).

## The green check mark (✅ Proved)

An entry or a theorem note gets the green check mark **✅ Proved** only when a reader can check every claim it
makes from the repository alone:

1. **Our own written proof of every claim:** correctness of each algorithm, every stated complexity and exact count
   on its domain, every lower bound, and every factual caveat. The proofs are in the files listed in
   `proof.documents`. External citations are credit (who published first), never a substitute for the proof.
2. **Deterministic checks:** the scripts or tests in `proof.checks` re-run the proofs' computable facts on stated
   ranges with fixed inputs and seeds, and they pass in the recorded run. A check covers its finite range; the
   written proof covers the general statement.
3. **A logged audit:** `proof.audit` names the RESEARCH_LOG entry that records the claim-by-claim audit behind
   the mark.

The validator checks that the listed files exist and that the audit entry is in the log. It cannot check the
mathematics; the audit and the readers do. Staged entries (V0) cannot carry the mark. If a gap is found, the mark
is removed in a new RESEARCH_LOG entry, and the old entry is not deleted. The verification level (V0–V2) is a
separate statement about the measurements; the check mark is about proofs.

## Background versus claims

An entry separates what it **claims** from what it only **cites**:

- **Claims** are statements the entry itself makes about its problem and algorithms: correctness, complexities,
  exact counts on stated domains, lower bounds, separations, factual caveats. Every claim needs a written proof in
  the repository (for example in `PROOFS.md`) and a deterministic check, as the check mark requires.
- **Background** goes in the optional `background` field. It holds statements about the literature or the state of
  research that the entry relies on for context but does not prove: NP-hardness, "no polynomial-time algorithm is
  known", conditional lower bounds, the reason for a T6 tag. Each item names its source, as precisely as possible
  (theorem or section). Background is shown under its own heading in generated READMEs, and the check mark does not
  cover it.

A tag is a classification. When a tag rests on background (for example T6, or a lower bound known from the
literature), the entry says so.

**Machine model.** Proofs about code count operations in a stated model:

- **Elementary operations** cost O(1) each, unless the entry states otherwise. They are allocating, appending
  to and indexing lists, dictionary and set operations (each counted as one operation), and arithmetic and
  comparisons on machine-size integers. One cost-model paragraph in PROOFS.md states this for each entry.
- **Library routines with a non-trivial cost**, such as `sorted`, `list.sort`, `bisect`, `itertools.permutations`,
  `str.find` and arithmetic on big integers, are charged a stated cost as a **machine-model assumption**:
  - the assumption is listed in the entry's `background`, citing exactly what its source supports;
  - every claim that depends on it is worded as conditional on it;
  - an assumption that rests on no published source names, as its `source`, the PROOFS.md section that states it.

  A claim worded that way counts as proved.

O and Θ have their usual asymptotic meaning. A bound in a parameter that can be 0 is written so that it is true
on every infinite family of inputs, for example O(2ⁿ(m+1)), or it carries the hypothesis it needs (m ≥ 1).

## Tagging decisions (2026-10)

1. **Exp → better exp gets its own tag, T8** (super-poly → faster super-poly). If polynomial time is open for the
   problem, T6 stays primary and T8 goes in `secondary_tags` (TSP, 3-SAT, permanent, graph isomorphism,
   factoring). T8 counts toward validated pairs.
2. **Constant-factor / fixed-size improvements are out of scope as entries**, because section 1 requires an asymptotic
   difference. AlphaDev-style results are kept as methodology notes in `notes/`, since they matter for the
   search pipeline. A fixed-size scheme that yields an asymptotic bound when applied recursively (e.g. an
   AlphaTensor rank) is in scope through that bound.
3. **Quantum separations in query / oracle / black-box models get tag T9.** The validator requires a quantum
   algorithm *and* a classical lower-bound record in `lower_bounds`; it checks that the record exists, not that the
   bound is proved (the bound may be cited). For T9, the cost that matters is queries, not
   simulation time, so V2 uses `"measure": "reported"` with the harness's `reported_cost(output)`. T9 records
   separations *relative to an oracle*. It does not prove BQP ≠ BPP.

## License of contributions

Contributions are accepted under the repository's licenses ("inbound = outbound"): code under the Apache License 2.0
(see its section 5), and data and documentation under CC BY 4.0. By submitting a contribution you confirm that it is
your own work, or that you have the right to submit it under these licenses. You may add
`Signed-off-by: Your Name <email>` (Developer Certificate of Origin) to your commits.

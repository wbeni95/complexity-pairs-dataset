# Theorems

This folder holds mathematical results that are **not complexity pairs**: exact statements about algorithms and
objects related to the dataset, each with a complete proof. They are kept apart from `pairs/` and `staging/` because
they make no claim of the form "two algorithms with different asymptotic cost", and the validator does not process
them.

## What every note contains

Each note is a folder `theorems/<id>/` with three files:

| File | Content |
|---|---|
| `README.md` | the precise statement with all definitions, a complete proof, the sources, the provenance label (below) and the exact scope: what the note does **not** claim |
| `meta.json` | machine-readable summary: `id`, `title`, `statement`, `provenance`, `sources`, `verify`; it must validate against [meta.schema.json](meta.schema.json) |
| `verify.py` | a deterministic script (fixed inputs and seeds, Python standard library only) that re-checks every computed fact the proof uses and exits with code 0 only if all checks pass |

The proof is the written argument in the README. `verify.py` is evidence: it checks the concrete numbers a proof
relies on (for example a certificate value) and runs exhaustive or seeded tests of the statement and its lemmas on a
stated finite scope. A computation alone never counts as a proof here.

## Provenance labels

Every note says where the result stands relative to the literature, in `meta.json` (`provenance`) and at the top
of its README.

| `class` | Meaning |
|---|---|
| `literature` | The result is in the literature, and the note re-proves it. The source is credited exactly (section, proposition), and the note says what it adds, if anything (an independent proof, independent verification code, explicit certificates). |
| `own-extension` | Our generalization of a cited base result. The note names the base and states exactly what goes beyond it. |
| `own` | No literature was found after a documented search. The note lists what was checked. This is a statement about that search, not a claim of priority. |

`bases` lists the cited results a label rests on. The flag **`pending: true`** marks a note where a source that could
not be accessed might already cover the result. The class is then provisional, and `pending_note` says which
source is missing and what remains open. A pending note never claims more novelty than its class states.

## Notes

| Note | Provenance | Statement (short) |
|---|---|---|
| [no-integral-form-z-half-schemes](no-integral-form-z-half-schemes/) | literature | AlphaEvolve's ⟨2,4,5;32⟩ and Smirnov's ⟨3,3,6;40⟩ matrix multiplication schemes, both with coefficients in ℤ[1/2], have no equivalent form with integer coefficients. |
| [knuth-window-concave-length-weights](knuth-window-concave-length-weights/) | literature, **pending** | Knuth's restricted root window is exact for the interval recurrence with concave nondecreasing length weights, under the largest and the smallest tie rule, with an explicit trajectory of chosen roots. |

## Running the checks

From the repository root:

```bash
python theorems/no-integral-form-z-half-schemes/verify.py           # downloads two pinned files (or: --cache DIR)
python theorems/knuth-window-concave-length-weights/verify.py       # offline, well under a minute
```

Each script prints one line per check and ends with `ALL CHECKS PASSED` (exit code 0) or a list of the failed
checks (exit code 1).

## License

As for the rest of the repository: the scripts (`verify.py`) are under the [Apache License 2.0](../LICENSE), and
the texts and metadata (`README.md`, `meta.json`, `meta.schema.json`) are under [CC BY 4.0](../LICENSE-DATA).
Corrections and independent re-verification are welcome. Please open an issue.

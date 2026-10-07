# Reproducing the results

Every claim in this repository is meant to be checkable from the repository alone. This page says how to replay
the checks, which results are deterministic, and which are not.

## Environment

- Python 3.12 or 3.14. CI runs both.
- Install the pinned dependencies. `jsonschema` is the only third-party package the repository imports;
  `requirements.txt` also pins its dependencies.

  ```bash
  python -m venv .venv
  . .venv/bin/activate          # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  ```

- Optional: `rustc`, for the tests of the Rust search kernel in `search/`. Those tests are skipped without it.

## Replaying everything

```bash
python tools/replay_proofs.py         # re-run the checks behind every item marked ✅ (deterministic; one PASS/FAIL line per command)
python tools/replay_proofs.py SLUG    # the same for one item
python tools/check_all.py            # unit tests, V1 runs, V2 scaling fits, index freshness
python tools/check_all.py --sources  # also resolve every DOI / arXiv id online (Crossref, DataCite, arXiv)
python tools/check_all.py --record   # also store the run in ledger/runs/
```

## Replaying one item

| Item | Proof | Checks |
|---|---|---|
| A pair in `pairs/` | `pairs/<slug>/PROOFS.md` and the entry text | `python tools/replay_proofs.py <slug>` runs its V1 correctness runs and every check listed in its `proof.checks` field; `python tools/validate.py pairs/<slug> --scaling -v` also re-measures its V2 fits. |
| A theorem note in `theorems/` | `theorems/<id>/README.md` | `python theorems/<id>/verify.py` |
| Exact operation counts | the "exact counts" sections of PROOFS.md | `python experiments/2026-10-07_closed_form_checks.py` and `python experiments/2026-10-07_count_proof_checks.py` |

Every script prints one line per check and ends with a summary. Count checks by the `[PASS]` / `[FAIL]` prefix of
each line, or read the unittest summary.

## What is deterministic

- **V1 correctness runs.** The validator seeds every instance from the entry id and the size.
- **Exact-count V2 measurements** (`"measure": "reported"`): the same counts on every run, with the same Python
  version.
- **Unit tests, theorem-note `verify.py` scripts and the count-check scripts.** They use fixed inputs and seeds.

## What is not deterministic

- **Wall-clock V2 fits** (`"measure": "time"`) depend on the machine and its load. They are measurements, never
  proofs. On a busy machine a timing fit can fail; rerun it on a quiet one.
- **Counts that depend on CPython built-ins**, such as the comparisons made by `sorted`, can differ between Python
  versions. Each recorded run in `ledger/runs/` states the Python version, the platform, the `jsonschema` version
  and the git commit it was made with.
- **`tools/check_sources.py`** contacts external services, which can be unavailable. CI reports their failures
  without blocking.

## Recorded runs

`ledger/runs/*.json` holds the complete output of recorded runs: every V1 result, every V2 measurement (the values
as well as the fits) and the shape diagnostics. To compare your own run with a recorded one, run
`python tools/check_all.py --record` and compare the two files. RESEARCH_LOG.md states, for each recorded run,
whether the exact-count series are identical to the previous one.

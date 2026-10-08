"""Controls for the eight entries added on 2026-10-07: can each harness.check oracle actually fail, and how much
of the V1 battery does it judge?

For every V1 instance (generated exactly as tools/validate.py generates them, seed f"{id}|v1|{n}|{trial}"),
the fastest implementation's output is computed and then
  (a) check(instance, output) must be True or None (None = oracle cannot judge that instance);
  (b) for every judged instance, check(instance, wrong) must be False for a deliberately wrong answer
      built by an entry-specific perturbation (distance + 1, length + 1, negated decision, count +- 1, ...).
It also prints the battery composition where it matters (yes/no answers).
This is the analogue of the control in RESEARCH_LOG RL-008: a checker that cannot fail proves nothing.

Run from the repository root:  python experiments/2026-10-07_oracle_controls.py

Outcome (2026-10-07, deterministic; about 4 s): every oracle accepted every correct output it judged and rejected
every perturbed one: APSP 70 judged, 56/56 rejected (14 instances with nothing finite to perturb); palindromes
108, 108/108; element distinctness 84, 84/84 (47 yes / 37 no); chromatic number 90, 90/90; RMQ 70, 65/65 (5 with
no queries); bipartite matching 111 judged + 3 not judged (a side > 160), 111/111; max flow 66 judged + 12 not
judged (n > 14), 66/66; 3-SAT 84, 84/84 (53 satisfiable / 31 unsatisfiable).

One check line per entry, starting with [PASS] or [FAIL]: (a) and (b) on every instance, and the counts stated in
the outcome above (judged, not judged, rejected, nothing to perturb, and the yes/no split where there is one). The run
ends with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1).
"""
import copy
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FAILED = []


def check_line(ok, *parts):
    """Print one check line with a [PASS] or [FAIL] prefix and remember the failures."""
    print("[PASS]" if ok else "[FAIL]", *parts, flush=True)
    if not ok:
        FAILED.append(" ".join(str(p) for p in parts).strip())
    return ok


def finish_checks():
    """End of the run: ALL CHECKS PASSED (exit code 0), or the failed checks and exit code 1."""
    if FAILED:
        print(f"FAILED: {len(FAILED)} check(s):")
        for label in FAILED:
            print(f"  {label}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


def perturb_apsp(inst, out):
    rows = [list(r) for r in out]
    for i, r in enumerate(rows):
        for j, d in enumerate(r):
            if i != j and d is not None:
                rows[i][j] = d + 1
                return tuple(tuple(r) for r in rows)
    return None                                   # nothing finite off the diagonal to perturb


def perturb_rmq(inst, out):
    return None if not out else (out[0] - 1,) + out[1:]


PERTURB = {
    "all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall": perturb_apsp,
    "longest-palindromic-substring": lambda inst, out: (out[0] + 1, out[1]),
    "element-distinctness-pairs-vs-sorting": lambda inst, out: not out,
    "chromatic-number-subset-dp-vs-inclusion-exclusion": lambda inst, out: out + 1,
    "range-minimum-queries-naive-vs-sparse-table": perturb_rmq,
    "bipartite-matching-kuhn-vs-hopcroft-karp": lambda inst, out: out + 1,
    "max-flow-edmonds-karp-vs-dinic": lambda inst, out: out + 1,
    "3sat-brute-force-vs-schoening": lambda inst, out: not out,
}

# (judged, not judged, wrong answers rejected, nothing to perturb, yes/no split) as stated in the outcome above
EXPECTED = {
    "all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall": (70, 0, 56, 14, {}),
    "longest-palindromic-substring": (108, 0, 108, 0, {}),
    "element-distinctness-pairs-vs-sorting": (84, 0, 84, 0, {True: 47, False: 37}),
    "chromatic-number-subset-dp-vs-inclusion-exclusion": (90, 0, 90, 0, {}),
    "range-minimum-queries-naive-vs-sparse-table": (70, 0, 65, 5, {}),
    "bipartite-matching-kuhn-vs-hopcroft-karp": (111, 3, 111, 0, {}),
    "max-flow-edmonds-karp-vs-dinic": (66, 12, 66, 0, {}),
    "3sat-brute-force-vs-schoening": (84, 0, 84, 0, {True: 53, False: 31}),
}

for entry_id, perturb in PERTURB.items():
    d = ROOT / "pairs" / entry_id
    entry = json.loads((d / "entry.json").read_text(encoding="utf-8"))
    H = load(d / entry["test_harness"]["module"], f"h_{len(entry_id)}_{entry_id[:5]}")
    spec = entry["algorithms"][-1]["implementation"]
    file_part, func = spec.rsplit(":", 1)
    fn = getattr(load(d / file_part, f"impl_{entry_id[:8]}"), func)
    judged = unjudged = rejected = unperturbable = 0
    not_accepted, wrong_accepted = [], []
    answers = Counter()
    for n in entry["test_harness"]["v1_sizes"]:
        for trial in range(entry["test_harness"].get("trials", 3)):
            inst = H.generate(n, random.Random(f"{entry_id}|v1|{n}|{trial}"))
            random.seed(f"controls|{entry_id}|{n}|{trial}")
            out = fn(copy.deepcopy(inst))
            if isinstance(out, bool):
                answers[out] += 1
            verdict = H.check(inst, out)
            if verdict not in (True, None):
                not_accepted.append((n, trial, verdict))
            if verdict is None:
                unjudged += 1
                continue
            judged += 1
            wrong = perturb(inst, out)
            if wrong is None:
                unperturbable += 1
                continue
            if H.check(inst, wrong) is False:
                rejected += 1
            else:
                wrong_accepted.append((n, trial))
    extra = f", answers {dict(answers)}" if answers else ""
    failed = f" | correct output not accepted at (n, trial, verdict) {not_accepted[:3]}; wrong answer not rejected " \
             f"at (n, trial) {wrong_accepted[:3]}" if not_accepted or wrong_accepted else ""
    check_line(not not_accepted and not wrong_accepted
               and (judged, unjudged, rejected, unperturbable, dict(answers)) == EXPECTED[entry_id],
               f"{entry_id}: {judged} judged (all True), {unjudged} not judged; wrong answers rejected {rejected}/"
               f"{judged - unperturbable} ({unperturbable} instances had nothing to perturb){extra}{failed}")

finish_checks()

"""Experiment (research/2026-10-07_search_flipgraph.md, run groups G3c, G3d, G3e): main 4x4x4 runs over GF(2).

Best known rank over GF(2): 47 (Fawzi et al. 2022, AlphaTensor, doi:10.1038/s41586-022-05172-4). Strassen's
scheme applied to 2x2 blocks of 2x2 blocks gives 49 (search.gf2mm.kron_scheme, verified in the tests).

History of this script (kept on purpose): a first version (G3c with 12 + 3 x 150M flips and G3d with 2 x 60M
flips, all without weight cap) was launched and ABORTED by the agent after a few seconds, during stage 1 seed 101,
because the G3b result had just arrived: the weight cap 4 (variant V3) reached rank 49 in 1.6M flips on seed 2,
lower than any uncapped run (52 at best). A second launch of that same old version (an editing mistake: the new
file had not been written yet) was also aborted after a few seconds. Neither produced a result; their partial
logs were overwritten by this version. The plan below was revised to include capped runs.

G3e (weight cap, from the standard algorithm, rank 64): cap 4 with seeds 401..412 and cap 5 with seeds 501..506,
  5,000,000 steps each.
G3d (from Strassen squared, rank 49; it has no shared factor, so the walk starts with plus transitions):
  50,000,000 steps each, slack 3 and 3 plus transitions per escape (see
  experiments/2026-10-07_flipgraph_4x4_strassen2_probe.py for why), plateau 200,000:
  seeds 301, 302 uncapped; seed 303 cap 6; seed 304 cap 8.
G3c (uncapped, from the standard algorithm), two stages (continue from the lowest-rank schemes found):
  stage 1: seeds 101..108, 10,000,000 flips each;
  stage 2: the 2 best stage-1 schemes (lowest rank, ties broken by earlier flip, then seed) are each continued for
           150,000,000 flips (seeds 201, 202).
Base policy (all runs unless stated): P2 of experiments/2026-10-07_flipgraph_4x4_calibration.py (plus transitions,
plateau 1,000,000, slack 1, linear reductions), the best mean in that calibration (52.5 over 2 seeds; not
significant). Safety cap 1,800 s of wall-clock per run (a run cut by it says "stopped by time").
Every best scheme is saved with status "matches best known" / "above best known" / "BELOW best known".

Run from the repository root:  python experiments/2026-10-07_flipgraph_4x4.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm  # noqa: E402
from search.driver import WalkConfig  # noqa: E402
from search.experiment import run_batch  # noqa: E402

POLICY = dict(plateau=1_000_000, escape="plus", slack=1, reduction="linear")
BEST_KNOWN = 47
FMT = (4, 4, 4)
SCRIPT = "experiments/2026-10-07_flipgraph_4x4.py"


def cfg(seed, flips, tag, **over):
    pol = dict(POLICY, **over)
    return WalkConfig(fmt=FMT, seed=seed, max_flips=flips, max_seconds=1800, verify_every=1_000_000,
                      log_every=1_000_000, extra={"tag": tag}, **pol)


# ---- G3e: weight-capped walks from the standard algorithm (cheap; run first)
run_batch("2026-10-07_flipgraph_4x4_G3e_capped", SCRIPT,
          [cfg(s, 5_000_000, "cap4", max_weight=4) for s in range(401, 413)]
          + [cfg(s, 5_000_000, "cap5", max_weight=5) for s in range(501, 507)], best_known=BEST_KNOWN)

# ---- G3d: from Strassen squared
fmt, s49 = gf2mm.kron_scheme((2, 2, 2), gf2mm.strassen_scheme(), (2, 2, 2), gf2mm.strassen_scheme())
assert fmt == FMT and len(s49) == 49 and gf2mm.verify(fmt, s49)
st2 = dict(plateau=200_000, slack=3, plus_per_escape=3)
run_batch("2026-10-07_flipgraph_4x4_G3d_strassen2", SCRIPT,
          [cfg(301, 50_000_000, "st2", **st2), cfg(302, 50_000_000, "st2", **st2),
           cfg(303, 50_000_000, "st2cap6", max_weight=6, **st2), cfg(304, 50_000_000, "st2cap8", max_weight=8, **st2)],
          best_known=BEST_KNOWN, start=s49, start_label="Strassen (x) Strassen, rank 49")

# ---- G3c stage 1: uncapped from the standard algorithm
stage1 = run_batch("2026-10-07_flipgraph_4x4_G3c_stage1", SCRIPT,
                   [cfg(s, 10_000_000, "s1") for s in range(101, 109)], best_known=BEST_KNOWN)
ranked = sorted(stage1, key=lambda r: (r["best_rank"], r["best_reached_at_flip"], r["seed"]))
print("# stage-1 ranking (seed, best rank, at flip):", [(r["seed"], r["best_rank"], r["best_reached_at_flip"])
                                                       for r in ranked])

# ---- G3c stage 2
for k, rec in enumerate(ranked[:2]):
    best_file = [p for p in rec["saved_schemes"] if p.endswith(f"_rank{rec['best_rank']}.json")][0]
    _, start, _ = gf2mm.load_scheme(ROOT / best_file)
    run_batch(f"2026-10-07_flipgraph_4x4_G3c_stage2_from_seed{rec['seed']}", SCRIPT,
              [cfg(201 + k, 150_000_000, "s2")], best_known=BEST_KNOWN, start=start,
              start_label=f"stage-1 best scheme of seed {rec['seed']} (rank {rec['best_rank']}, {best_file})")

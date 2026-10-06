#!/usr/bin/env python3
"""Targeted search (research/2026-10-06d_exotic_formats.md, sections 3 and 5): walks below the best known GF(2) rank
in the formats selected in the report's decision log.

Usage (from the repository root; each invocation is one background job of at most 20 minutes, 4 walks at a time):
  ./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py library   # small verified schemes for block starts
  ./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 245       # (2,4,5): GF(2) record 33, Q record 32
  ./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 336       # (3,3,6): GF(2) record 42, Q record 40
  ./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 256       # (2,5,6): GF(2) record 47
  ./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 445       # (4,4,5): GF(2) record 60
  ./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 256b      # follow-ups with plateau 2 000, slack 1
  ./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 336b

Arms per format:
  std  - the standard algorithm as the start;
  blk  - a block start built here from verified smaller schemes (search/blocks.py); for std and blk, a walk that
         reaches the record is a rediscovery (a pipeline check);
  own60 - (4,4,5) only: our own rank-60 scheme from the calibration as the start (schemes saved only if below 60);
  pub  - the published record scheme as the start (Kauers-Moosbauer flips repository @ e31a0a0f, or AlphaEvolve's
         (2,5,6) scheme reduced mod 2; read from the cache of 2026-10-06d_fmt_records.py / _char0_records.py, never
         copied into the repository); the walk tries to go below the record. Its schemes are saved only if below
         the record (search.campaign.run_arm(save_below=...)).
Every result is re-verified by the exact verifier before it is logged (search/rust_kernel.py).
Logs: search/runs/2026-10-06d_tgt_<fmt>.jsonl; schemes: search/schemes/rust-2026-10-06d/targets/.

RESULT: see the report, section 5 (console copies search/runs/2026-10-06d_tgt_<fmt>.console.txt).
"""
import importlib.util
import io
import os
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import campaign, gf2mm, rust_kernel  # noqa: E402
from search.machine import set_below_normal_priority  # noqa: E402

spec = importlib.util.spec_from_file_location("rec", ROOT / "experiments" / "2026-10-06d_fmt_records.py")
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)
spec2 = importlib.util.spec_from_file_location("c0", ROOT / "experiments" / "2026-10-06d_fmt_char0_records.py")
c0 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(c0)

FULL = os.environ.get("FMT_FULL_REDUCE", "0") == "1"  # chosen from the calibration (report, decision D6)

PLANS = {
    "245": dict(fmt=(2, 4, 5), record=33, km="245-33-mod0.exp", arms=[("std", 8, 60), ("blk", 8, 60), ("pub", 16, 60)]),
    "336": dict(fmt=(3, 3, 6), record=42, km="336-42-mod2.exp", arms=[("std", 8, 180), ("blk", 8, 180), ("pub", 8, 180)]),
    "256": dict(fmt=(2, 5, 6), record=47, ae="2x5x6", arms=[("std", 4, 180), ("blk", 4, 180), ("pub", 8, 180)]),
    # (4,4,5): after the calibration (block starts reached 60 in 2/16 walks), more block-start walks, plus walks from
    # the published 60 and from our own rank-60 scheme of the calibration (report section 4.3, decision D7).
    "445": dict(fmt=(4, 4, 5), record=60, km="445-60-mod2.exp",
                own="search/schemes/rust-2026-10-06d/cal/4x4x5_rank60_blk_off_seed1.json",
                arms=[("blk", 8, 240), ("pub", 4, 240), ("own60", 4, 240)]),
}
# Follow-up after the (2,5,6) diagnostic (experiments/2026-10-06d_fmt_256_probe.py: with plateau 2 000 and slack 1 the
# walks improve at once, with the default 50 000 / 3 they never did): standard starts with that policy (decision D12).
PLANS["256b"] = dict(fmt=(2, 5, 6), record=47, ae="2x5x6", arms=[("std", 4, 300)], plateau=2000, slack=1)
PLANS["336b"] = dict(fmt=(3, 3, 6), record=42, km="336-42-mod2.exp", arms=[("std", 4, 300)], plateau=2000, slack=1)
LIBRARY = [((2, 2, 5), 18), ((2, 3, 5), 25), ((2, 2, 6), 21), ((2, 3, 6), 30)]


def published_start(plan):
    fmt = plan["fmt"]
    if "km" in plan:
        z = zipfile.ZipFile(io.BytesIO(rec.get("KM")))
        name = [x for x in z.namelist() if x.endswith("/solutions/" + plan["km"])][0]
        terms = rec.to_gf2(fmt, rec.parse_exp(z.read(name).decode()), True)
        label = f"published: jakobmoosbauer/flips@e31a0a0f solutions/{plan['km']} (reduced mod 2)"
    else:
        f, url = c0.FILES[plan["ae"]]
        rec.URL[plan["ae"]] = url
        terms = rec.to_gf2(fmt, c0.parse_perminov_json(rec.get(plan["ae"]).decode(), fmt), True)
        label = "published: AlphaEvolve 2x5x6 rank 47 (dronperminov/FastMatrixMultiplication@64f58a5e, reduced mod 2)"
    assert gf2mm.verify(fmt, terms) and gf2mm.verify_explicit(fmt, terms) and len(terms) == plan["record"]
    return terms, label


def run_library():
    set_below_normal_priority()
    save = ROOT / "search" / "schemes" / "rust-2026-10-06d" / "library"
    log = ROOT / "search" / "runs" / "2026-10-06d_library.jsonl"
    print(f"# library build {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    for fmt, best in LIBRARY:
        res = campaign.run_arm("lib", fmt, gf2mm.standard_scheme(fmt), "standard", [1, 2, 3, 4], 30, best, log, save,
                               target_rank=best)
        print(f"{fmt} best known {best}: {campaign.describe(res, best)}", flush=True)


def main(key):
    if key == "library":
        return run_library()
    set_below_normal_priority()
    plan = PLANS[key]
    fmt, record = plan["fmt"], plan["record"]
    name = "x".join(map(str, fmt))
    log = ROOT / "search" / "runs" / f"2026-10-06d_tgt_{name}.jsonl"
    save = ROOT / "search" / "schemes" / "rust-2026-10-06d" / "targets"
    starts = ROOT / "search" / "schemes" / "rust-2026-10-06d" / "starts"
    print(f"# target {fmt}: best known GF(2) rank {record}; full_reduce={FULL}; started "
          f"{time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    seed_base = 1000 if not key.endswith("b") else 6000
    policy = {"plateau": plan.get("plateau", 50_000), "slack": plan.get("slack", 3)}
    for arm, nseeds, secs in plan["arms"]:
        if arm in ("std", "blk"):
            start, label = campaign.build_start(fmt, "standard" if arm == "std" else "block", starts)
            save_below = None
        elif arm == "own60":
            f, start, _ = gf2mm.load_scheme(ROOT / plan["own"])
            assert tuple(f) == fmt and gf2mm.verify(fmt, start) and gf2mm.verify_explicit(fmt, start)
            label = f"own rank-{len(start)} scheme {plan['own']}"
            save_below = record
        else:
            start, label = published_start(plan)
            save_below = record
        seeds = list(range(seed_base + 1, seed_base + nseeds + 1))
        seed_base += 1000
        t0 = time.time()
        arm_name = f"{arm}{'_full' if FULL else ''}{'_p' + str(policy['plateau']) + 's' + str(policy['slack']) if key.endswith('b') else ''}"
        res = campaign.run_arm(arm_name, fmt, start, label, seeds, secs, record, log, save,
                               full_reduce=FULL, save_below=save_below, **policy)
        print(f"{arm:4s} start rank {len(start)} ({label}); seeds {seeds[0]}-{seeds[-1]} x {secs} s; "
              f"wall {time.time() - t0:.0f} s", flush=True)
        print(f"     {campaign.describe(res, record)}", flush=True)
        for s in res:
            if s.get("best_rank") is not None and s["best_rank"] < record:
                print(f"     *** BELOW THE BEST KNOWN RANK: seed {s['seed']} rank {s['best_rank']} -- saved, "
                      f"needs the full verification of the brief (step 5) ***", flush=True)
        bad = [s for s in res if not s.get("verified")]
        if bad:
            print(f"     UNVERIFIED RESULTS: {bad}", flush=True)
    print(f"# finished {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])

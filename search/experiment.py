"""Shared bookkeeping for the experiment scripts in experiments/2026-10-07_*.py.

`run_batch` runs a list of walk configurations one after another in this process (below-normal priority),
writes one JSONL event log per run to search/runs/, saves schemes to search/schemes/ and writes a JSON summary
of the batch to search/runs/<name>.json. Saved schemes:
  * the best scheme of every run, labelled "matches best known", "above best known" (a near-miss) or
    "BELOW best known -- candidate, needs independent checks";
  * the first scheme reached at every rank <= best known in that run (if different from the best).
Each scheme is checked with the exact verifier before it is written (`gf2mm.save_scheme` refuses otherwise).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from . import gf2mm
from .driver import WalkConfig, run_walk
from .machine import CpuMeter, environment, set_below_normal_priority

REPO = Path(__file__).resolve().parent.parent
SCHEMES = REPO / "search" / "schemes"
RUNS = REPO / "search" / "runs"


def status_label(rank: int, best_known: int | None) -> str:
    if best_known is None:
        return "best known rank not given"
    if rank < best_known:
        return "BELOW best known -- candidate, needs independent checks"
    if rank == best_known:
        return "matches best known"
    return "above best known"


def fmt_name(fmt) -> str:
    return "x".join(str(x) for x in fmt)


def run_batch(name: str, script: str, configs: list[WalkConfig], best_known: int | None, start=None,
              start_label: str = "standard algorithm", save_best: bool = True) -> list[dict]:
    """Run the configs sequentially; print one line per run; return the list of run records."""
    prio = set_below_normal_priority()
    SCHEMES.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    print(f"# {name}: {len(configs)} run(s); below-normal priority set: {prio}; start: {start_label}")
    print(f"# environment: {json.dumps(environment())}")
    records = []
    batch_meter = CpuMeter().start()
    for cfg in configs:
        tag = f"{name}_{fmt_name(cfg.fmt)}_seed{cfg.seed}"
        if cfg.extra.get("tag"):
            tag += "_" + cfg.extra["tag"]
        cfg.keep_ranks_upto = best_known if best_known is not None else cfg.keep_ranks_upto
        meter = CpuMeter().start()
        started = time.strftime("%Y-%m-%dT%H:%M:%S")
        res = run_walk(cfg, start=start, logfile=str(RUNS / f"{tag}.jsonl"))
        load = meter.stop()
        saved = []
        to_save = {}
        if save_best:
            to_save[res["best_rank"]] = (res["best_reached_at_flip"], res["best_reached_at_seconds"], res["best_scheme"])
        for r, (fl, secs, sch) in res["first_at_rank"].items():
            to_save.setdefault(r, (fl, secs, sch))
        for r, (fl, secs, sch) in sorted(to_save.items()):
            path = SCHEMES / f"{tag}_rank{r}.json"
            gf2mm.save_scheme(path, cfg.fmt, sch, status=status_label(r, best_known), best_known_rank=best_known,
                              provenance={"script": script, "run_tag": tag, "seed": cfg.seed,
                                          "start": start_label, "reached_at_flip": fl, "reached_at_seconds": secs,
                                          "run_total_flips": res["flips"], "run_wall_seconds": res["wall_seconds"],
                                          "config": res["config"]})
            saved.append(str(path.relative_to(REPO)).replace(os.sep, "/"))
        rec = {k: v for k, v in res.items() if k not in ("best_scheme", "first_at_rank")}
        rec.update(started=started, machine=load, saved_schemes=saved, tag=tag,
                   status=status_label(res["best_rank"], best_known))
        records.append(rec)
        traj = " ".join(f"{r}@{fl}" for r, fl, _ in res["trajectory"])
        print(f"{tag}: best rank {res['best_rank']} ({rec['status']}) reached at flip {res['best_reached_at_flip']:,} "
              f"/ {res['best_reached_at_seconds']:.1f} s; {res['flips']:,} flips in {res['wall_seconds']:.1f} s "
              f"({res['flips_per_second']:,} flips/s), stopped by {res['stopped_by']}; plus {res['plus_transitions']}, "
              f"restarts {res['restarts']}, verifications passed {res['full_verifications_passed']}; "
              f"system CPU {load['system_cpu_utilisation']}, process CPU {load['process_cpu_seconds']} s")
        print(f"    trajectory (rank@flip): {traj}")
    batch_load = batch_meter.stop()
    with open(RUNS / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump({"name": name, "script": script, "best_known_rank": best_known, "start": start_label,
                   "environment": environment(), "batch_machine": batch_load, "runs": records}, f, indent=1)
        f.write("\n")
    print(f"# batch wall {batch_load['wall_seconds']} s, process CPU {batch_load['process_cpu_seconds']} s, "
          f"system CPU utilisation {batch_load['system_cpu_utilisation']}")
    return records

"""Search campaigns over several matrix multiplication formats (research/2026-10-06d_exotic_formats.md).

`run_arm` runs one arm (a start scheme plus kernel parameters) on a list of seeds with search.rust_kernel.run_parallel
(one process per walk, below-normal priority, every result re-verified by the exact Python verifier before it is
logged or saved), appends one JSON line per walk to a log, saves every verified best scheme (or, with save_below=r,
only those of rank < r), and returns the per-walk summaries. `clopper_pearson` gives exact binomial intervals for the calibration rates.

Start schemes: "standard" (the schoolbook algorithm) or "block" (search.blocks.best_block_start over a library of
verified schemes from earlier rounds). Block starts are saved (verified) next to the schemes they produce.
"""
from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

from . import blocks, gf2mm, rust_kernel
from .experiment import status_label
from .machine import CpuMeter, environment, set_below_normal_priority

REPO = Path(__file__).resolve().parent.parent


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact two-sided (1 - alpha) interval for a binomial proportion (bisection on the exact binomial CDF)."""
    def cdf(x, p):  # P(X <= x)
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(x + 1))

    lower = 0.0 if k == 0 else _lower(k, n, alpha, cdf)
    upper = 1.0 if k == n else _upper(k, n, alpha, cdf)
    return lower, upper


def _lower(k, n, alpha, cdf):
    lo, hi = 0.0, 1.0  # find p with P(X >= k) = alpha/2; P(X >= k) increases with p
    for _ in range(200):
        mid = (lo + hi) / 2
        if 1 - cdf(k - 1, mid) < alpha / 2:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _upper(k, n, alpha, cdf):
    lo, hi = 0.0, 1.0  # find p with P(X <= k) = alpha/2; P(X <= k) decreases with p
    for _ in range(200):
        mid = (lo + hi) / 2
        if cdf(k, mid) > alpha / 2:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def library():
    lib = blocks.load_library(blocks.default_library_paths(REPO) +
                              sorted((REPO / "search" / "schemes" / "rust-2026-10-06d" / "library").glob("*.json")))
    for k, v in blocks.strassen_entry().items():
        if k not in lib or lib[k][0] > v[0]:
            lib[k] = v
    return lib


def build_start(fmt, kind: str, save_dir: Path | None = None):
    """Returns (terms, label). kind: 'standard' or 'block'."""
    fmt = tuple(fmt)
    if kind == "standard":
        return gf2mm.standard_scheme(fmt), "standard"
    if kind != "block":
        raise ValueError(kind)
    rank, desc, terms = blocks.best_block_start(library(), fmt)
    if not (gf2mm.verify(fmt, terms) and gf2mm.verify_explicit(fmt, terms)):
        raise AssertionError("block start failed verification")
    label = f"block start, rank {rank}: {desc}"
    if save_dir is not None:
        save_dir.mkdir(parents=True, exist_ok=True)
        path = save_dir / f"{'x'.join(map(str, fmt))}_start_rank{rank}.json"
        gf2mm.save_scheme(path, fmt, terms, status="start scheme (direct sum of smaller verified schemes)",
                          provenance={"construction": desc, "module": "search/blocks.py"})
        label += f" ({path.relative_to(REPO).as_posix()})"
    return terms, label


def run_arm(name: str, fmt, start, start_label: str, seeds, seconds: float, best_known: int, log: Path,
            save_dir: Path, workers: int = 4, plateau: int = 50_000, slack: int = 3, full_reduce: bool = False,
            dead_end: bool = True, target_rank: int = 0, save_below: int | None = None) -> list[dict]:
    set_below_normal_priority()
    fmt = tuple(fmt)
    info = rust_kernel.build()
    meter = CpuMeter().start()
    t0 = time.strftime("%H:%M:%S")
    results = rust_kernel.run_parallel(fmt, start, seeds, workers, max_seconds=seconds, plateau=plateau, slack=slack,
                                       full_reduce=full_reduce, dead_end=dead_end, target_rank=target_rank)
    load = meter.stop()
    t1 = time.strftime("%H:%M:%S")
    env = environment()
    env["kernel_sha256"] = info["source_sha256"]
    out = []
    log.parent.mkdir(parents=True, exist_ok=True)
    save_dir.mkdir(parents=True, exist_ok=True)
    for res in results:
        summary = {k: v for k, v in res.items() if k != "best"}
        summary.update(arm=name, start=start_label, start_rank=len(start), best_known=best_known,
                       best_rank=len(res["best"]) if "best" in res else None,
                       params={"seconds": seconds, "plateau": plateau, "slack": slack, "full_reduce": full_reduce,
                               "dead_end": dead_end, "target_rank": target_rank, "workers": workers},
                       window=[t0, t1], machine_load=load, environment=env)
        with open(log, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(summary, default=str) + "\n")
        if res.get("verified") and (save_below is None or len(res["best"]) < save_below):
            r = len(res["best"])
            path = save_dir / f"{'x'.join(map(str, fmt))}_rank{r}_{name}_seed{res['seed']}.json"
            gf2mm.save_scheme(path, fmt, res["best"], status=status_label(r, best_known), best_known_rank=best_known,
                              provenance={"kernel": "search/kernel/flipwalk.rs", "kernel_sha256": info["source_sha256"],
                                          "arm": name, "start": start_label, "seed": res["seed"],
                                          "stats": res.get("stats"), "improvements": res.get("improvements"),
                                          "params": summary["params"]})
        out.append(summary)
    return out


def describe(arm: list[dict], record: int) -> str:
    ranks = [s["best_rank"] for s in arm]
    hits = sum(1 for r in ranks if r is not None and r <= record)
    lo, hi = clopper_pearson(hits, len(ranks))
    below = sum(1 for r in ranks if r is not None and r < record)
    first = [min((t for rr, st, t in s.get("improvements", []) if rr <= record), default=None) for s in arm]
    first = [round(x, 1) for x in first if x is not None]
    steps = sum(s["stats"]["steps"] for s in arm if "stats" in s)
    flips = sum(s["stats"]["flips"] for s in arm if "stats" in s)
    deps = sum(s["stats"].get("dep_reductions", 0) for s in arm if "stats" in s)
    return (f"best ranks {ranks}; reached <= {record}: {hits}/{len(ranks)} (95% CI {lo:.3f}-{hi:.3f}); "
            f"below {record}: {below}; first reached (s) {sorted(first)}; steps {steps:.4g}; flips {flips:.4g}; "
            f"dep_reductions {deps}")


def walk_seconds(arm):
    return sum(s.get("wall_seconds", 0) for s in arm)


def env_note():
    return {"cpus": os.cpu_count()}

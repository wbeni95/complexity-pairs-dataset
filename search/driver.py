"""Random-walk driver for the GF(2) flip graph: seeds, budgets, plateau escapes, logging, periodic verification.

Walk policy. The flip-graph method (Kauers & Moosbauer, ISSAC 2023) performs random walks on a graph whose
vertices are schemes; Arai, Ichikawa & Hukushima (arXiv:2312.16960) add transitions that do not reduce the rank.
We read only the abstracts of these papers, so the policy below is our own simple design, not a
reimplementation of theirs:

  * every step applies one random flip; reductions are applied eagerly (see `search.flipgraph`);
  * `best` is the lowest rank seen so far; a pool keeps up to `pool_size` distinct-in-time schemes of rank `best`
    (the scheme at each arrival at rank `best`; when full, a random slot is overwritten);
  * a plateau is `plateau` consecutive flips without a rank decrease. On a plateau:
      escape="plus":    if rank < best + slack, apply a plus transition (rank + 1; up to `plus_per_escape` of
                        them while rank < best + slack); otherwise restart from a random pool scheme;
      escape="restart": restart from a random pool scheme;
      escape="none":    keep walking;
  * optional weight cap (our own heuristic, off by default): with `max_weight` > 0 a sampled flip that would create
    a factor of Hamming weight > max_weight is rejected; the step still counts toward `max_flips` and `flips`;
  * optional one-step lookahead (our own heuristic, off by default): every `lookahead_every` flips, all available
    flips are scanned (`FlipGraphState.reducing_flips`) and, if some flip enables a reduction, a random such flip
    is applied. These extra flips are reported as `lookahead_hits` and are not counted in `flips`;
  * the run stops after `max_flips` steps (flips plus dead-end events where no flip is available; with
    escape="none" a dead end stops the run), after `max_seconds` of wall-clock time (if set), or when
    `best <= target_rank` (if set).

Determinism: with a fixed seed and a flip budget the trajectory is fully determined (CPython's random.Random is
stable across versions for randrange / getrandbits). A run stopped by `max_seconds` is not reproducible in its
length, and the summary says so ("stopped_by": "time").

Every new best scheme, every restart and every `verify_every` flips the full scheme is checked with the exact
verifier (`search.gf2mm.verify`); a failure raises RuntimeError (it would be a bug in the moves).
"""
from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass, field

from .flipgraph import FlipGraphState
from .gf2mm import standard_scheme, verify


@dataclass
class WalkConfig:
    fmt: tuple
    seed: int
    max_flips: int
    plateau: int = 100_000
    escape: str = "plus"          # "plus" | "restart" | "none"
    slack: int = 1                # plus transitions may raise the rank to at most best + slack
    plus_per_escape: int = 1      # plus transitions applied per escape (each still limited by slack)
    pool_size: int = 64
    reduction: str = "linear"     # "linear" (R1+R2+R3) | "pair" (R1+R2)
    max_seconds: float | None = None
    target_rank: int | None = None
    verify_every: int = 500_000
    log_every: int = 500_000
    keep_ranks_upto: int | None = None   # keep the first scheme reached at every rank <= this value
    max_weight: int = 0           # heuristic: reject flips creating factors of Hamming weight > max_weight (0 = off)
    lookahead_every: int = 0      # every k flips, scan all flips and take one that enables a reduction (0 = off)
    extra: dict = field(default_factory=dict)


def run_walk(cfg: WalkConfig, start=None, logfile=None, echo=None) -> dict:
    """Run one walk. `start` defaults to the standard algorithm. `logfile`: path of a JSONL event log.
    `echo`: callable(str) for human-readable progress lines (e.g. print). Returns a summary dict that includes
    the best scheme and the first scheme reached at every rank <= cfg.keep_ranks_upto."""
    if cfg.escape not in ("plus", "restart", "none"):
        raise ValueError("escape must be 'plus', 'restart' or 'none'")
    fmt = tuple(cfg.fmt)
    rng = random.Random(cfg.seed)
    start = list(start) if start is not None else standard_scheme(fmt)
    if not verify(fmt, start):
        raise ValueError("start scheme fails the exact verifier")
    log = open(logfile, "w", encoding="utf-8") if logfile else None

    def emit(event, **kw):
        if log:
            log.write(json.dumps({"event": event, **kw}) + "\n")
            log.flush()

    t0 = time.perf_counter()
    state = FlipGraphState(start, rng, cfg.reduction, cfg.max_weight)
    best = state.rank
    best_scheme = state.scheme()
    best_flips, best_time = 0, 0.0
    first_at_rank = {}            # rank -> (flips, seconds, scheme)
    trajectory = [(state.rank, 0, 0.0)]  # (new best rank, flips, seconds)

    def keep(rank, flips, secs, scheme):
        if cfg.keep_ranks_upto is not None and rank <= cfg.keep_ranks_upto and rank not in first_at_rank:
            first_at_rank[rank] = (flips, round(secs, 3), scheme)

    keep(best, 0, 0.0, best_scheme)
    pool = [best_scheme]
    emit("start", config=asdict(cfg) | {"fmt": list(fmt)}, start_rank=len(start), rank_after_reduce=state.rank)

    flips = 0
    since = 0
    n_plus = n_restart = n_verify = n_stuck = 0
    reductions_before = 0          # reduction events of states discarded by restarts
    rejected_before = 0
    n_scans = n_hits = 0           # lookahead scans, and scans that found a reducing flip (taken, not counted in flips)
    stopped_by = "flips"
    last_rank = state.rank
    while flips + n_stuck < cfg.max_flips:   # dead-end events (no flip available) also consume the budget
        if not state.flip():
            n_stuck += 1
            if cfg.escape == "none":
                stopped_by = "no flip available"
                break
            since = cfg.plateau        # no flip available: force an escape
        else:
            flips += 1
            since += 1
            if cfg.lookahead_every and flips % cfg.lookahead_every == 0:
                n_scans += 1
                cands = state.reducing_flips()
                if cands:
                    n_hits += 1
                    state.apply_flip(*cands[rng.randrange(len(cands))])
        r = state.rank
        if r < last_rank:
            since = 0
            if r < best:
                best = r
                best_scheme = state.scheme()
                secs = time.perf_counter() - t0
                best_flips, best_time = flips, secs
                if not verify(fmt, best_scheme):
                    raise RuntimeError(f"verifier rejected the new best scheme at flip {flips}")
                n_verify += 1
                pool = [best_scheme]
                trajectory.append((best, flips, round(secs, 3)))
                keep(best, flips, secs, best_scheme)
                emit("best", rank=best, flips=flips, seconds=round(secs, 3))
                if echo:
                    echo(f"  seed {cfg.seed}: rank {best} at flip {flips:,} ({secs:.1f} s)")
                if cfg.target_rank is not None and best <= cfg.target_rank:
                    stopped_by = "target"
                    break
            elif r == best:
                sch = state.scheme()
                if len(pool) < cfg.pool_size:
                    pool.append(sch)
                else:
                    pool[rng.randrange(cfg.pool_size)] = sch
        last_rank = r

        if since >= cfg.plateau:
            since = 0
            if cfg.escape == "plus" and state.rank < best + cfg.slack and state.plus():
                n_plus += 1
                for _ in range(cfg.plus_per_escape - 1):      # optional extra plus transitions (default: none)
                    if state.rank < best + cfg.slack and state.plus():
                        n_plus += 1
            elif cfg.escape in ("plus", "restart"):
                reductions_before += state.n_reductions
                rejected_before += state.n_rejected
                state = FlipGraphState(pool[rng.randrange(len(pool))], rng, cfg.reduction, cfg.max_weight)
                if not verify(fmt, state.scheme()):
                    raise RuntimeError("verifier rejected a restart scheme")
                n_verify += 1
                n_restart += 1
            last_rank = state.rank

        if flips and flips % 4096 == 0:
            if cfg.verify_every and flips % cfg.verify_every < 4096:
                if not verify(fmt, state.scheme()):
                    raise RuntimeError(f"verifier rejected the walk state at flip {flips}")
                n_verify += 1
            if cfg.log_every and flips % cfg.log_every < 4096:
                secs = time.perf_counter() - t0
                emit("progress", flips=flips, rank=state.rank, best=best, seconds=round(secs, 3),
                     plus=n_plus, restarts=n_restart, flips_per_second=round(flips / secs) if secs else None)
            if cfg.max_seconds is not None and time.perf_counter() - t0 > cfg.max_seconds:
                stopped_by = "time"
                break

    wall = time.perf_counter() - t0
    if not verify(fmt, best_scheme):
        raise RuntimeError("verifier rejected the final best scheme")
    n_verify += 1
    summary = {
        "format": list(fmt),
        "seed": cfg.seed,
        "config": asdict(cfg) | {"fmt": list(fmt)},
        "start_rank": len(start),
        "best_rank": best,
        "best_reached_at_flip": best_flips,
        "best_reached_at_seconds": round(best_time, 3),
        "flips": flips,
        "wall_seconds": round(wall, 3),
        "flips_per_second": round(flips / wall) if wall else None,
        "flips_since_last_improvement": flips - best_flips,
        "stopped_by": stopped_by,
        "plus_transitions": n_plus,
        "rejected_by_weight_cap": rejected_before + state.n_rejected,
        "lookahead_scans": n_scans,
        "lookahead_hits": n_hits,
        "restarts": n_restart,
        "no_flip_available_events": n_stuck,
        "reduction_events": reductions_before + state.n_reductions,
        "full_verifications_passed": n_verify,
        "trajectory": trajectory,
        "best_scheme": best_scheme,
        "first_at_rank": {r: v for r, v in sorted(first_at_rank.items())},
    }
    emit("end", **{k: v for k, v in summary.items() if k not in ("best_scheme", "first_at_rank", "config")})
    if log:
        log.close()
    return summary

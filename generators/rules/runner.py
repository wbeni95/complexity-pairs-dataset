"""Batch screening, deduplication, clustering and summaries for the rule modules."""
from __future__ import annotations

import time
from collections import Counter, defaultdict

from . import load
from .common import screen


def run_rule(rule: str, seed: int, count: int, screen_seed: int = 0, families=None) -> list[dict]:
    mod = load(rule)
    specs = mod.generate(seed, count) if families is None else mod.generate(seed, count, families=families)
    cache: dict = {}
    out = []
    for i, spec in enumerate(specs):
        cand = mod.build(spec)
        rec = screen(cand, seed=screen_seed, cache=cache)
        rec["gen_seed"], rec["gen_index"] = seed, i
        out.append(rec)
    return out


def compact(rec: dict) -> dict:
    """Candidate-store record: drops bulky per-n count lists (reproducible from generator + seed)."""
    r = dict(rec)
    sc = r.get("scaling")
    if sc and "error" not in sc:
        r["scaling"] = {"resolved": sc["resolved"], "key": sc["key"], "cached": sc.get("cached", False),
                        **{side: {k: sc[side][k] for k in ("cost", "alpha", "local_min", "local_max", "n_values",
                                                           "counts_equal_spec", "best_library") if k in sc[side]}
                           | {"rivals": [[x["cost"], x["alpha"], x["rejected"]] for x in sc[side]["rivals"]]}
                           for side in ("slow", "fast")}}
    return r


def summarise(records: list[dict]) -> dict:
    verdicts = Counter(r["verdict"] for r in records)
    canon = defaultdict(list)
    for r in records:
        canon[r.get("canonical", r["id"])].append(r)
    unique = len(canon)
    conflicting = sum(1 for v in canon.values() if len({x["verdict"] for x in v}) > 1)
    clusters = defaultdict(Counter)
    for r in records:
        clusters[r.get("cluster", "?")][r["verdict"]] += 1
    confusion = Counter((str(r.get("precondition")), r["verdict"]) for r in records)
    scal = [r["scaling"] for r in records if r["verdict"] == "EXACT" and r.get("scaling")]
    resolved = sum(1 for s in scal if s.get("resolved"))
    keys = {s.get("key") for s in scal if "error" not in s}
    errors = [s["error"] for s in scal if "error" in s]
    unresolved = sorted({(s["key"], s["slow"]["cost"], s["slow"]["alpha"], s["fast"]["cost"], s["fast"]["alpha"])
                         for s in scal if "error" not in s and not s["resolved"]})
    spec_mismatch = sum(1 for s in scal if "error" not in s and any(s[x].get("counts_equal_spec") is False for x in ("slow", "fast")))
    return {
        "candidates": len(records), "verdicts": dict(verdicts), "unique_canonical": unique,
        "duplicates": len(records) - unique, "canonical_classes_with_conflicting_verdicts": conflicting,
        "clusters": {k: dict(v) for k, v in sorted(clusters.items())},
        "precondition_vs_verdict": {f"{a}|{b}": c for (a, b), c in sorted(confusion.items())},
        "exact_with_scaling": len(scal), "scaling_resolved": resolved, "distinct_scaling_keys": len(keys),
        "scaling_errors": errors, "unresolved_fits": [list(u) for u in unresolved],
        "counts_not_equal_spec": spec_mismatch,
    }

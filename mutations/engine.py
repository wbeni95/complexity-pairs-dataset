"""Differential testing, shrinking, classification, cost fitting and records for mutants.

Classification (one per mutant):
  SURVIVED      subject agreed with the oracle on every test (the number of tests is recorded)
  KILLED        at least one disagreement; a counterexample is shrunk (smallest size first, then simpler values)
  TRIVIAL       survived, but the mutant is a known trivial reparametrisation (reason recorded)
  INVALID       the mutant is not well defined: an operation it needs does not exist in the structure, a literal
                has no meaning there, or it crashed / exceeded a limit (reason recorded)
  INCONCLUSIVE  the oracle itself failed or too few tests ran
NEAR-MISS is a flag on KILLED mutants: agreement rate >= 0.9, or numeric outputs within a bounded ratio.
"""
from __future__ import annotations

import importlib.util
import _thread
import json
import math
import random
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from . import algebra

REPO = Path(__file__).resolve().parent.parent

_validate = None


def validate_module():
    """tools/validate.py imported as a module (not modified): fit_slope and eval_cost are reused."""
    global _validate
    if _validate is None:
        spec = importlib.util.spec_from_file_location("cpairs_tools_validate", REPO / "tools" / "validate.py")
        mod = importlib.util.module_from_spec(spec)
        stdout = sys.stdout
        spec.loader.exec_module(mod)
        sys.stdout = stdout
        _validate = mod
    return _validate


INVALID_EXC = (algebra.UndefinedOp, algebra.OrderError, algebra.LiftError, ZeroDivisionError)


@dataclass
class Mutant:
    pair: str
    family: str                 # "MIRROR" or "OPSWAP"
    operator: str               # e.g. "negate", "rev-order", "semiring:MinPlus"
    mode: str                   # "io", "inject", "ast", "ast+inject"
    subject_name: str
    description: str
    subject: Callable
    oracle: Callable
    gen: Callable               # gen(n, rng) -> instance
    sizes: list
    trials: int = 20
    equal: Callable | None = None
    trivial: str | None = None
    structure: str | None = None
    oracle_name: str = ""
    simplify: Callable | None = None   # simplify(instance) -> iterable of simpler candidate instances
    cost: dict | None = None           # {"run": f(n)->counts dict, "n_values": [...], "measure": key, "claimed": expr,
                                       #  "library": [exprs], "tolerance": float}
    literature: list = field(default_factory=list)
    notes: str = ""
    provenance: dict = field(default_factory=dict)
    max_seconds: float = 60.0

    @property
    def id(self):
        return f"{self.pair}|{self.family}|{self.operator}|{self.mode}|{self.subject_name}"


def _default_equal(a, b):
    return algebra.unwrap(a) == algebra.unwrap(b)


def jsonable(x, depth=0):
    x = algebra.unwrap(x)
    if depth > 6:
        return repr(x)
    if isinstance(x, float):
        if math.isinf(x):
            return "inf" if x > 0 else "-inf"
        return x
    if isinstance(x, (int, str, bool)) or x is None:
        return x
    if isinstance(x, (list, tuple)):
        return [jsonable(y, depth + 1) for y in x]
    if isinstance(x, dict):
        return {str(k): jsonable(v, depth + 1) for k, v in x.items()}
    return repr(x)


CALL_TIMEOUT_S = 5.0          # a single oracle or subject call longer than this is a limit violation
_deadline = [None]
_watch_started = [False]


def _watchdog():
    while True:
        time.sleep(0.05)
        d = _deadline[0]
        if d is not None and time.perf_counter() > d:
            _deadline[0] = None
            _thread.interrupt_main()   # raises KeyboardInterrupt in the main thread (the running call)


def _call(fn, inst, timeout: float | None = None):
    """Run one oracle/subject call. Mutants can loop forever (e.g. a flipped comparison that never reaches a break),
    so a watchdog thread interrupts any call that exceeds CALL_TIMEOUT_S."""
    if not _watch_started[0]:
        threading.Thread(target=_watchdog, daemon=True).start()
        _watch_started[0] = True
    _deadline[0] = time.perf_counter() + (timeout or CALL_TIMEOUT_S)
    try:
        return ("ok", fn(inst))
    except KeyboardInterrupt:
        return ("timeout", f"call exceeded {timeout or CALL_TIMEOUT_S:.0f} s (watchdog)")
    except INVALID_EXC as e:
        return ("invalid", f"{type(e).__name__}: {e}")
    except RecursionError as e:
        return ("crash", f"RecursionError: {e}")
    except Exception as e:  # noqa: BLE001 -- a crashing mutant is data
        tb = traceback.extract_tb(e.__traceback__)[-1]
        return ("crash", f"{type(e).__name__}: {e} (line {tb.lineno})")
    finally:
        _deadline[0] = None


def run_mutant(m: Mutant, seed: str = "2026-10-06d") -> dict:
    eq = m.equal or _default_equal
    t0 = time.perf_counter()
    stats = {"tests": 0, "agree": 0, "disagree": 0, "invalid": 0, "crash": 0, "timeout": 0, "oracle_fail": 0}
    first_bad = None
    first_invalid = None
    ratios = []
    for n in m.sizes:
        for t in range(m.trials):
            if time.perf_counter() - t0 > m.max_seconds:
                break
            rng = random.Random(f"{seed}|{m.id}|{n}|{t}")
            inst = m.gen(n, rng)
            ost, ref = _call(m.oracle, inst)
            if ost != "ok":
                stats["oracle_fail"] += 1
                if first_invalid is None:
                    first_invalid = ("oracle", ref, inst)
                continue
            sst, out = _call(m.subject, inst)
            stats["tests"] += 1
            if sst != "ok":
                stats[sst] += 1
                if first_invalid is None:
                    first_invalid = (sst, out, inst)
                continue
            if eq(out, ref):
                stats["agree"] += 1
            else:
                stats["disagree"] += 1
                r = _ratio(out, ref)
                if r is not None:
                    ratios.append(r)
                if first_bad is None:
                    first_bad = (n, t, inst, ref, out)
    elapsed = time.perf_counter() - t0
    rec = {"id": m.id, "pair": m.pair, "family": m.family, "operator": m.operator, "mode": m.mode,
           "structure": m.structure, "subject": m.subject_name, "oracle": m.oracle_name,
           "description": m.description, "sizes": m.sizes, "trials_per_size": m.trials, "seed": seed,
           "tests": stats, "elapsed_s": round(elapsed, 3), "trivial_reason": m.trivial,
           "literature": m.literature, "notes": m.notes, "provenance": m.provenance}
    if stats["oracle_fail"] and stats["tests"] == 0:
        rec["status"] = "INCONCLUSIVE"
        rec["reason"] = f"oracle failed: {first_invalid[1]}"
    elif stats["invalid"] or stats["crash"] or stats["timeout"]:
        rec["status"] = "INVALID"
        kind, msg, inst = first_invalid
        bad = stats["invalid"] + stats["crash"] + stats["timeout"]
        rec["reason"] = f"{kind} in {bad}/{stats['tests']} tests; first: {msg}"
        if stats["disagree"]:
            rec["reason"] += f"; additionally {stats['disagree']} disagreements"
        rec["invalid_instance"] = jsonable(inst)
    elif stats["disagree"]:
        rec["status"] = "KILLED"
        rec["agreement_rate"] = round(stats["agree"] / stats["tests"], 4)
        rec["counterexample"] = shrink(m, first_bad, eq, seed)
        nm = []
        if rec["agreement_rate"] >= 0.9:
            nm.append(f"agrees on {stats['agree']}/{stats['tests']} tests")
        if ratios and all(0.5 <= r <= 2 for r in ratios):
            nm.append(f"subject/oracle ratio in [{min(ratios):.4g}, {max(ratios):.4g}] on the disagreeing tests")
        if nm:
            rec["near_miss"] = "; ".join(nm)
    elif stats["tests"] < 10:
        rec["status"] = "INCONCLUSIVE"
        rec["reason"] = f"only {stats['tests']} tests ran in the time budget"
    else:
        rec["status"] = "TRIVIAL" if m.trivial else "SURVIVED"
    if rec["status"] in ("SURVIVED", "TRIVIAL") and m.cost:
        try:
            rec["cost_fit"] = fit_cost(m.cost)
        except Exception as e:  # noqa: BLE001
            rec["cost_fit"] = {"error": f"{type(e).__name__}: {e}"}
    return rec


def _ratio(out, ref):
    out, ref = algebra.unwrap(out), algebra.unwrap(ref)
    try:
        if isinstance(out, (int, float)) and isinstance(ref, (int, float)) and ref not in (0,) \
                and not isinstance(out, bool) and math.isfinite(out) and math.isfinite(ref):
            return out / ref
    except TypeError:
        pass
    return None


def shrink(m: Mutant, first_bad, eq, seed, seeds_per_size: int = 60, max_steps: int = 400) -> dict:
    """Smallest failing size first (seeded search), then value simplification while the failure persists."""
    n0, t0, inst, ref, out = first_bad

    def fails(x):
        ost, r = _call(m.oracle, x)
        if ost != "ok":
            return None
        sst, o = _call(m.subject, x)
        if sst != "ok":
            return None
        return None if eq(o, r) else (r, o)

    best = (inst, ref, out, n0)
    candidates_n = sorted({n for n in range(0, n0 + 1)} | set(m.sizes))
    found = False
    for n in candidates_n:
        if n > n0:
            break
        for t in range(seeds_per_size):
            rng = random.Random(f"{seed}|shrink|{m.id}|{n}|{t}")
            try:
                x = m.gen(n, rng)
            except Exception:  # noqa: BLE001 -- the generator may reject tiny n
                break
            f = fails(x)
            if f:
                best = (x, f[0], f[1], n)
                found = True
                break
        if found:
            break
    x = best[0]
    steps = 0
    if m.simplify:
        improved = True
        while improved and steps < max_steps:
            improved = False
            for y in m.simplify(x):
                steps += 1
                f = fails(y)
                if f:
                    x, best = y, (y, f[0], f[1], best[3])
                    improved = True
                    break
                if steps >= max_steps:
                    break
    return {"size": best[3], "instance": jsonable(best[0]), "oracle_output": jsonable(best[1]),
            "subject_output": jsonable(best[2]), "simplify_steps": steps}


# --------------------------------------------------------------------------------------------------
# Generic simplifiers
# --------------------------------------------------------------------------------------------------

def _simpler_values(v, pool):
    out = []
    for c in pool:
        try:
            if c != v and (abs(c) < abs(v) if isinstance(c, (int, float)) and isinstance(v, (int, float))
                           and math.isfinite(v) else True):
                out.append(c)
        except TypeError:
            pass
    return out


def simplify_vector(pool=(0, 1, -1, 2)):
    def simp(x):
        seq = list(x)
        for i, v in enumerate(seq):
            for c in _simpler_values(v, pool):
                y = seq[:]
                y[i] = c
                yield type(x)(y) if isinstance(x, tuple) else y
    return simp


def simplify_matrix(pool=(0, 1, -1, 2), symmetric=False, keep_diag=True):
    def simp(M):
        n = len(M)
        rows = [list(r) for r in M]
        for i in range(n):
            for j in range(n):
                if keep_diag and i == j:
                    continue
                if symmetric and j < i:
                    continue
                for c in _simpler_values(rows[i][j], pool):
                    y = [r[:] for r in rows]
                    y[i][j] = c
                    if symmetric:
                        y[j][i] = c
                    yield tuple(tuple(r) for r in y)
    return simp


def simplify_pair(simp_a, simp_b):
    def simp(inst):
        a, b = inst
        for y in simp_a(a):
            yield (y, b)
        for y in simp_b(b):
            yield (a, y)
    return simp


# --------------------------------------------------------------------------------------------------
# Cost fitting (reuses tools/validate.py: fit_slope, eval_cost)
# --------------------------------------------------------------------------------------------------

DEFAULT_LIBRARY = ["n", "n * log(n)", "n**2", "n**2 * log(n)", "n**log2(7)", "n**3", "n**log2(3)",
                   "n**4", "2**n", "n * 2**n", "n**2 * 2**n", "3**n", "factorial(n)"]


def fit_cost(cost: dict) -> dict:
    v = validate_module()
    ns = cost["n_values"]
    measure = cost.get("measure", "total")
    counts = []
    for n in ns:
        c = cost["run"](n)
        counts.append(c)
    vals = [c[measure] if measure != "total" else sum(c[k] for k in ("add", "mul", "neg", "inv")) for c in counts]
    if min(vals) <= 0:
        return {"error": "non-positive count", "values": vals}
    ys = [math.log(x) for x in vals]
    tol = cost.get("tolerance", 0.03)
    lib = list(dict.fromkeys([cost["claimed"]] + cost.get("library", DEFAULT_LIBRARY)))
    alphas = {}
    for expr in lib:
        try:
            xs = [math.log(v.eval_cost(expr, n)) for n in ns]
        except (ValueError, OverflowError, ZeroDivisionError):
            continue
        if max(xs) - min(xs) < 1e-12:
            continue
        alphas[expr] = round(v.fit_slope(xs, ys), 4)
    fitting = [e for e, a in alphas.items() if abs(a - 1) <= tol]
    best = min(alphas, key=lambda e: abs(alphas[e] - 1)) if alphas else None
    return {"measure": measure, "n_values": ns, "values": vals, "counts": counts, "claimed": cost["claimed"],
            "tolerance": tol, "alphas": alphas, "best_fit": best, "fitting_within_tol": fitting,
            "claimed_fits": cost["claimed"] in fitting,
            "rejected_rivals": [e for e in alphas if e not in fitting],
            "discriminating": fitting == [cost["claimed"]]}


def write_records(records: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, default=repr) + "\n")

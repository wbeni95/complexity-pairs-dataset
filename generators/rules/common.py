"""Common screening harness for rule-mined candidates (generators/rules, round 2026-10-06d).

A *rule* is a speed-up template: a structural precondition, a slow -> fast transformation, a predicted cost
change and a failure mode. Each rule module provides

    CATALOGUE                 dict: precondition / transformation / cost_change / failure_mode / literature
    generate(seed, count)     -> list of JSON-able specs (deterministic in seed)
    build(spec)               -> Candidate

and this module screens every candidate the same way:

  1. correctness: the slow and the rule-produced fast algorithm run on seeded random instances
     (`random.Random(f"{id}|screen|{seed}|{n}|{trial}")`), and each instance is scored
     (exact?, closeness in [0, 1]);
  2. verdict:
        EXACT      every screened instance agrees exactly (a screen, not a proof);
        NEAR-MISS  not exact, but exact-rate >= 0.5 or mean closeness >= 0.9;
        WRONG      otherwise;
        INVALID    the candidate is ill-formed or degenerate (the slow algorithm fails, or the rule
                   predicts no cost change, so there is no pair);
  3. for EXACT candidates with a scaling plan: exact operation counts (instrumented primitives: the
     algorithms only reach the data through counted operations) at growing n, and a log-log fit
     against the claimed cost, with rivals, using `eval_cost` and `fit_slope` imported unchanged from
     tools/validate.py. The other side's claimed cost is always added as a rival, so "resolved" means
     both claims fit and each side rejects the other's cost.

Cost claims come from the rule specification (generators/README.md); the fit is the check.
"""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import math
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _load_validate():
    name = "_cpd_tools_validate"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / "validate.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_validate = _load_validate()
eval_cost = _validate.eval_cost
fit_slope = _validate.fit_slope

VERDICTS = ("EXACT", "NEAR-MISS", "WRONG", "INVALID")
NEAR_EXACT_RATE = 0.5
NEAR_CLOSENESS = 0.9

# Library of candidate costs used to report the best-fitting library cost of every EXACT series.
LIBRARY = ["log(n)", "log(n)**2", "sqrt(n)", "n", "n*log(n)", "n**2", "n**2*log(n)", "n**3", "n**4",
           "2**(n/2)", "1.5**n", "phi**n", "2**n", "n*2**n", "3**n", "4**n", "n*4**n"]


class Ops:
    """Operation counter handed to every algorithm; only counted primitives touch the data."""
    __slots__ = ("n",)

    def __init__(self):
        self.n = 0


def spec_hash(obj) -> str:
    return hashlib.sha1(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def short_hash(obj, k: int = 12) -> str:
    return spec_hash(obj)[:k]


class Candidate:
    """Base class. Subclasses set rule, family, screen_sizes, trials and implement instance/slow/fast."""
    rule = ""
    trials = 8
    screen_sizes: tuple = (6,)

    def __init__(self, spec: dict):
        self.spec = spec
        self.family = spec["family"]
        self.id = f"{self.rule}-{short_hash(spec, 10)}"

    # --- to implement -------------------------------------------------------------------------
    def instance(self, rng, n):
        raise NotImplementedError

    def slow(self, inst, ops):
        raise NotImplementedError

    def fast(self, inst, ops):
        raise NotImplementedError

    # --- optional ------------------------------------------------------------------------------
    def precondition(self):
        """The rule's stated structural precondition, checked exactly (True/False), or None if not defined."""
        return None

    def predicates(self) -> dict:
        """Further named structural properties (used to test rule hypotheses)."""
        return {}

    def degenerate(self):
        """A reason string if the rule predicts no cost change (no pair), else None."""
        return None

    def score(self, inst, a, b):
        ok = a == b
        return ok, 1.0 if ok else 0.0

    def scaling(self):
        """None, or {"slow": {"n_values", "cost", "rivals"}, "fast": {...}, "tolerance": t}."""
        return None

    def scaling_key(self):
        return self.id

    def scale_instance(self, rng, n, side):
        return self.instance(rng, n)

    def canonical(self) -> str:
        return short_hash(self.spec)

    def cluster(self) -> str:
        return self.family


import ast as _ast


def _log_eval(node, n):
    """log(cost) evaluated in log space, for the same expression grammar as tools/validate.py eval_cost;
    used only when eval_cost overflows a float (e.g. a rival lambda**n at n = 16000)."""
    if isinstance(node, _ast.Expression):
        return _log_eval(node.body, n)
    if isinstance(node, _ast.BinOp):
        if isinstance(node.op, _ast.Mult):
            return _log_eval(node.left, n) + _log_eval(node.right, n)
        if isinstance(node.op, _ast.Div):
            return _log_eval(node.left, n) - _log_eval(node.right, n)
        if isinstance(node.op, _ast.Pow):
            base = eval_cost(_ast.unparse(node.left), n)
            expo = eval_cost(_ast.unparse(node.right), n)
            return expo * math.log(base)
        if isinstance(node.op, (_ast.Add, _ast.Sub)):
            a, b = _log_eval(node.left, n), _log_eval(node.right, n)
            m = max(a, b)
            sgn = 1 if isinstance(node.op, _ast.Add) else -1
            return m + math.log(math.exp(a - m) + sgn * math.exp(b - m))
    return math.log(eval_cost(_ast.unparse(node), n))


def log_cost(expr: str, n) -> float:
    """math.log(eval_cost(expr, n)), falling back to log-space evaluation on float overflow."""
    n = float(n)  # an int n would make eval_cost build a huge integer for e.g. 4**n at n = 10^15 (hangs)
    try:
        return math.log(eval_cost(expr, n))
    except OverflowError:
        return _log_eval(_ast.parse(expr, mode="eval"), n)


def fit_claim(ns, values, claim, rivals=(), tol=0.05) -> dict:
    xs = [log_cost(claim, n) for n in ns]
    ys = [math.log(v) for v in values]
    if max(xs) - min(xs) < 1e-12:  # constant claim: checked like tools/validate.py, by max/min of the values
        ratio = max(values) / min(values)
        return {"cost": claim, "alpha": None, "max_over_min": round(ratio, 4), "tol": tol, "rivals": [],
                "ok": ratio <= 1 + tol, "local_min": None, "local_max": None}
    alpha = fit_slope(xs, ys)
    local = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(len(ns) - 1) if xs[i + 1] != xs[i]]
    rv = []
    for r in rivals:
        rx = [log_cost(r, n) for n in ns]
        ra = fit_slope(rx, ys) if max(rx) - min(rx) > 1e-12 else math.inf
        rv.append({"cost": r, "alpha": round(ra, 4), "rejected": abs(ra - 1) > tol})
    ok = abs(alpha - 1) <= tol and all(r["rejected"] for r in rv)
    return {"cost": claim, "alpha": round(alpha, 4), "local_min": round(min(local), 4),
            "local_max": round(max(local), 4), "tol": tol, "rivals": rv, "ok": ok}


def best_library_fit(ns, values):
    best = None
    ys = [math.log(v) for v in values]
    for c in LIBRARY:
        try:
            xs = [log_cost(c, n) for n in ns]
        except (ValueError, OverflowError, ZeroDivisionError):
            continue
        if max(xs) - min(xs) < 1e-12:
            continue
        a = fit_slope(xs, ys)
        if best is None or abs(a - 1) < abs(best[1] - 1):
            best = (c, a)
    return {"cost": best[0], "alpha": round(best[1], 4)} if best else None


def measure_counts(cand: Candidate, side: str, ns) -> list[int]:
    fn = cand.slow if side == "slow" else cand.fast
    out = []
    for n in ns:
        rng = random.Random(f"{cand.scaling_key()}|scale|{side}|{n}")
        inst = cand.scale_instance(rng, n, side)
        ops = Ops()
        fn(inst, ops)
        out.append(max(ops.n, 1))
    return out


def run_scaling(cand: Candidate, cache: dict | None = None) -> dict | None:
    plan = cand.scaling()
    if not plan:
        return None
    key = cand.scaling_key()
    if cache is not None and key in cache:
        return dict(cache[key], cached=True)
    tol = plan.get("tolerance", 0.05)
    res = {"key": key}
    for side, other in (("slow", "fast"), ("fast", "slow")):
        p = plan[side]
        vals = measure_counts(cand, side, p["n_values"])
        rivals = list(p.get("rivals", []))
        if plan[other]["cost"] not in rivals:
            rivals.append(plan[other]["cost"])
        f = fit_claim(p["n_values"], vals, p["cost"], rivals, tol)
        f["n_values"] = list(p["n_values"])
        f["counts"] = vals
        exp_fn = getattr(cand, "expected_counts", None)
        expected = exp_fn(side, p["n_values"]) if exp_fn else None
        if expected is not None:
            f["counts_equal_spec"] = [max(e, 1) for e in expected] == vals
        f["best_library"] = best_library_fit(p["n_values"], vals)
        res[side] = f
    res["resolved"] = res["slow"]["ok"] and res["fast"]["ok"]
    if cache is not None:
        cache[key] = res
    return res


def screen(cand: Candidate, seed: int = 0, trials: int | None = None, do_scaling: bool = True,
           cache: dict | None = None) -> dict:
    t0 = time.perf_counter()
    rec = {"id": cand.id, "rule": cand.rule, "family": cand.family, "spec": cand.spec}
    try:
        rec["precondition"] = cand.precondition()
        rec["predicates"] = cand.predicates()
        rec["canonical"] = cand.canonical()
        rec["cluster"] = cand.cluster()
        deg = cand.degenerate()
    except Exception as e:  # ill-formed candidate
        rec.update(verdict="INVALID", reason=f"analysis failed: {type(e).__name__}: {e}")
        return rec
    n_inst = n_exact = 0
    closes = []
    fast_errors = 0
    for n in cand.screen_sizes:
        for t in range(cand.trials if trials is None else trials):
            rng = random.Random(f"{cand.id}|screen|{seed}|{n}|{t}")
            inst = cand.instance(rng, n)
            try:
                a = cand.slow(inst, Ops())
            except Exception as e:
                rec.update(verdict="INVALID", reason=f"slow failed at n={n}: {type(e).__name__}: {e}")
                return rec
            try:
                b = cand.fast(inst, Ops())
                ex, cl = cand.score(inst, a, b)
            except Exception:
                fast_errors += 1
                ex, cl = False, 0.0
            n_inst += 1
            n_exact += bool(ex)
            closes.append(float(cl))
    rate = n_exact / n_inst
    mean_c = sum(closes) / len(closes)
    rec.update(instances=n_inst, exact_rate=round(rate, 4), closeness_mean=round(mean_c, 4),
               closeness_min=round(min(closes), 4), fast_errors=fast_errors)
    if deg:
        rec.update(verdict="INVALID", reason=f"degenerate: {deg}")
    elif n_exact == n_inst:
        rec["verdict"] = "EXACT"
    elif rate >= NEAR_EXACT_RATE or mean_c >= NEAR_CLOSENESS:
        rec["verdict"] = "NEAR-MISS"
    else:
        rec["verdict"] = "WRONG"
    if rec["verdict"] == "EXACT" and do_scaling:
        try:
            sc = run_scaling(cand, cache)
        except Exception as e:
            sc = {"error": f"{type(e).__name__}: {e}"}
        if sc is not None:
            rec["scaling"] = sc
    rec["seconds"] = round(time.perf_counter() - t0, 3)
    return rec


# ------------------------------------------------------------------------------------------------
# Canonical forms (deduplication up to relabelling)
# ------------------------------------------------------------------------------------------------

def canon_table_exact(T) -> tuple:
    """Exact canonical form of a binary operation table under relabelling (min over all N! bijections)."""
    N = len(T)
    best = None
    for p in itertools.permutations(range(N)):
        inv = [0] * N
        for i, pi in enumerate(p):
            inv[pi] = i
        flat = tuple(p[T[inv[a]][inv[b]]] for a in range(N) for b in range(N))
        if best is None or flat < best:
            best = flat
    return best


def table_fingerprint(T) -> str:
    """Relabelling-invariant fingerprint by colour refinement. Isomorphic tables always get the same
    fingerprint; non-isomorphic tables may collide (so dedup by fingerprint can only over-merge)."""
    N = len(T)
    col = [(T[x][x] == x, sum(T[x][y] == x for y in range(N)), sum(T[y][x] == x for y in range(N)),
            sum(T[x][y] == y for y in range(N)), T[T[x][x]][x] == x) for x in range(N)]
    keys = sorted(set(col))
    col = [keys.index(c) for c in col]
    for _ in range(N):
        sig = [(col[x], tuple(sorted((col[y], col[T[x][y]], col[T[y][x]]) for y in range(N)))) for x in range(N)]
        keys = sorted(set(sig))
        new = [keys.index(s) for s in sig]
        if len(set(new)) == len(set(col)):
            col = new
            break
        col = new
    final = sorted((col[x], col[y], col[T[x][y]]) for x in range(N) for y in range(N))
    return short_hash([N, final], 16)


def relabel_table(T, perm):
    N = len(T)
    out = [[0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            out[perm[i]][perm[j]] = perm[T[i][j]]
    return out


def write_jsonl(path: Path, records) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

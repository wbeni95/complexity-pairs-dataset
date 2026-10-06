#!/usr/bin/env python3
"""Validate complexity-pair entries.

What it checks (see START_HERE.txt section 3 for the level definitions):

  always   schema, folder rules, id == folder name, README present,
           implementation files resolvable
  V1+      >= 2 implementations, >= 1 source, test harness present;
           runs every implementation on the harness battery and requires
           them to agree with each other (and with harness.check, if any)
  V2+      every implementation declares harness.scaling; with --scaling
           the runtime is measured and log(time) is fitted against
           log(cost(n)); the slope must be 1 +- tolerance
  V3       verification.proofs must cite at least one complexity proof

Levels are cumulative: an entry claiming V2 must also pass V1.

Reproducibility: instances come from per-(entry, n, trial) seeded generators, and the global `random`
module is re-seeded before every implementation call, so randomized algorithms (Miller-Rabin, the
quantum simulations, ...) give identical answers and query counts on every run of the same Python
version. Wall-clock timings are inherently not reproducible; --record stores them with the environment.

Folder rules:
  pairs/      V1+ entries, any tag except T7
  staging/    V0 entries, any tag except T7
  synthetic/  T7 (bloated) entries only -- never counted as validated

Usage:
  python tools/validate.py                 # all entries, V1 runs, no timing
  python tools/validate.py --scaling       # also re-measure V2 claims
  python tools/validate.py --probe         # also try levels above the claim
  python tools/validate.py pairs/fibonacci-naive-vs-dp
"""
from __future__ import annotations

import argparse
import ast
import copy
import gc
import importlib.metadata
import importlib.util
import itertools
import json
import math
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "schema" / "entry.schema.json"
sys.path.insert(0, str(REPO))  # lets harnesses and implementations import shared code from lib/
LOCATIONS = ("pairs", "staging", "synthetic")
LEVELS = ("V0", "V1", "V2", "V3")
LEDGER_DIR = REPO / "ledger" / "runs"

MIN_SAMPLE_S = 0.02      # each timing sample loops until it lasts this long
REPEATS = 3              # best-of-N per n
MIN_COST_SPAN = math.log(8)  # cost(n) must vary by >= 8x across n_values (timing is noisy)
MIN_COUNT_SPAN = math.log(3)  # reported operation counts are exact, so 3x is enough


# --------------------------------------------------------------------------
# Discovery / loading
# --------------------------------------------------------------------------

def discover_entries(paths: list[str] | None = None) -> list[Path]:
    """Return entry folders (each containing entry.json)."""
    if paths:
        dirs = [Path(p).resolve() for p in paths]
    else:
        dirs = []
        for loc in LOCATIONS:
            base = REPO / loc
            if base.is_dir():
                dirs.extend(sorted(d for d in base.iterdir() if (d / "entry.json").is_file()))
    return dirs


def load_entry(entry_dir: Path) -> dict:
    with open(entry_dir / "entry.json", encoding="utf-8") as f:
        return json.load(f)


def location_of(entry_dir: Path) -> str | None:
    try:
        rel = entry_dir.resolve().relative_to(REPO)
    except ValueError:
        return None
    return rel.parts[0] if rel.parts and rel.parts[0] in LOCATIONS else None


def resolve_in_repo(entry_dir: Path, rel_path: str) -> Path:
    p = (entry_dir / rel_path).resolve()
    p.relative_to(REPO)  # raises ValueError if it escapes the repo
    return p


_module_cache: dict[Path, object] = {}


def load_module(path: Path):
    if path in _module_cache:
        return _module_cache[path]
    name = "cpairs_" + "_".join(path.relative_to(REPO).with_suffix("").parts).replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    _module_cache[path] = mod
    return mod


def load_callable(entry_dir: Path, spec: str):
    file_part, func = spec.rsplit(":", 1)
    mod = load_module(resolve_in_repo(entry_dir, file_part))
    fn = getattr(mod, func, None)
    if not callable(fn):
        raise AttributeError(f"{spec}: no callable '{func}'")
    return fn


# --------------------------------------------------------------------------
# Safe evaluation of claimed cost expressions, e.g. "n**2 * log(n)"
# --------------------------------------------------------------------------

_COST_FUNCS = {
    "log": math.log,
    "log2": math.log2,
    "sqrt": math.sqrt,
    "exp": math.exp,
    "factorial": lambda x: math.factorial(int(x)),
}
_COST_CONSTS = {"e": math.e, "pi": math.pi, "phi": (1 + 5 ** 0.5) / 2}
_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
}


def eval_cost(expr: str, n: int) -> float:
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            if node.id == "n":
                return n
            if node.id in _COST_CONSTS:
                return _COST_CONSTS[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            return _BINOPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -ev(node.operand)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in _COST_FUNCS and not node.keywords):
            return _COST_FUNCS[node.func.id](*[ev(a) for a in node.args])
        raise ValueError(f"disallowed syntax in cost expression: {ast.dump(node)}")

    return ev(ast.parse(expr, mode="eval"))


# --------------------------------------------------------------------------
# V1: correctness battery
# --------------------------------------------------------------------------

def implemented(entry: dict) -> list[dict]:
    return [a for a in entry["algorithms"] if a.get("implementation")]


def run_v1(entry: dict, entry_dir: Path, rec: dict | None = None) -> list[str]:
    stats = {"instances": 0, "algorithm_runs": 0}
    errors = _run_v1(entry, entry_dir, stats)
    if rec is not None:
        rec["v1"] = {"passed": not errors, **stats, "errors": errors}
    return errors


def _run_v1(entry: dict, entry_dir: Path, stats: dict) -> list[str]:
    errors = []
    th = entry["test_harness"]
    harness = load_module(resolve_in_repo(entry_dir, th["module"]))
    algs = implemented(entry)
    fns = [load_callable(entry_dir, a["implementation"]) for a in algs]
    equal = getattr(harness, "equal", lambda a, b: a == b)
    check = getattr(harness, "check", None)
    compared: set[tuple[int, int]] = set()

    for n in th["v1_sizes"]:
        for trial in range(th.get("trials", 3)):
            rng = random.Random(f"{entry['id']}|v1|{n}|{trial}")
            inst = harness.generate(n, rng)
            stats["instances"] += 1
            snapshot = copy.deepcopy(inst)
            outs = []
            for i, (alg, fn) in enumerate(zip(algs, fns)):
                max_n = alg.get("harness", {}).get("v1_max_n")
                if max_n is not None and n > max_n:
                    continue
                random.seed(f"{entry['id']}|v1|{n}|{trial}|{alg['name']}")  # reproducible internal randomness
                out = fn(inst)
                stats["algorithm_runs"] += 1
                if inst != snapshot:
                    errors.append(f"V1: '{alg['name']}' mutated its input (n={n}); implementations must treat input as read-only")
                    return errors
                if check is not None and check(inst, out) is False:
                    errors.append(f"V1: '{alg['name']}' failed harness.check at n={n}, trial {trial}")
                outs.append((i, out))
            for (i, a), (j, b) in itertools.combinations(outs, 2):
                compared.add((i, j))
                if not equal(a, b):
                    errors.append(f"V1: '{algs[i]['name']}' and '{algs[j]['name']}' disagree at n={n}, trial {trial}: {a!r} vs {b!r}")
            if len(errors) > 5:
                return errors

    for i, j in itertools.combinations(range(len(algs)), 2):
        if (i, j) not in compared:
            errors.append(f"V1: '{algs[i]['name']}' and '{algs[j]['name']}' were never compared (raise v1_max_n or add smaller v1_sizes)")
    return errors


# --------------------------------------------------------------------------
# V2: empirical scaling
# --------------------------------------------------------------------------

def time_call(fn, inst) -> float:
    t0 = time.perf_counter()
    fn(inst)
    first = time.perf_counter() - t0
    loops = max(1, math.ceil(MIN_SAMPLE_S / max(first, 1e-9)))
    best = first if loops == 1 else math.inf
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        for _ in range(REPEATS):
            t0 = time.perf_counter()
            for _ in range(loops):
                fn(inst)
            best = min(best, (time.perf_counter() - t0) / loops)
    finally:
        if gc_was_enabled:
            gc.enable()
    return best


def fit_slope(xs: list[float], ys: list[float]) -> float:
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def run_v2(entry: dict, entry_dir: Path, verbose: bool, rec: dict | None = None) -> list[str]:
    errors = []
    measurements = rec.setdefault("v2", []) if rec is not None else []
    th = entry["test_harness"]
    harness = load_module(resolve_in_repo(entry_dir, th["module"]))
    gen = getattr(harness, "generate_scaling", harness.generate)
    for alg in implemented(entry):
        sc = alg.get("harness", {}).get("scaling")
        if not sc:
            errors.append(f"V2: '{alg['name']}' has no harness.scaling")
            continue
        fn = load_callable(entry_dir, alg["implementation"])
        ns = sc["n_values"]
        measure = sc.get("measure", "time")
        samples = sc.get("samples", 1)
        if ns != sorted(set(ns)):
            errors.append(f"V2: '{alg['name']}' n_values must be strictly increasing")
            continue
        if measure == "reported" and not hasattr(harness, "reported_cost"):
            errors.append(f"V2: '{alg['name']}' uses measure='reported' but the harness has no reported_cost(output)")
            continue
        try:
            xs = [math.log(eval_cost(sc["cost"], n)) for n in ns]
        except (ValueError, OverflowError, ZeroDivisionError) as e:
            errors.append(f"V2: '{alg['name']}' bad cost expression {sc['cost']!r}: {e}")
            continue
        constant = max(xs) - min(xs) < 1e-12
        min_span = MIN_COST_SPAN if measure == "time" else MIN_COUNT_SPAN
        if constant and measure == "time":
            errors.append(f"V2: '{alg['name']}' constant cost can only be checked with measure='reported'")
            continue
        if not constant and max(xs) - min(xs) < min_span:
            errors.append(f"V2: '{alg['name']}' n_values too narrow: cost varies < {math.exp(min_span):.0f}x, fit would be meaningless")
            continue

        t_start = time.perf_counter()
        values = []
        for n in ns:
            vals = []
            for k in range(samples):
                rng = random.Random(f"{entry['id']}|v2|{n}" + (f"|{k}" if k else ""))
                inst = gen(n, rng)
                random.seed(f"{entry['id']}|v2|{n}|{k}|{alg['name']}")  # reproducible internal randomness
                vals.append(time_call(fn, inst) if measure == "time" else float(harness.reported_cost(fn(inst))))
            values.append(sum(vals) / len(vals))
        if min(values) <= 0:
            errors.append(f"V2: '{alg['name']}' measured a non-positive value")
            continue
        tol = sc.get("tolerance", 0.25)
        if constant:
            ratio = max(values) / min(values)
            ok = ratio <= 1 + tol
            summary = f"constant cost: max/min = {ratio:.3f} (tol {tol})"
        else:
            alpha = fit_slope(xs, [math.log(v) for v in values])
            ok = abs(alpha - 1) <= tol
            summary = f"alpha={alpha:.3f} (tol {tol})"
        status = "ok" if ok else "FAIL"
        if verbose or not ok:
            unit = (lambda v: f"{v * 1e3:.3g}ms") if measure == "time" else (lambda v: f"{v:.4g}")
            detail = ", ".join(f"n={n}: {unit(v)}" for n, v in zip(ns, values))
            print(f"      V2 {alg['name']} [{measure}]: cost={sc['cost']}  {summary}  {status}  "
                  f"[{time.perf_counter() - t_start:.1f}s]  {detail}")
        measurements.append({
            "algorithm": alg["name"], "measure": measure, "cost": sc["cost"], "samples": samples,
            "n_values": ns, "values": values, "unit": "seconds" if measure == "time" else "count",
            "alpha": None if constant else alpha, "max_over_min": ratio if constant else None,
            "tolerance": tol, "passed": ok,
        })
        if not ok:
            errors.append(f"V2: '{alg['name']}' {summary} vs claimed cost {sc['cost']!r}")
    return errors


# --------------------------------------------------------------------------
# Static checks + orchestration
# --------------------------------------------------------------------------

def all_tags(entry: dict) -> set[str]:
    return {entry["pair_type"], *entry.get("secondary_tags", [])}


def tag_consistency(entry: dict) -> list[str]:
    """Tags must be backed by the algorithms (and lower bounds) the entry actually records."""
    errors = []
    tags = all_tags(entry)
    models = {a["model"] for a in entry["algorithms"]}
    classical = models & {"classical-deterministic", "classical-randomized"}
    if "T4" in tags and not {"classical-deterministic", "classical-randomized"} <= models:
        errors.append("T4 needs at least one classical-randomized and one classical-deterministic algorithm")
    if "T5" in tags and not ("quantum" in models and classical):
        errors.append("T5 needs at least one quantum and one classical algorithm")
    if "T9" in tags:
        if "quantum" not in models:
            errors.append("T9 needs a quantum algorithm")
        if not any(lb["model"] != "quantum" for lb in entry.get("lower_bounds", [])):
            errors.append("T9 needs a classical lower bound in lower_bounds (the advantage must be proven)")
    if "T7" in tags and entry["pair_type"] != "T7":
        errors.append("T7 must be the primary tag when present")
    return errors


def static_checks(entry: dict, entry_dir: Path, validator) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for err in sorted(validator.iter_errors(entry), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"schema: {loc}: {err.message}")
    if errors:
        return errors, warnings

    loc = location_of(entry_dir)
    level = LEVELS.index(entry["verification"]["level"])
    tag = entry["pair_type"]

    if entry["id"] != entry_dir.name:
        errors.append(f"id '{entry['id']}' != folder name '{entry_dir.name}'")
    if not (entry_dir / "README.md").is_file():
        errors.append("missing README.md (human-readable mirror of entry.json)")
    if tag in entry.get("secondary_tags", []):
        errors.append("secondary_tags must not repeat pair_type")
    errors += tag_consistency(entry)

    if loc is None:
        errors.append(f"entry must live under one of {LOCATIONS}")
    elif loc == "pairs":
        if level < 1:
            errors.append("pairs/ holds V1+ entries only; V0 belongs in staging/")
        if tag == "T7":
            errors.append("T7 (synthetic) entries belong in synthetic/")
    elif loc == "staging":
        if level != 0:
            errors.append("staging/ holds V0 entries only; move to pairs/ once V1 passes")
        if tag == "T7":
            errors.append("T7 (synthetic) entries belong in synthetic/")
    elif loc == "synthetic" and tag != "T7":
        errors.append("synthetic/ holds T7 entries only")

    for alg in entry["algorithms"]:
        spec = alg.get("implementation")
        if spec:
            try:
                path = resolve_in_repo(entry_dir, spec.rsplit(":", 1)[0])
                if not path.is_file():
                    errors.append(f"implementation not found: {spec}")
            except ValueError:
                errors.append(f"implementation path escapes the repo: {spec}")

    if level >= 1:
        if len(entry["sources"]) < 1:
            errors.append("V1+ requires at least one source")
        if "test_harness" not in entry:
            errors.append("V1+ requires test_harness")
        if len(implemented(entry)) < 2:
            errors.append("V1+ requires at least two implemented algorithms")
    if level >= 2:
        for alg in implemented(entry):
            if not alg.get("harness", {}).get("scaling"):
                errors.append(f"V2+ requires harness.scaling for '{alg['name']}'")
    if level >= 3 and not entry["verification"].get("proofs"):
        errors.append("V3 requires verification.proofs (cited complexity proofs)")
    if level == 0 and not entry["sources"]:
        warnings.append("no sources yet: even V0 should cite where the claim comes from")
    return errors, warnings


def validate_entry(entry_dir: Path, validator, args, recorder: list | None = None) -> bool:
    rel = entry_dir.relative_to(REPO) if entry_dir.is_relative_to(REPO) else entry_dir
    try:
        entry = load_entry(entry_dir)
    except (OSError, json.JSONDecodeError) as e:
        print(f"[FAIL] {rel}\n      cannot read entry.json: {e}")
        return False

    errors, warnings = static_checks(entry, entry_dir, validator)
    claimed_label = entry.get("verification", {}).get("level") if isinstance(entry, dict) else None
    claimed = LEVELS.index(claimed_label) if claimed_label in LEVELS else 0
    can_run = not errors and "test_harness" in entry and len(implemented(entry)) >= 2
    achieved = 0
    notes = []
    rec: dict = {"path": Path(rel).as_posix(), "id": entry.get("id"), "claimed": claimed_label}

    if can_run and (claimed >= 1 or args.probe) and not args.static:
        try:
            v1_errors = run_v1(entry, entry_dir, rec)
        except Exception as e:  # noqa: BLE001 -- report any crash in contributed code
            v1_errors = [f"V1: crashed: {type(e).__name__}: {e}"]
        if not v1_errors:
            achieved = 1
        if claimed >= 1:
            errors += v1_errors

        want_v2 = args.scaling and (claimed >= 2 or args.probe)
        if achieved >= 1 and want_v2:
            try:
                v2_errors = run_v2(entry, entry_dir, args.verbose, rec)
            except Exception as e:  # noqa: BLE001
                v2_errors = [f"V2: crashed: {type(e).__name__}: {e}"]
            if not v2_errors:
                achieved = 2
            if claimed >= 2:
                errors += v2_errors
        elif claimed >= 2 and not errors:
            notes.append("V2 claim not re-measured (run with --scaling)")
            achieved = claimed
        if achieved >= 2 and entry["verification"].get("proofs"):
            achieved = 3
    elif not errors:
        achieved = claimed

    status = "FAIL" if errors else "OK"
    line = f"[{status}] {rel}  claimed {claimed_label or '?'}"
    if not errors and args.probe and achieved > claimed:
        line += f"  (passes {LEVELS[achieved]} -- consider raising the claim)"
    print(line)
    for msg in errors:
        print(f"      error: {msg}")
    for msg in warnings + notes:
        print(f"      note: {msg}")
    if recorder is not None:
        rec.update(status=status, achieved=None if errors else LEVELS[achieved],
                   errors=errors, notes=warnings + notes)
        recorder.append(rec)
    return not errors


def run_metadata(args) -> dict:
    """Everything needed to interpret (and try to reproduce) a recorded run."""
    def git(*cmd):
        try:
            out = subprocess.run(["git", *cmd], cwd=REPO, capture_output=True, text=True, timeout=20)
            return out.stdout.strip() if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None
    status = git("status", "--porcelain")
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty": None if status is None else bool(status),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "jsonschema": importlib.metadata.version("jsonschema"),
        "arguments": {"paths": args.paths, "scaling": args.scaling, "probe": args.probe, "static": args.static},
        "timing_parameters": {"min_sample_s": MIN_SAMPLE_S, "repeats": REPEATS,
                              "statistic": "per n: best of `repeats` samples, each the mean over a loop lasting >= min_sample_s"},
    }


def write_record(meta: dict, records: list) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.fromisoformat(meta["timestamp_utc"]).strftime("%Y%m%dT%H%M%SZ")
    path = LEDGER_DIR / f"{stamp}.json"
    doc = {"run": meta,
           "summary": {"entries": len(records), "ok": sum(r["status"] == "OK" for r in records)},
           "entries": records}
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to a legacy code page
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="entry folders (default: all)")
    ap.add_argument("--scaling", action="store_true", help="measure runtimes for V2 claims")
    ap.add_argument("--probe", action="store_true", help="also try V1/V2 above the claimed level")
    ap.add_argument("--static", action="store_true", help="schema and folder rules only, run nothing")
    ap.add_argument("-v", "--verbose", action="store_true", help="print every scaling measurement")
    ap.add_argument("--record", action="store_true",
                    help="write every result and measurement to ledger/runs/<UTC timestamp>.json")
    args = ap.parse_args(argv)

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("jsonschema is required: pip install -r requirements.txt", file=sys.stderr)
        return 2
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        validator = Draft202012Validator(json.load(f))

    entries = discover_entries(args.paths)
    if not entries:
        print("no entries found")
        return 1
    recorder: list | None = [] if args.record else None
    meta = run_metadata(args) if args.record else None
    results = [validate_entry(d, validator, args, recorder) for d in entries]
    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} entries OK")
    if args.record:
        print(f"evidence recorded: {write_record(meta, recorder).relative_to(REPO).as_posix()}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

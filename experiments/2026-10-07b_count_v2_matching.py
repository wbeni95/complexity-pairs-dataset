"""Count-based V2 for pairs/bipartite-matching-kuhn-vs-hopcroft-karp: exact edge scans on G_k, fits, rivals.

Question: with edge scans counted by the harness (CountingNeighbours wraps every adjacency list of the
adversarial family G_k; the implementations are unchanged), do the counts fit n^3 (Kuhn) and n^2.5
(Hopcroft-Karp) as functions of n = V = 4k^2 + k, tightly enough to reject Kuhn vs n^2.5 (which the timing
fit did not reject, RL-030) and Hopcroft-Karp vs n^2 and n^3?

Cross-check: the harness counts must equal, value for value, the counts of the instrumented COPIES of the
two implementations in experiments/2026-10-07_bipartite_matching_counts.py (kuhn_counts, hk_counts), which
count the same quantity ("adjacency-list entries scanned") by explicit counters.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_count_v2_matching.py
Deterministic (G_k is deterministic; validator seeds are irrelevant here).

Outcome (run 2026-10-06 local date, Python 3.14.2; deterministic, identical on rerun):
  * the harness counts equal the instrumented copies' counts for every k (Kuhn k = 3..11, HK k = 4..15);
    HK ran exactly k + 1 phases for every k = 4..15.
  * Kuhn, k = 3..11: 987 ... 2088999 scans (0.1431-0.1480 V E); alpha 1.0055 vs n^3; rival n^2.5 1.2066
    (rejected); n^3 log n 0.9412 (rejected); diagnostic resolved. Over k = 5..11 alpha 1.0081.
  * HK, k = 4..15: 4572 ... 3116527 scans (1.0153-1.0501 E sqrt V); alpha 1.0041 vs n^2.5; rivals n^2
    1.2551, n^3 0.8367 (rejected); diagnostic 0.9360 / 1.0828 (resolved).
  Written to entry.json: the existing n_values, tolerance 0.03.

Check lines (harness counts equal the copies' counts; HK phases k + 1) start with [PASS] or [FAIL]; the run ends
with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1). The ratios, fits, rivals and slopes
are reported, not checked.
"""
import ast
import importlib.util
import types
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("cv2h", HERE / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

# That script has no __main__ guard, so only its two counting functions are taken from its source (AST),
# unchanged, and executed in a fresh namespace; its module-level experiment is not run.
_src = (HERE / "2026-10-07_bipartite_matching_counts.py").read_text(encoding="utf-8")
_tree = ast.parse(_src)
_mod = ast.Module(body=[n for n in _tree.body if isinstance(n, ast.FunctionDef)
                        and n.name in ("kuhn_counts", "hk_counts")], type_ignores=[])
_ns = {}
exec(compile(_mod, "2026-10-07_bipartite_matching_counts.py", "exec"), _ns)
C = types.SimpleNamespace(**_ns)

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

EID = "bipartite-matching-kuhn-vs-hopcroft-karp"
KUHN = "Kuhn's augmenting paths (one DFS per left vertex)"
HK = "Hopcroft-Karp"
_, entry, harness = H.entry_and_harness(EID)


def n_of(k):
    return 4 * k * k + k


ks_k = list(range(3, 12))
ks_h = list(range(4, 16))
k_ns = [n_of(k) for k in ks_k]
h_ns = [n_of(k) for k in ks_h]

kc = H.counts(EID, KUHN, k_ns, 1)
hc = H.counts(EID, HK, h_ns, 1)

print("== cross-check against the instrumented copies (experiments/2026-10-07_bipartite_matching_counts.py) ==")
ok = True
for k, n, v in zip(ks_k, k_ns, kc):
    size, scans = C.kuhn_counts(harness.adversarial(k))
    ok &= scans == int(v)
    E = 2 * k ** 4 + k * k
    check_line(scans == int(v), f"  Kuhn k={k} V={n}: harness {int(v)}, copy {scans}, /(V E) = {v / (n * E):.4f}")
for k, n, v in zip(ks_h, h_ns, hc):
    size, scans, phases = C.hk_counts(harness.adversarial(k))
    ok &= scans == int(v)
    E = 2 * k ** 4 + k * k
    check_line(scans == int(v) and phases == k + 1,
               f"  HK   k={k} V={n}: harness {int(v)}, copy {scans}, phases {phases} (k+1 = {k + 1}), "
               f"/(E sqrt V) = {v / (E * math.sqrt(n)):.4f}")
check_line(ok, "  all equal:", ok)

print("\n== Kuhn (claim n**3) ==")
for tol in (0.05, 0.03):
    H.report(f"k=3..11 tol={tol}", k_ns, kc, "n**3", ["n**2.5", "n**3*log(n)"], tol)
H.report("k=5..11 tol=0.03", k_ns[2:], kc[2:], "n**3", ["n**2.5"], 0.03)

print("\n== Hopcroft-Karp (claim n**2.5) ==")
for tol in (0.05, 0.03):
    H.report(f"k=4..15 tol={tol}", h_ns, hc, "n**2.5", ["n**2", "n**3"], tol)

finish_checks()


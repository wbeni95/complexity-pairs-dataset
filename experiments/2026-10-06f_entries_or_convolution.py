"""Experiment (research/2026-10-06f_new_entries.md): OR-convolution entry, pairs/or-convolution-naive-vs-zeta-mobius.

What it checks (deterministic; no timing):
  1. Ring-operation counts: naive exactly 2 * 4^n for n = 0..10, zeta-Moebius exactly (3n + 2) * 2^(n-1) for
     n = 1..16 (n = 0: 1 multiplication).
  2. Oracle control on seeded V1-style instances (n = 0..11): check() accepts the correct output and rejects
       plus1  - one entry increased by 1;
       andc   - the AND convolution of the same inputs (when it differs);
       xorc   - the XOR convolution of the same inputs (when it differs);
       nomob  - the pointwise product of the zeta transforms, i.e. the Moebius step left out (when it differs);
       short  - the output with its last entry removed.
  3. AND convolution as the complement mirror: h_AND[S] = h_OR'[~S] where f'[X] = f[~X], g'[X] = g[~X]
     (A & B = S iff ~A | ~B = ~S), checked for both implementations against a naive AND convolution on n = 0..9.
  4. Fits (validator formula, tolerance 0.02), with rivals.

Run from the repository root:  .venv/Scripts/python.exe experiments/2026-10-06f_entries_or_convolution.py
RESULT (2026-10-06): counts exact; oracle control accepts all correct and rejects all wrong outputs; the mirror holds
on every instance (tallies printed and copied into the report).

Check lines (1, zeta-Moebius == naive on the control instances, 2 with every kind tested at least once and the
published totals 86 correct and 383 wrong, 3) start with [PASS] or [FAIL]; the run ends with
ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1). The counts at the V2 sizes and the fits (4)
are reported, not checked.
"""
import importlib.util
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "or-convolution-naive-vs-zeta-mobius"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "orc_harness")
N = load(ENTRY / "implementations" / "naive.py", "orc_naive")
Z = load(ENTRY / "implementations" / "zeta_mobius.py", "orc_zeta")

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


def fit_slope(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


def alpha(cost, ns, vals):
    return fit_slope([math.log(cost(n)) for n in ns], [math.log(v) for v in vals])


def count(fn, n):
    inst = H.generate_scaling(n, random.Random(f"orc-exp|{n}"))
    fn(inst)
    return H.reported_cost(None)


def conv(f, g, op):
    h = [0] * len(f)
    for a in range(len(f)):
        for b in range(len(f)):
            h[op(a, b)] += f[a] * g[b]
    return h


def main():
    naive = {n: count(N.or_convolution_naive, n) for n in range(0, 11)}
    fast = {n: count(Z.or_convolution_zeta_mobius, n) for n in range(0, 17)}
    ok = all(naive[n] == 2 * 4 ** n for n in naive)
    check_line(ok, "1. naive = 2 * 4^n for n = 0..10:", ok)
    ok = all(2 * fast[n] == (3 * n + 2) * 2 ** n for n in range(1, 17))
    check_line(ok, "   zeta-Moebius = (3n+2) 2^(n-1) for n = 1..16:", ok, "| n = 0:", fast[0])
    print("   naive at V2 sizes:", {n: naive[n] for n in (3, 4, 5, 6, 7, 8)})
    print("   fast at V2 sizes:", {n: fast[n] for n in (4, 6, 8, 10, 12, 14, 16)})

    kinds = ("correct", "plus1", "andc", "xorc", "nomob", "short")
    tally = {k: [0, 0] for k in kinds}
    fast_differs = []
    for n in range(0, 12):
        for t in range(8 if n <= 9 else 3):
            f, g = H.generate(n, random.Random(f"orc-control|{n}|{t}"))
            h = Z.or_convolution_zeta_mobius((f, g))
            if n <= 9 and h != N.or_convolution_naive((f, g)):
                fast_differs.append((n, t))
            tally["correct"][0] += 1
            tally["correct"][1] += H.check((f, g), h) is True
            i = random.Random(f"orc-plus|{n}|{t}").randrange(len(h))
            wrongs = [("plus1", [x + (j == i) for j, x in enumerate(h)])]
            if n <= 9:
                for kind, op in (("andc", lambda a, b: a & b), ("xorc", lambda a, b: a ^ b)):
                    w = conv(f, g, op)
                    if w != h:
                        wrongs.append((kind, w))
            zf, zg = Z._zeta(f), Z._zeta(g)
            nomob = [x * y for x, y in zip(zf, zg)]
            if nomob != h:
                wrongs.append(("nomob", nomob))
            if len(h) > 1:
                wrongs.append(("short", h[:-1]))
            for kind, w in wrongs:
                tally[kind][0] += 1
                tally[kind][1] += H.check((f, g), w) is False
    check_line(not fast_differs, "   zeta-Moebius == naive on every control instance with n <= 9:",
               not fast_differs if not fast_differs else f"False, differs at (n, t) = {fast_differs[:5]}")
    ok = tally["correct"][0] == tally["correct"][1] and all(t[0] == t[1] and t[0] > 0 for k, t in tally.items()
                                                             if k != "correct")
    ok = ok and tally["correct"][0] == 86 and sum(t[0] for k, t in tally.items() if k != "correct") == 383
    check_line(ok, "2. oracle control [tested, rejected; correct: tested, accepted]:", tally, "-> all as expected:", ok)

    good = total = 0
    for n in range(0, 10):
        for t in range(5):
            f, g = H.generate(n, random.Random(f"orc-and|{n}|{t}"))
            full = (1 << n) - 1
            fc = tuple(f[full ^ x] for x in range(1 << n))
            gc = tuple(g[full ^ x] for x in range(1 << n))
            want = conv(f, g, lambda a, b: a & b)
            for impl in (N.or_convolution_naive, Z.or_convolution_zeta_mobius):
                hc = impl((fc, gc))
                total += 1
                good += [hc[full ^ s] for s in range(1 << n)] == want
    check_line(good == total,
               f"3. AND convolution via complement mirror: correct on {good} of {total} (instance, implementation) pairs")

    nn = [3, 4, 5, 6, 7, 8]
    vn = [naive[n] for n in nn]
    nf = [4, 6, 8, 10, 12, 14, 16]
    vf = [fast[n] for n in nf]
    print("4. naive fits: 2*4^n", round(alpha(lambda n: 4 ** n, nn, vn), 4),
          "| rivals n*2^n", round(alpha(lambda n: n * 2 ** n, nn, vn), 4),
          "3^n", round(alpha(lambda n: 3 ** n, nn, vn), 4), "n*4^n", round(alpha(lambda n: n * 4 ** n, nn, vn), 4))
    print("   fast fits: (3n+2)2^n", round(alpha(lambda n: (3 * n + 2) * 2 ** n, nf, vf), 4),
          "| rivals 2^n", round(alpha(lambda n: 2 ** n, nf, vf), 4),
          "n^2*2^n", round(alpha(lambda n: n * n * 2 ** n, nf, vf), 4),
          "3^n", round(alpha(lambda n: 3 ** n, nf, vf), 4),
          "| bare n*2^n (info)", round(alpha(lambda n: n * 2 ** n, nf, vf), 4))
    finish_checks()


if __name__ == "__main__":
    main()

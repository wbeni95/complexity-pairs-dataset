"""Experiment (research/2026-10-06f_new_entries.md): Boolean matrix multiplication entry,
pairs/boolean-matrix-multiplication-naive-vs-strassen.

What it checks (deterministic; no timing):
  1. Product counts on the V2 instances: schoolbook exactly n^3 ANDs, Strassen exactly 7^(log2(n/16)) * 16^3
     multiplications, for n = 16, 32, 64, 128 (and, for information, the padded counts at n = 17, 40).
  2. Oracle control on seeded V1-style instances (n = 1..40): check() accepts the correct product and rejects
       flip   - one entry flipped;
       count  - the integer product AB itself (entries up to n), when it differs from the Boolean product;
       transp - the transposed product, when it differs;
       order  - the product BA, when it differs;
       shape  - the product with its last row removed.
  3. Negative controls: the same Strassen code run directly on Boolean values, with
       (a) + and - both read as OR and * as AND (the semiring has no subtraction), and
       (b) + and - read as XOR and * as AND (Strassen over GF(2), which computes the product mod 2);
     both disagree with the Boolean product on most random instances above the cutoff, which is why the
     algorithm embeds 0/1 into the integers (Fischer-Meyer, Munro).
  4. Fits (validator formula, tolerance 0.02), with rivals.

Run from the repository root:  .venv/Scripts/python.exe experiments/2026-10-06f_entries_boolean_matmul.py
RESULT (2026-10-06): counts exact; oracle control accepts all correct and rejects all wrong outputs; both
negative controls fail on most instances (tallies printed and copied into the report).

Check lines (1, Strassen == schoolbook on the control instances, 2 with every kind tested at least once and the
published totals 240 correct and 906 wrong, 3 with the published tallies 25 of 40 and 33 of 40) start with [PASS] or
[FAIL]; the run ends with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1). The fits (4) are
reported, not checked.
"""
import importlib.util
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "boolean-matrix-multiplication-naive-vs-strassen"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "bmm_harness")
N = load(ENTRY / "implementations" / "naive.py", "bmm_naive")
S = load(ENTRY / "implementations" / "strassen_over_integers.py", "bmm_strassen")

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
    inst = H.generate_scaling(n, random.Random(f"bmm-exp|{n}"))
    fn(inst)
    return H.reported_cost(None)


class OrAnd:
    """Boolean value with + and - both read as OR, * as AND (no additive inverse)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def _o(self, x):
        return x.v if isinstance(x, OrAnd) else x

    def __add__(self, o):
        return OrAnd(self.v | self._o(o))

    __radd__ = __sub__ = __rsub__ = __add__

    def __mul__(self, o):
        return OrAnd(self.v & self._o(o))

    __rmul__ = __mul__

    def __gt__(self, o):
        return self.v > self._o(o)


class Gf2(OrAnd):
    """+ and - read as XOR, * as AND: arithmetic modulo 2."""

    def __add__(self, o):
        return Gf2(self.v ^ self._o(o))

    __radd__ = __sub__ = __rsub__ = __add__

    def __mul__(self, o):
        return Gf2(self.v & self._o(o))

    __rmul__ = __mul__


def main():
    ns = [16, 32, 64, 128]
    naive = {n: count(N.bmm_naive, n) for n in ns + [17, 40]}
    stras = {n: count(S.bmm_strassen, n) for n in ns + [17, 40]}
    ok = all(naive[n] == n ** 3 for n in naive)
    check_line(ok, "1. schoolbook = n^3:", ok, {n: naive[n] for n in ns})
    ok = all(stras[n] == 7 ** (n.bit_length() - 5) * 16 ** 3 for n in ns)
    check_line(ok, "   Strassen = 7^(log2(n/16)) 16^3:", ok,
               {n: stras[n] for n in ns}, "| padded n = 17, 40:", stras[17], stras[40])

    kinds = ("correct", "flip", "count", "transp", "order", "shape")
    tally = {k: [0, 0] for k in kinds}
    strassen_differs = []
    for n in list(range(1, 21)) + [24, 31, 33, 40]:
        for t in range(10):
            A, B = H.generate(n, random.Random(f"bmm-control|{n}|{t}"))
            C = N.bmm_naive((A, B))
            if C != S.bmm_strassen((A, B)):
                strassen_differs.append((n, t))
            tally["correct"][0] += 1
            tally["correct"][1] += H.check((A, B), C) is True
            rng = random.Random(f"bmm-flip|{n}|{t}")
            i, j = rng.randrange(n), rng.randrange(n)
            wrongs = [("flip", [[x ^ (r == i and c == j) for c, x in enumerate(row)] for r, row in enumerate(C)]),
                      ("shape", C[:-1])]
            P = [[sum(A[r][k] * B[k][c] for k in range(n)) for c in range(n)] for r in range(n)]
            if P != C:
                wrongs.append(("count", P))
            T = [list(col) for col in zip(*C)]
            if T != C:
                wrongs.append(("transp", T))
            BA = N.bmm_naive((B, A))
            if BA != C:
                wrongs.append(("order", BA))
            for kind, w in wrongs:
                tally[kind][0] += 1
                tally[kind][1] += H.check((A, B), w) is False
    check_line(not strassen_differs, "   Strassen == schoolbook on every control instance (n = 1..20, 24, 31, 33, 40):",
               not strassen_differs if not strassen_differs else f"False, differs at (n, t) = {strassen_differs[:5]}")
    ok = tally["correct"][0] == tally["correct"][1] and all(t[0] == t[1] and t[0] > 0 for k, t in tally.items()
                                                             if k != "correct")
    ok = ok and tally["correct"][0] == 240 and sum(t[0] for k, t in tally.items() if k != "correct") == 906
    check_line(ok, "2. oracle control [tested, rejected; correct: tested, accepted]:", tally, "-> all as expected:", ok)

    for label, cls in (("OR/OR/AND", OrAnd), ("XOR/XOR/AND (GF(2))", Gf2)):
        wrong = total = 0
        for n in (17, 32, 48, 64):
            for t in range(10):
                A, B = H.generate(n, random.Random(f"bmm-neg|{n}|{t}"))
                Aw = tuple(tuple(cls(x) for x in row) for row in A)
                Bw = tuple(tuple(cls(x) for x in row) for row in B)
                out = S.bmm_strassen((Aw, Bw))
                total += 1
                wrong += H.check((A, B), out) is False
        published = {"OR/OR/AND": 25, "XOR/XOR/AND (GF(2))": 33}[label]
        check_line(wrong == published and total == 40,
                   f"3. negative control, Strassen code on Booleans with {label}: wrong on {wrong} of {total} instances")

    vn = [naive[n] for n in ns]
    vs = [stras[n] for n in ns]
    print("4. fits: schoolbook vs n^3:", round(alpha(lambda n: n ** 3, ns, vn), 4),
          "| rival n^log2(7):", round(alpha(lambda n: n ** math.log2(7), ns, vn), 4),
          "| rival n^2:", round(alpha(lambda n: n ** 2, ns, vn), 4))
    print("   Strassen vs n^log2(7):", round(alpha(lambda n: n ** math.log2(7), ns, vs), 4),
          "| rival n^3:", round(alpha(lambda n: n ** 3, ns, vs), 4),
          "| rival n^2:", round(alpha(lambda n: n ** 2, ns, vs), 4))
    finish_checks()


if __name__ == "__main__":
    main()

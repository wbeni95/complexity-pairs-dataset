#!/usr/bin/env python3
"""Checks for pairs/cayley-dickson-powering-repeated-vs-square-multiply (deterministic, under a minute).

Every number quoted in the entry's README and verification field is printed here. The basis-table product and the
remainder formula used below are written independently of the implementations' recursive product.

Sections (p = 2^61 - 1 unless stated):
  1  the table product (e_i e_j = s(i, j) e_(i xor j)) equals the recursive product, m = 0..5.
  2  Lemma 1 and Lemma 2 mod p: x + conj(x) = t 1, x conj(x) = conj(x) x = n 1; x^2 = t x - n 1; span{1, x} closed,
     commutative, associative; m = 0..5.
  3  Lemma 4 with every product written in PROOFS.md section 7: (e_1 e_2) e_4 = e_7 = -e_1 (e_2 e_4) for m = 3, 4, 5;
     x = e_1 + e_10, y = e_4: x x = -2, x y = e_5 - e_14, (x x) y = -2 e_4 != x (x y) = -2 e_4 - 2 e_15, m = 4, 5.
  4  Lemma 2: random bracketings of e copies of x equal the left power x^e, e <= 12, m = 3, 4, 5.
  5  Proposition S and the oracle: both algorithms = left power (table product) = remainder formula, on extra
     instances (m = 3, 4, 5, e <= 64 and random large e against the remainder formula).
  6  exact counts: residue multiplications = 4^m (e - 1) and 4^m (floor(log2 e) + popcount(e) - 1), e = 1..300
     (m = 3) and e = 1..100 (m = 4, 5), and square-and-multiply at large e; one product = 4^m residue multiplications for m = 0..5.
  7  integer growth example: x = 1 + e_1 over Z, x^e = alpha + beta e_1 with alpha^2 + beta^2 = 2^e and
     2^((e-1)/2) <= max(|alpha|, |beta|) <= 2^(e/2), e <= 200.
  8  oracle control: wrong outputs rejected, true outputs accepted.
  9  the remaining facts of PROOFS.md: the numbers of multiplications, additions and subtractions, negations and
     reductions in one product (m = 0..6); the four doubling rules on random pairs (m = 1..5); bin(e)[3:] lists the
     n - 1 digits after the leading one (e = 1..4096); binary powering with the para-product x * y = conj(x) conj(y)
     gives B(4) = -4 while the left power is -4 e_1, for x = 1 + e_1 mod p (m = 1..5); the recursion depth of the
     product (m = 0..5); the working memory of square-and-multiply (n = 64..8192); x^2 = 0 for the generator's
     isotropic elements.
Output: one [PASS] / [FAIL] line per check; the run ends with ALL CHECKS PASSED (exit code 0) or a list of the failed
checks (exit code 1).
Usage (from the repository root): python experiments/2026-10-07_cayley_dickson_powering_checks.py
"""
import importlib.util
import random
import sys
import time
import tracemalloc
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "cayley-dickson-powering-repeated-vs-square-multiply"
FAIL = []


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "cd_powering_harness")
REP = load(ENTRY / "implementations" / "repeated.py", "cd_powering_repeated")
SQM = load(ENTRY / "implementations" / "square_multiply.py", "cd_powering_square")
P = H.P


def report(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAIL.append(label)


def tmul(x, y, p=P):
    return H.table_mul(x, y, p)


def conj(x, p=P):
    return REP.cd_conj(x, p)


def basis(dim, i):
    return tuple(1 if k == i else 0 for k in range(dim))


def add(x, y, p=P):
    return tuple((a + b) % p for a, b in zip(x, y))


def scale(s, x, p=P):
    return tuple(s * a % p for a in x)


def unit(dim):
    return basis(dim, 0)


def rand_elem(rng, dim):
    return tuple(rng.randrange(P) for _ in range(dim))


def left_power(x, e):
    r = x
    for _ in range(e - 1):
        r = tmul(r, x)
    return r


def section1(rng):
    bad = tot = 0
    for m in range(6):
        dim = 1 << m
        for _ in range(40):
            x, y = rand_elem(rng, dim), rand_elem(rng, dim)
            tot += 1
            bad += REP.cd_mul(x, y, P) != tmul(x, y) or SQM.cd_mul(x, y, P) != tmul(x, y)
    report("1 table product = recursive product of both implementations, m = 0..5", bad == 0, f"{tot - bad}/{tot}")


def section2(rng):
    bad = tot = 0
    for m in range(6):
        dim = 1 << m
        one = unit(dim)
        for _ in range(15):
            x = rand_elem(rng, dim)
            t, n = 2 * x[0] % P, sum(v * v for v in x) % P
            xb = conj(x)
            ok = add(x, xb) == scale(t, one) and tmul(x, xb) == scale(n, one) == tmul(xb, x)
            ok &= tmul(x, x) == add(scale(t, x), scale(-n, one))
            us = [add(scale(rng.randrange(P), one), scale(rng.randrange(P), x)) for _ in range(3)]
            u, v, w = us
            uv = tmul(u, v)
            k = next((i for i in range(1, dim) if x[i]), None)
            if k is not None:
                beta = uv[k] * pow(x[k], P - 2, P) % P
                alpha = (uv[0] - beta * x[0]) % P
                ok &= add(scale(alpha, one), scale(beta, x)) == uv
            ok &= uv == tmul(v, u) and tmul(tmul(u, v), w) == tmul(u, tmul(v, w))
            tot += 1
            bad += not ok
    report("2 Lemma 1 and Lemma 2 mod p, m = 0..5", bad == 0, f"{tot - bad}/{tot} random elements")


def section3(rng):
    for m in (3, 4, 5):
        dim = 1 << m
        e_ = lambda i: basis(dim, i)  # noqa: E731
        neg = lambda v: scale(P - 1, v)  # noqa: E731
        a, b, c = e_(1), e_(2), e_(4)
        lhs, rhs = tmul(tmul(a, b), c), tmul(a, tmul(b, c))
        steps = (tmul(e_(1), e_(2)) == e_(3) and tmul(e_(3), e_(4)) == e_(7) and tmul(e_(2), e_(4)) == e_(6)
                 and tmul(e_(1), e_(6)) == neg(e_(7)))
        steps &= (tmul(e_(2), e_(1)) == neg(e_(3)) and tmul(e_(1), e_(4)) == e_(5)
                  and tmul(e_(1), e_(5)) == neg(e_(4)) and tmul(e_(2), e_(5)) == e_(7)
                  and tmul(e_(6), e_(1)) == e_(7) and tmul(e_(6), e_(2)) == e_(4))
        report(f"3 m={m}: e_1 e_2 = e_3, e_2 e_1 = -e_3, e_3 e_4 = e_7, e_2 e_4 = e_6, e_1 e_6 = -e_7, e_1 e_4 = e_5, "
               "e_1 e_5 = -e_4, e_2 e_5 = e_7, e_6 e_1 = e_7, e_6 e_2 = e_4; (e_1 e_2) e_4 = e_7 and "
               "e_1 (e_2 e_4) = -e_7 (mod p)", steps and lhs == e_(7) and rhs == neg(e_(7)))
    for m in (4, 5):
        dim = 1 << m
        x = add(basis(dim, 1), basis(dim, 10))
        y = basis(dim, 4)
        l, r = tmul(tmul(x, x), y), tmul(x, tmul(x, y))
        nz = lambda v: [(i, c if c < P // 2 else c - P) for i, c in enumerate(v) if c]  # noqa: E731
        e_ = lambda i: basis(dim, i)  # noqa: E731
        neg = lambda v: scale(P - 1, v)  # noqa: E731
        vals = (tmul(x, x) == scale(P - 2, unit(dim)) and tmul(e_(1), e_(4)) == e_(5)
                and tmul(e_(10), e_(4)) == neg(e_(14)) and tmul(x, y) == add(e_(5), neg(e_(14)))
                and tmul(e_(1), e_(5)) == neg(e_(4)) and tmul(e_(1), e_(14)) == e_(15)
                and tmul(e_(10), e_(5)) == neg(e_(15)) and tmul(e_(10), e_(14)) == e_(4)
                and l == scale(P - 2, e_(4)) and r == add(scale(P - 2, e_(4)), scale(P - 2, e_(15))))
        report(f"3 m={m}: x = e_1 + e_10, y = e_4: x x = -2, x y = e_5 - e_14, (x x) y = -2 e_4 != "
               "x (x y) = -2 e_4 - 2 e_15 (and the basis products of PROOFS.md section 7)", vals and l != r,
               f"(x x) y = {nz(l)}, x (x y) = {nz(r)}")


def random_bracketing(x, e, rng):
    if e == 1:
        return x
    i = rng.randint(1, e - 1)
    return tmul(random_bracketing(x, i, rng), random_bracketing(x, e - i, rng))


def section4(rng):
    bad = tot = 0
    for m in (3, 4, 5):
        dim = 1 << m
        for _ in range(4):
            x = rand_elem(rng, dim)
            for e in range(1, 13):
                lp = left_power(x, e)
                for _ in range(3):
                    tot += 1
                    bad += random_bracketing(x, e, rng) != lp
    report("4 random bracketings of e copies of x = left power, e <= 12, m = 3, 4, 5", bad == 0, f"{tot - bad}/{tot}")


def section5(rng):
    bad = tot = 0
    for m in (3, 4, 5):
        dim = 1 << m
        for _ in range(4):
            x = rand_elem(rng, dim)
            lp = x
            for e in range(1, 65):
                if e > 1:
                    lp = tmul(lp, x)
                inst = (x, e, P)
                tot += 1
                bad += not (REP.cd_power_repeated(inst) == SQM.cd_power_square_multiply(inst) == lp
                            == H.quadratic_power(x, e, P))
    report("5 repeated = square-and-multiply = left power (table product) = remainder formula, e <= 64, m = 3, 4, 5",
           bad == 0, f"{tot - bad}/{tot}")
    bad = tot = 0
    for m in (3, 4, 5):
        dim = 1 << m
        for _ in range(5):
            x = rand_elem(rng, dim)
            e = rng.getrandbits(200) | (1 << 199)
            tot += 1
            bad += SQM.cd_power_square_multiply((x, e, P)) != H.quadratic_power(x, e, P)
    report("5 square-and-multiply = remainder formula for random 200-bit e, m = 3, 4, 5", bad == 0, f"{tot - bad}/{tot}")


def counted(fn, x, e):
    H._ops["mul"] = 0
    fn((tuple(H.CountingInt(v) for v in x), e, P))
    return H._ops["mul"]


def section6(rng):
    for m in range(6):
        dim = 1 << m
        x, y = rand_elem(rng, dim), rand_elem(rng, dim)
        H._ops["mul"] = 0
        REP.cd_mul(tuple(H.CountingInt(v) for v in x), tuple(H.CountingInt(v) for v in y), P)
        report(f"6 one product in dimension 2^{m} makes 4^{m} = {4 ** m} residue multiplications",
               H._ops["mul"] == 4 ** m)
    bad = 0
    for m in (3, 4, 5):
        dim = 1 << m
        x = rand_elem(rng, dim)
        for e in range(1, (301 if m == 3 else 101)):
            r = counted(REP.cd_power_repeated, x, e)
            s = counted(SQM.cd_power_square_multiply, x, e)
            bad += r != 4 ** m * (e - 1) or s != 4 ** m * (e.bit_length() - 1 + bin(e).count("1") - 1)
    report("6 exact counts 4^m (e - 1) and 4^m (floor(log2 e) + popcount(e) - 1), e = 1..300 (m = 3), 1..100 (m = 4, 5)",
           bad == 0, f"{500 - bad}/500 exponents, two counts each")
    bad = 0
    for n in (16, 32, 64, 128, 256, 512, 1024):
        e = (1 << n) - 1
        x = rand_elem(rng, 8)
        bad += counted(SQM.cd_power_square_multiply, x, e) != 128 * (n - 1)
        e2 = rng.getrandbits(n - 1) | (1 << (n - 1))
        bad += counted(SQM.cd_power_square_multiply, x, e2) != 64 * (n - 1 + bin(e2).count("1") - 1)
    report("6 square-and-multiply at e = 2^n - 1 and random n-bit e, n = 16..1024 (octonions)", bad == 0,
           f"{14 - bad}/14 counts")
    v2 = {"repeated": [], "square": []}
    for n in (6, 7, 8, 9, 10, 11):
        inst = H.generate_scaling(n, random.Random(f"v2|{n}"))
        REP.cd_power_repeated(inst)
        v2["repeated"].append((n, H.reported_cost(None)))
    for n in (16, 32, 64, 128, 256, 512):
        inst = H.generate_scaling(n, random.Random(f"v2|{n}"))
        SQM.cd_power_square_multiply(inst)
        v2["square"].append((n, H.reported_cost(None)))
    report("6 V2 points equal 64 (2^n - 2) and 128 (n - 1)",
           all(c == 64 * (2 ** n - 2) for n, c in v2["repeated"]) and all(c == 128 * (n - 1) for n, c in v2["square"]),
           str(v2))


def section7():
    # x = 1 + e_1 over Z, computed with the recursive product of the implementation modulo M = 2^202 (far above
    # every |coordinate| <= 2^100 for e <= 200) and mapped back to signed integers; compared with (1 + i)^e.
    M = 1 << 202
    signed = lambda v: v - M if v >= M // 2 else v  # noqa: E731
    ok = True
    for m in (1, 3, 5):
        dim = 1 << m
        x = (1, 1) + (0,) * (dim - 2)
        r, a, b = x, 1, 1
        for e in range(1, 201):
            if e > 1:
                r = REP.cd_mul(r, x, M)
                a, b = a - b, a + b                # (a + b i)(1 + i)
            alpha, beta = signed(r[0]), signed(r[1])
            ok &= (alpha, beta) == (a, b) and all(v == 0 for v in r[2:])
            big = max(abs(alpha), abs(beta))
            ok &= alpha * alpha + beta * beta == 2 ** e and 2 ** (e - 1) <= big * big <= 2 ** e
    report("7 x = 1 + e_1 over Z (m = 1, 3, 5): x^e = (1 + i)^e, alpha^2 + beta^2 = 2^e, "
           "2^((e-1)/2) <= max(|alpha|, |beta|) <= 2^(e/2), e <= 200", ok, "600 powers")


def section8(rng):
    rejected = presented = accepted = 0
    for n in (1, 2, 3, 5, 8, 13, 40, 100):
        for t in range(4):
            inst = H.generate(n, random.Random(f"oracle|{n}|{t}"))
            x, e, p = inst
            true = SQM.cd_power_square_multiply(inst)
            accepted += H.check(inst, true) is True
            dim = len(x)
            wrong = [tuple((v + (1 if i == j else 0)) % p for i, v in enumerate(true)) for j in (0, dim - 1)]
            wrong.append(SQM.cd_power_square_multiply((x, e + 1, p)))
            wrong.append(tuple(reversed(true)))
            wrong.append(conj(true))
            for w in wrong:
                if w != true:
                    presented += 1
                    rejected += H.check(inst, w) is False
            presented += 3
            rejected += H.check(inst, list(true)) is False
            rejected += H.check(inst, true[:-1]) is False
            rejected += H.check(inst, tuple(v + p for v in true)) is False
    report("8 oracle control: wrong outputs rejected, true outputs accepted", rejected == presented and accepted == 32,
           f"{rejected}/{presented} wrong rejected, {accepted}/32 true accepted")


class Rec:
    """A residue that records the arithmetic done on it: multiplications, additions and subtractions, negations,
    reductions mod p. Values are kept exactly (Python ints)."""
    __slots__ = ("v",)
    ops = {"mul": 0, "addsub": 0, "neg": 0, "mod": 0}

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _v(x):
        return x.v if isinstance(x, Rec) else x

    def _op(self, kind, v):
        Rec.ops[kind] += 1
        return Rec(v)

    def __mul__(self, o):
        return self._op("mul", self.v * self._v(o))

    __rmul__ = __mul__

    def __add__(self, o):
        return self._op("addsub", self.v + self._v(o))

    __radd__ = __add__

    def __sub__(self, o):
        return self._op("addsub", self.v - self._v(o))

    def __rsub__(self, o):
        return self._op("addsub", self._v(o) - self.v)

    def __neg__(self):
        return self._op("neg", -self.v)

    def __mod__(self, o):
        return self._op("mod", self.v % self._v(o))


def para_mul(x, y):
    """The para-product x * y = conj(x) conj(y), with the table product mod p."""
    return tmul(conj(x), conj(y))


def section9(rng):
    # (a) the operations of one product, PROOFS.md section 1
    bad = 0
    rows = []
    for m in range(0, 7):
        dim = 1 << m
        x = tuple(Rec(rng.randrange(P)) for _ in range(dim))
        y = tuple(Rec(rng.randrange(P)) for _ in range(dim))
        for k in Rec.ops:
            Rec.ops[k] = 0
        out = REP.cd_mul(x, y, P)
        mul, addsub, neg = 4 ** m, 4 ** m - 2 ** m, (4 ** m - 3 * 2 ** m + 2) // 3
        got = dict(Rec.ops)
        bad += got != {"mul": mul, "addsub": addsub, "neg": neg, "mod": mul + addsub + neg}
        bad += tuple(v.v for v in out) != tmul(tuple(v.v for v in x), tuple(v.v for v in y))
        rows.append((m, got["mul"], got["addsub"], got["neg"], got["mod"]))
    report("9 one product: 4^m multiplications, 4^m - 2^m additions/subtractions, (4^m - 3 2^m + 2)/3 negations, one "
           "reduction after each (m = 0..6)", bad == 0, "(m, mul, add/sub, neg, mod) = " + str(rows))
    # (b) the four doubling rules, PROOFS.md section 7
    bad = tot = 0
    for m in range(1, 6):
        dim = 1 << m
        h = dim // 2
        zero = (0,) * h
        for _ in range(8):
            u, v = rand_elem(rng, h), rand_elem(rng, h)
            tot += 1
            bad += (tmul(u + zero, v + zero) != tmul(u, v) + zero
                    or tmul(u + zero, zero + v) != zero + tmul(v, u)
                    or tmul(zero + u, v + zero) != zero + tmul(u, conj(v))
                    or tmul(zero + u, zero + v) != tuple((-c) % P for c in tmul(conj(v), u)) + zero)
    report("9 doubling rules (u,0)(v,0) = (uv,0), (u,0)(0,v) = (0,vu), (0,u)(v,0) = (0,u conj v), "
           "(0,u)(0,v) = (-conj(v) u, 0), m = 1..5", bad == 0, f"{tot - bad}/{tot} random pairs")
    # (c) the digits read by square-and-multiply, PROOFS.md section 3
    bad = sum(1 for e in range(1, 4097)
              if bin(e)[3:] != format(e, "b")[1:] or len(bin(e)[3:]) != e.bit_length() - 1)
    report("9 bin(e)[3:] is the string of the n - 1 binary digits after the leading one", bad == 0,
           f"e = 1..4096: {4096 - bad}/4096")
    # (d) the para-product, PROOFS.md section 8
    ok = True
    for m in range(1, 6):
        dim = 1 << m
        x = add(unit(dim), basis(dim, 1))
        p2 = para_mul(x, x)
        b4 = para_mul(p2, p2)
        p3 = para_mul(p2, x)
        p4 = para_mul(p3, x)
        i_ = basis(dim, 1)
        ok &= (p2 == scale(P - 2, i_) and b4 == scale(P - 4, unit(dim)) and p3 == add(scale(2, unit(dim)), scale(2, i_))
               and p4 == scale(P - 4, i_) and b4 != p4)
    report("9 para-product mod p, x = 1 + e_1 (m = 1..5): P_2 = B(2) = -2 e_1, B(4) = -4 while P_3 = 2 + 2 e_1 and "
           "P_4 = -4 e_1", ok, "5 dimensions")
    # (e) recursion depth of the product, PROOFS.md section 10
    rows = []
    for m in range(0, 6):
        dim = 1 << m
        depth = [0, 0]

        def prof(frame, event, arg):
            if frame.f_code is REP.cd_mul.__code__:
                if event == "call":
                    depth[0] += 1
                    depth[1] = max(depth[1], depth[0])
                elif event == "return":
                    depth[0] -= 1

        x, y = rand_elem(rng, dim), rand_elem(rng, dim)
        sys.setprofile(prof)
        try:
            REP.cd_mul(x, y, P)
        finally:
            sys.setprofile(None)
        rows.append((m, depth[1]))
    report("9 recursion depth of one product = m + 1 nested calls (m = 0..5)", all(d == m + 1 for m, d in rows),
           str(rows))
    # (f) working memory of square-and-multiply, PROOFS.md section 10
    x = rand_elem(rng, 8)
    peaks = []
    for n in (64, 256, 1024, 4096, 8192):
        e = rng.getrandbits(n - 1) | (1 << (n - 1))
        tracemalloc.start()
        SQM.cd_power_square_multiply((x, e, P))
        peaks.append((n, tracemalloc.get_traced_memory()[1]))
        tracemalloc.stop()
    base = peaks[0][1]
    report("9 working memory of square-and-multiply: peak <= peak(n = 64) + 4096 + 4n bytes, n = 64..8192 (octonions)",
           all(pk <= base + 4096 + 4 * n for n, pk in peaks), "(n, peak bytes) = " + str(peaks))
    # (g) generator facts, PROOFS.md section 12
    bad = tot = 0
    for m in (3, 4, 5):
        dim = 1 << m
        for _ in range(7 if m < 5 else 6):
            v = H._isotropic_imaginary(dim, rng, P)
            tot += 1
            bad += v[0] != 0 or sum(c * c for c in v) % P != 0 or tmul(v, v) != (0,) * dim
    report("9 generator: isotropic imaginary elements have n(x) = 0 mod p and x^2 = 0", bad == 0,
           f"{tot - bad}/{tot} generated elements, m = 3, 4, 5")


def main():
    t0 = time.time()
    rng = random.Random(20261007)
    section1(rng)
    section2(rng)
    section3(rng)
    section4(rng)
    section5(rng)
    section6(rng)
    section7()
    section8(rng)
    section9(rng)
    print(f"total {time.time() - t0:.1f} s")
    if FAIL:
        print(f"FAILED: {len(FAIL)} check(s): {FAIL}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

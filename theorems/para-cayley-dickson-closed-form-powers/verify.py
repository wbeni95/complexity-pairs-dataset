#!/usr/bin/env python3
"""Verifier for theorems/para-cayley-dickson-closed-form-powers (see README.md in this folder).

Deterministic exact checks (integers and fractions, no floating point) of the theorem, its lemmas and the remarks;
computations are evidence, the proof is in the README. Standard library only; no network; a few seconds on a laptop.
Exit code 0 only if every check passes.

Objects (as in the README). A_0 = R with the identity conjugation; A_m = A_(m-1) x A_(m-1) with
(a, b)(c, d) = (ac - conj(d) b, d a + b conj(c)) and conj(a, b) = (conj(a), -b). Elements are tuples of 2^m exact
numbers in the standard basis (index 0 is the unit 1, index 1 is e_1). t(x) = x + conj(x) = 2 x_0,
n(x) = x conj(x) = sum of squares. Para-product x * y = conj(x) conj(y); left powers p_1 = x, p_(k+1) = p_k * x.
Left-to-right binary powering: B(1) = x, B(2a) = B(a) * B(a), B(2a + 1) = B(2a) * x.

Checks:
  L1  Lemma 1: x + conj(x) = t(x) 1, x conj(x) = conj(x) x = n(x) 1, 1 is a two-sided unit (m = 0..5).
  L2  Lemma 2: x^2 = t x - n 1; conj(uv) = conj(u) conj(v) for u, v in span{1, x}; span{1, x} is closed,
      commutative and associative (m = 0..5).
  T   Theorem: p_(2j+1) = n^j x and p_(2j+2) = n^j conj(x)^2 for all exponents up to 200 (m <= 4) and 96 (m = 5),
      on seeded random integer elements, on special elements (0, real, purely imaginary, 1 + e_1) and on elements
      with fraction coordinates; the key identity (x * x) * x = n(x) x.
  C   Remark 3 and the setting: the witness x = e_1 + e_10, y = 1 + e_4 with (x * y) * x != n(x) y for m = 4, 5, 6,
      with every basis product and intermediate value written in the README;
      (x * y) * x = n(x) y for y in span{1, x} (m = 0..6);
      A_(m-1) x 0 is a subalgebra closed under conjugation (m = 1..6); the doubling rules (u, 0)(0, 1) = (0, u),
      (u, 0)(0, v) = (0, v u), (0, 1)(u, 0) = (0, conj u), (0, u)(v, 0) = (0, u conj v), (0, u)(0, v) = (-conj(v) u, 0)
      (m = 1..6); A_m is not associative for m = 3..6
      (e_1 e_2 = e_3, e_3 e_4 = e_7, e_2 e_4 = e_6, e_1 e_6 = -e_7); A_1 multiplies like the complex numbers.
  B   Remark 2: B(e) = p_e for every e = 2^j - 1 and 2^j - 2 (e <= 255) on random elements; B(4) = p_4 exactly when
      x^4 = n(x) conj(x)^2; the witness x = 1 + e_1 (B(4) = -4, p_4 = -4 e_1) for m = 1..5.
  A   Remark 1 and Scope: the closed-form evaluation (scalar power n^j and one algebra product) returns p_e; a counted
      evaluation makes 2^m multiplications and 2^m - 1 additions for n(x) and 2^m final multiplications; conj
      negates exactly the coordinates x_1..x_(2^m-1); scalar binary powering makes floor(log2 j) + popcount(j) - 1
      multiplications; n^j has between j floor(log2 n) + 1 and j (floor(log2 n) + 1) bits.
Usage (from the repository root): python theorems/para-cayley-dickson-closed-form-powers/verify.py
"""
import random
import sys
import time
from fractions import Fraction

FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ------------------------------------------------------------------------------------------------ the algebras
def conj(x):
    if len(x) == 1:
        return x
    h = len(x) // 2
    return conj(x[:h]) + tuple(-c for c in x[h:])


def mul(x, y):
    """Cayley-Dickson product (a, b)(c, d) = (ac - conj(d) b, d a + b conj(c))."""
    if len(x) == 1:
        return (x[0] * y[0],)
    h = len(x) // 2
    a, b, c, d = x[:h], x[h:], y[:h], y[h:]
    first = tuple(p - q for p, q in zip(mul(a, c), mul(conj(d), b)))
    second = tuple(p + q for p, q in zip(mul(d, a), mul(b, conj(c))))
    return first + second


def para(x, y):
    return mul(conj(x), conj(y))


def add(x, y):
    return tuple(p + q for p, q in zip(x, y))


def scale(s, x):
    return tuple(s * c for c in x)


def unit(dim):
    return (1,) + (0,) * (dim - 1)


def basis(dim, i):
    return tuple(1 if k == i else 0 for k in range(dim))


def norm(x):
    return sum(c * c for c in x)


def trace(x):
    return 2 * x[0]


def left_powers(x, E):
    """[None, p_1, ..., p_E] by the definition p_(k+1) = p_k * x."""
    p = [None, x]
    for _ in range(2, E + 1):
        p.append(para(p[-1], x))
    return p


def ltr(x, e):
    """Left-to-right binary powering with the para-product: B(1) = x, B(2a) = B(a)*B(a), B(2a+1) = B(2a)*x."""
    r = x
    for bit in bin(e)[3:]:
        r = para(r, r)
        if bit == "1":
            r = para(r, x)
    return r


def closed_form(x, e):
    """p_e by the theorem: n^j x for e = 2j + 1, n^j conj(x)^2 for e = 2j + 2 (fast scalar power n^j)."""
    n = norm(x)
    j, r = divmod(e - 1, 2)
    if r == 0:
        return scale(pow(n, j), x)
    xb = conj(x)
    return scale(pow(n, j), mul(xb, xb))


class Counted:
    """An exact number that counts the multiplications and additions it takes part in (for Remark 1)."""
    __slots__ = ("v",)
    ops = {"mul": 0, "add": 0}

    def __init__(self, v):
        self.v = v

    @classmethod
    def reset(cls):
        cls.ops["mul"] = 0
        cls.ops["add"] = 0

    @staticmethod
    def _v(o):
        return o.v if isinstance(o, Counted) else o

    def __mul__(self, o):
        Counted.ops["mul"] += 1
        return Counted(self.v * self._v(o))

    __rmul__ = __mul__

    def __add__(self, o):
        Counted.ops["add"] += 1
        return Counted(self.v + self._v(o))

    __radd__ = __add__


def rand_elem(rng, dim, lo=-3, hi=3):
    return tuple(rng.randint(lo, hi) for _ in range(dim))


# ------------------------------------------------------------------------------------------------ checks
def part_lemma1(rng):
    bad = 0
    total = 0
    for m in range(6):
        dim = 1 << m
        one = unit(dim)
        for _ in range(20):
            x = rand_elem(rng, dim)
            xb = conj(x)
            total += 1
            ok = (add(x, xb) == scale(trace(x), one) and mul(x, xb) == scale(norm(x), one)
                  and mul(xb, x) == scale(norm(x), one) and mul(one, x) == x and mul(x, one) == x
                  and conj(xb) == x)
            bad += not ok
    check("Lemma 1: x + conj(x) = t(x) 1, x conj(x) = conj(x) x = n(x) 1, unit, conj involutive (m = 0..5)",
          bad == 0, f"{total - bad}/{total} random integer elements")


def part_lemma2(rng):
    bad = 0
    total = 0
    for m in range(6):
        dim = 1 << m
        one = unit(dim)
        for _ in range(12):
            x = rand_elem(rng, dim)
            t, n = trace(x), norm(x)
            total += 1
            ok = mul(x, x) == add(scale(t, x), scale(-n, one))
            span = [add(scale(rng.randint(-4, 4), one), scale(rng.randint(-4, 4), x)) for _ in range(3)]
            u, v, w = span
            uv = mul(u, v)
            # closure: uv = alpha 1 + beta x, with alpha, beta read off coordinate 0 and a non-real coordinate
            k = next((i for i in range(1, dim) if x[i] != 0), None)
            if k is not None:
                beta = Fraction(uv[k], x[k])
                alpha = uv[0] - beta * x[0]
                ok &= add(scale(alpha, one), scale(beta, x)) == uv
            else:
                ok &= all(c == 0 for c in uv[1:])
            ok &= uv == mul(v, u)                                    # commutative
            ok &= mul(mul(u, v), w) == mul(u, mul(v, w))             # associative
            ok &= conj(uv) == mul(conj(u), conj(v))                  # conj multiplicative on span{1, x}
            bad += not ok
    check("Lemma 2: x^2 = t x - n 1; span{1, x} closed, commutative, associative; conj multiplicative on it "
          "(m = 0..5)", bad == 0, f"{total - bad}/{total} random elements, 3 random span elements each")


def part_theorem(rng):
    rows = []
    allok = True
    for m in range(6):
        dim = 1 << m
        E = 200 if m <= 4 else 96
        count = 12 if m <= 4 else 6
        els = [rand_elem(rng, dim) for _ in range(count)]
        els += [(0,) * dim, scale(3, unit(dim)), scale(-2, unit(dim))]
        if dim >= 2:
            els += [add(unit(dim), basis(dim, 1)), tuple([0] + [rng.randint(-2, 2) for _ in range(dim - 1)])]
        ok_m = 0
        for x in els:
            p = left_powers(x, E)
            n = norm(x)
            xb2 = mul(conj(x), conj(x))
            ok = all(p[2 * j + 1] == scale(n ** j, x) for j in range(0, (E - 1) // 2 + 1)) and \
                all(p[2 * j + 2] == scale(n ** j, xb2) for j in range(0, (E - 2) // 2 + 1))
            ok &= para(para(x, x), x) == scale(n, x)
            ok_m += ok
            allok &= ok
        rows.append(f"m={m}: {ok_m}/{len(els)} (e <= {E})")
    check("Theorem: p_(2j+1) = n^j x and p_(2j+2) = n^j conj(x)^2, and (x * x) * x = n(x) x", allok, "; ".join(rows))
    # fraction coordinates
    okf = 0
    tot = 0
    for m in range(6):
        dim = 1 << m
        for _ in range(3):
            x = tuple(Fraction(rng.randint(-5, 5), rng.randint(1, 4)) for _ in range(dim))
            p = left_powers(x, 40)
            tot += 1
            okf += all(p[e] == closed_form(x, e) for e in range(1, 41))
    check("Theorem with fraction coordinates (m = 0..5, e <= 40)", okf == tot, f"{okf}/{tot}")
    # key identity on many random elements
    bad = sum(1 for m in range(6) for _ in range(30)
              for x in [rand_elem(rng, 1 << m, -9, 9)] if para(para(x, x), x) != scale(norm(x), x))
    check("key identity (x * x) * x = n(x) x on 180 further random elements (m = 0..5)", bad == 0,
          f"{180 - bad}/180")


def part_controls(rng):
    for m in (4, 5, 6):
        dim = 1 << m
        e_ = lambda i: basis(dim, i)  # noqa: E731
        neg = lambda v: scale(-1, v)  # noqa: E731
        x = add(basis(dim, 1), basis(dim, 10))
        y = add(unit(dim), basis(dim, 4))
        lhs = para(para(x, y), x)
        expect = add(add(scale(2, unit(dim)), scale(2, basis(dim, 4))), scale(2, basis(dim, 15)))
        # the basis products written out in Remark 3, and the intermediate value z = x * y
        products = [((1, 4), e_(5)), ((10, 4), neg(e_(14))), ((1, 1), neg(unit(dim))), ((10, 10), neg(unit(dim))),
                    ((1, 10), neg(e_(11))), ((10, 1), e_(11)), ((5, 1), e_(4)), ((5, 10), e_(15)),
                    ((14, 1), neg(e_(15))), ((14, 10), neg(e_(4))),
                    ((2, 5), e_(7)), ((6, 1), e_(7)), ((2, 6), neg(e_(4))), ((2, 1), neg(e_(3)))]
        prods_ok = all(mul(e_(i), e_(j)) == v for (i, j), v in products)
        z = para(x, y)
        z_ok = (z == add(add(neg(e_(1)), e_(5)), add(neg(e_(10)), neg(e_(14)))) and conj(x) == neg(x)
                and conj(y) == add(unit(dim), neg(e_(4))) and conj(z) == neg(z))
        check(f"witness m={m}: x = e_1 + e_10, y = 1 + e_4: the {len(products)} basis products of Remark 3, "
              "x * y = -e_1 + e_5 - e_10 - e_14, (x * y) * x = 2 + 2 e_4 + 2 e_15 != n(x) y = 2 + 2 e_4,"
              " while (x * x) * x = n(x) x", prods_ok and z_ok and lhs == expect and lhs != scale(norm(x), y)
              and norm(x) == 2 and para(para(x, x), x) == scale(norm(x), x))
    bad = tot = 0
    for m in range(0, 7):
        dim = 1 << m
        for _ in range(10):
            x = rand_elem(rng, dim)
            y = add(scale(rng.randint(-5, 5), unit(dim)), scale(rng.randint(-5, 5), x))
            tot += 1
            bad += para(para(x, y), x) != scale(norm(x), y)
    check("Remark 3: (x * y) * x = n(x) y for every y in span{1, x} (m = 0..6, random x, y)", bad == 0,
          f"{tot - bad}/{tot}")
    bad = 0
    for m in range(1, 7):
        dim = 1 << m
        h = dim // 2
        for _ in range(10):
            a = rand_elem(rng, h) + (0,) * h
            c = rand_elem(rng, h) + (0,) * h
            bad += mul(a, c) != mul(a[:h], c[:h]) + (0,) * h or conj(a) != conj(a[:h]) + (0,) * h
    check("A_(m-1) x 0 is a subalgebra on which conj and the product are those of A_(m-1) (m = 1..6)", bad == 0,
          f"{60 - bad}/60 random pairs")
    # the doubling rules used in the setting: (u, 0)(0, 1) = (0, u), (u, 0)(0, v) = (0, v u), (0, 1)(u, 0) = (0, conj u)
    bad = tot = 0
    for m in range(1, 7):
        dim = 1 << m
        h = dim // 2
        for _ in range(10):
            u, v = rand_elem(rng, h), rand_elem(rng, h)
            zero = (0,) * h
            one_h = unit(h)
            tot += 1
            bad += (mul(u + zero, zero + one_h) != zero + u or mul(u + zero, zero + v) != zero + mul(v, u)
                    or mul(zero + one_h, u + zero) != zero + conj(u)
                    or mul(zero + u, v + zero) != zero + mul(u, conj(v))
                    or mul(zero + u, zero + v) != scale(-1, mul(conj(v), u)) + zero)
    check("setting and Remark 3: (u, 0)(0, 1) = (0, u), (u, 0)(0, v) = (0, v u), (0, 1)(u, 0) = (0, conj u), "
          "(0, u)(v, 0) = (0, u conj v), (0, u)(0, v) = (-conj(v) u, 0) (m = 1..6)", bad == 0,
          f"{tot - bad}/{tot} random pairs (u, v)")
    q = 1 << 2
    check("setting: e_1 e_2 = e_3 and e_2 e_1 = -e_3 in A_2",
          mul(basis(q, 1), basis(q, 2)) == basis(q, 3) and mul(basis(q, 2), basis(q, 1)) == scale(-1, basis(q, 3)))
    for m in (3, 4, 5, 6):
        dim = 1 << m
        a, b, c = basis(dim, 1), basis(dim, 2), basis(dim, 4)
        steps = (mul(basis(dim, 3), c) == basis(dim, 7) and mul(b, c) == basis(dim, 6)
                 and mul(a, basis(dim, 6)) == scale(-1, basis(dim, 7)))
        check(f"A_{m} is not associative: e_3 e_4 = e_7, e_2 e_4 = e_6, e_1 e_6 = -e_7; (e_1 e_2) e_4 = e_7 and "
              "e_1 (e_2 e_4) = -e_7",
              steps and mul(mul(a, b), c) == basis(dim, 7) and mul(a, mul(b, c)) == scale(-1, basis(dim, 7)))
    pairs = [tuple(rng.randint(-9, 9) for _ in range(4)) for _ in range(200)]
    ok = all(mul((a, b), (c, d)) == (a * c - b * d, a * d + b * c) for a, b, c, d in pairs)
    check("A_1: (a, b)(c, d) = (ac - bd, ad + bc), the product of the complex numbers a + bi and c + di", ok,
          f"{len(pairs)} random integer pairs")


def part_binary(rng):
    exps = sorted({(1 << j) - 1 for j in range(1, 9)} | {(1 << j) - 2 for j in range(2, 9)})
    bad = 0
    tot = 0
    for m in range(6):
        dim = 1 << m
        for _ in range(6 if m <= 4 else 3):
            x = rand_elem(rng, dim)
            p = left_powers(x, max(exps))
            tot += 1
            bad += any(ltr(x, e) != p[e] for e in exps)
    check("B(e) = p_e for every e = 2^j - 1, 2^j - 2 up to 255 (m = 0..5, random elements)", bad == 0,
          f"{tot - bad}/{tot}; exponents {exps}")
    # B(4) = p_4 iff x^4 = n conj(x)^2
    agree = 0
    tot = 0
    wrong4 = 0
    for m in range(6):
        dim = 1 << m
        for _ in range(20):
            x = rand_elem(rng, dim)
            p4 = left_powers(x, 4)[4]
            c1 = ltr(x, 4) == p4
            x2 = mul(x, x)
            c2 = mul(x2, x2) == scale(norm(x), mul(conj(x), conj(x)))
            agree += c1 == c2
            wrong4 += not c1
            tot += 1
    check("B(4) = p_4 exactly when x^2 x^2 = n(x) conj(x)^2", agree == tot,
          f"{agree}/{tot} random elements; B(4) != p_4 on {wrong4}")
    first = []
    for m in range(1, 6):
        dim = 1 << m
        x = add(unit(dim), basis(dim, 1))
        p = left_powers(x, 4)
        first.append(ltr(x, 4) == scale(-4, unit(dim)) and p[4] == scale(-4, basis(dim, 1))
                     and mul(x, x) == scale(2, basis(dim, 1)) and mul(conj(x), conj(x)) == scale(-2, basis(dim, 1)))
    check("witness x = 1 + e_1 (m = 1..5): x^2 = 2 e_1, conj(x)^2 = -2 e_1, B(4) = -4 while p_4 = -4 e_1", all(first))


def part_algorithm(rng):
    bad = 0
    tot = 0
    for m in range(6):
        dim = 1 << m
        for _ in range(4):
            x = rand_elem(rng, dim)
            p = left_powers(x, 150)
            tot += 1
            bad += any(closed_form(x, e) != p[e] for e in range(1, 151))
    check("closed-form evaluation (scalar power n^j and one algebra product) = p_e for e <= 150 (m = 0..5)",
          bad == 0, f"{tot - bad}/{tot}")
    # Remark 1, operation counts of n(x) and of the final scaling, by a counted evaluation of the closed form
    bad = tot = 0
    rows = []
    for m in range(0, 7):
        dim = 1 << m
        for e in (1, 2, 5, 8, 13, 20):
            x = tuple(Counted(c) for c in rand_elem(rng, dim))
            Counted.reset()
            s = x[0] * x[0]                                   # n(x) as a running sum of squares
            for c in x[1:]:
                s = s + c * c
            norm_counts = dict(Counted.ops)
            j, r = divmod(e - 1, 2)
            nj = pow(s.v, j)                                  # scalar power: its count is checked below
            plain = tuple(c.v for c in x)
            base = plain if r == 0 else mul(conj(plain), conj(plain))
            Counted.reset()
            out = tuple(Counted(nj) * c for c in base)        # final scaling by n^j
            scale_counts = dict(Counted.ops)
            tot += 1
            ok = (norm_counts == {"mul": dim, "add": dim - 1} and scale_counts == {"mul": dim, "add": 0}
                  and s.v == norm(plain) and tuple(c.v for c in out) == closed_form(plain, e))
            ok = ok and tuple(c.v for c in out) == left_powers(plain, e)[e]
            bad += not ok
        rows.append((m, norm_counts["mul"], norm_counts["add"], scale_counts["mul"]))   # measured, last e
    check("Remark 1: counted evaluation: n(x) makes 2^m multiplications and 2^m - 1 additions, the final scaling 2^m "
          "multiplications, and the result is p_e (m = 0..6, e in {1, 2, 5, 8, 13, 20})", bad == 0,
          f"{tot - bad}/{tot} evaluations; (m, mult, add, final mult) = {rows}")
    # Remark 1, operation counts: conj changes the sign of exactly the coordinates 1..2^m - 1
    bad = tot = 0
    for m in range(0, 7):
        dim = 1 << m
        for _ in range(5):
            x = rand_elem(rng, dim, 1, 9)                       # nonzero coordinates, so every sign change shows
            tot += 1
            bad += conj(x) != (x[0],) + tuple(-c for c in x[1:])
    check("Remark 1: conj negates exactly the 2^m - 1 coordinates x_1..x_(2^m-1) (m = 0..6)", bad == 0,
          f"{tot - bad}/{tot} random elements with nonzero coordinates")
    # Remark 1: left-to-right binary powering of a scalar makes floor(log2 j) + popcount(j) - 1 multiplications
    bad = 0
    for j in range(1, 2049):
        for n in (2, 3, 7):
            r, mults = n, 0
            for bit in bin(j)[3:]:
                r, mults = r * r, mults + 1
                if bit == "1":
                    r, mults = r * n, mults + 1
            bad += r != n ** j or mults != (j.bit_length() - 1) + bin(j).count("1") - 1 \
                or mults > 2 * (j.bit_length() - 1)
    check("Remark 1: scalar binary powering gives n^j with floor(log2 j) + popcount(j) - 1 <= 2 floor(log2 j) "
          "multiplications", bad == 0, f"j = 1..2048, n in {{2, 3, 7}}: {3 * 2048 - bad}/{3 * 2048}")
    # Scope: for n >= 2 and j >= 1, n^j has between jk + 1 and j(k + 1) bits, k = floor(log2 n)
    bad = tot = 0
    for n in range(2, 65):
        k = n.bit_length() - 1
        for j in range(1, 101):
            b = (n ** j).bit_length()
            tot += 1
            bad += not (j * k + 1 <= b <= j * (k + 1))
    check("Scope: n^j has between j floor(log2 n) + 1 and j (floor(log2 n) + 1) bits", bad == 0,
          f"n = 2..64, j = 1..100: {tot - bad}/{tot}")


def main():
    t0 = time.time()
    rng = random.Random(20261007)
    for name, fn in (("L1", part_lemma1), ("L2", part_lemma2), ("T", part_theorem), ("C", part_controls),
                     ("B", part_binary), ("A", part_algorithm)):
        t = time.time()
        print(f"== part {name}")
        fn(rng)
        print(f"   ({time.time() - t:.1f} s)")
    print(f"total {time.time() - t0:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

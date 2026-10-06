"""Exact shape diagnostic for exact operation counts (informational; added in round 2026-10-06f).

What it does. A V2 claim with `measure: "reported"` says that an exact count a(n) grows like the cost expression.
The V2 fit compares log a(n) with log cost(n) over a few n and accepts a slope of 1 +- tolerance. This module looks
at the *exact* counts instead and tries to identify their growth shape exactly:

    cost(n) ~ C * b^n * n^p * (log n)^q          (b: exponential base, p: polynomial power, q: log power)

* on a CONSECUTIVE grid n = lo, lo+s, lo+2s, ... a guessed recurrence in t = n/s (constant coefficients by
  Berlekamp-Massey, else polynomial coefficients by holonomic guessing) gives the dominant root lambda = b^s with its
  exact minimal polynomial and the exponent theta = p (multiplicity - 1, or the exact Birkhoff-Trjitzinsky balance);
  log factors are not visible here (a (log n)^q factor makes a sequence non-holonomic in n);
* on a DOUBLING grid n = 2^k a recurrence in k gives lambda = 2^p (exact) and theta = q (multiplicity - 1);
  exponential factors are not visible here (b must be 1).

The claimed shape is derived from the V2 `cost` expression by an exact parser (`parse_cost`), or given explicitly
(`expect`). Every run ends in exactly one category with one machine-readable reason (`REASONS`):

    MATCH         the identified shape and the claim agree exactly in every visible component;
    MISMATCH      an identified shape differs from the claim (`differs` lists base / polynomial_factor / log_power);
    UNDETERMINED  the diagnostic cannot decide; the reason says why;
    SKIPPED       not applicable (timing measure, or no shape block).

A guess counts only if it is overdetermined, has a one-dimensional solution space and reproduces held-out terms
(the RL-082 rule). A MATCH is strong evidence, not a proof: the recurrence is a conjecture verified on finitely many
terms. The diagnostic is informational: tools/validate.py records it but never changes a V2 verdict because of it.

Everything is exact (fractions, integer polynomials, Sturm root isolation) except: float values used for display
and ordering, the numeric guard on theta for P-recursive guesses, and the labelled Durand-Kerner fallback in the
dominance check (a numeric confirmation is reported but never counts as a certificate).

See notes/v2-shape-diagnostic.md (for readers) and research/2026-10-06f_shape_diagnostic.md (design, evidence).
"""
from __future__ import annotations

import ast
import math
from dataclasses import dataclass
from fractions import Fraction

from . import exactalg as ea
from . import recurrences as rc

SHAPE_VERSION = 1

DEFAULTS = {
    "max_order": 6,            # C-finite and P-recursive recurrence order limit
    "max_degree": 4,           # P-recursive coefficient degree limit
    "holdout_c_finite": 4,     # held-out terms for a constant-coefficient guess (RL-082: guess_c_finite)
    "holdout_p_recursive": 3,  # held-out terms for a polynomial-coefficient guess (RL-082: guess_p_recursive)
    "extra_c_finite": 2,       # training terms beyond the 2L that determine an order-L recurrence
    "extra_p_recursive": 4,    # equations beyond (unknowns - 1)
    "min_holdout": 2,          # a shape block may lower the holdout, never below this
    "theta_guard": 0.15,       # P-recursive only: |numeric theta slope - exact theta| must not exceed this
    "probe_points": 3,         # instance-dependence probe: this many small n ...
    "probe_seeds": 2,          # ... each re-run with this many other seeds
    "max_terms": 64,           # largest grid a shape block may request
    "max_radical_index": 12,   # c^(1/v) with v above this is treated as an approximation (e.g. n**2.807)
}

CATEGORIES = ("MATCH", "MISMATCH", "UNDETERMINED", "SKIPPED")

# reason -> (category, one-line meaning). The order of the UNDETERMINED reasons is their precedence.
REASONS = {
    "exact_shape_agrees": ("MATCH", "the identified dominant root (exact minimal polynomial) and exponent equal the claim"),
    "differs": ("MISMATCH", "an identified component differs from the claim; see `differs`, `found`, `claimed`"),
    "timing_measure": ("SKIPPED", "wall-clock timings are not exact counts"),
    "no_shape_block": ("SKIPPED", "the scaling claim declares no shape block"),
    "invalid_shape_block": ("UNDETERMINED", "the shape block is inconsistent (grid, expect, limits)"),
    "randomised_counts": ("UNDETERMINED", "samples > 1: the values are sample means of a random count, not an exact sequence"),
    "count_failed": ("UNDETERMINED", "computing a count on the shape grid raised an exception"),
    "non_integer_counts": ("UNDETERMINED", "a reported count is not an integer"),
    "instance_dependent_counts": ("UNDETERMINED", "the count changes when the instance (or internal randomness) is re-drawn"),
    "python_version_dependent": ("UNDETERMINED", "declared: the count includes work inside CPython built-ins (RL-069)"),
    "too_few_terms": ("UNDETERMINED", "a candidate recurrence exists but the terms cannot overdetermine and check it"),
    "holdout_not_reproduced": ("UNDETERMINED", "a recurrence fitted the training terms but failed a held-out term"),
    "solution_space_not_one_dimensional": ("UNDETERMINED", "the fitting system has several independent solutions"),
    "no_recurrence_within_limits": ("UNDETERMINED", "no recurrence within the order/degree limits fits the terms"),
    "factorial_type_growth": ("UNDETERMINED", "the recurrence implies super-exponential (factorial-type) growth"),
    "dominance_not_certified": ("UNDETERMINED", "no exact certificate that the root dominates all other roots"),
    "asymptotics_not_determined": ("UNDETERMINED", "the recurrence does not fix the exponent (repeated root, subdominant solution)"),
    "cost_not_parseable": ("UNDETERMINED", "the claimed cost is outside the exact shape grammar and no `expect` is given"),
    "cost_outside_grid_family": ("UNDETERMINED", "the claimed shape has a component this grid cannot see"),
    "internal_error": ("UNDETERMINED", "the diagnostic itself failed (bug); the V2 verdict is unaffected"),
}


class NotParseable(ValueError):
    """The cost (or expect) is outside the exact shape grammar."""


class OutsideGridFamily(ValueError):
    """The claimed shape has a component that the chosen grid cannot see."""


class InvalidBlock(ValueError):
    """The shape block is inconsistent."""


# ==============================================================================================================
# Exact positive constants: rationals, quadratic surds a + b sqrt(d), radicals c^(1/v), roots of given polynomials
# ==============================================================================================================
# Representation (tuples, immutable):
#   ("q", F)               rational F
#   ("s", a, b, d)         a + b*sqrt(d), b != 0, d > 1 square-free
#   ("r", c, v)            c^(1/v), c > 0 rational, v >= 3, normalised (irreducible x^v - c)
#   ("p", poly, approx)    the real root nearest `approx` of the irreducible integer polynomial `poly` (lowest first)
#   ("f", x)               inexact float (pi, e, logarithms, ...): allowed as a constant factor only


def _q(x) -> tuple:
    return ("q", Fraction(x))


ONE = _q(1)
TWO = _q(2)


def _int_root(n: int, k: int) -> int | None:
    """Exact integer k-th root of n >= 0, or None."""
    if n < 0:
        return None
    if n in (0, 1):
        return n
    r = round(n ** (1.0 / k))
    for c in (r - 1, r, r + 1):
        if c >= 0 and c ** k == n:
            return c
    lo, hi = 0, 1 << (n.bit_length() // k + 1)
    while lo <= hi:
        m = (lo + hi) // 2
        p = m ** k
        if p == n:
            return m
        if p < n:
            lo = m + 1
        else:
            hi = m - 1
    return None


def _frac_root(c: Fraction, k: int) -> Fraction | None:
    a, b = _int_root(c.numerator, k), _int_root(c.denominator, k)
    return None if a is None or b is None else Fraction(a, b)


def _squarefree_split(n: int) -> tuple[int, int]:
    """n = s^2 * d with d square-free (n >= 1, trial division; fine for the small integers of cost formulas)."""
    s, d, p = 1, 1, 2
    while p * p <= n:
        e = 0
        while n % p == 0:
            n //= p
            e += 1
        s *= p ** (e // 2)
        if e % 2:
            d *= p
        p += 1
    return s, d * n


def _sqrt_rational(c: Fraction) -> tuple:
    """Exact sqrt of a rational c > 0 as ("q", .) or ("s", 0, b, d)."""
    num = c.numerator * c.denominator  # sqrt(p/q) = sqrt(p q) / q
    s, d = _squarefree_split(num)
    coeff = Fraction(s, c.denominator)
    return ("q", coeff) if d == 1 else ("s", Fraction(0), coeff, d)


def _radical(c: Fraction, v: int) -> tuple:
    """Normalised c^(1/v) for rational c > 0: the smallest d | v with c a perfect (v/d)-th power gives s^(1/d),
    s = c^(d/v); then x^d - s is irreducible (Capelli), so ("r", s, d) has minimal polynomial x^d - s."""
    if c <= 0:
        return ("f", float(c) ** (1.0 / v) if c >= 0 else float("nan"))
    for d in range(1, v + 1):
        if v % d:
            continue
        s = _frac_root(c, v // d)
        if s is not None:
            if d == 1:
                return ("q", s)
            if d == 2:
                return _sqrt_rational(s)
            if d > DEFAULTS["max_radical_index"]:
                return ("f", float(s) ** (1.0 / d))
            return ("r", s, d)
    raise AssertionError("unreachable")


def value(x: tuple) -> float:
    k = x[0]
    if k == "q":
        return float(x[1])
    if k == "s":
        return float(x[1]) + float(x[2]) * math.sqrt(x[3])
    if k == "r":
        return float(x[1]) ** (1.0 / x[2])
    if k == "p":
        return x[2]
    return float(x[1])


def is_exact(x: tuple) -> bool:
    return x[0] != "f"


def _as_radical(x: tuple):
    """("q", c>0) -> (c, 1); ("s", 0, b>0, d) -> (b^2 d, 2); ("r", c, v) -> (c, v); else None."""
    if x[0] == "q" and x[1] > 0:
        return x[1], 1
    if x[0] == "s" and x[1] == 0 and x[2] > 0:
        return x[2] * x[2] * x[3], 2
    if x[0] == "r":
        return x[1], x[2]
    return None


def mul(x: tuple, y: tuple) -> tuple:
    if x[0] == "f" or y[0] == "f" or x[0] == "p" or y[0] == "p":
        return ("f", value(x) * value(y))
    if x[0] == "q" and y[0] == "q":
        return ("q", x[1] * y[1])
    if x[0] == "q" and y[0] == "s":
        x, y = y, x
    if x[0] == "s" and y[0] == "q":
        return ("q", Fraction(0)) if y[1] == 0 else ("s", x[1] * y[1], x[2] * y[1], x[3])
    if x[0] == "s" and y[0] == "s" and x[3] == y[3]:
        a, b = x[1] * y[1] + x[2] * y[2] * x[3], x[1] * y[2] + x[2] * y[1]
        return ("q", a) if b == 0 else ("s", a, b, x[3])
    rx, ry = _as_radical(x), _as_radical(y)
    if rx and ry:
        L = rx[1] * ry[1] // math.gcd(rx[1], ry[1])
        return _radical(rx[0] ** (L // rx[1]) * ry[0] ** (L // ry[1]), L)
    return ("f", value(x) * value(y))


def inv(x: tuple) -> tuple:
    k = x[0]
    if k == "q":
        if x[1] == 0:
            raise ZeroDivisionError("division by zero in a cost constant")
        return ("q", 1 / x[1])
    if k == "s":
        a, b, d = x[1], x[2], x[3]
        nrm = a * a - b * b * d
        return ("s", a / nrm, -b / nrm, d)
    if k == "r":
        return _radical(1 / x[1], x[2])
    return ("f", 1.0 / value(x))


def div(x: tuple, y: tuple) -> tuple:
    return mul(x, inv(y))


def add(x: tuple, y: tuple) -> tuple:
    if x[0] == "q" and y[0] == "q":
        return ("q", x[1] + y[1])
    if x[0] == "q" and y[0] == "s":
        x, y = y, x
    if x[0] == "s" and y[0] == "q":
        return ("s", x[1] + y[1], x[2], x[3])
    if x[0] == "s" and y[0] == "s" and x[3] == y[3]:
        b = x[2] + y[2]
        return ("q", x[1] + y[1]) if b == 0 else ("s", x[1] + y[1], b, x[3])
    return ("f", value(x) + value(y))


def neg(x: tuple) -> tuple:
    if x[0] == "q":
        return ("q", -x[1])
    if x[0] == "s":
        return ("s", -x[1], -x[2], x[3])
    return ("f", -value(x))


def powq(x: tuple, e: Fraction) -> tuple:
    """x ** e for a rational exponent e (exact where possible)."""
    e = Fraction(e)
    if e == 1:
        return x
    if x[0] == "f" or x[0] == "p":
        return ("f", value(x) ** float(e))
    if e.denominator == 1:
        k = abs(e.numerator)
        if k > 256:
            return ("f", value(x) ** float(e))
        out, base = ONE, x
        while k:
            if k & 1:
                out = mul(out, base)
            base = mul(base, base)
            k >>= 1
        return inv(out) if e < 0 else out
    r = _as_radical(x)
    if r is None:
        return ("f", value(x) ** float(e))
    c, v = r
    u, w = e.numerator, e.denominator
    if abs(u) > 256 or v * w > 4 * DEFAULTS["max_radical_index"]:
        return ("f", value(x) ** float(e))
    return _radical(c ** u, v * w)


def minpoly(x: tuple) -> list[int]:
    """Minimal polynomial over Z (primitive, positive leading coefficient, lowest degree first)."""
    k = x[0]
    if k == "q":
        return ea.pint([-x[1], 1])
    if k == "s":
        a, b, d = x[1], x[2], x[3]
        return ea.pint([a * a - b * b * d, -2 * a, 1])
    if k == "r":
        c, v = x[1], x[2]
        return ea.pint([-c] + [0] * (v - 1) + [1])
    if k == "p":
        return list(x[1])
    raise NotParseable("inexact constant has no minimal polynomial")


def root_index(mp: list[int], v: float) -> tuple[int, float]:
    """Index (in increasing order) of the real root of mp nearest to v, and the smallest gap between real roots."""
    ivs = [ea.real_root_approx(mp, iv, Fraction(1, 10 ** 24)) for iv in ea.real_roots_isolated(mp)]
    mids = [float((lo + hi) / 2) for lo, hi in ivs]
    if not mids:
        return -1, 0.0
    idx = min(range(len(mids)), key=lambda i: abs(mids[i] - v))
    gap = min((b - a for a, b in zip(mids, mids[1:])), default=math.inf)
    return idx, gap


def same_number(mp1: list[int], v1: float, mp2: list[int], v2: float) -> bool:
    """Exact equality of two real algebraic numbers given by minimal polynomial and value."""
    if ea.pint(mp1) != ea.pint(mp2):
        return False
    i1, gap = root_index(mp1, v1)
    i2, _ = root_index(mp1, v2)
    if gap < 1e-9 * max(1.0, abs(v1)):  # roots too close for float disambiguation: refuse to call them equal
        return False
    return i1 == i2 and i1 >= 0


def const_equal(x: tuple, y: tuple) -> bool:
    if not (is_exact(x) and is_exact(y)):
        return abs(value(x) - value(y)) <= 1e-12 * max(1.0, abs(value(x)))
    return same_number(minpoly(x), value(x), minpoly(y), value(y))


def const_str(x: tuple) -> str:
    k = x[0]
    if k == "q":
        return str(x[1])
    if k == "s":
        a, b, d = x[1], x[2], x[3]
        bs = ("" if b == 1 else ("-" if b == -1 else f"{b}*")) + f"sqrt({d})"
        if a == 0:
            return bs
        return f"{a} + {bs}" if b > 0 else f"{a} - {bs.lstrip('-')}"
    if k == "r":
        return f"({x[1]})^(1/{x[2]})"
    if k == "p":
        return f"root of {ea.pstr(x[1])} near {x[2]:.10g}"
    return f"{x[1]:.10g} (inexact)"


def p_rational(p2: tuple) -> Fraction | None:
    """p for p2 = 2^p if p is rational, else None."""
    r = _as_radical(p2)
    if r is None:
        return None
    c, v = r
    num, den = c.numerator, c.denominator
    if num == 1 and den & (den - 1) == 0:
        return Fraction(-(den.bit_length() - 1), v)
    if den == 1 and num & (num - 1) == 0:
        return Fraction(num.bit_length() - 1, v)
    return None


def poly_str_highest_first(mp: list[int]) -> str:
    return ea.pstr(mp)


# ==============================================================================================================
# Parsing the claimed cost into a shape (b, 2^p, q)
# ==============================================================================================================

@dataclass(frozen=True)
class Shape:
    base: tuple    # exact constant b
    p2: tuple      # exact constant 2^p
    q: Fraction    # log power
    coef: float    # leading coefficient (sign matters for sums)


_CONST_NAMES = {"e": ("f", math.e), "pi": ("f", math.pi), "phi": ("s", Fraction(1, 2), Fraction(1, 2), 5)}
_FUNCS = ("log", "log2", "sqrt", "exp", "factorial")


def _contains_n(node) -> bool:
    return any(isinstance(m, ast.Name) and m.id == "n" for m in ast.walk(node))


def _contains_decimal(node) -> bool:
    return any(isinstance(m, ast.Constant) and isinstance(m.value, float) and not float(m.value).is_integer()
               for m in ast.walk(node))


def _check_node(node):
    for m in ast.walk(node):
        if isinstance(m, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div,
                          ast.Pow, ast.USub)):
            continue
        if isinstance(m, ast.Constant) and isinstance(m.value, (int, float)) and not isinstance(m.value, bool):
            continue
        if isinstance(m, ast.Name) and (m.id == "n" or m.id in _CONST_NAMES or m.id in _FUNCS):
            continue
        if isinstance(m, ast.Call) and isinstance(m.func, ast.Name) and m.func.id in _FUNCS and not m.keywords \
                and len(m.args) == 1:
            continue
        raise NotParseable(f"disallowed syntax: {ast.dump(m)[:60]}")


def const_value(node) -> tuple:
    """Exact value of an n-free subexpression where possible, else ("f", float)."""
    if isinstance(node, ast.Constant):
        v = node.value
        return ("q", Fraction(v)) if isinstance(v, int) else ("q", Fraction(repr(v)))
    if isinstance(node, ast.Name):
        if node.id in _CONST_NAMES:
            return _CONST_NAMES[node.id]
        raise NotParseable(f"unknown name {node.id}")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return neg(const_value(node.operand))
    if isinstance(node, ast.BinOp):
        a, b = const_value(node.left), const_value(node.right)
        if isinstance(node.op, ast.Add):
            return add(a, b)
        if isinstance(node.op, ast.Sub):
            return add(a, neg(b))
        if isinstance(node.op, ast.Mult):
            return mul(a, b)
        if isinstance(node.op, ast.Div):
            return div(a, b)
        if isinstance(node.op, ast.Pow):
            if b[0] == "q":
                return powq(a, b[1])
            return ("f", value(a) ** value(b))
    if isinstance(node, ast.Call):
        f, arg = node.func.id, const_value(node.args[0])
        if f == "sqrt":
            return powq(arg, Fraction(1, 2))
        if f == "log":
            return ("f", math.log(value(arg)))
        if f == "log2":
            return ("f", math.log2(value(arg)))
        if f == "exp":
            return ("f", math.exp(value(arg)))
        if f == "factorial":
            return ("f", float(math.factorial(int(value(arg)))))
    raise NotParseable(f"cannot evaluate constant {ast.dump(node)[:60]}")


def exp2_of(node) -> tuple | None:
    """2^E for an n-free exponent expression E, exactly (e.g. E = log2(7) -> 7, E = 5/2 -> sqrt(32)), or None."""
    if _contains_n(node):
        return None
    if isinstance(node, ast.Constant):
        v = node.value
        e = Fraction(v) if isinstance(v, int) else Fraction(repr(v))
        r = powq(TWO, e)
        return r if is_exact(r) else None
    if isinstance(node, ast.Call) and node.func.id == "log2":
        c = const_value(node.args[0])
        return c if is_exact(c) and value(c) > 0 else None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        r = exp2_of(node.operand)
        return None if r is None else inv(r)
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, (ast.Add, ast.Sub)):
            a, b = exp2_of(node.left), exp2_of(node.right)
            if a is None or b is None:
                return None
            r = mul(a, b) if isinstance(node.op, ast.Add) else div(a, b)
            return r if is_exact(r) else None
        if isinstance(node.op, (ast.Mult, ast.Div)):
            try:
                rv = const_value(node.right)
            except NotParseable:
                rv = ("f", 0.0)
            if isinstance(node.op, ast.Mult):
                try:
                    lv = const_value(node.left)
                except NotParseable:
                    lv = ("f", 0.0)
                if lv[0] == "q":
                    r = exp2_of(node.right)
                    r = None if r is None else powq(r, lv[1])
                elif rv[0] == "q":
                    r = exp2_of(node.left)
                    r = None if r is None else powq(r, rv[1])
                else:
                    return None
            else:
                if rv[0] != "q" or rv[1] == 0:
                    return None
                r = exp2_of(node.left)
                r = None if r is None else powq(r, 1 / rv[1])
            return r if r is not None and is_exact(r) else None
    return None


def _linear_in_n(node) -> tuple[Fraction, float] | None:
    """(alpha, beta) with node == alpha*n + beta, alpha exact rational; None if not linear in n."""
    if not _contains_n(node):
        try:
            return Fraction(0), value(const_value(node))
        except (NotParseable, ValueError, ZeroDivisionError, OverflowError):
            return None
    if isinstance(node, ast.Name) and node.id == "n":
        return Fraction(1), 0.0
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        r = _linear_in_n(node.operand)
        return None if r is None else (-r[0], -r[1])
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, (ast.Add, ast.Sub)):
            a, b = _linear_in_n(node.left), _linear_in_n(node.right)
            if a is None or b is None:
                return None
            s = 1 if isinstance(node.op, ast.Add) else -1
            return a[0] + s * b[0], a[1] + s * b[1]
        if isinstance(node.op, ast.Mult):
            for lin_side, c_side in ((node.left, node.right), (node.right, node.left)):
                if not _contains_n(c_side):
                    c = const_value(c_side)
                    r = _linear_in_n(lin_side)
                    if r is None or c[0] != "q":
                        return None
                    return r[0] * c[1], r[1] * float(c[1])
            return None
        if isinstance(node.op, ast.Div) and not _contains_n(node.right):
            c = const_value(node.right)
            r = _linear_in_n(node.left)
            if r is None or c[0] != "q" or c[1] == 0:
                return None
            return r[0] / c[1], r[1] / float(c[1])
    return None


def _cmp_const(x: tuple, y: tuple) -> int:
    if const_equal(x, y):
        return 0
    return -1 if value(x) < value(y) else 1


def _cmp_shape(s: Shape, t: Shape) -> int:
    for a, b in ((s.base, t.base), (s.p2, t.p2)):
        c = _cmp_const(a, b)
        if c:
            return c
    return (s.q > t.q) - (s.q < t.q)


def _const_shape(node) -> Shape:
    c = const_value(node)
    return Shape(ONE, ONE, Fraction(0), value(c))


def _shape(node) -> Shape:
    if not _contains_n(node):
        return _const_shape(node)
    if isinstance(node, ast.Name):  # n
        return Shape(ONE, TWO, Fraction(0), 1.0)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        s = _shape(node.operand)
        return Shape(s.base, s.p2, s.q, -s.coef)
    if isinstance(node, ast.Call):
        f, arg = node.func.id, node.args[0]
        if f == "sqrt":
            return _pow_shape(_shape(arg), ("q", Fraction(1, 2)), None)
        if f in ("log", "log2"):
            s = _shape(arg)
            scale = 1.0 if f == "log" else 1 / math.log(2)
            if not const_equal(s.base, ONE) and value(s.base) > 1:
                return Shape(ONE, TWO, Fraction(0), math.log(value(s.base)) * scale)
            p = math.log2(value(s.p2))
            if const_equal(s.base, ONE) and p > 1e-12:
                return Shape(ONE, ONE, Fraction(1), p * math.log(2) * scale)
            raise NotParseable(f"{f}() of a non-growing expression (log log n and similar are not in the grammar)")
        if f == "exp":
            raise NotParseable("exp(...) of n: the exponential base e is transcendental (write 2**n etc., or give expect)")
        if f == "factorial":
            raise NotParseable("factorial of n: factorial-type costs are outside the b^n n^p (log n)^q grammar")
    if isinstance(node, ast.BinOp):
        op = node.op
        if isinstance(op, ast.Pow):
            L, R = node.left, node.right
            if _contains_n(L) and _contains_n(R):
                raise NotParseable("n in both base and exponent (e.g. n**n) is outside the grammar")
            if _contains_n(L):
                return _pow_shape(_shape(L), const_value(R), R)
            lin = _linear_in_n(R)
            if lin is None:
                raise NotParseable("exponent of an exponential is not linear in n")
            if _contains_decimal(L):
                raise NotParseable("decimal literal in an exponential base is an approximation; give expect.base "
                                   "as a minimal polynomial")
            c = const_value(L)
            if not is_exact(c) or value(c) <= 0:
                raise NotParseable(f"exponential base {ast.unparse(L)} is not an exact positive algebraic number")
            alpha, beta = lin
            b = powq(c, alpha)
            if not is_exact(b):
                raise NotParseable(f"base ({ast.unparse(L)})^{alpha} is not exactly representable")
            return Shape(b, ONE, Fraction(0), value(c) ** beta)
        s, t = _shape(node.left) if _contains_n(node.left) else _const_shape(node.left), \
            _shape(node.right) if _contains_n(node.right) else _const_shape(node.right)
        if isinstance(op, ast.Mult):
            return Shape(mul(s.base, t.base), mul(s.p2, t.p2), s.q + t.q, s.coef * t.coef)
        if isinstance(op, ast.Div):
            if t.coef == 0:
                raise NotParseable("division by zero")
            return Shape(div(s.base, t.base), div(s.p2, t.p2), s.q - t.q, s.coef / t.coef)
        if isinstance(op, (ast.Add, ast.Sub)):
            if isinstance(op, ast.Sub):
                t = Shape(t.base, t.p2, t.q, -t.coef)
            c = _cmp_shape(s, t)
            if c > 0:
                return s
            if c < 0:
                return t
            co = s.coef + t.coef
            if abs(co) <= 1e-12 * max(abs(s.coef), abs(t.coef)):
                raise NotParseable("the leading terms cancel; write the cost without cancelling terms")
            return Shape(s.base, s.p2, s.q, co)
    raise NotParseable(f"unsupported expression {ast.dump(node)[:60]}")


def _pow_shape(s: Shape, r: tuple, r_node) -> Shape:
    """s ** r for an n-free exponent r."""
    if r[0] == "q":
        e = r[1]
        b, p2 = powq(s.base, e), powq(s.p2, e)
        if not (is_exact(b) and is_exact(p2)):
            raise NotParseable(f"power {e} of the shape is not exactly representable (e.g. a decimal exponent)")
        coef = s.coef ** float(e) if s.coef > 0 else float("nan")
        return Shape(b, p2, s.q * e, coef)
    # irrational exponent such as log2(7): only n^p ** r with p rational, no base and no log factor
    p = p_rational(s.p2)
    if r_node is None or p is None or not const_equal(s.base, ONE) or s.q != 0:
        raise NotParseable("an irrational exponent is supported only on a pure power of n (n**log2(7))")
    E = exp2_of(r_node)
    if E is None:
        raise NotParseable(f"exponent {ast.unparse(r_node)} is not of the form rational + log2(algebraic)")
    p2 = powq(E, p)
    if not is_exact(p2):
        raise NotParseable("power of n not exactly representable")
    return Shape(ONE, p2, Fraction(0), s.coef ** value(r) if s.coef > 0 else float("nan"))


def parse_cost(expr: str) -> Shape:
    """The claimed growth shape of a cost expression (the V2 grammar of tools/validate.eval_cost).

    Exact for: n, integers, decimals (as exact decimal rationals), phi, sqrt, + - * / **, log/log2 of n-powers,
    c**(alpha*n + beta) with c an exact algebraic constant (rational, a + b sqrt(d), c^(1/v)), n**(rational) and
    n**log2(c). Raises NotParseable for factorial, exp of n, e or pi in a base, decimal bases, n**n, log log n."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise NotParseable(f"syntax error: {e}") from None
    _check_node(tree)
    s = _shape(tree.body)
    if not (s.coef > 0):
        raise NotParseable("the cost is not positive for large n")
    if not (is_exact(s.base) and is_exact(s.p2)):
        raise NotParseable("inexact base or power")
    return s


def parse_expect(expect: dict) -> Shape:
    """Explicit claimed shape: {"base": expr | {"minpoly": [highest first], "approx": x}, "polynomial_factor": expr,
    "log_power": rational}. Missing components default to base 1, polynomial_factor 0, log_power 0."""
    if not isinstance(expect, dict):
        raise InvalidBlock("expect must be an object")
    b = expect.get("base", "1")
    if isinstance(b, dict):
        coeffs = b.get("minpoly")
        approx = b.get("approx")
        if not (isinstance(coeffs, list) and len(coeffs) >= 2 and all(isinstance(c, int) for c in coeffs)
                and isinstance(approx, (int, float))):
            raise InvalidBlock("expect.base as an object needs minpoly (integers, highest degree first) and approx")
        poly = ea.pint(list(reversed(coeffs)))
        if ea.pdeg(poly) < 1 or ea.pdeg(poly) > 8:
            raise InvalidBlock("expect.base.minpoly must have degree 1..8")
        # every real root of every irreducible factor; the one nearest `approx` must be unambiguous
        cands = []
        for f in ea.factor_kronecker(poly):
            for iv in ea.real_roots_isolated(f):
                lo, hi = ea.real_root_approx(f, iv, Fraction(1, 10 ** 24))
                cands.append((abs(float((lo + hi) / 2) - approx), float((lo + hi) / 2), f))
        cands.sort(key=lambda c: c[0])
        if not cands:
            raise InvalidBlock("expect.base: minpoly has no real root")
        if len(cands) > 1 and not cands[0][0] < 0.5 * cands[1][0]:
            raise InvalidBlock("expect.base: approx does not single out one real root of minpoly")
        _, root, mp = cands[0]
        mp = ea.pint(mp)
        if root <= 0:
            raise InvalidBlock("expect.base must be positive")
        base = ("q", Fraction(-mp[0], mp[1])) if len(mp) == 2 else ("p", tuple(mp), root)
    else:
        try:
            tree = ast.parse(str(b), mode="eval")
            _check_node(tree)
            if _contains_n(tree):
                raise InvalidBlock("expect.base must not contain n")
            base = const_value(tree.body)
        except (NotParseable, SyntaxError) as e:
            raise InvalidBlock(f"expect.base: {e}") from None
        if not is_exact(base) or value(base) <= 0:
            raise InvalidBlock("expect.base must be an exact positive constant (or a minpoly object)")
    pf = expect.get("polynomial_factor", "0")
    try:
        tree = ast.parse(str(pf), mode="eval")
        _check_node(tree)
    except (NotParseable, SyntaxError) as e:
        raise InvalidBlock(f"expect.polynomial_factor: {e}") from None
    p2 = exp2_of(tree.body)
    if p2 is None:
        raise InvalidBlock("expect.polynomial_factor must be rational + log2(exact constant), e.g. '-1/2', 'log2(7)'")
    lp = expect.get("log_power", 0)
    try:
        q = Fraction(str(lp))
    except (ValueError, ZeroDivisionError):
        raise InvalidBlock("expect.log_power must be a rational number") from None
    return Shape(base, p2, q, 1.0)


@dataclass(frozen=True)
class Expected:
    lam: tuple       # exact constant: dominant root on the grid
    theta: Fraction  # exponent of t on the grid
    shape: Shape


def expected_on_grid(s: Shape, sequence: str, step: int = 1) -> Expected:
    """What the claimed shape predicts for a guessed recurrence on the grid (lambda, theta in t)."""
    if sequence == "consecutive":
        if s.q != 0:
            raise OutsideGridFamily(f"(log n)^{s.q} is not visible on a consecutive grid (a log factor makes the "
                                    "count non-holonomic in n); use sequence 'doubling'")
        p = p_rational(s.p2)
        if p is None:
            raise OutsideGridFamily(f"n^{math.log2(value(s.p2)):.6g} with an irrational exponent is not visible on a "
                                    "consecutive grid; use sequence 'doubling'")
        lam = powq(s.base, Fraction(step))
        return Expected(lam, p, s)
    if sequence == "doubling":
        if not const_equal(s.base, ONE):
            raise OutsideGridFamily(f"the exponential factor ({const_str(s.base)})^n is not visible on a doubling grid;"
                                    " use sequence 'consecutive'")
        return Expected(s.p2, s.q, s)
    raise InvalidBlock(f"unknown sequence kind {sequence!r}")


# ==============================================================================================================
# Shape block -> grid
# ==============================================================================================================

@dataclass(frozen=True)
class Grid:
    sequence: str
    ns: list
    ts: list      # recurrence variable: n/step (consecutive) or k = log2 n (doubling)
    step: int


def grid_from_block(block: dict) -> Grid:
    if not isinstance(block, dict):
        raise InvalidBlock("shape must be an object")
    seq = block.get("sequence")
    rng = block.get("n_range")
    if seq not in ("consecutive", "doubling"):
        raise InvalidBlock("sequence must be 'consecutive' or 'doubling'")
    if not (isinstance(rng, list) and len(rng) == 2 and all(isinstance(x, int) and x >= 1 for x in rng)
            and rng[0] < rng[1]):
        raise InvalidBlock("n_range must be [lo, hi] with 1 <= lo < hi")
    lo, hi = rng
    if seq == "consecutive":
        step = block.get("step", 1)
        if not (isinstance(step, int) and step >= 1) or lo % step:
            raise InvalidBlock("step must be a positive integer dividing n_range[0]")
        ns = list(range(lo, hi + 1, step))
        ts = [n // step for n in ns]
    else:
        if "step" in block:
            raise InvalidBlock("step applies to consecutive grids only")
        if lo & (lo - 1) or hi & (hi - 1):
            raise InvalidBlock("a doubling grid needs powers of two as n_range endpoints")
        step = 1
        ns, n = [], lo
        while n <= hi:
            ns.append(n)
            n *= 2
        ts = [n.bit_length() - 1 for n in ns]
    if len(ns) > DEFAULTS["max_terms"]:
        raise InvalidBlock(f"the grid has {len(ns)} points; at most {DEFAULTS['max_terms']} are allowed")
    for key in ("max_order", "max_degree"):
        v = block.get(key, DEFAULTS[key])
        if not (isinstance(v, int) and 1 <= v <= 10):
            raise InvalidBlock(f"{key} must be an integer in 1..10")
    h = block.get("holdout")
    if h is not None and not (isinstance(h, int) and h >= DEFAULTS["min_holdout"]):
        raise InvalidBlock(f"holdout must be an integer >= {DEFAULTS['min_holdout']}")
    return Grid(seq, ns, ts, step)


def probe_points(grid: Grid) -> list[int]:
    """The small n at which the instance-dependence probe re-draws instances: the first few grid points >= 3."""
    big = [n for n in grid.ns if n >= 3]
    return (big or grid.ns)[:DEFAULTS["probe_points"]]


# ==============================================================================================================
# Identification
# ==============================================================================================================

def _dominance(chi: list, mp: list[int], iv: tuple, mult: int) -> tuple[str, str]:
    """('certified' | 'numeric' | 'fails', explanation) for the root lam of mp in iv being the dominant term.

    Exact sufficient tests per distinct irreducible factor f of chi (Schur: sum |z|^2 <= ||companion||_F^2):
      f = mp: the other roots of mp are smaller if S(mp) - lo^2 < lo^2;
      f != mp: all roots of f are smaller if S(f) < lo^2; or, for rational lam, all roots of f have modulus exactly
      lam (f(lam x) is cyclotomic) and f has a LOWER multiplicity than mp (e.g. floor-type parity terms (-1)^n
      beside a polynomial count: n^(m-1) still dominates).
    Otherwise a floating-point Durand-Kerner check is reported ('numeric'/'fails'); it is never a certificate."""
    lo = Fraction(iv[0])
    lam_rational = len(mp) == 2
    lamq = Fraction(-mp[0], mp[1]) if lam_rational else None
    groups: dict[tuple, int] = {}
    for f in ea.factor_kronecker(chi):
        groups[tuple(ea.pint(f))] = groups.get(tuple(ea.pint(f)), 0) + 1
    ok, notes = True, []
    for f, mf in groups.items():
        f = list(f)
        if f == ea.pint(mp):
            if ea.pdeg(f) > 1 and not ea.schur_sum_sq_bound(f) - lo * lo < lo * lo:
                ok = False
                notes.append(f"conjugates of {ea.pstr(f)} not bounded")
            continue
        if ea.schur_sum_sq_bound(f) < lo * lo:
            continue
        if lam_rational and lamq > 0 and mf < mult and _all_roots_modulus(f, lamq):
            notes.append(f"{ea.pstr(f)}: same modulus, lower multiplicity")
            continue
        ok = False
        notes.append(f"{ea.pstr(f)} not bounded")
    if ok:
        return "certified", "; ".join(notes) or "Schur bounds"
    roots = ea.durand_kerner(chi)
    lam = float((Fraction(iv[0]) + Fraction(iv[1])) / 2)
    others = [z for z in roots if abs(z - lam) > 1e-7 * max(1.0, lam)]
    num_ok = all(abs(z) < lam * (1 - 1e-9) for z in others)
    return ("numeric" if num_ok else "fails"), "; ".join(notes)


def _all_roots_modulus(f: list[int], r: Fraction) -> bool:
    """Do all complex roots of f have modulus exactly r? (f(r x) scaled is a product of cyclotomic polynomials.)"""
    g = ea.pint([Fraction(c) * r ** i for i, c in enumerate(f)])
    d = ea.pdeg(g)
    for N in range(1, 8 * d * d + 3):
        xn = [Fraction(-1)] + [Fraction(0)] * (N - 1) + [Fraction(1)]
        if not ea.pdivmod(xn, g)[1] and ea.pdeg(ea.pgcd(g, ea.pderiv(g))) == 0:
            return True
    return False


def _c_finite(seq: list, h: int, extra: int, max_order: int) -> dict:
    train = seq[:-h]
    c = rc.berlekamp_massey(train)
    L = len(c)
    out = {"kind": "C-finite", "order": L, "terms_used": len(train), "terms_checked": len(seq), "holdout": h}
    if L == 0:
        return {**out, "status": "degenerate"}
    if L > max_order:
        return {**out, "status": "order_exceeds_limit"}
    if 2 * L + extra > len(train):
        return {**out, "status": "too_few", "needed": 2 * L + extra + h}
    ok = all(Fraction(seq[n]) == sum(c[i - 1] * Fraction(seq[n - i]) for i in range(1, L + 1))
             for n in range(L, len(seq)))
    if not ok:
        bad = next(n for n in range(L, len(seq))
                   if Fraction(seq[n]) != sum(c[i - 1] * Fraction(seq[n - i]) for i in range(1, L + 1)))
        return {**out, "status": "holdout_failed", "first_failure_index": bad}
    charpoly = [-x for x in reversed(c)] + [Fraction(1)]
    return {**out, "status": "found", "coeffs": c, "charpoly": charpoly}


def _p_recursive(seq: list, t0: int, h: int, extra: int, max_order: int, max_degree: int) -> tuple[dict | None, list]:
    """Search order 1..max_order, degree 1..max_degree (degree 0 is the C-finite case), smallest order+degree first.
    Returns (accepted guess or None, per-candidate statuses)."""
    statuses = []
    train = seq[:-h]
    for total in range(2, max_order + max_degree + 1):
        for order in range(1, max_order + 1):
            degree = total - order
            if not 1 <= degree <= max_degree:
                continue
            unknowns = (order + 1) * (degree + 1)
            rows = []
            for k in range(order, len(train)):
                t = t0 + k
                rows.append([Fraction(t) ** j * Fraction(train[k - i]) for i in range(order + 1)
                             for j in range(degree + 1)])
            if len(rows) < unknowns - 1 + extra:
                statuses.append((order, degree, "too_few"))
                continue
            ns = ea.nullspace(rows)
            if not ns:
                statuses.append((order, degree, "none"))
                continue
            if len(ns) > 1:
                statuses.append((order, degree, "multi"))
                continue
            v = ns[0]
            polys = [ea.ptrim(v[i * (degree + 1):(i + 1) * (degree + 1)]) for i in range(order + 1)]
            if not polys[0]:
                statuses.append((order, degree, "degenerate"))
                continue

            def residual(k):
                t = t0 + k
                return sum(ea.peval(polys[i], Fraction(t)) * Fraction(seq[k - i]) for i in range(order + 1))

            if any(residual(k) != 0 for k in range(order, len(seq))):
                statuses.append((order, degree, "holdout_failed"))
                continue
            statuses.append((order, degree, "found"))
            return ({"kind": "P-recursive", "order": order, "degree": degree, "polys": polys, "start": t0,
                     "equations": len(rows), "unknowns": unknowns, "terms_used": len(train),
                     "terms_checked": len(seq), "holdout": h}, statuses)
    return None, statuses


def _recurrence_str(g: dict) -> str:
    if g["kind"] == "C-finite":
        terms = " + ".join(f"({c})a(t-{i + 1})" for i, c in enumerate(g["coeffs"]) if c)
        return f"a(t) = {terms}"
    return " + ".join(f"({ea.pstr(p, 't')})a(t-{i})" for i, p in enumerate(g["polys"]) if p) + " = 0"


def identify(seq: list[int], ts: list[int], block: dict | None = None) -> dict:
    """Identify the growth of an exact integer sequence a(t) on consecutive t (t = ts[0], ts[0]+1, ...).

    Returns {"status": "found", "lambda", "minpoly", "theta", ...} or {"status": <UNDETERMINED reason>, ...}."""
    block = block or {}
    max_order = block.get("max_order", DEFAULTS["max_order"])
    max_degree = block.get("max_degree", DEFAULTS["max_degree"])
    h_cf = block.get("holdout", DEFAULTS["holdout_c_finite"])
    h_pr = block.get("holdout", DEFAULTS["holdout_p_recursive"])
    limits = {"max_order": max_order, "max_degree": max_degree, "holdout_c_finite": h_cf,
              "holdout_p_recursive": h_pr, "extra_c_finite": DEFAULTS["extra_c_finite"],
              "extra_p_recursive": DEFAULTS["extra_p_recursive"]}
    if any(ts[i + 1] != ts[i] + 1 for i in range(len(ts) - 1)):
        return {"status": "invalid_shape_block", "detail": "recurrence variable is not consecutive", "limits": limits}
    if len(seq) < 2 * 1 + DEFAULTS["extra_c_finite"] + h_cf:
        return {"status": "too_few_terms", "limits": limits,
                "detail": f"{len(seq)} terms; even an order-1 recurrence needs {2 + DEFAULTS['extra_c_finite'] + h_cf}"}
    cf = _c_finite(seq, h_cf, DEFAULTS["extra_c_finite"], max_order)
    g = None
    pr_status: list = []
    if cf["status"] == "found":
        g = cf
    else:
        g, pr_status = _p_recursive(seq, ts[0], h_pr, DEFAULTS["extra_p_recursive"], max_order, max_degree)
    search = {"c_finite": {k: v for k, v in cf.items() if k in ("status", "order", "needed", "first_failure_index")},
              "p_recursive": [f"{o}/{d}:{s}" for o, d, s in pr_status]}
    if g is None:
        pr = {s for _, _, s in pr_status}
        if cf["status"] == "holdout_failed" or "holdout_failed" in pr:
            reason, det = "holdout_not_reproduced", (
                f"C-finite order {cf['order']} fitted the training terms but failed term index "
                f"{cf.get('first_failure_index')}" if cf["status"] == "holdout_failed"
                else "a P-recursive guess fitted the training terms but failed a held-out term")
        elif "multi" in pr:
            reason, det = "solution_space_not_one_dimensional", "every fitting P-recursive system had a nullspace of dimension > 1"
        elif cf["status"] == "too_few":
            reason, det = "too_few_terms", (f"shortest C-finite recurrence of the training terms has order {cf['order']}; "
                                            f"confirming it needs at least {cf['needed']} terms (a longer prefix may reveal a higher order), "
                                            f"{len(seq)} available")
        elif pr_status and all(s == "too_few" for _, _, s in pr_status):
            reason, det = "too_few_terms", "no P-recursive candidate within the limits is overdetermined by these terms"
        else:
            tested = [f"{o}/{d}" for o, d, s in pr_status if s != "too_few"]
            reason, det = "no_recurrence_within_limits", (
                f"C-finite: {cf['status']} (order {cf['order']}); P-recursive order/degree tested: "
                f"{', '.join(tested) or 'none'}; limits {max_order}/{max_degree}")
        return {"status": reason, "detail": det, "search": search, "limits": limits}

    found = {"recurrence_kind": g["kind"], "order": g["order"], "recurrence": _recurrence_str(g),
             "terms_used": g["terms_used"], "terms_checked": g["terms_checked"], "holdout": g["holdout"]}
    if g["kind"] == "P-recursive":
        found["degree"] = g["degree"]
        chi, D, alpha, beta = rc.p_recursive_characteristic(g)
        if alpha[0] == 0:
            return {"status": "factorial_type_growth", "found": found, "search": search, "limits": limits,
                    "detail": f"deg p_0 < max degree {D}: the solutions grow factorially (super-exponential); "
                              "the b^n n^p (log n)^q shape does not apply"}
    else:
        chi = g["charpoly"]
    gr = rc.growth_from_charpoly(chi)
    found["characteristic_polynomial"] = ea.pstr(chi)
    found["characteristic_factors"] = [ea.pstr(f) for f in ea.factor_kronecker(chi)]
    if gr["lambda"] is None:
        return {"status": "asymptotics_not_determined", "found": found, "search": search, "limits": limits,
                "detail": "the characteristic polynomial has no real root"}
    mp, iv, mult = ea.pint(gr["minpoly"]), gr["lambda_interval"], gr["multiplicity"]
    found.update(lambda_value=gr["lambda"], lambda_minpoly=ea.pstr(mp), lambda_minpoly_coeffs=list(reversed(mp)),
                 multiplicity=mult)
    if g["kind"] == "P-recursive" and mult > 1:
        return {"status": "asymptotics_not_determined", "found": found, "search": search, "limits": limits,
                "detail": "the dominant root of the P-recursive characteristic polynomial is repeated; the exact "
                          "theta formula needs a simple root"}
    cert, why = _dominance(chi, mp, iv, mult)
    found["dominance"] = cert
    if cert != "certified":
        return {"status": "dominance_not_certified", "found": found, "search": search, "limits": limits,
                "detail": f"exact test failed ({why}); floating-point check: {cert}"}
    if g["kind"] == "C-finite":
        theta = Fraction(mult - 1)
        found["theta_rule"] = "multiplicity - 1 (minimal recurrence: every root appears with full multiplicity)"
    else:
        th = rc.theta_p_recursive(g, gr["minpoly"])
        theta = th[0] if len(th) == 1 else (Fraction(0) if not th else None)
        found["theta_rule"] = "Birkhoff-Trjitzinsky balance at order 1/t (simple root)"
        tnum = rc.theta_numeric(seq, gr["lambda"], start=ts[0], tail=min(6, len(seq)))
        found["theta_numeric"] = round(tnum, 6)
        if theta is None:
            found["theta"] = "in Q(lambda): " + ea.pstr(th, "lambda")
        if theta is None or abs(tnum - float(theta)) > DEFAULTS["theta_guard"]:
            return {"status": "asymptotics_not_determined", "found": found, "search": search, "limits": limits,
                    "detail": f"numeric slope {tnum:.4f} disagrees with the exact theta "
                              f"({'irrational' if theta is None else theta}) by more than "
                              f"{DEFAULTS['theta_guard']}: the counts may follow a subdominant solution"}
    found["theta"] = str(theta)
    return {"status": "found", "found": found, "search": search, "limits": limits,
            "_lambda": (mp, gr["lambda"]), "_theta": theta}


# ==============================================================================================================
# Decision
# ==============================================================================================================

def describe(sequence: str, lam_mp: list[int], lam_val: float, theta: Fraction | None, step: int = 1) -> dict:
    """The three components (base, polynomial_factor, log_power) that a grid result implies."""
    mpstr = ea.pstr(lam_mp)
    if sequence == "consecutive":
        base = f"{lam_val:.12g} ({mpstr})" if step == 1 else             f"{lam_val ** (1 / step):.12g} (root per step of {step}: {lam_val:.12g}, {mpstr})"
        return {"base": base, "polynomial_factor": f"n^{_fs(theta)}",
                "log_power": "not visible on a consecutive grid"}
    p2 = ("q", Fraction(-lam_mp[0], lam_mp[1])) if len(lam_mp) == 2 else None
    pr = p_rational(p2) if p2 else None
    if pr is not None:
        pf = f"n^{_fs(pr)}"
    else:
        pf = f"n^log2({lam_val:.12g}) = n^{math.log2(lam_val):.6f} (2^p root of {mpstr})"
    return {"base": "not visible on a doubling grid (must be 1)", "polynomial_factor": pf,
            "log_power": f"(log n)^{_fs(theta)}"}


def _fs(x) -> str:
    if x is None:
        return "?"
    x = Fraction(x)
    return str(x) if x.denominator == 1 else f"({x})"


def outcome(category: str, reason: str, **fields) -> dict:
    assert REASONS[reason][0] == category, (category, reason)
    return {"category": category, "reason": reason, **fields}


def run(cost: str, block: dict, grid: Grid, values: list | None, *, samples: int = 1,
        probe: dict | None = None) -> dict:
    """Decide the category of one shape run. `values` are the counts on grid.ns (None if not computed)."""
    base_fields = {"version": SHAPE_VERSION, "sequence": grid.sequence, "n_values": grid.ns}
    if grid.step != 1:
        base_fields["step"] = grid.step
    if samples > 1:
        return outcome("UNDETERMINED", "randomised_counts", **base_fields,
                       detail=f"samples = {samples}: V2 averages a random count; an average of finitely many draws "
                              "is not an exact sequence")
    if probe is not None:
        base_fields["instance_probe"] = probe
        if not probe.get("identical", True):
            return outcome("UNDETERMINED", "instance_dependent_counts", **base_fields,
                           detail=probe.get("detail", "counts differ between seeds"))
    ints = []
    for v in values:
        if isinstance(v, bool):
            ints = None
            break
        if isinstance(v, int):
            ints.append(v)
        elif isinstance(v, float) and v.is_integer() and abs(v) < 2 ** 53:
            ints.append(int(v))
        elif isinstance(v, Fraction) and v.denominator == 1:
            ints.append(int(v))
        else:
            ints = None
            break
    if ints is None:
        return outcome("UNDETERMINED", "non_integer_counts", **base_fields, values=[repr(v) for v in values],
                       detail="the diagnostic needs exact integer counts")
    base_fields["values"] = ints
    ident = identify(ints, grid.ts, block)
    fields = {**base_fields, "limits": ident.get("limits"), "search": ident.get("search")}
    if "found" in ident:
        fields["found_recurrence"] = ident["found"]
    # claimed shape (computed in every case, recorded for information)
    claimed, claim_reason, claim_detail = None, None, None
    try:
        s = parse_expect(block["expect"]) if "expect" in block else parse_cost(cost)
        exp = expected_on_grid(s, grid.sequence, grid.step)
        claimed = exp
        fields["claimed"] = {"source": "expect" if "expect" in block else "cost",
                             **describe(grid.sequence, minpoly(exp.lam), value(exp.lam), exp.theta, grid.step)}
    except InvalidBlock as e:
        claim_reason, claim_detail = "invalid_shape_block", str(e)
    except NotParseable as e:
        claim_reason, claim_detail = "cost_not_parseable", str(e)
    except OutsideGridFamily as e:
        claim_reason, claim_detail = "cost_outside_grid_family", str(e)
    if claim_reason:
        fields["claimed"] = {"source": "expect" if "expect" in block else "cost", "error": claim_detail}
    if ident["status"] == "found":
        mp, lv = ident["_lambda"]
        fields["found"] = describe(grid.sequence, mp, lv, ident["_theta"], grid.step)
    if block.get("python_version_dependent"):
        return outcome("UNDETERMINED", "python_version_dependent", **fields,
                       detail="declared in the shape block: the count includes comparisons inside CPython built-ins, "
                              "so an exact recurrence may hold for this Python version only (RL-069)")
    if ident["status"] != "found":
        return outcome("UNDETERMINED", ident["status"], **fields, detail=ident.get("detail", ""))
    if claim_reason:
        return outcome("UNDETERMINED", claim_reason, **fields, detail=claim_detail)
    mp, lv = ident["_lambda"]
    same_lam = same_number(mp, lv, minpoly(claimed.lam), value(claimed.lam))
    same_theta = ident["_theta"] is not None and ident["_theta"] == claimed.theta
    if same_lam and same_theta:
        return outcome("MATCH", "exact_shape_agrees", **fields,
                       detail="dominant root (exact minimal polynomial) and exponent agree with the claim")
    names = ("base", "polynomial_factor") if grid.sequence == "consecutive" else ("polynomial_factor", "log_power")
    differs = [nm for nm, same in zip(names, (same_lam, same_theta)) if not same]
    return outcome("MISMATCH", "differs", **fields, differs=differs,
                   detail="; ".join(f"{d}: found {fields['found'][d]}, claimed {fields['claimed'][d]}" for d in differs))


def summary_line(res: dict) -> str:
    """One human-readable line for verbose validator output."""
    cat, reason = res["category"], res["reason"]
    if cat == "SKIPPED":
        return f"SKIPPED ({reason})"
    grid = ""
    if res.get("n_values"):
        ns = res["n_values"]
        grid = f"[{res['sequence']} n={ns[0]}..{ns[-1]}, {len(ns)} terms] "
    if cat == "MATCH":
        f = res["found"]
        comp = f["base"] if res["sequence"] == "consecutive" else f["log_power"]
        rec = res.get("found_recurrence", {})
        return (f"{grid}MATCH  {f['polynomial_factor']}, "
                f"{'base ' + comp if res['sequence'] == 'consecutive' else comp}  "
                f"({rec.get('recurrence_kind')} order {rec.get('order')}, {rec.get('terms_used')} terms used, "
                f"{rec.get('terms_checked')} checked)")
    if cat == "MISMATCH":
        return f"{grid}MISMATCH ({', '.join(res['differs'])}): {res['detail']}"
    return f"{grid}UNDETERMINED ({reason}): {res.get('detail', '')}"

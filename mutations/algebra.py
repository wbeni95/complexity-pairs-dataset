"""Algebraic structures for operation-swap mutations (standard library only).

A `Structure` bundles a carrier sampler, the two operations (add = "plus" ⊕, mul = "times" ⊗), their identities
and, when they exist, an additive inverse (neg), a multiplicative inverse (inv) and division by an integer
(div_int). Nothing here is assumed about the algebraic properties: `check_properties` tests them mechanically,
exhaustively on finite carriers and on a stated bounded sample domain on infinite ones.

Element wrappers make UNCHANGED copies of repository implementations compute in a substituted structure:

* `make_ring_elem(S)`: for code written over (+, ×) ("ring origin"): Python `+` is ⊕, `*` is ⊗, `-` is the
  additive inverse (raises `UndefinedOp` if S has none), `x // k` is multiplication by k⁻¹ (k an int), `x % m` is
  the identity (reduction is part of S's representation). A plain int k that meets an element is lifted to
  k·1 (k-fold ⊕ of the unit), which is how literal 0 / 1 in the code acquire their meaning.
* `make_tropical_elem(S, sense)`: for code written over (min, +) or (max, +) ("tropical origin"): Python `+` is
  ⊗, comparisons express the ⊕-order (a "better" than b iff a ⊕ b = a ≠ b; raises `OrderError` if ⊕ is not
  selective on the operands), literal 0 is lifted to the unit 1 and ±inf to the zero 0. Any other literal has
  no meaning in S and raises `LiftError`.
* `Rev`: an int whose comparisons are reversed while arithmetic is unchanged (comparison-flip mirror).

Every operation performed through a wrapper increments a counter dict, which gives exact operation counts.
"""
from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction

INF = math.inf


class UndefinedOp(TypeError):
    """The code asks for an operation the structure does not have (e.g. subtraction in a semiring)."""


class OrderError(TypeError):
    """Comparison requested, but ⊕ is not selective on the operands (no total order to compare by)."""


class LiftError(TypeError):
    """A literal in the code has no meaning in the substituted structure."""


# --------------------------------------------------------------------------------------------------
# Structures
# --------------------------------------------------------------------------------------------------

class Structure:
    name = "?"
    label = "?"
    finite_carrier: list | None = None   # full carrier if finite (properties checked exhaustively)
    domain: list = []                     # bounded sample domain for property checks on infinite carriers
    zero = None
    one = None
    has_neg = False
    has_inv = False
    commutative_mul_expected = True       # documentation only; checked mechanically
    kind = "semiring"                     # "semiring", "monoid" (only ⊕ meaningful), "magma-mul" (only ⊗)

    def add(self, a, b):
        raise UndefinedOp(f"{self.name}: no ⊕")

    def mul(self, a, b):
        raise UndefinedOp(f"{self.name}: no ⊗")

    def neg(self, a):
        raise UndefinedOp(f"{self.name}: no additive inverse (subtraction undefined)")

    def inv(self, a):
        raise UndefinedOp(f"{self.name}: no multiplicative inverse")

    def div_int(self, a, k: int):
        """a · (k·1)⁻¹."""
        kk = self.lift(k)
        return self.mul(a, self.inv(kk))

    def div(self, a, b):
        """Exact division a / b (a · b⁻¹)."""
        return self.mul(a, self.inv(b))

    def lift(self, k: int):
        """k-fold ⊕ of the unit (negative k: additive inverse)."""
        if k == 0:
            return self.zero
        if k < 0:
            return self.neg(self.lift(-k))
        acc = self.one
        for _ in range(k - 1):
            acc = self.add(acc, self.one)
        return acc

    def sample(self, rng: random.Random):
        return rng.choice(self.finite_carrier if self.finite_carrier else self.domain)

    def eq(self, a, b):
        return a == b

    def canon(self, a):
        return a

    def __repr__(self):
        return f"<{self.name}>"


class IntRing(Structure):
    name, label = "Z", "(+,×) over Z"
    domain = list(range(-6, 7))
    zero, one, has_neg = 0, 1, True

    def add(self, a, b): return a + b
    def mul(self, a, b): return a * b
    def neg(self, a): return -a

    def inv(self, a):
        if a in (1, -1):
            return a
        raise UndefinedOp(f"Z: {a} has no multiplicative inverse")

    def div_int(self, a, k):
        q, r = divmod(a, k)
        if r:
            raise UndefinedOp(f"Z: {a} is not divisible by {k}")
        return q

    def div(self, a, b):
        if b == 0:
            raise UndefinedOp("Z: division by 0")
        return self.div_int(a, b)

    def lift(self, k): return k
    def sample(self, rng): return rng.randint(-5, 5)


class Zp(Structure):
    def __init__(self, p: int):
        self.p = p
        self.name, self.label = f"Z{p}", f"(+,×) over Z_{p}"
        self.zero, self.one, self.has_neg = 0, 1 % p, True
        self.finite_carrier = list(range(p)) if p <= 97 else None
        self.domain = list(range(min(p, 41)))
        self.has_inv = _is_prime(p)

    def add(self, a, b): return (a + b) % self.p
    def mul(self, a, b): return a * b % self.p
    def neg(self, a): return -a % self.p

    def inv(self, a):
        a %= self.p
        if math.gcd(a, self.p) != 1:
            raise UndefinedOp(f"Z_{self.p}: {a} has no multiplicative inverse")
        return pow(a, -1, self.p)

    def lift(self, k): return k % self.p
    def sample(self, rng): return rng.randrange(self.p)
    def canon(self, a): return a % self.p


class GF2(Zp):
    """(xor, and) on {0, 1}: the field with two elements."""
    def __init__(self):
        super().__init__(2)
        self.name, self.label = "GF2", "(xor,and) over GF(2)"


def _tadd_min(a, b): return a if a <= b else b
def _tadd_max(a, b): return a if a >= b else b


class MinPlus(Structure):
    """(min, +) over Z ∪ {+inf}. lo = smallest sampled weight (0 by default: non-negative weights)."""
    def __init__(self, lo=0, hi=20, name=None):
        self.lo, self.hi = lo, hi
        self.name = name or ("MinPlus" if lo >= 0 else "MinPlusZ")
        self.label = "(min,+)" + ("" if lo >= 0 else f" incl. negatives (weights {lo}..{hi})")
        self.zero, self.one = INF, 0
        self.domain = sorted(set([lo, lo + 1, 0, 1, 2, 3, 5, hi // 2, hi])) + [INF]

    def add(self, a, b): return _tadd_min(a, b)
    def mul(self, a, b): return INF if (a == INF or b == INF) else a + b
    def sample(self, rng): return INF if rng.random() < 0.1 else rng.randint(self.lo, self.hi)


class MaxPlus(Structure):
    def __init__(self, lo=0, hi=20, name=None):
        self.lo, self.hi = lo, hi
        self.name = name or "MaxPlus"
        self.label = "(max,+)" + ("" if lo >= 0 else f" incl. negatives (weights {lo}..{hi})")
        self.zero, self.one = -INF, 0
        self.domain = sorted(set([lo, lo + 1, 0, 1, 2, 3, 5, hi // 2, hi])) + [-INF]

    def add(self, a, b): return _tadd_max(a, b)
    def mul(self, a, b): return -INF if (a == -INF or b == -INF) else a + b
    def sample(self, rng): return -INF if rng.random() < 0.1 else rng.randint(self.lo, self.hi)


class MaxMin(Structure):
    """(max, min) bottleneck / widest-path semiring over Z ∪ {±inf}."""
    name, label = "MaxMin", "(max,min) bottleneck"
    zero, one = -INF, INF
    domain = [-INF, 0, 1, 2, 3, 5, 8, 13, 20, INF]

    def add(self, a, b): return _tadd_max(a, b)
    def mul(self, a, b): return _tadd_min(a, b)
    def sample(self, rng): return -INF if rng.random() < 0.1 else rng.randint(0, 20)


class MinMax(Structure):
    """(min, max) minimax semiring over Z ∪ {±inf}."""
    name, label = "MinMax", "(min,max) minimax"
    zero, one = INF, -INF
    domain = [-INF, 0, 1, 2, 3, 5, 8, 13, 20, INF]

    def add(self, a, b): return _tadd_min(a, b)
    def mul(self, a, b): return _tadd_max(a, b)
    def sample(self, rng): return INF if rng.random() < 0.1 else rng.randint(0, 20)


class Boolean(Structure):
    name, label = "Bool", "(∨,∧) Boolean"
    finite_carrier = [False, True]
    zero, one = False, True

    def add(self, a, b): return a or b
    def mul(self, a, b): return a and b
    def sample(self, rng): return rng.random() < 0.5


class MaxTimesUnit(Structure):
    """(max, ×) on [0, 1] ∩ {k/8}: the Viterbi / reliability semiring."""
    name, label = "Viterbi", "(max,×) on [0,1]"
    zero, one = Fraction(0), Fraction(1)
    domain = [Fraction(k, 8) for k in range(9)]

    def add(self, a, b): return _tadd_max(a, b)
    def mul(self, a, b): return a * b
    def sample(self, rng): return Fraction(rng.randint(0, 8), 8)


class MaxTimesZ(Structure):
    """(max, ×) on Z ∪ {-inf} INCLUDING negative numbers. Not a semiring (distributivity fails); kept as a probe."""
    name, label = "MaxTimesZ", "(max,×) on Z incl. negatives"
    zero, one = -INF, 1
    domain = [-INF, -5, -3, -2, -1, 0, 1, 2, 3, 5]

    def add(self, a, b): return _tadd_max(a, b)

    def mul(self, a, b):
        if a == -INF or b == -INF:
            return -INF
        return a * b

    def sample(self, rng): return rng.randint(-5, 5)


class MinTimesPos(Structure):
    """(min, ×) on positive integers ∪ {+inf}."""
    name, label = "MinTimesPos", "(min,×) on Z>0"
    zero, one = INF, 1
    domain = [1, 2, 3, 4, 5, 7, 9, INF]

    def add(self, a, b): return _tadd_min(a, b)
    def mul(self, a, b): return INF if (a == INF or b == INF) else a * b
    def sample(self, rng): return rng.randint(1, 9)


# ---- ⊕-only structures (monoids / magmas), for transforms that use one operation only ---------------

class Monoid(Structure):
    kind = "monoid"

    def __init__(self, name, label, op, zero, sampler, domain, has_neg=False, neg=None):
        self.name, self.label, self._op, self.zero = name, label, op, zero
        self._sampler, self.domain, self.has_neg, self._neg = sampler, domain, has_neg, neg
        self.one = None

    def add(self, a, b): return self._op(a, b)

    def neg(self, a):
        if self._neg is None:
            raise UndefinedOp(f"{self.name}: no inverse")
        return self._neg(a)

    def lift(self, k):
        if k == 0 and self.zero is not None:
            return self.zero
        raise LiftError(f"{self.name}: literal {k} has no meaning")

    def sample(self, rng): return self._sampler(rng)


def monoids() -> dict[str, Monoid]:
    s = lambda lo, hi: (lambda rng: rng.randint(lo, hi))  # noqa: E731
    return {
        "Sum": Monoid("Sum", "(Z,+)", lambda a, b: a + b, 0, s(-9, 9), list(range(-5, 6)), True, lambda a: -a),
        "Min": Monoid("Min", "(Z∪{+inf},min)", _tadd_min, INF, s(-20, 20), [-5, -1, 0, 1, 3, 7, INF]),
        "Max": Monoid("Max", "(Z∪{-inf},max)", _tadd_max, -INF, s(-20, 20), [-INF, -5, -1, 0, 1, 3, 7]),
        "Xor": Monoid("Xor", "(N,xor)", lambda a, b: a ^ b, 0, s(0, 63), list(range(0, 16)), True, lambda a: a),
        "Or": Monoid("Or", "(N,|)", lambda a, b: a | b, 0, s(0, 63), list(range(0, 16))),
        "And": Monoid("And", "(N,&) with zero=-1", lambda a, b: a & b, -1, s(0, 63), [-1] + list(range(0, 16))),
        "Gcd": Monoid("Gcd", "(N,gcd)", math.gcd, 0, s(0, 60), list(range(0, 13))),
        "Concat": Monoid("Concat", "(strings,concatenation)", lambda a, b: a + b, "",
                         lambda rng: rng.choice("abc"), ["", "a", "b", "ab", "ba"]),
        "Minus": Monoid("Minus", "(Z, a-b) [non-associative]", lambda a, b: a - b, 0, s(-9, 9), list(range(-4, 5))),
        "LeftZero": Monoid("LeftZero", "(Z, a⊕b=a) [left-zero band, no identity]", lambda a, b: a, None,
                           s(-9, 9), list(range(-3, 4))),
    }


# ---- ⊗-only structures (for exponentiation by squaring) -------------------------------------------

class MulMagma(Structure):
    kind = "magma-mul"

    def __init__(self, name, label, op, one, sampler, domain, eq=None):
        self.name, self.label, self._op, self.one = name, label, op, one
        self._sampler, self.domain, self.zero = sampler, domain, None
        self._eq = eq

    def mul(self, a, b): return self._op(a, b)

    def lift(self, k):
        if k == 1 and self.one is not None:
            return self.one
        raise LiftError(f"{self.name}: literal {k} has no meaning (no identity element)" if self.one is None
                        else f"{self.name}: literal {k} has no meaning")

    def sample(self, rng): return self._sampler(rng)


def _oct_mul(x, y, m):
    """Octonion product via Cayley-Dickson on quaternion pairs, integer coefficients mod m."""
    def qmul(a, b):
        a0, a1, a2, a3 = a
        b0, b1, b2, b3 = b
        return ((a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3) % m, (a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2) % m,
                (a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1) % m, (a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0) % m)

    def qconj(a): return (a[0], -a[1] % m, -a[2] % m, -a[3] % m)
    def qadd(a, b): return tuple((u + v) % m for u, v in zip(a, b))
    def qsub(a, b): return tuple((u - v) % m for u, v in zip(a, b))
    a, b, c, d = x[:4], x[4:], y[:4], y[4:]
    # (a, b)(c, d) = (ac - d* b, da + b c*)
    return qsub(qmul(a, c), qmul(qconj(d), b)) + qadd(qmul(d, a), qmul(b, qconj(c)))


def mul_magmas(m: int = 1009) -> dict[str, MulMagma]:
    r = lambda rng: rng.randrange(m)  # noqa: E731
    dom = list(range(0, 12)) + [m - 1, m - 2]
    mat_one = (1, 0, 0, 1)

    def matmul(x, y):
        a, b, c, d = x
        e, f, g, h = y
        return ((a * e + b * g) % m, (a * f + b * h) % m, (c * e + d * g) % m, (c * f + d * h) % m)

    oct_one = (1, 0, 0, 0, 0, 0, 0, 0)
    return {
        "MulMod": MulMagma("MulMod", f"(Z_{m},×)", lambda a, b: a * b % m, 1, r, dom),
        "AddMod": MulMagma("AddMod", f"(Z_{m},+) as ⊗", lambda a, b: (a + b) % m, 0, r, dom),
        "Min": MulMagma("Min", "(Z∪{+inf},min) as ⊗", _tadd_min, INF, lambda rng: rng.randint(-50, 50), [-3, 0, 2, 9, INF]),
        "Circle": MulMagma("Circle", f"(Z_{m}, a+b+ab) [associative]", lambda a, b: (a + b + a * b) % m, 0, r, dom),
        "Mat2": MulMagma("Mat2", f"2x2 matrices over Z_{m} [associative, non-commutative]", matmul, mat_one,
                         lambda rng: tuple(rng.randrange(m) for _ in range(4)),
                         [(1, 1, 1, 0), (0, 1, 1, 0), (2, 3, 5, 7), (1, 0, 0, 1), (0, 0, 1, 1)]),
        "Octonion": MulMagma("Octonion", f"octonions over Z_{m} [non-associative, alternative]",
                             lambda a, b: _oct_mul(a, b, m), oct_one,
                             lambda rng: tuple(rng.randrange(m) for _ in range(8)),
                             [oct_one, (0, 1, 0, 0, 0, 0, 0, 0), (0, 0, 1, 0, 0, 1, 0, 0), (1, 2, 3, 4, 5, 6, 7, 8),
                              (0, 0, 0, 1, 0, 0, 1, 0), (3, 0, 0, 0, 0, 0, 0, 1)]),
        "Skew": MulMagma("Skew", f"(Z_{m}, a+b+ab(a-b)) [identity 0, non-associative]",
                         lambda a, b: (a + b + a * b * (a - b)) % m, 0, r, dom),
        "CommNA": MulMagma("CommNA", f"(Z_{m}, a+b+a²b²) [identity 0, commutative, non-associative]",
                           lambda a, b: (a + b + a * a * b * b) % m, 0, r, dom),
    }


def semirings() -> dict[str, Structure]:
    """The operation-swap targets of the pilot (the brief's list plus probes)."""
    return {
        "Z": IntRing(),
        "Z7": Zp(7),
        "GF2": GF2(),
        "MinPlus": MinPlus(),
        "MaxPlus": MaxPlus(),
        "MaxMin": MaxMin(),
        "Bool": Boolean(),
        "MinMax": MinMax(),
        "Viterbi": MaxTimesUnit(),
        "MinTimesPos": MinTimesPos(),
        "MaxTimesZ": MaxTimesZ(),
        "MinPlusZ": MinPlus(lo=-10, hi=10),
    }


def _generator(p):
    """Least generator of Z_p^* (p prime): g^((p-1)/q) != 1 for every prime q | p-1."""
    m, qs, d = p - 1, [], 2
    while d * d <= m:
        if m % d == 0:
            qs.append(d)
            while m % d == 0:
                m //= d
        d += 1
    if m > 1:
        qs.append(m)
    return next(g for g in range(2, p) if all(pow(g, (p - 1) // q, p) != 1 for q in qs))


def _is_prime(p):
    return p >= 2 and all(p % d for d in range(2, int(p ** 0.5) + 1))


# --------------------------------------------------------------------------------------------------
# Element wrappers (injection into unchanged code)
# --------------------------------------------------------------------------------------------------

def new_counter() -> dict:
    return {"add": 0, "mul": 0, "neg": 0, "inv": 0, "cmp": 0}


def make_ring_elem(S: Structure, counter: dict | None = None, sub_fallback: str | None = None):
    """Element class for (+,×)-origin code. sub_fallback='add' makes a - b compute a ⊕ b (sign-forgetting probe)."""
    cnt = counter if counter is not None else new_counter()

    class RE:
        __slots__ = ("v",)
        structure = S
        counter = cnt

        def __init__(self, v):
            self.v = v

        @staticmethod
        def _l(x):
            if isinstance(x, RE):
                return x.v
            if isinstance(x, bool):
                x = int(x)
            if isinstance(x, int):
                return S.lift(x)
            raise LiftError(f"{S.name}: cannot lift {x!r}")

        def __add__(self, o):
            cnt["add"] += 1
            return RE(S.add(self.v, RE._l(o)))

        def __radd__(self, o):
            cnt["add"] += 1
            return RE(S.add(RE._l(o), self.v))

        def __mul__(self, o):
            cnt["mul"] += 1
            return RE(S.mul(self.v, RE._l(o)))

        def __rmul__(self, o):
            cnt["mul"] += 1
            return RE(S.mul(RE._l(o), self.v))

        def _negv(self, v):
            if sub_fallback == "add":
                return v
            cnt["neg"] += 1
            return S.neg(v)

        def __neg__(self):
            return RE(self._negv(self.v))

        def __sub__(self, o):
            cnt["add"] += 1
            return RE(S.add(self.v, self._negv(RE._l(o))))

        def __rsub__(self, o):
            cnt["add"] += 1
            return RE(S.add(RE._l(o), self._negv(self.v)))

        def __floordiv__(self, k):
            cnt["inv"] += 1
            if isinstance(k, RE):
                return RE(S.div(self.v, k.v))
            if not isinstance(k, int):
                raise UndefinedOp("division by a non-integer")
            return RE(S.div_int(self.v, k))

        def __mod__(self, m):
            return self  # reduction is part of the representation

        def __bool__(self):
            return not S.eq(self.v, S.zero)

        def __eq__(self, o):
            try:
                return S.eq(self.v, RE._l(o))
            except LiftError:
                return NotImplemented

        def __hash__(self):
            return hash(self.v)

        def __lt__(self, o):
            raise OrderError(f"{S.name}: ring-origin code compared values")

        __gt__ = __le__ = __ge__ = __lt__

        def __repr__(self):
            return f"{S.name}:{self.v!r}"

    return RE


def make_tropical_elem(S: Structure, sense: str = "min", counter: dict | None = None):
    """Element class for (min,+)- or (max,+)-origin code: + is ⊗, order comes from ⊕ (selectivity checked at runtime)."""
    cnt = counter if counter is not None else new_counter()
    assert sense in ("min", "max")

    class TE:
        __slots__ = ("v",)
        structure = S
        counter = cnt

        def __init__(self, v):
            self.v = v

        @staticmethod
        def _l(x):
            if isinstance(x, TE):
                return x.v
            if isinstance(x, (int, float)) and not isinstance(x, bool):
                if x == 0:
                    return S.one
                if x in (INF, -INF):
                    return S.zero
            raise LiftError(f"{S.name}: literal {x!r} in (min/max,+)-origin code has no meaning")

        def __add__(self, o):
            cnt["mul"] += 1
            return TE(S.mul(self.v, TE._l(o)))

        def __radd__(self, o):
            cnt["mul"] += 1
            return TE(S.mul(TE._l(o), self.v))

        def oplus(self, o):
            cnt["add"] += 1
            return TE(S.add(self.v, TE._l(o)))

        def _better(self, a, b):
            """True iff a is strictly better than b in the ⊕-order."""
            cnt["cmp"] += 1
            s = S.add(a, b)
            if S.eq(a, b):
                return False
            if S.eq(s, a):
                return True
            if S.eq(s, b):
                return False
            raise OrderError(f"{S.name}: ⊕ not selective on ({a!r}, {b!r}): {s!r}")

        # "<" in min-origin code and ">" in max-origin code mean "strictly better".
        def __lt__(self, o):
            ov = TE._l(o)
            return self._better(self.v, ov) if sense == "min" else self._better(ov, self.v)

        def __gt__(self, o):
            ov = TE._l(o)
            return self._better(ov, self.v) if sense == "min" else self._better(self.v, ov)

        def __le__(self, o):
            return self == o or self.__lt__(o)

        def __ge__(self, o):
            return self == o or self.__gt__(o)

        def __eq__(self, o):
            try:
                return S.eq(self.v, TE._l(o))
            except LiftError:
                return NotImplemented

        def __hash__(self):
            return hash(self.v)

        def __repr__(self):
            return f"{S.name}:{self.v!r}"

    return TE


CURRENT_TE = [None]   # element class of the running tropical-origin mutant (set by the runner)


def oplus(a, b):
    """⊕ for tropical-origin elements (used by AST rewrites that turn relaxation into accumulation).
    Plain literals (0 = unit, ±inf = zero) are lifted with the element class of the running mutant."""
    if hasattr(a, "oplus"):
        return a.oplus(b)
    TE = type(b) if hasattr(b, "oplus") else CURRENT_TE[0]
    if TE is None:
        raise LiftError("⊕ of two plain values with no structure in scope")
    return TE(TE._l(a)).oplus(b)


class Rev:
    """Integer with reversed comparisons and ordinary arithmetic (the comparison-flip mirror)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v.v if isinstance(v, Rev) else v

    @staticmethod
    def _v(x):
        return x.v if isinstance(x, Rev) else x

    def __add__(self, o): return Rev(self.v + Rev._v(o))
    __radd__ = __add__
    def __sub__(self, o): return Rev(self.v - Rev._v(o))
    def __rsub__(self, o): return Rev(Rev._v(o) - self.v)
    def __mul__(self, o): return Rev(self.v * Rev._v(o))
    __rmul__ = __mul__
    def __neg__(self): return Rev(-self.v)
    def __floordiv__(self, o): return Rev(self.v // Rev._v(o))
    def __pow__(self, k): return Rev(self.v ** k)
    def __divmod__(self, o): return divmod(self.v, Rev._v(o))
    def __lt__(self, o): return self.v > Rev._v(o)
    def __gt__(self, o): return self.v < Rev._v(o)
    def __le__(self, o): return self.v >= Rev._v(o)
    def __ge__(self, o): return self.v <= Rev._v(o)
    def __eq__(self, o): return self.v == Rev._v(o)
    def __hash__(self): return hash(self.v)
    def __index__(self): return self.v
    def __int__(self): return self.v
    def __repr__(self): return f"Rev({self.v!r})"


def unwrap(x):
    """Strip wrappers recursively (outputs of injected runs -> plain values)."""
    if hasattr(x, "v") and type(x).__name__ in ("RE", "TE", "Rev"):
        return unwrap(x.v)
    if isinstance(x, (list, tuple)):
        return type(x)(unwrap(y) for y in x) if isinstance(x, tuple) else [unwrap(y) for y in x]
    return x


# --------------------------------------------------------------------------------------------------
# Mechanical property checks
# --------------------------------------------------------------------------------------------------

def _carrier(S):
    if S.finite_carrier is not None:
        return S.finite_carrier, "exhaustive (finite carrier)"
    return S.domain, f"bounded sample domain of {len(S.domain)} elements"


def check_properties(S: Structure, max_triples: int = 20000) -> dict:
    """Test algebraic laws on S. Returns {property: {"holds": bool|None, "witness": ..., "scope": ...}}.

    A law that fails has a concrete witness. A law that holds was checked on every tuple of the carrier (finite) or
    of the stated sample domain (infinite): there it is evidence, not proof. Existence properties (inverses,
    roots of unity) on infinite carriers search the sample domain only; "not found" is then labelled as such.
    """
    C, scope = _carrier(S)
    out: dict = {}
    has_add = S.kind in ("semiring", "monoid")
    has_mul = S.kind in ("semiring", "magma-mul")
    triples = list(itertools.product(C, repeat=3))
    if len(triples) > max_triples:
        triples = random.Random(f"props|{S.name}").sample(triples, max_triples)
    pairs = list(itertools.product(C, repeat=2))

    def law(name, pred, tuples):
        for t in tuples:
            try:
                ok = pred(*t)
            except UndefinedOp:
                out[name] = {"holds": None, "witness": None, "scope": "operation undefined"}
                return
            if not ok:
                out[name] = {"holds": False, "witness": [repr(x) for x in t], "scope": scope}
                return
        out[name] = {"holds": True, "witness": None, "scope": scope}

    E = S.eq
    if has_add:
        law("add_associative", lambda a, b, c: E(S.add(S.add(a, b), c), S.add(a, S.add(b, c))), triples)
        law("add_commutative", lambda a, b: E(S.add(a, b), S.add(b, a)), pairs)
        if S.zero is not None:
            law("add_identity", lambda a: E(S.add(a, S.zero), a) and E(S.add(S.zero, a), a), [(a,) for a in C])
        else:
            out["add_identity"] = {"holds": False, "witness": "no zero element declared", "scope": "declared"}
        law("add_idempotent", lambda a: E(S.add(a, a), a), [(a,) for a in C])
        law("add_selective", lambda a, b: E(S.add(a, b), a) or E(S.add(a, b), b), pairs)
        if S.zero is not None:
            def inv_exists(a):
                cands = list(C)
                if S.has_neg:
                    try:
                        cands.append(S.neg(a))
                    except UndefinedOp:
                        pass
                return any(E(S.add(a, b), S.zero) for b in cands)
            law("add_inverse_exists", inv_exists, [(a,) for a in C])
            if out["add_inverse_exists"]["holds"] and S.finite_carrier is None:
                out["add_inverse_exists"]["scope"] += " (witness b found for every a in the domain)"
    if has_mul:
        law("mul_associative", lambda a, b, c: E(S.mul(S.mul(a, b), c), S.mul(a, S.mul(b, c))), triples)
        law("mul_commutative", lambda a, b: E(S.mul(a, b), S.mul(b, a)), pairs)
        if S.one is not None:
            law("mul_identity", lambda a: E(S.mul(a, S.one), a) and E(S.mul(S.one, a), a), [(a,) for a in C])
        # power-associativity up to the 6th power: every bracketing of x^k gives the same value
        def power_assoc(a):
            vals = {1: {repr(a): a}}
            for k in range(2, 7):
                vals[k] = {}
                for i in range(1, k):
                    for x in vals[i].values():
                        for y in vals[k - i].values():
                            z = S.mul(x, y)
                            vals[k][repr(z)] = z
                if len(vals[k]) > 1:
                    return False
            return True
        law("mul_power_associative_to_6", power_assoc, [(a,) for a in C])
    if S.kind == "semiring":
        law("distributive_left", lambda a, b, c: E(S.mul(a, S.add(b, c)), S.add(S.mul(a, b), S.mul(a, c))), triples)
        law("distributive_right", lambda a, b, c: E(S.mul(S.add(b, c), a), S.add(S.mul(b, a), S.mul(c, a))), triples)
        law("zero_annihilates", lambda a: E(S.mul(a, S.zero), S.zero) and E(S.mul(S.zero, a), S.zero), [(a,) for a in C])
        # absorptive (0-closed / bounded): 1 ⊕ a = 1 for every a -- cycles never help
        law("absorptive_one_plus_a_is_one", lambda a: E(S.add(S.one, a), S.one), [(a,) for a in C])

        def mul_inv(a):
            if E(a, S.zero):
                return True
            return any(E(S.mul(a, b), S.one) for b in C) or (S.has_inv and _try_inv(S, a))
        law("mul_inverse_exists_for_nonzero", mul_inv, [(a,) for a in C])
        two = S.add(S.one, S.one)
        out["two_invertible"] = {"holds": (not E(two, S.zero)) and (any(E(S.mul(two, b), S.one) for b in C)
                                                                    or (S.has_inv and _try_inv(S, two))),
                                 "witness": repr(two), "scope": scope}
        out["characteristic"] = {"holds": None, "witness": _characteristic(S), "scope": "k·1 = 0 for the least k ≤ 64"}
        roots = {}
        for k in (2, 4, 8, 16):
            roots[k] = _primitive_root(S, k, C)
        out["primitive_roots_of_unity"] = {"holds": None, "witness": {str(k): (None if r is None else repr(r))
                                                                    for k, r in roots.items()},
                                           "scope": scope + "; Z_p, p prime: exact (k | p-1, witness g^((p-1)/k))"}
    return out


def _try_inv(S, a):
    try:
        b = S.inv(a)
        return S.eq(S.mul(a, b), S.one)
    except UndefinedOp:
        return False


def _characteristic(S):
    acc = S.one
    for k in range(1, 65):
        if S.eq(acc, S.zero):
            return k
        acc = S.add(acc, S.one)
    return "0 or > 64 (k·1 never equals 0 for k ≤ 64)"


def _primitive_root(S, k, C):
    """An element w with w^k = 1 and w^j != 1 for 0 < j < k, searched in C (all of Z_p if p <= 10^6)."""
    cands = C
    if isinstance(S, Zp) and _is_prime(S.p):
        # exact: Z_p^* is cyclic of order p-1, so a primitive k-th root exists iff k | p-1; witness g^((p-1)/k)
        if (S.p - 1) % k:
            return None
        return pow(_generator(S.p), (S.p - 1) // k, S.p)
    if isinstance(S, Zp) and S.p <= 10 ** 6:
        cands = range(S.p)
    for w in cands:
        acc, ok = S.one, True
        for j in range(1, k + 1):
            acc = S.mul(acc, w)
            if S.eq(acc, S.one) and j < k:
                ok = False
                break
        if ok and S.eq(acc, S.one):
            return w
    return None

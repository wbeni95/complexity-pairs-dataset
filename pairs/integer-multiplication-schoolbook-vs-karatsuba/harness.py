"""Instances: two n-digit non-negative integers as little-endian tuples of base-2^15 digits.

The top digit of each factor is non-zero (so both really have n digits). Besides uniform digits, some
V1 factors are BASE^n - 1 (all digits BASE-1) or random mixes of 0 and BASE-1 digits, to exercise
carries and borrows.
"""

BITS = 15
BASE = 1 << BITS


def generate(n, rng):
    def number():
        r = rng.random()
        if r < 0.1:             # BASE^n - 1: the maximal n-digit number, carries everywhere
            digits = [BASE - 1] * n
        elif r < 0.4:           # carry / borrow stress: long runs of 0 and BASE-1
            digits = [rng.choice((0, BASE - 1)) for _ in range(n)]
        else:
            digits = [rng.randrange(BASE) for _ in range(n)]
        if n:
            digits[-1] = digits[-1] or 1 + rng.randrange(BASE - 1)
        return tuple(digits)
    return number(), number()




def _value(digits):
    v = 0
    for d in reversed(digits):
        v = (v << BITS) | d
    return v


def check(instance, output):
    """Oracle: Python's built-in big-integer product (used here only, never in the implementations)."""
    a, b = instance
    if len(output) != len(a) + len(b) or not all(0 <= d < BASE for d in output):
        return False
    return _value(output) == _value(a) * _value(b)


# --- Exact digit-multiplication counting for V2 (measure: "reported") --------------------------------
# Timing could not separate the two exponents well enough (RESEARCH_LOG: deviation analysis F2): the
# Karatsuba timing data also fit n^2. The scaling instances therefore use an int-like digit type that
# counts every digit multiplication the UNCHANGED implementations perform and propagates through the
# carry/borrow arithmetic, and reported_cost returns that count.

_mults = 0


def _v(x):
    return x.v if isinstance(x, CountingDigit) else x


class CountingDigit:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __mul__(self, o):
        global _mults
        _mults += 1
        return CountingDigit(self.v * _v(o))

    __rmul__ = __mul__

    def __add__(self, o):
        return CountingDigit(self.v + _v(o))

    __radd__ = __add__

    def __sub__(self, o):
        return CountingDigit(self.v - _v(o))

    def __rsub__(self, o):
        return CountingDigit(_v(o) - self.v)

    def __neg__(self):
        return CountingDigit(-self.v)

    def __and__(self, o):
        return CountingDigit(self.v & _v(o))

    __rand__ = __and__

    def __or__(self, o):
        return CountingDigit(self.v | _v(o))

    __ror__ = __or__

    def __rshift__(self, o):
        return CountingDigit(self.v >> _v(o))

    def __lshift__(self, o):
        return CountingDigit(self.v << _v(o))

    def __lt__(self, o):
        return self.v < _v(o)

    def __le__(self, o):
        return self.v <= _v(o)

    def __gt__(self, o):
        return self.v > _v(o)

    def __ge__(self, o):
        return self.v >= _v(o)

    def __eq__(self, o):
        return self.v == _v(o)

    def __ne__(self, o):
        return self.v != _v(o)

    def __bool__(self):
        return bool(self.v)

    def __int__(self):
        return self.v

    __index__ = __int__

    def __hash__(self):
        return hash(self.v)


def generate_scaling(n, rng):
    """Uniform non-zero digits (as before) wrapped in CountingDigit; resets the multiplication counter."""
    global _mults
    a, b = (tuple(rng.randrange(1, BASE) for _ in range(n)), tuple(rng.randrange(1, BASE) for _ in range(n)))
    _mults = 0
    return tuple(CountingDigit(d) for d in a), tuple(CountingDigit(d) for d in b)


def reported_cost(output):
    """Number of digit multiplications performed since the counting instance was generated."""
    return _mults

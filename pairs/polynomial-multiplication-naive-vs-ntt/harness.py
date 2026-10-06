"""Instances: two polynomials of n coefficients each, uniform in Z_p, p = 998244353."""

P = 998244353


def generate(n, rng):
    return (tuple(rng.randrange(P) for _ in range(n)), tuple(rng.randrange(P) for _ in range(n)))


def check(instance, output):
    """Independent spot check: A(x) * B(x) == C(x) mod p at a few fixed points (Horner evaluation)."""
    A, B = instance
    if not A or not B:
        return output == []
    if len(output) != len(A) + len(B) - 1:
        return False

    def ev(poly, x):
        acc = 0
        for c in reversed(poly):
            acc = (acc * x + c) % P
        return acc

    return all(ev(A, x) * ev(B, x) % P == ev(output, x) for x in (2, 12345, P - 7))


# --- Exact multiplication counting for V2 (measure: "reported"; RESEARCH_LOG RL-047/RL-048) ----------
# Timing cannot tell n log n from n (RL-018). generate_scaling() draws the same coefficients as generate()
# (same seeds) and wraps each in CountingCoeff, an int-like type that propagates through +, -, *, % and
# counts every multiplication in which at least one operand derives from an input coefficient. The
# implementations are UNCHANGED. What this does and does not see (experiments/2026-10-06c_ntt_counts.py):
#   schoolbook: every a * b (exactly n^2 when no coefficient is 0; `if a:` skips zero rows);
#   NTT: butterfly products a[k + half] * w, pointwise products and the final scaling by n^-1. NOT seen:
#   twiddle updates w * w_len and pow() (plain ints created from literals inside the implementation) and the
#   first-stage butterflies whose a[k + half] is a padding zero (plain int). For n a power of two (size 2n)
#   the count is exactly 3 n log2(n) + 5 n.

_mults = 0


def _cv(x):
    return x.v if isinstance(x, CountingCoeff) else x


class CountingCoeff:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __mul__(self, o):
        global _mults
        _mults += 1
        return CountingCoeff(self.v * _cv(o))

    __rmul__ = __mul__

    def __add__(self, o):
        return CountingCoeff(self.v + _cv(o))

    __radd__ = __add__

    def __sub__(self, o):
        return CountingCoeff(self.v - _cv(o))

    def __rsub__(self, o):
        return CountingCoeff(_cv(o) - self.v)

    def __mod__(self, o):
        return CountingCoeff(self.v % _cv(o))

    def __bool__(self):
        return bool(self.v)

    def __eq__(self, o):
        return self.v == _cv(o)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountingCoeff({self.v!r})"


def generate_scaling(n, rng):
    """The coefficients of generate(n, rng), wrapped in CountingCoeff; resets the multiplication counter."""
    global _mults
    A, B = generate(n, rng)
    _mults = 0
    return tuple(CountingCoeff(c) for c in A), tuple(CountingCoeff(c) for c in B)


def reported_cost(output):
    """Multiplications on input-derived values since the counting instance was generated."""
    return _mults

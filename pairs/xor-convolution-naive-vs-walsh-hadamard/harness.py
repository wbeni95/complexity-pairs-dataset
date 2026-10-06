"""Instances: (a, b), two integer vectors of length N = 2^n with entries in [-9, 9], indexed by n-bit strings.

V1 oracle (check): the XOR convolution theorem tested character by character, without any transform code. For a
character chi_s(x) = (-1)^popcount(s & x), the output h must satisfy
    sum_k h[k] chi_s(k) = (sum_i a[i] chi_s(i)) * (sum_j b[j] chi_s(j)).
The 2^n characters form a basis of the functions on (Z_2)^n, so checking every s determines h uniquely (a complete
check, used for n <= 8). For larger n, 48 characters chosen by a seeded generator are checked (a probabilistic spot
check, like Freivalds' test). The output length is checked too.

V2 (measure: "reported"): the scaling instances are built from CountingInt, a number type that counts every ring
operation (+, -, *, //) performed by the UNCHANGED implementations; reported_cost returns that count. Exact
counts (proven in the entry and checked in experiments/2026-10-07b_xor_convolution_counts.py): naive 2 * 4^n,
FWHT (3n + 2) * 2^n.
"""
import random


def generate(n, rng):
    size = 1 << n
    return (tuple(rng.randint(-9, 9) for _ in range(size)),
            tuple(rng.randint(-9, 9) for _ in range(size)))


def _chi_sum(vec, s):
    return sum(-v if bin(s & x).count("1") & 1 else v for x, v in enumerate(vec))


def check(instance, output):
    a, b = instance
    size = len(a)
    if len(output) != size:
        return False
    n = size.bit_length() - 1
    if n <= 8:
        chars = range(size)
    else:
        rng = random.Random(f"xor-check|{n}|{sum(a)}|{sum(b)}")
        chars = [rng.randrange(size) for _ in range(48)]
    h = [int(x) for x in output]
    return all(_chi_sum(h, s) == _chi_sum(a, s) * _chi_sum(b, s) for s in chars)


# --- Exact operation counting for V2 ------------------------------------------------------------------

_ops = 0


class CountingInt:
    """An integer that counts every +, -, * and // it takes part in (module counter _ops)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def __add__(self, other):
        global _ops
        _ops += 1
        return CountingInt(self.v + self._val(other))

    __radd__ = __add__

    def __sub__(self, other):
        global _ops
        _ops += 1
        return CountingInt(self.v - self._val(other))

    def __rsub__(self, other):
        global _ops
        _ops += 1
        return CountingInt(self._val(other) - self.v)

    def __mul__(self, other):
        global _ops
        _ops += 1
        return CountingInt(self.v * self._val(other))

    __rmul__ = __mul__

    def __floordiv__(self, other):
        global _ops
        _ops += 1
        return CountingInt(self.v // self._val(other))

    def __int__(self):
        return self.v

    def __eq__(self, other):
        return self.v == self._val(other)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountingInt({self.v})"


def generate_scaling(n, rng):
    """Random vectors of CountingInt entries; resets the operation counter."""
    global _ops
    _ops = 0
    size = 1 << n
    return (tuple(CountingInt(rng.randint(-9, 9)) for _ in range(size)),
            tuple(CountingInt(rng.randint(-9, 9)) for _ in range(size)))


def reported_cost(output):
    """Ring operations (+, -, *, //) performed since the scaling instance was generated."""
    return _ops

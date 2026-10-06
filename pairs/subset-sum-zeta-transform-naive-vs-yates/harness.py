"""Instances: a tuple f of 2^n integers in [-9, 9]; f[S] is the value of the set S (a bitmask over n elements).

V1 oracle (check): the definition evaluated by a different loop. For each S it scans ALL 2^n masks T and adds f[T]
when T & ~S == 0 (no submask enumeration, no transform). For n <= 8 every S is checked (Theta(4^n), complete); for
larger n, 64 seeded random sets S plus the full set (spot check). The output length is checked too.

V2 (measure: "reported"): scaling instances are built from CountingInt, which counts every addition and
subtraction performed by the UNCHANGED implementations; reported_cost returns the count. Exact counts (proven in
the entry, checked in experiments/2026-10-07b_zeta_transform_counts.py): naive 3^n, Yates n * 2^(n-1).
"""
import random


def generate(n, rng):
    return tuple(rng.randint(-9, 9) for _ in range(1 << n))


def check(f, output):
    size = len(f)
    if len(output) != size:
        return False
    n = size.bit_length() - 1
    if n <= 8:
        sets = range(size)
    else:
        rng = random.Random(f"zeta-check|{n}|{sum(f)}")
        sets = [rng.randrange(size) for _ in range(64)] + [size - 1]
    for s in sets:
        total = 0
        for t in range(size):
            if t & ~s == 0:
                total += f[t]
        if int(output[s]) != total:
            return False
    return True


# --- Exact operation counting for V2 ------------------------------------------------------------------

_ops = 0


class CountingInt:
    """An integer that counts every + and - it takes part in (module counter _ops)."""
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

    def __int__(self):
        return self.v

    def __eq__(self, other):
        return self.v == self._val(other)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountingInt({self.v})"


def generate_scaling(n, rng):
    """Random set function of CountingInt values; resets the operation counter."""
    global _ops
    _ops = 0
    return tuple(CountingInt(rng.randint(-9, 9)) for _ in range(1 << n))


def reported_cost(output):
    """Additions and subtractions performed since the scaling instance was generated."""
    return _ops

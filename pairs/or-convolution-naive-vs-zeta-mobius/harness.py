"""Instances: (f, g), two integer vectors of length N = 2^n with entries in [-9, 9], indexed by subsets of an n-element
set (bitmasks). Output: h with h[S] = sum over A | B = S of f[A] g[B] (OR convolution, the covering product).

V1 oracle (check), written without the transforms or the pair loop of the implementations:
  1. the zeta identity, for EVERY set S: zeta_h[S] = zeta_f[S] * zeta_g[S], where each zeta vector is computed by
     enumerating the submasks of every S (t -> (t - 1) & S; Theta(3^n), a different algorithm from the Yates passes
     of the implementation). Zeta is invertible, so this determines h uniquely: a complete check at every n;
  2. the definition, for up to 6 seeded sets S when n <= 10: h[S] = sum over A subset of S of f[A] times the sum of
     g[(S minus A) | C] over C subset of A (every B with A | B = S has this form), by explicit submask recursion.
The output length is checked too.

V2 (measure: "reported"): scaling instances are built from CountingInt, which counts every +, - and * performed by
the UNCHANGED implementations. Exact counts (derived in entry.json, checked in
experiments/2026-10-06f_entries_or_convolution.py): naive 2 * 4^n, zeta-Moebius (3n + 2) * 2^(n-1).
"""
import random


def generate(n, rng):
    size = 1 << n
    return (tuple(rng.randint(-9, 9) for _ in range(size)),
            tuple(rng.randint(-9, 9) for _ in range(size)))


def _zeta_by_submasks(vec):
    out = []
    for s in range(len(vec)):
        acc = 0
        t = s
        while True:
            acc += vec[t]
            if t == 0:
                break
            t = (t - 1) & s
        out.append(acc)
    return out


def _submasks(s):
    t = s
    while True:
        yield t
        if t == 0:
            return
        t = (t - 1) & s


def _definition(f, g, s):
    return sum(f[a] * sum(g[(s & ~a) | c] for c in _submasks(a)) for a in _submasks(s))


def check(instance, output):
    f, g = instance
    size = len(f)
    if len(output) != size:
        return False
    h = [int(x) for x in output]
    n = size.bit_length() - 1
    zh, zf, zg = _zeta_by_submasks(h), _zeta_by_submasks(f), _zeta_by_submasks(g)
    if any(a != b * c for a, b, c in zip(zh, zf, zg)):
        return False
    rng = random.Random(f"or-check|{n}|{sum(f)}|{sum(g)}")
    if n <= 10:
        for s in [rng.randrange(size) for _ in range(min(6, size))]:
            if h[s] != _definition(f, g, s):
                return False
    return True


# --- Exact operation counting for V2 ------------------------------------------------------------------

_ops = 0


class CountingInt:
    """An integer that counts every +, - and * it takes part in (module counter _ops)."""
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

    def __int__(self):
        return self.v

    def __eq__(self, other):
        return self.v == self._val(other)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountingInt({self.v})"


def generate_scaling(n, rng):
    """Random set functions of CountingInt values; resets the operation counter."""
    global _ops
    _ops = 0
    size = 1 << n
    return (tuple(CountingInt(rng.randint(-9, 9)) for _ in range(size)),
            tuple(CountingInt(rng.randint(-9, 9)) for _ in range(size)))


def reported_cost(output):
    """Additions, subtractions and multiplications performed since the scaling instance was generated."""
    return _ops

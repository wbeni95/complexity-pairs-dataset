"""Instances: two random n x n integer matrices with entries in [-9, 9]."""


def generate(n, rng):
    def mat():
        return tuple(tuple(rng.randint(-9, 9) for _ in range(n)) for _ in range(n))
    return mat(), mat()


def check(instance, output):
    """Freivalds-style spot check: A(Bx) == Cx for a random 0/1 vector x (independent of both algorithms)."""
    import random
    A, B = instance
    n = len(A)
    if n == 0:
        return output == []
    x = [random.Random(n).randint(0, 1) for _ in range(n)]
    Bx = [sum(B[i][j] * x[j] for j in range(n)) for i in range(n)]
    ABx = [sum(A[i][j] * Bx[j] for j in range(n)) for i in range(n)]
    Cx = [sum(output[i][j] * x[j] for j in range(n)) for i in range(n)]
    return ABx == Cx


# --- Exact multiplication counting for V2 (measure: "reported") -------------------------------------
# Wall-clock timing cannot separate n^3 from n^2.807 at feasible sizes (RESEARCH_LOG RL-006). Instead the
# scaling instances use a number type that counts every scalar multiplication the UNCHANGED implementations
# perform (padding zeros included), and reported_cost returns that count.

_mults = 0


class CountingInt:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def __mul__(self, other):
        global _mults
        _mults += 1
        return CountingInt(self.v * self._val(other))

    __rmul__ = __mul__

    def __add__(self, other):
        return CountingInt(self.v + self._val(other))

    __radd__ = __add__

    def __sub__(self, other):
        return CountingInt(self.v - self._val(other))

    def __rsub__(self, other):
        return CountingInt(self._val(other) - self.v)

    def __eq__(self, other):
        return self.v == self._val(other)

    def __hash__(self):
        return hash(self.v)


def generate_scaling(n, rng):
    """Random n x n matrices whose entries count multiplications; resets the counter."""
    global _mults
    _mults = 0

    def mat():
        return tuple(tuple(CountingInt(rng.randint(-9, 9)) for _ in range(n)) for _ in range(n))
    return mat(), mat()


def reported_cost(output):
    """Number of scalar multiplications performed since the instance was generated."""
    return _mults

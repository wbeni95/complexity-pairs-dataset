"""Instances: two n x n 0/1 matrices (tuples of tuples of the integers 0 and 1); output: their Boolean product as a
list of lists of 0/1 integers, C[i][j] = 1 iff A[i][k] = B[k][j] = 1 for some k.

generate(n, rng) mixes densities p in {0.05, 0.2, 0.5, 0.9} for each factor independently, and sometimes uses
special matrices (all zeros, all ones, the identity, a random permutation matrix), so that sparse products (mostly
0), dense products (mostly 1) and exact structures all occur.

check(instance, output) is independent of both implementations: it packs the rows of B into integer bitmasks and
computes row i of the product as the bitwise OR of the rows k of B with A[i][k] = 1 (a row-union formulation; no
inner products, no integer arithmetic on entries), then compares with the output, which must be an n x n matrix of
0/1 integers.

V2 (measure: "reported"): generate_scaling builds random 0/1 matrices (density 1/2) from CountingInt, a number type
that counts every scalar product: integer multiplication (Strassen over Z) and AND (the Boolean semiring product,
schoolbook). Additions, subtractions, ORs and comparisons are not counted. The implementations are unchanged; on
n = 16, 32, 64, 128 the counts are exactly n^3 (schoolbook) and 7^(log2(n/16)) * 16^3 (Strassen).
"""


def _special(n, rng):
    kind = rng.choice(("zero", "ones", "identity", "permutation"))
    if kind == "zero":
        return tuple(tuple(0 for _ in range(n)) for _ in range(n))
    if kind == "ones":
        return tuple(tuple(1 for _ in range(n)) for _ in range(n))
    if kind == "identity":
        return tuple(tuple(int(i == j) for j in range(n)) for i in range(n))
    perm = rng.sample(range(n), n)
    return tuple(tuple(int(perm[i] == j) for j in range(n)) for i in range(n))


def _random(n, rng):
    p = rng.choice((0.05, 0.2, 0.5, 0.9))
    return tuple(tuple(int(rng.random() < p) for _ in range(n)) for _ in range(n))


def generate(n, rng):
    def mat():
        return _special(n, rng) if rng.random() < 0.2 else _random(n, rng)
    return mat(), mat()


def check(instance, output):
    A, B = instance
    n = len(A)
    if not isinstance(output, list) or len(output) != n:
        return False
    rowmask = [sum(int(B[k][j]) << j for j in range(n)) for k in range(n)]
    for i in range(n):
        row = output[i]
        if len(row) != n or any(x not in (0, 1) for x in row):
            return False
        expect = 0
        for k in range(n):
            if A[i][k]:
                expect |= rowmask[k]
        if sum(int(x) << j for j, x in enumerate(row)) != expect:
            return False
    return True


# --- Exact product counting for V2 (measure: "reported") --------------------------------------------

_products = 0


class CountingInt:
    """An integer that counts every multiplication and AND it takes part in (module counter _products)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def __mul__(self, other):
        global _products
        _products += 1
        return CountingInt(self.v * self._val(other))

    __rmul__ = __mul__

    def __and__(self, other):
        global _products
        _products += 1
        return CountingInt(self.v & self._val(other))

    __rand__ = __and__

    def __or__(self, other):
        return CountingInt(self.v | self._val(other))

    __ror__ = __or__

    def __add__(self, other):
        return CountingInt(self.v + self._val(other))

    __radd__ = __add__

    def __sub__(self, other):
        return CountingInt(self.v - self._val(other))

    def __rsub__(self, other):
        return CountingInt(self._val(other) - self.v)

    def __gt__(self, other):
        return self.v > self._val(other)

    def __eq__(self, other):
        return self.v == self._val(other)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountingInt({self.v})"


def generate_scaling(n, rng):
    """Random 0/1 matrices (density 1/2) of CountingInt entries; resets the product counter."""
    global _products
    _products = 0

    def mat():
        return tuple(tuple(CountingInt(rng.randint(0, 1)) for _ in range(n)) for _ in range(n))
    return mat(), mat()


def reported_cost(output):
    """Scalar products (multiplications or ANDs) performed since the instance was generated."""
    return _products

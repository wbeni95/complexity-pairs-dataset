"""Harness for the entry "powering in Cayley-Dickson algebras (octonions, sedenions, dimension 32)".

Instance: (x, e, p) with the odd modulus p = 2^61 - 1, x a tuple of 2^m residues mod p for m in {3, 4, 5}
(octonions, sedenions, dimension 32), and e >= 1 of bit length exactly n. Output: the left power x^e as a tuple of
residues; by power-associativity every bracketing of the e factors gives the same element (PROOFS.md, section 5).

check(): an oracle written separately from the implementations, with two tiers.
  every e   x^e = alpha * 1 + beta * x, where alpha + beta X is X^e reduced modulo X^2 - t X + n over Z/pZ, with
            t = 2 x_0 and n = sum of the squares of the coordinates (PROOFS.md, section 5). This is computed with
            polynomials of degree < 2 only; no Cayley-Dickson product is used.
  e <= 40   in addition, the left powers are computed from the definition with a product written differently from
            the implementations: a table of basis products e_i e_j = s(i, j) e_(i xor j), with the signs s built
            from the doubling rules, and c_k = sum over i xor j = k of s(i, j) x_i y_j.

V2 (measure "reported"): generate_scaling(n) gives m = 3 (octonions) and e = 2^n - 1, with coordinates of type
CountingInt, which counts every multiplication of two residues; the implementations are unchanged. One algebra
product in dimension 2^m makes exactly 4^m such multiplications, so the counts are 4^m times the numbers of algebra
products: 64 (2^n - 2) for repeated multiplication and 64 * 2(n - 1) for square-and-multiply.
"""

P = (1 << 61) - 1


# --------------------------------------------------------------------------------------------------
# Oracle
# --------------------------------------------------------------------------------------------------

def _basis_sign_table(m):
    """s[i][j] in {+1, -1} with e_i e_j = s[i][j] e_(i ^ j) in A_m, from the doubling rules on basis pairs:
    (u, 0)(v, 0) = (uv, 0); (u, 0)(0, v) = (0, v u); (0, u)(v, 0) = (0, u conj(v)); (0, u)(0, v) = (-conj(v) u, 0),
    with conj(e_0) = e_0 and conj(e_i) = -e_i for i >= 1."""
    s = [[1]]
    for level in range(1, m + 1):
        h = 1 << (level - 1)
        prev = s
        cv = [1] + [-1] * (h - 1)                 # sign of conj on the basis of A_(level-1)
        new = [[0] * (2 * h) for _ in range(2 * h)]
        for i in range(h):
            for j in range(h):
                new[i][j] = prev[i][j]                       # (u,0)(v,0) = (uv, 0)
                new[i][h + j] = prev[j][i]                   # (u,0)(0,v) = (0, vu)
                new[h + i][j] = prev[i][j] * cv[j]           # (0,u)(v,0) = (0, u conj(v))
                new[h + i][h + j] = -cv[j] * prev[j][i]      # (0,u)(0,v) = (-conj(v) u, 0)
        s = new
    return s


_tables = {}


def table_mul(x, y, p):
    dim = len(x)
    m = dim.bit_length() - 1
    if m not in _tables:
        _tables[m] = _basis_sign_table(m)
    s = _tables[m]
    out = [0] * dim
    for i in range(dim):
        if x[i]:
            for j in range(dim):
                out[i ^ j] += s[i][j] * x[i] * y[j]
    return tuple(v % p for v in out)


def quadratic_power(x, e, p):
    """x^e from X^e mod (X^2 - tX + n) over Z/pZ: returns the coordinates of alpha * 1 + beta * x."""
    t = 2 * x[0] % p
    n = sum(v * v for v in x) % p

    def mul(u, v):                                   # (u0 + u1 X)(v0 + v1 X) with X^2 = tX - n
        a = u[0] * v[0]
        b = u[0] * v[1] + u[1] * v[0]
        c = u[1] * v[1]
        return ((a - c * n) % p, (b + c * t) % p)

    r, base, k = (1, 0), (0, 1), e
    while k:
        if k & 1:
            r = mul(r, base)
        base = mul(base, base)
        k >>= 1
    alpha, beta = r
    return tuple(((alpha if i == 0 else 0) + beta * x[i]) % p for i in range(len(x)))


def check(instance, output):
    x, e, p = instance
    if not isinstance(output, tuple) or len(output) != len(x):
        return False
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v < p for v in output):
        return False
    xr = tuple(v % p for v in x)
    if output != quadratic_power(xr, e, p):
        return False
    if e <= 40:
        r = xr
        for _ in range(e - 1):
            r = table_mul(r, xr, p)
        if output != r:
            return False
    return True


# --------------------------------------------------------------------------------------------------
# V1 instances
# --------------------------------------------------------------------------------------------------

def _isotropic_imaginary(dim, rng, p):
    """A purely imaginary x with n(x) = 0 mod p (so x^2 = 0): x = a e_1 + b e_2 + c e_3, c^2 = -(a^2 + b^2)."""
    while True:
        a, b = rng.randrange(1, p), rng.randrange(1, p)
        q = (-(a * a + b * b)) % p
        c = pow(q, (p + 1) // 4, p)                  # candidate square root (p = 3 mod 4), accepted only if verified
        if c * c % p == q:
            v = [0] * dim
            v[1], v[2], v[3] = a, b, c
            return tuple(v)


def _exponent(n, rng):
    kind = rng.random()
    if n == 1:
        return 1
    if kind < 0.15:
        return (1 << n) - 1                          # all bits set
    if kind < 0.25:
        return 1 << (n - 1)                          # a power of two
    return rng.getrandbits(n - 1) | (1 << (n - 1))


def generate(n, rng):
    m = rng.choice((3, 4, 5))
    dim = 1 << m
    kind = rng.random()
    if kind < 0.5:
        x = tuple(rng.randrange(P) for _ in range(dim))
    elif kind < 0.65:
        x = tuple(rng.randint(-3, 3) % P for _ in range(dim))
    elif kind < 0.72:
        x = (rng.randrange(P),) + (0,) * (dim - 1)  # a real element
    elif kind < 0.8:
        x = (0,) + tuple(rng.randrange(P) for _ in range(dim - 1))   # purely imaginary
    elif kind < 0.87:
        x = _isotropic_imaginary(dim, rng, P)        # x^2 = 0
    elif kind < 0.93:
        x = (1, 1) + (0,) * (dim - 2)                # 1 + e_1
    else:
        x = tuple(rng.choice((0, 0, 0, 1, P - 1)) for _ in range(dim))
    return (x, _exponent(n, rng), P)


# --------------------------------------------------------------------------------------------------
# Exact operation counting for V2 (measure: "reported")
# --------------------------------------------------------------------------------------------------

_ops = {"mul": 0}


class CountingInt:
    """A residue representative that counts every multiplication it takes part in (+, -, %, unary - are free)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def __mul__(self, other):
        _ops["mul"] += 1
        return CountingInt(self.v * self._val(other))

    __rmul__ = __mul__

    def __add__(self, other):
        return CountingInt(self.v + self._val(other))

    __radd__ = __add__

    def __sub__(self, other):
        return CountingInt(self.v - self._val(other))

    def __rsub__(self, other):
        return CountingInt(self._val(other) - self.v)

    def __neg__(self):
        return CountingInt(-self.v)

    def __mod__(self, other):
        return CountingInt(self.v % self._val(other))

    def __int__(self):
        return int(self.v)

    def __repr__(self):
        return f"CountingInt({self.v})"


def generate_scaling(n, rng):
    """Octonions (m = 3), e = 2^n - 1 (the worst case of square-and-multiply at bit length n), CountingInt
    coordinates; resets the counter."""
    _ops["mul"] = 0
    x = tuple(CountingInt(rng.randrange(P)) for _ in range(8))
    return (x, (1 << n) - 1, P)


def reported_cost(output):
    """Multiplications of residues since the scaling instance was generated."""
    return _ops["mul"]


def equal(a, b):
    return tuple(int(v) for v in a) == tuple(int(v) for v in b)

"""Harness for XOR-SAT / #XOR-SAT: brute force over 2^n assignments vs Gaussian elimination over GF(2).

Instances: (n, rows), each row a tuple of n + 1 bits (a_1, ..., a_n, b): the augmented matrix [A | b] of the linear
system A x = b over GF(2) (one XOR clause a_1 x_1 XOR ... XOR a_n x_n = b per row). Outputs: (count, witness), the
number of solutions and one solution (a tuple of n bits) or None. The two algorithms may return different
solutions, so `equal` compares the counts and whether a witness exists; `check` verifies the witness.

generate(n, rng) mixes, for n >= 2:
  0  random dense rows (every coefficient and b uniform), m in {n/2, n, 3n/2} (both answers occur);
  1  random sparse 3-XOR rows (three distinct variables), m = round(c n), c in {0.5, 0.8, 1, 1.5};
  2  planted consistent: random A of random density, b = A x* for a hidden x*;
  3  forced inconsistent: a planted system plus one row that is the XOR of a random subset of rows with b flipped;
  4  rank-deficient: repeated rows, sums of rows, all-zero rows 0 = 0 and (rarely) 0 = 1;
  5  the V2 family X_n below with its columns permuted and its rows shuffled.
For n = 0, 1 it returns the edge cases (no rows, 0 = 0, 0 = 1, x = 0, x = 1, contradictory pairs).

check(instance, output) is independent of both implementations (different representation and pivot rule) and
certificate-based. It inserts the rows, packed into Python integers, into an XOR basis keyed by the HIGHEST set
coefficient, tracking for every basis vector the set of input rows it combines. Then:
  - if some row reduces to 0 = 1, the combination is re-verified against the input rows (their XOR has A part 0 and
    b = 1): a proof that there is no solution, so only (0, None) is accepted;
  - otherwise the r basis vectors are re-verified as combinations of input rows with distinct leading columns, so
    rank(A) >= r and there are at most 2^(n - r) solutions; n - r null-space vectors (one per non-leading column,
    built by substitution) are verified against every input row, and the witness is verified against every input
    row, so there are at least 2^(n - r) solutions. Only count = 2^(n - r) with a verified witness is accepted.
  - for n <= 10 the count is also compared with an exhaustive count over itertools.product.

V2 (measure "reported"): generate_scaling(n, rng) builds the deterministic family X_n (rng not used) from CountingBit
entries and resets the counter. Rows: E_0 = (1, 1, ..., 1) and R_k = x_1 + x_{k+1} + ... + x_n for k = 2..n
(R_n = x_1 alone), b = A x* for x*_j = 1 iff j is divisible by 3. X_n is square and of full rank (every column
gets a pivot), so the solution is unique and every prefix of rows is independent and consistent:
  * brute force: assignment by assignment, row i (0-based) is reached by exactly 2^(n-i) assignments and costs
    2n + 1 counted operations, so the total is exactly (2n + 1)(2^(n+1) - 2);
  * Gaussian elimination: the first row (all ones) is the pivot of column 1 and turns every other row into the
    prefix x_2 + ... + x_k, after which column c has n - c rows below its pivot that all need elimination: the
    worst case of forward elimination, exactly n (n^2 + 6n - 4) / 3 counted operations (derivation in entry.json).
CountingBit counts every AND, XOR and truth test on an input bit or a value computed from one. The implementations
are unchanged and count nothing themselves.
"""
import itertools


# --------------------------------------------------------------------------
# Instances for V1
# --------------------------------------------------------------------------

def _apply(row, x):
    return sum(a & v for a, v in zip(row, x)) & 1


def _planted(n, m, rng, density=None):
    p = density if density is not None else rng.choice((0.2, 0.5, 0.8))
    x = [rng.randint(0, 1) for _ in range(n)]
    rows = []
    for _ in range(m):
        a = [1 if rng.random() < p else 0 for _ in range(n)]
        rows.append(tuple(a) + (_apply(a, x),))
    return rows


def _family(n):
    """The V2 family X_n as plain-integer rows (n >= 1)."""
    A = [[1] * n] + [[1] + [0] * (k - 1) + [1] * (n - k) for k in range(2, n + 1)]
    x = [1 if (j + 1) % 3 == 0 else 0 for j in range(n)]
    return [tuple(a) + (_apply(a, x),) for a in A]


def _small(n, rng):
    if n == 0:
        return 0, rng.choice(((), ((0,),), ((1,),), ((0,), (0,))))
    choices = [(), ((1, 0),), ((1, 1),), ((0, 0),), ((0, 1),), ((1, 0), (1, 1)), ((1, 1), (1, 1), (0, 0))]
    return 1, rng.choice(choices)


def generate(n, rng):
    if n < 2:
        return _small(n, rng)
    kind = rng.randrange(6)
    if kind == 0:
        m = rng.choice((n // 2, n, (3 * n) // 2)) or 1
        return n, tuple(tuple(rng.randint(0, 1) for _ in range(n + 1)) for _ in range(m))
    if kind == 1:
        m = max(1, round(rng.choice((0.5, 0.8, 1.0, 1.5)) * n))
        rows = []
        for _ in range(m):
            row = [0] * (n + 1)
            for v in rng.sample(range(n), min(3, n)):
                row[v] = 1
            row[n] = rng.randint(0, 1)
            rows.append(tuple(row))
        return n, tuple(rows)
    if kind == 2:
        return n, tuple(_planted(n, rng.choice((n // 2 or 1, n, n + 2)), rng))
    if kind == 3:
        rows = _planted(n, rng.choice((n // 2 or 1, n)), rng)
        subset = [r for r in rows if rng.random() < 0.5] or rows[:1]
        comb = [0] * (n + 1)
        for r in subset:
            comb = [c ^ v for c, v in zip(comb, r)]
        comb[n] ^= 1
        rows.insert(rng.randrange(len(rows) + 1), tuple(comb))
        return n, tuple(rows)
    if kind == 4:
        base = _planted(n, max(1, n // 2), rng)
        rows = list(base)
        for _ in range(n):
            r = rng.random()
            if r < 0.3:
                rows.append(rng.choice(base))
            elif r < 0.7:
                a, b = rng.choice(base), rng.choice(base)
                rows.append(tuple(u ^ v for u, v in zip(a, b)))
            else:
                rows.append((0,) * n + ((1 if rng.random() < 0.1 else 0),))
        rng.shuffle(rows)
        return n, tuple(rows)
    perm = rng.sample(range(n), n)                         # kind == 5: V2 family, permuted
    rows = [tuple(row[perm[j]] for j in range(n)) + (row[n],) for row in _family(n)]
    rng.shuffle(rows)
    return n, tuple(rows)


# --------------------------------------------------------------------------
# Independent oracle
# --------------------------------------------------------------------------

def _parity(v):
    return bin(v).count("1") & 1


def _xor_rows(R, comb):
    acc = 0
    i = 0
    while comb:
        if comb & 1:
            acc ^= R[i]
        comb >>= 1
        i += 1
    return acc


def _exhaustive_count(n, rows):
    return sum(all(_apply(r[:n], x) == r[n] for r in rows) for x in itertools.product((0, 1), repeat=n))


def check(instance, output):
    n, rows = instance
    if not isinstance(output, tuple) or len(output) != 2:
        return False
    count, wit = output
    full = (1 << n) - 1
    R = [sum(int(bit) << j for j, bit in enumerate(row)) for row in rows]   # bit j = a_{j+1}, bit n = b
    if n <= 10 and count != _exhaustive_count(n, rows):
        return False
    basis = {}                                             # leading column -> (vector, combination of input rows)
    for i, v in enumerate(R):
        comb = 1 << i
        while v & full:
            h = (v & full).bit_length() - 1
            if h not in basis:
                basis[h] = (v, comb)
                break
            bv, bc = basis[h]
            v ^= bv
            comb ^= bc
        else:
            if v >> n & 1:                                 # 0 = 1: re-verify the certificate on the input rows
                if _xor_rows(R, comb) != 1 << n:
                    return None
                return count == 0 and wit is None
    for h, (v, comb) in basis.items():                     # rank >= r: independent combinations of input rows
        if _xor_rows(R, comb) != v or (v & full).bit_length() - 1 != h:
            return None
    r = len(basis)
    free = [c for c in range(n) if c not in basis]

    def substitute(xbits, homogeneous):
        for p in sorted(basis):                            # leading columns in increasing order
            v = basis[p][0]
            val = _parity(v & ((1 << p) - 1) & xbits) ^ (0 if homogeneous else (v >> n & 1))
            xbits = (xbits & ~(1 << p)) | (val << p)
        return xbits

    for f in free:                                         # n - r null-space vectors, independent by construction
        x = substitute(1 << f, True)
        if any(_parity(Ri & full & x) for Ri in R) or any((x >> g & 1) != (g == f) for g in free):
            return None
    if count == 0:                                         # claimed no solution: refute with a verified solution
        x = substitute(0, False)
        return False if all(_parity(Ri & full & x) == (Ri >> n & 1) for Ri in R) else None
    if count != 2 ** (n - r) or not isinstance(wit, tuple) or len(wit) != n or any(b not in (0, 1) for b in wit):
        return False
    return all(_apply(row[:n], wit) == row[n] for row in rows)


def equal(a, b):
    return a[0] == b[0] and (a[1] is None) == (b[1] is None)


# --------------------------------------------------------------------------
# Exact operation counting for V2 (measure: "reported")
# --------------------------------------------------------------------------

_ops = 0


class CountingBit:
    """A bit that counts every AND, XOR and truth test it takes part in (results stay counting)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingBit) else x

    def __and__(self, o):
        global _ops
        _ops += 1
        return CountingBit(self.v & self._val(o))

    __rand__ = __and__

    def __xor__(self, o):
        global _ops
        _ops += 1
        return CountingBit(self.v ^ self._val(o))

    __rxor__ = __xor__

    def __bool__(self):
        global _ops
        _ops += 1
        return self.v != 0

    def __eq__(self, o):
        global _ops
        _ops += 1
        return self.v == self._val(o)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountingBit({self.v})"


def generate_scaling(n, rng):
    """The family X_n (deterministic; rng unused) with counting entries; resets the operation counter."""
    global _ops
    rows = tuple(tuple(CountingBit(b) for b in row) for row in _family(n))
    _ops = 0
    return n, rows


def reported_cost(output):
    """AND, XOR and truth-test operations on input-derived bits since the instance was generated."""
    return _ops

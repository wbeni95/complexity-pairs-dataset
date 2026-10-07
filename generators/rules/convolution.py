"""Rule R2: transform-based convolution over an index operation (FFT/NTT, FWHT, zeta/Moebius, prefix sums).

Problem (one per index operation T on [N], N = 2^k): given a, b in Z_p^N (p = 998244353), compute
    c[k] = sum over (i, j) with T[i][j] = k of a[i] * b[j]                       ("T-convolution").
Slow: all N^2 index pairs (one multiplication and one addition each, counted).
Rule: find a labelling phi under which T becomes a library structure with a fast transform, then run the
transform. The structure detector is preprocessing on the fixed operation (not counted per instance):

    xor     elementary abelian group Z_2^k        FWHT                       (3k + 2) N ops
    cyclic  Z_N                                    radix-2 NTT                ~ (9/2) k N ops
    prod    Z_(N/2) x Z_2                          2-D NTT
    or      Boolean lattice (join = union)        zeta / Moebius (Yates)     ~ k N ops
    max     chain (join = max)                     prefix sums / differences  ~ 4 N ops
    sat     saturating addition min(i + j, N-1)   linear NTT convolution of length 2N, then fold the tail
            (a commutative monoid that is neither a group nor a semilattice: the "lifted transform" rule,
             convolve in Z and map down by the homomorphism k -> min(k, N-1))

If no structure matches exactly, the rule still applies the transform of the best-scoring structure
("blind" application); the screen measures how close that gets (fraction of output coordinates correct).
The repaired rule (`fast_repaired`) adds a sparse correction for the table entries that disagree with the
structure: exact for every table, cost = transform + 3 |D| counted operations (one multiplication, one addition
and one subtraction per disagreeing entry; |D| = number of disagreeing entries).

Families generated (each with a random relabelling): xor, cyclic, prod, or, and, max, min, sat (structured);
sub (i - j mod N), random, random_comm, latin (Latin squares isotopic to Z_N); perturbed_xor / _or / _cyclic
(t entries of a structured table changed).
"""
from __future__ import annotations

import random

from .common import Candidate, canon_table_exact, relabel_table, table_fingerprint

RULE = "convolution"
P = 998244353  # 119 * 2^23 + 1, primitive root 3

CATALOGUE = {
    "name": "transform-based convolution over an index structure",
    "precondition": "the index operation is (isomorphic to) a group or semilattice with a fast factorised transform "
                    "that diagonalises it: Z_2^k (Walsh-Hadamard), Z_(2^a) products (NTT), Boolean lattice "
                    "(zeta/Moebius), chain (prefix sums), or a homomorphic image of one of them (lift, then fold)",
    "transformation": "transform both inputs, multiply pointwise, inverse transform (relabelled by the detected isomorphism)",
    "cost_change": "Theta(N^2) -> Theta(N log N) (Theta(N) for a chain)",
    "failure_mode": "no structure: non-associative or non-commutative tables, Latin squares that are not groups, or "
                    "perturbed tables; the transform of the nearest structure is then wrong on the outputs that the "
                    "disagreeing entries feed",
    "repair": "transform + sparse correction over the disagreeing entries D: exact, cost = cost(transform) + 3|D| "
              "counted operations; beats naive iff 3|D| < 2N^2 - cost(transform)",
    "literature": "Cooley-Tukey 1965 (doi:10.1090/S0025-5718-1965-0178586-1) [recalled]; Yates 1937 [recalled]; dataset "
                  "entries polynomial-multiplication-naive-vs-ntt, xor-convolution, subset-sum-zeta-transform",
}

STRUCTS = ("xor", "cyclic", "prod", "or", "max", "sat")


# ----------------------------------------------------------------------------------------------
# Ideal structures on labels 0..N-1
# ----------------------------------------------------------------------------------------------

def ideal(S, N):
    k = N.bit_length() - 1
    if S == "xor":
        return lambda u, v: u ^ v
    if S == "cyclic":
        return lambda u, v: (u + v) % N
    if S == "prod":  # Z_(N/2) x Z_2, label = 2*x + y
        h = N // 2
        return lambda u, v: 2 * (((u >> 1) + (v >> 1)) % h) + ((u ^ v) & 1)
    if S == "or":
        return lambda u, v: u | v
    if S == "max":
        return lambda u, v: max(u, v)
    if S == "sat":
        return lambda u, v: min(u + v, N - 1)
    raise ValueError(S)


def ideal_table(S, N):
    f = ideal(S, N)
    return [[f(u, v) for v in range(N)] for u in range(N)]


def base_table(family, N, rng):
    if family in STRUCTS:
        return ideal_table(family, N)
    if family == "and":
        return [[u & v for v in range(N)] for u in range(N)]
    if family == "min":
        return [[min(u, v) for v in range(N)] for u in range(N)]
    if family == "sub":
        return [[(u - v) % N for v in range(N)] for u in range(N)]
    if family == "random":
        return [[rng.randrange(N) for _ in range(N)] for _ in range(N)]
    if family == "random_comm":
        T = [[0] * N for _ in range(N)]
        for u in range(N):
            for v in range(u, N):
                T[u][v] = T[v][u] = rng.randrange(N)
        return T
    if family == "latin":
        p1, p2, p3 = (rng.sample(range(N), N) for _ in range(3))
        return [[p3[(p1[u] + p2[v]) % N] for v in range(N)] for u in range(N)]
    if family.startswith("perturbed_"):
        raise ValueError("perturbed tables are built in generate()")
    raise ValueError(family)


# ----------------------------------------------------------------------------------------------
# Structure detection (preprocessing on the operation)
# ----------------------------------------------------------------------------------------------

def _identity(T):
    N = len(T)
    return max(range(N), key=lambda x: (sum(T[x][y] == y for y in range(N)) + sum(T[y][x] == y for y in range(N)), -x))


def _score(T, S, phi):
    N = len(T)
    if phi is None or len(set(phi)) != N:
        return 0.0, None
    f = ideal(S, N)
    D = [(u, v) for u in range(N) for v in range(N) if T[phi[u]][phi[v]] != phi[f(u, v)]]
    return 1 - len(D) / (N * N), D


def _powers(T, e, g, N):
    phi = [e]
    for _ in range(N - 1):
        phi.append(T[phi[-1]][g])
    return phi


def detect(T):
    """Best (score, structure, phi, D) over the library; phi maps ideal labels to table elements."""
    N = len(T)
    k = N.bit_length() - 1
    e = _identity(T)
    cands = []
    # xor: span a basis greedily
    phi = {0: e}
    for g in range(N):
        if len(phi) == N:
            break
        if g in phi.values():
            continue
        b = len(phi).bit_length() - 1
        if (1 << b) != len(phi) or b >= k:
            break
        for u in list(phi):
            phi[u | (1 << b)] = T[phi[u]][g]
    if len(phi) == N:
        cands.append(("xor", [phi[u] for u in range(N)]))
    # cyclic and sat: powers of a generator
    for S in ("cyclic", "sat"):
        best = None
        for g in range(N):
            ph = _powers(T, e, g, N)
            sc, _ = _score(T, S, ph)
            if best is None or sc > best[0]:
                best = (sc, ph)
        cands.append((S, best[1]))
    # prod Z_(N/2) x Z_2: generator g1 of order N/2 (powers), then g2
    if N >= 4:
        h = N // 2
        best = None
        for g1 in range(N):
            pw = _powers(T, e, g1, h)
            if len(set(pw)) != h:
                continue
            for g2 in range(N):
                if g2 in pw:
                    continue
                ph = [0] * N
                for x in range(h):
                    ph[2 * x] = pw[x]
                    ph[2 * x + 1] = T[pw[x]][g2]
                sc, _ = _score(T, "prod", ph)
                if best is None or sc > best[0]:
                    best = (sc, ph)
            if best and best[0] == 1.0:
                break
        if best:
            cands.append(("prod", best[1]))
    # or: atoms of the join order x <= y iff T[x][y] == y
    atoms = [x for x in range(N) if x != e and not any(z not in (e, x) and T[z][x] == x for z in range(N))]
    if len(atoms) == k:
        ph = []
        for mask in range(N):
            v = e
            for i, a in enumerate(atoms):
                if mask >> i & 1:
                    v = T[v][a]
            ph.append(v)
        cands.append(("or", ph))
    # max: chain order by the number of elements absorbed
    order = sorted(range(N), key=lambda x: (sum(T[x][y] == x for y in range(N)), x))
    cands.append(("max", order))
    best = None
    for S, ph in cands:
        sc, D = _score(T, S, ph)
        if best is None or sc > best[0]:
            best = (sc, S, ph, D)
    return best


# ----------------------------------------------------------------------------------------------
# Counted transforms
# ----------------------------------------------------------------------------------------------

def _fwht(a, ops, inverse=False):
    n = len(a)
    h = 1
    while h < n:
        for i in range(0, n, 2 * h):
            for j in range(i, i + h):
                x, y = a[j], a[j + h]
                a[j] = (x + y) % P
                a[j + h] = (x - y) % P
        ops.n += n
        h *= 2
    if inverse:
        ninv = pow(n, P - 2, P)
        for i in range(n):
            a[i] = a[i] * ninv % P
        ops.n += n


def _ntt(a, ops, inverse=False):
    n = len(a)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            a[i], a[j] = a[j], a[i]
    length = 2
    while length <= n:
        w = pow(3, (P - 1) // length, P)
        if inverse:
            w = pow(w, P - 2, P)
        half = length // 2
        tw = [1] * half
        for t in range(1, half):
            tw[t] = tw[t - 1] * w % P   # twiddles: precomputable constants, not counted
        for i in range(0, n, length):
            for t in range(half):
                u = a[i + t]
                v = a[i + t + half] * tw[t] % P
                a[i + t] = (u + v) % P
                a[i + t + half] = (u - v) % P
        ops.n += 3 * (n // 2)
        length <<= 1
    if inverse:
        ninv = pow(n, P - 2, P)
        for i in range(n):
            a[i] = a[i] * ninv % P
        ops.n += n


def _ntt2(a, ops, h, inverse=False):
    """2-D NTT on an h x 2 array stored as a[2*x + y]."""
    rows = [[a[2 * x + y] for x in range(h)] for y in range(2)]
    for r in rows:
        _ntt(r, ops, inverse)
    for x in range(h):
        u, v = rows[0][x], rows[1][x]
        rows[0][x], rows[1][x] = (u + v) % P, (u - v) % P
    ops.n += 2 * h
    if inverse:
        inv2 = pow(2, P - 2, P)
        for y in range(2):
            for x in range(h):
                rows[y][x] = rows[y][x] * inv2 % P
        ops.n += 2 * h
    for y in range(2):
        for x in range(h):
            a[2 * x + y] = rows[y][x]


def _zeta(a, ops, inverse=False):
    n = len(a)
    bit = 1
    while bit < n:
        for m in range(n):
            if m & bit:
                a[m] = (a[m] - a[m ^ bit]) % P if inverse else (a[m] + a[m ^ bit]) % P
        ops.n += n // 2
        bit <<= 1


def ideal_conv(S, A, B, ops):
    N = len(A)
    A, B = list(A), list(B)
    if S == "xor":
        _fwht(A, ops)
        _fwht(B, ops)
        C = [x * y % P for x, y in zip(A, B)]
        ops.n += N
        _fwht(C, ops, inverse=True)
        return C
    if S == "cyclic":
        _ntt(A, ops)
        _ntt(B, ops)
        C = [x * y % P for x, y in zip(A, B)]
        ops.n += N
        _ntt(C, ops, inverse=True)
        return C
    if S == "prod":
        h = N // 2
        _ntt2(A, ops, h)
        _ntt2(B, ops, h)
        C = [x * y % P for x, y in zip(A, B)]
        ops.n += N
        _ntt2(C, ops, h, inverse=True)
        return C
    if S == "or":
        _zeta(A, ops)
        _zeta(B, ops)
        C = [x * y % P for x, y in zip(A, B)]
        ops.n += N
        _zeta(C, ops, inverse=True)
        return C
    if S == "max":
        for X in (A, B):
            for i in range(1, N):
                X[i] = (X[i] + X[i - 1]) % P
        C = [x * y % P for x, y in zip(A, B)]
        for i in range(N - 1, 0, -1):
            C[i] = (C[i] - C[i - 1]) % P
        ops.n += 4 * N - 3
        return C
    if S == "sat":
        M = 2 * N
        A2, B2 = A + [0] * N, B + [0] * N
        _ntt(A2, ops)
        _ntt(B2, ops)
        L = [x * y % P for x, y in zip(A2, B2)]
        ops.n += M
        _ntt(L, ops, inverse=True)
        C = L[:N]
        for t in range(N, M):
            C[N - 1] = (C[N - 1] + L[t]) % P
        ops.n += N
        return C
    raise ValueError(S)


# ----------------------------------------------------------------------------------------------
# Generation
# ----------------------------------------------------------------------------------------------

FAMILY_PLAN = [
    # (family, N choices, count weight)
    ("xor", (4, 8, 16), 30), ("cyclic", (4, 8, 16), 30), ("prod", (8, 16), 12), ("or", (4, 8, 16), 24),
    ("and", (4, 8, 16), 12), ("max", (4, 8, 16), 20), ("min", (4, 8), 10), ("sat", (4, 8, 16), 16),
    ("sub", (4, 8), 8), ("random", (4,), 30), ("random_comm", (4,), 30), ("latin", (4, 8), 20),
    ("perturbed_xor", (8,), 24), ("perturbed_or", (8,), 16), ("perturbed_cyclic", (8,), 16),
]


def generate(seed: int, count: int) -> list[dict]:
    rng = random.Random(f"rules|convolution|{seed}")
    fams = [f for f, _, w in FAMILY_PLAN for _ in range(w)]
    nchoice = {f: ns for f, ns, _ in FAMILY_PLAN}
    out = []
    for _ in range(count):
        fam = rng.choice(fams)
        N = rng.choice(nchoice[fam])
        if fam.startswith("perturbed_"):
            T = ideal_table(fam.split("_", 1)[1], N)
            t = rng.choice([1, 2, 4, 8])
            cells = rng.sample([(u, v) for u in range(N) for v in range(N)], t)
            for u, v in cells:
                T[u][v] = rng.choice([x for x in range(N) if x != T[u][v]])
            extra = {"t": t}
        else:
            T = base_table(fam, N, rng)
            extra = {}
        perm = rng.sample(range(N), N)
        T = relabel_table(T, perm)
        out.append({"family": fam, "N": N, "table": T, **extra})
    return out


def build(spec: dict) -> Candidate:
    return ConvCandidate(spec)


class ConvCandidate(Candidate):
    rule = RULE
    trials = 6

    def __init__(self, spec):
        super().__init__(spec)
        self.T = spec["table"]
        self.N = spec["N"]
        self.screen_sizes = (self.N,)
        self.score_struct, self.S, self.phi, self.D = detect(self.T)

    def instance(self, rng, n):
        return (self.T, self.phi, self.S, [rng.randrange(P) for _ in range(n)], [rng.randrange(P) for _ in range(n)])

    def slow(self, inst, ops):
        T, _, _, a, b = inst
        N = len(a)
        c = [0] * N
        for i in range(N):
            ai, Ti = a[i], T[i]
            for j in range(N):
                k = Ti[j]
                c[k] = (c[k] + ai * b[j]) % P
        ops.n += 2 * N * N
        return c

    def fast(self, inst, ops):
        _, phi, S, a, b = inst
        N = len(a)
        C = ideal_conv(S, [a[phi[u]] for u in range(N)], [b[phi[u]] for u in range(N)], ops)
        c = [0] * N
        for u in range(N):
            c[phi[u]] = C[u]
        return c

    def fast_repaired(self, inst, ops):
        """Transform of the best structure + sparse correction over the disagreeing entries: exact for any table."""
        T, phi, S, a, b = inst
        c = self.fast(inst, ops)
        f = ideal(S, len(a))
        for u, v in self.D:
            x, y = phi[u], phi[v]
            prod_ = a[x] * b[y] % P
            c[T[x][y]] = (c[T[x][y]] + prod_) % P
            c[phi[f(u, v)]] = (c[phi[f(u, v)]] - prod_) % P
            ops.n += 3
        return c

    def score(self, inst, a, b):
        agree = sum(x == y for x, y in zip(a, b)) / len(a)
        return agree == 1.0, agree

    def precondition(self):
        return self.score_struct == 1.0

    def predicates(self):
        T, N = self.T, self.N
        R = range(N)
        assoc = all(T[T[x][y]][z] == T[x][T[y][z]] for x in R for y in R for z in R)
        comm = all(T[x][y] == T[y][x] for x in R for y in R)
        idem = sum(T[x][x] == x for x in R) / N
        return {"associative": assoc, "commutative": comm, "idempotent_fraction": idem,
                "best_structure": self.S, "structure_score": round(self.score_struct, 6), "mismatches": len(self.D)}

    def scaling(self):
        if self.score_struct != 1.0:
            return None
        fast_cost = "2**n" if self.S == "max" else "n*2**n"
        f_riv = ["n*2**n", "n**2*2**n"] if self.S == "max" else ["2**n", "n**2*2**n"]
        return {"slow": {"n_values": [3, 4, 5, 6, 7, 8, 9], "cost": "4**n", "rivals": ["n*2**n", "3**n"]},
                "fast": {"n_values": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "cost": fast_cost, "rivals": f_riv},
                "tolerance": 0.05}

    def scaling_key(self):
        return f"convolution|{self.S}"

    def scale_instance(self, rng, n, side):
        N = 2 ** n
        T = ideal_table(self.S, N) if side == "slow" else None
        return (T, list(range(N)), self.S, [rng.randrange(P) for _ in range(N)], [rng.randrange(P) for _ in range(N)])

    def canonical(self):
        if self.score_struct == 1.0:
            return f"iso:{self.S}:{self.N}"
        if self.N <= 5:
            return "exact:" + "".join(map(str, canon_table_exact(self.T)))
        return "wl:" + table_fingerprint(self.T)

    def cluster(self):
        tag = "exact-structure" if self.score_struct == 1.0 else "no-structure"
        return f"conv:{self.family}:{self.S}:{tag}"

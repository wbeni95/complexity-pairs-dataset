"""Exhaustive GF(2) tensor-rank test for very small tensors (used for: <2,2,2> has no rank-6 scheme over GF(2)).

Fact used (standard): for T in U (x) V (x) W with mode-1 slices T_1..T_u in V (x) W,
    rank(T) <= r   iff   there are r rank-one matrices M_1..M_r in V (x) W whose span contains S = span(T_x).
(If T_x = sum_r lambda_xr M_r then T = sum_r (sum_x lambda_xr e_x) (x) M_r, and conversely.)

Search: let s = dim S and k = r - s (if k < 0 the answer is no: flattening bound). A suitable set spans a space
L with S <= L and dim L / S <= k. So enumerate the subspaces Q of (V (x) W) / S of dimension <= k that are
spanned by images of rank-one matrices, and test whether the rank-one matrices whose image lies in Q span a
space containing S. Images are computed as normal forms modulo an echelon basis of S (a linear map onto a
complement of S, so normal forms of a subspace are closed under XOR). The enumeration is exhaustive: it decides
the question exactly, with cost about C(K, k) span computations, K = number of distinct nonzero images. This is
only feasible for tiny cases (k <= 2 or 3 with K in the low hundreds).
"""
from __future__ import annotations

from itertools import combinations

from .gf2mm import dims, mm_tensor, _outer_bc


def echelon(vectors):
    """Echelon basis {pivot bit: vector} of the GF(2) span of int vectors."""
    basis = {}
    for v in vectors:
        while v:
            hb = v.bit_length() - 1
            e = basis.get(hb)
            if e is None:
                basis[hb] = v
                break
            v ^= e
    return basis


def normal_form(v, basis):
    """Unique representative of v + span(basis): reduce at the pivots in descending order."""
    for hb in sorted(basis, reverse=True):
        if (v >> hb) & 1:
            v ^= basis[hb]
    return v


def _contains(basis, targets):
    return all(normal_form(t, basis) == 0 for t in targets)


def rank_at_most(slices, nb: int, nc: int, r: int):
    """Decide over GF(2) whether the tensor with mode-1 slices `slices` (ints with nb*nc bits, bit y*nc + z)
    has rank <= r. Returns (answer, witness, stats); witness = list of (b, c) rank-one matrices when True."""
    S = echelon(slices)
    s = len(S)
    stats = {"dim_S": s, "k": r - s, "subspaces_tested": 0}
    if r < s:
        return False, None, stats
    k = r - s
    groups = {}
    for b in range(1, 1 << nb):
        for c in range(1, 1 << nc):
            M = _outer_bc(b, c, nc)
            groups.setdefault(normal_form(M, S), []).append((b, c, M))
    keys = sorted(q for q in groups if q != 0)
    stats["rank_one_matrices"] = sum(len(g) for g in groups.values())
    stats["distinct_nonzero_images"] = len(keys)
    targets = list(S.values())
    zero_group = groups.get(0, [])
    for d in range(0, k + 1):
        for gens in combinations(keys, d):
            # Q = span(gens); skip dependent generator sets (their span was tested at a lower d)
            if len(echelon(gens)) < d:
                continue
            stats["subspaces_tested"] += 1
            elems = [0]
            for g in gens:
                elems += [e ^ g for e in elems]
            cand = list(zero_group)
            for e in elems[1:]:
                cand += groups.get(e, [])
            basis = echelon([M for _, _, M in cand])
            if _contains(basis, targets):
                # pick a basis of rank-one matrices spanning a space containing S
                chosen, cb = [], {}
                for b, c, M in cand:
                    v = M
                    while v:
                        hb = v.bit_length() - 1
                        if hb in cb:
                            v ^= cb[hb]
                        else:
                            cb[hb] = v
                            chosen.append((b, c, M))
                            break
                return True, [(b, c) for b, c, _ in chosen], stats
    return False, None, stats


def decomposition_from_witness(slices, witness, nc: int):
    """Turn rank-one matrices whose span contains every slice into terms (a, b, c) of a decomposition."""
    Ms = [_outer_bc(b, c, nc) for b, c in witness]
    # express each slice as a combination of the Ms (Gaussian elimination with combination tracking)
    basis = {}
    for idx, M in enumerate(Ms):
        v, comb = M, 1 << idx
        while v:
            hb = v.bit_length() - 1
            if hb in basis:
                v ^= basis[hb][0]
                comb ^= basis[hb][1]
            else:
                basis[hb] = (v, comb)
                break
    a = [0] * len(Ms)
    for x, T in enumerate(slices):
        v, comb = T, 0
        while v:
            hb = v.bit_length() - 1
            if hb not in basis:
                raise ValueError("slice not in the span of the witness")
            v ^= basis[hb][0]
            comb ^= basis[hb][1]
        for idx in range(len(Ms)):
            if (comb >> idx) & 1:
                a[idx] |= 1 << x
    return [(a[i], b, c) for i, (b, c) in enumerate(witness) if a[i]]


def mm_rank_at_most(fmt, r: int):
    """rank_at_most for the matrix multiplication tensor of format fmt."""
    na, nb, nc = dims(fmt)
    return rank_at_most(mm_tensor(fmt), nb, nc, r)

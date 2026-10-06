"""Flip-graph moves on GF(2) matrix multiplication schemes (after Kauers & Moosbauer, ISSAC 2023).

A scheme is a multiset of rank-one terms a (x) b (x) c (bitmask factors, see `search.gf2mm`). The moves below
never change the tensor the terms sum to; they only change the decomposition.

FLIP. Two terms that share a factor, here the first one:
    a(x)b(x)c + a(x)b'(x)c'  =  a(x)(b+b')(x)c + a(x)b'(x)(c+c')          (over GF(2), minus = plus)
The shared position p is any of the three; which of the two other positions plays the role of b is chosen at
random, and so is the order of the two terms. Flips keep the rank.

REDUCTIONS (applied eagerly, so the state never contains an available reduction):
    R1  a term with a zero factor is dropped;
    R2  two terms sharing two factors merge:  a(x)b(x)c + a(x)b(x)c' = a(x)b(x)(c+c');
    R3  ("linear" mode only) terms sharing a factor a whose b-factors are linearly dependent, b_k = sum_{l in L} b_l,
        merge:  a(x)b_k(x)c_k + sum_L a(x)b_l(x)c_l = sum_L a(x)b_l(x)(c_l + c_k).
R2 is R3 with |L| = 1. R3 is reachable by a sequence of flips followed by R2, so it adds no new edges to the
flip graph; it is a shortcut. (This R3 shortcut is our own implementation choice; we do not claim that
Kauers & Moosbauer's implementation uses it.)

PLUS TRANSITION (plateau escape; raises the rank by one). For two terms sharing no factor:
    a(x)b(x)c + a'(x)b'(x)c'  =  (a+a')(x)b(x)c + a'(x)b(x)(c+c') + a'(x)(b+b')(x)c'
with the roles of the three positions permuted at random. Rank-increasing transitions of this kind were proposed
in the adaptive flip-graph algorithm of Arai, Ichikawa & Hukushima (arXiv:2312.16960, whose abstract describes
"a flexibility that does not strictly reduce the number of multiplications"). We verified that paper's title and
abstract only; the identity above is derived and unit-tested here, and we do not claim it is exactly theirs.

Bookkeeping: for each position p a dict maps a factor value to the ids of the terms having it; a list of
(p, value) keys with at least two terms makes sampling a flip O(1). Sampling picks a shared key uniformly, then
an ordered pair inside its group uniformly; this is NOT uniform over all available flips (keys with large
groups are under-weighted), a documented simplification.
"""
from __future__ import annotations

import random

_OTHER = ((1, 2), (2, 0), (0, 1))  # the two positions other than p


def find_dependency(values):
    """Return a bitmask over indices of a nonempty subset of `values` summing to 0 over GF(2), or None if the
    values are linearly independent. (A zero value is itself a dependent subset.)"""
    basis = {}
    for idx, v in enumerate(values):
        comb = 1 << idx
        while v:
            hb = v.bit_length() - 1
            e = basis.get(hb)
            if e is None:
                basis[hb] = (v, comb)
                break
            v ^= e[0]
            comb ^= e[1]
        else:
            return comb
    return None


class FlipGraphState:
    """A mutable scheme with O(1) flip sampling and eager reductions.

    reduction = "linear" applies R1 + R2 + R3; reduction = "pair" applies R1 + R2 only (closest to the
    reductions of the flip graph proper)."""

    def __init__(self, terms, rng: random.Random, reduction: str = "linear", max_weight: int = 0):
        if reduction not in ("linear", "pair"):
            raise ValueError("reduction must be 'linear' or 'pair'")
        self.rng = rng
        self.max_weight = max_weight  # 0 = off; else flips creating a factor of larger Hamming weight are rejected
        self.n_rejected = 0
        self.linear = reduction == "linear"
        self.t = {}                  # term id -> [f0, f1, f2]
        self.live = []               # term ids (random access for plus transitions)
        self.live_pos = {}
        self.groups = ({}, {}, {})   # position -> {factor value: [term ids]}
        self.shared = []             # (p, value) keys whose group has >= 2 terms
        self.shared_pos = {}
        self.dirty = []              # (p, value) groups to re-check for reductions
        self.next_id = 0
        self.n_reductions = 0        # number of rank-decreasing events applied
        self.n_flips = 0
        self.n_plus = 0
        for term in terms:
            if term[0] and term[1] and term[2]:
                self._add(list(term))
        self.reduce()

    # ------------------------------------------------------------------ basic bookkeeping
    @property
    def rank(self) -> int:
        return len(self.t)

    def scheme(self):
        return [tuple(x) for x in self.t.values()]

    def _join(self, p, v, tid):
        g = self.groups[p].get(v)
        if g is None:
            self.groups[p][v] = [tid]
        else:
            g.append(tid)
            if len(g) == 2:
                key = (p, v)
                self.shared_pos[key] = len(self.shared)
                self.shared.append(key)
        self.dirty.append((p, v))

    def _leave(self, p, v, tid):
        g = self.groups[p][v]
        g.remove(tid)
        if len(g) == 1:
            key = (p, v)
            idx = self.shared_pos.pop(key)
            last = self.shared.pop()
            if last != key:
                self.shared[idx] = last
                self.shared_pos[last] = idx
        elif not g:
            del self.groups[p][v]

    def _add(self, term):
        tid = self.next_id
        self.next_id += 1
        self.t[tid] = term
        self.live_pos[tid] = len(self.live)
        self.live.append(tid)
        for p in (0, 1, 2):
            self._join(p, term[p], tid)
        return tid

    def _remove(self, tid):
        term = self.t.pop(tid)
        for p in (0, 1, 2):
            self._leave(p, term[p], tid)
        idx = self.live_pos.pop(tid)
        last = self.live.pop()
        if last != tid:
            self.live[idx] = last
            self.live_pos[last] = idx
        return term

    def _set(self, tid, p, v):
        """Set factor p of term tid to v (R1: drop the term if v == 0)."""
        term = self.t[tid]
        if v == 0:
            self._remove(tid)
            return
        self._leave(p, term[p], tid)
        term[p] = v
        self._join(p, v, tid)
        q, r = _OTHER[p]
        # groups in which this term's p-factor changed: dependencies there may have appeared
        self.dirty.append((q, term[q]))
        self.dirty.append((r, term[r]))

    # ------------------------------------------------------------------ reductions
    def reduce(self) -> int:
        """Apply reductions until none is available among the dirty groups; return the rank decrease."""
        start = len(self.t)
        dirty = self.dirty
        groups = self.groups
        t = self.t
        while dirty:
            p, v = dirty.pop()
            g = groups[p].get(v)
            if g is None or len(g) < 2:
                continue
            members = list(g)
            for q in _OTHER[p]:
                vals = [t[x][q] for x in members]
                if self.linear:
                    comb = find_dependency(vals)
                else:
                    comb = None
                    seen = {}
                    for idx, val in enumerate(vals):
                        if val in seen:
                            comb = (1 << idx) | (1 << seen[val])
                            break
                        seen[val] = idx
                if comb is None:
                    continue
                subset = [members[i] for i in range(len(members)) if (comb >> i) & 1]
                r = 3 - p - q
                k = subset[self.rng.randrange(len(subset))] if len(subset) > 1 else subset[0]
                if len(subset) == 1:          # zero factor (cannot happen while R1 is maintained)
                    self._remove(k)
                else:
                    wk = t[k][r]
                    self._remove(k)
                    for l in subset:
                        if l != k and l in t:
                            self._set(l, r, t[l][r] ^ wk)
                self.n_reductions += 1
                dirty.append((p, v))          # the group changed; look again
                break
        return start - len(self.t)

    # ------------------------------------------------------------------ moves
    def flip(self) -> bool:
        """Apply one random flip (and any reductions it enables). Return False if no flip is available.
        With max_weight > 0, a sampled flip that would create a factor of Hamming weight > max_weight is
        rejected (the state is unchanged, n_rejected is incremented, and True is returned: a step was taken)."""
        shared = self.shared
        if not shared:
            return False
        rng = self.rng
        p, v = shared[rng.randrange(len(shared))]
        g = self.groups[p][v]
        n = len(g)
        a = rng.randrange(n)
        b = rng.randrange(n - 1)
        if b >= a:
            b += 1
        i, j = g[a], g[b]
        q, r = _OTHER[p]
        if rng.getrandbits(1):
            q, r = r, q
        ti, tj = self.t[i], self.t[j]
        new_iq = ti[q] ^ tj[q]
        new_jr = tj[r] ^ ti[r]
        mw = self.max_weight
        if mw and (new_iq.bit_count() > mw or new_jr.bit_count() > mw):
            self.n_rejected += 1      # heuristic weight cap: the sampled flip is not applied
            return True
        self._set(i, q, new_iq)
        self._set(j, r, new_jr)
        self.n_flips += 1
        self.reduce()
        return True

    def apply_flip(self, i, j, p, q, r) -> None:
        """The flip of terms i, j (sharing factor p): i[q] += j[q], j[r] += i[r]; then reductions."""
        ti, tj = self.t[i], self.t[j]
        new_iq = ti[q] ^ tj[q]
        new_jr = tj[r] ^ ti[r]
        self._set(i, q, new_iq)
        self._set(j, r, new_jr)
        self.n_flips += 1
        self.reduce()

    def _in_span(self, v, tids, pos):
        """Is v in the GF(2) span of the pos-factors of the given terms?"""
        basis = {}
        for x in tids:
            w = self.t[x][pos]
            while w:
                hb = w.bit_length() - 1
                e = basis.get(hb)
                if e is None:
                    basis[hb] = w
                    break
                w ^= e
        while v:
            hb = v.bit_length() - 1
            e = basis.get(hb)
            if e is None:
                return False
            v ^= e
        return True

    def reducing_flips(self, limit: int = 0):
        """One-step lookahead: the flips (i, j, p, q, r) after which a reduction is available.

        Valid when no reduction is currently available (the invariant kept by `reduce`). With i[q] -> u = i[q]+j[q]
        and j[r] -> w = j[r]+i[r], a new dependency can only appear in (proof in the report):
          (1) the q-factors of the terms sharing i's r-factor, together with u;
          (3) the p- or r-factors of the terms whose q-factor is u, together with i's;
          (4) the r-factors of the terms sharing j's q-factor, together with w;
          (5) the p- or q-factors of the terms whose r-factor is w, together with j's.
        (The group sharing the flipped factor p keeps the spans of its q- and r-factors.) In "pair" mode only
        equalities count. Returns up to `limit` candidates (0 = all)."""
        out = []
        t = self.t
        groups = self.groups
        lin = self.linear
        for p, v in self.shared:
            g = groups[p][v]
            for i in g:
                ti = t[i]
                for j in g:
                    if i == j:
                        continue
                    tj = t[j]
                    for q, r in (_OTHER[p], _OTHER[p][::-1]):
                        u = ti[q] ^ tj[q]
                        w = tj[r] ^ ti[r]
                        hit = False
                        # (2) pair mode only: the shared group may hold i[q]+j[q] or j[r]+i[r] already
                        # (in linear mode that would be a dependency, excluded by the invariant)
                        if not lin:
                            hit = any((t[k][q] == u and k != i) or (t[k][r] == w and k != j) for k in g)
                        # (1)
                        K = [k for k in groups[r][ti[r]] if k != i]
                        if K and not hit:
                            hit = self._in_span(u, K, q) if lin else any(t[k][q] == u for k in K)
                        # (3)
                        if not hit:
                            K = groups[q].get(u)
                            if K:
                                if lin:
                                    hit = self._in_span(ti[p], K, p) or self._in_span(ti[r], K, r)
                                else:
                                    hit = any(t[k][p] == ti[p] or t[k][r] == ti[r] for k in K)
                        # (4)
                        if not hit:
                            K = [k for k in groups[q][tj[q]] if k != j]
                            if K:
                                hit = self._in_span(w, K, r) if lin else any(t[k][r] == w for k in K)
                        # (5)
                        if not hit:
                            K = groups[r].get(w)
                            if K:
                                if lin:
                                    hit = self._in_span(tj[p], K, p) or self._in_span(tj[q], K, q)
                                else:
                                    hit = any(t[k][p] == tj[p] or t[k][q] == tj[q] for k in K)
                        if hit:
                            out.append((i, j, p, q, r))
                            if limit and len(out) >= limit:
                                return out
        return out

    def plus(self) -> bool:
        """Apply one random plus transition (rank + 1, then reductions). Return False if no pair of terms
        without a common factor was found in 100 tries."""
        live = self.live
        if len(live) < 2:
            return False
        rng = self.rng
        t = self.t
        for _ in range(100):
            i = live[rng.randrange(len(live))]
            j = live[rng.randrange(len(live))]
            if i == j:
                continue
            ti, tj = t[i], t[j]
            if ti[0] != tj[0] and ti[1] != tj[1] and ti[2] != tj[2]:
                break
        else:
            return False
        p = rng.randrange(3)
        q, r = _OTHER[p]
        if rng.getrandbits(1):
            q, r = r, q
        a, b, c = ti[p], ti[q], ti[r]
        a2, b2, c2 = tj[p], tj[q], tj[r]
        # a(x)b(x)c + a2(x)b2(x)c2 = (a+a2)(x)b(x)c + a2(x)(b+b2)(x)c2 + a2(x)b(x)(c+c2)
        self._set(i, p, a ^ a2)
        self._set(j, q, b ^ b2)
        new = [0, 0, 0]
        new[p], new[q], new[r] = a2, b, c ^ c2
        self._add(new)
        self.n_plus += 1
        self.reduce()
        return True

    def check_invariants(self) -> None:
        """Consistency of the bookkeeping (for tests)."""
        for p in (0, 1, 2):
            count = 0
            for v, g in self.groups[p].items():
                assert g, "empty group kept"
                for tid in g:
                    assert self.t[tid][p] == v
                count += len(g)
                assert ((p, v) in self.shared_pos) == (len(g) >= 2)
            assert count == len(self.t)
        assert len(self.shared) == len(self.shared_pos)
        for key, idx in self.shared_pos.items():
            assert self.shared[idx] == key
        assert sorted(self.live) == sorted(self.t)
        for tid, idx in self.live_pos.items():
            assert self.live[idx] == tid
        for term in self.t.values():
            assert term[0] and term[1] and term[2], "zero factor kept"

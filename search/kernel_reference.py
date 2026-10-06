"""Line-by-line Python mirror of search/kernel/flipwalk.rs, for differential testing only.

Identical inputs and seeds must give identical results (best scheme, step count, counters) in both
implementations; tests/test_search_rust.py checks this. It is slow and not meant for real searches.
The time budget is not mirrored, so call it with max_seconds effectively unlimited.
Dead-end detection and escape (flipwalk.rs --dead-end, research/2026-10-06c_kernel_deadends.md) are mirrored;
walk(..., dead_end=False) reproduces the earlier kernel exactly.
"""
from __future__ import annotations

MASK64 = (1 << 64) - 1


class SplitMix64:
    def __init__(self, seed: int):
        self.state = seed & MASK64

    def next(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK64
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
        return z ^ (z >> 31)

    def below(self, n: int) -> int:
        return self.next() % n


def has_zero(t) -> bool:
    return t[0] == 0 or t[1] == 0 or t[2] == 0


def weight_ok(t, cap: int) -> bool:
    return cap == 0 or (bin(t[0]).count("1") <= cap and bin(t[1]).count("1") <= cap and bin(t[2]).count("1") <= cap)


def flip(terms, i, j, p, cap) -> bool:
    ti, tj = terms[i], terms[j]
    ni, nj = list(ti), list(tj)
    if p == 0:
        ni[1] ^= tj[1]
        nj[2] ^= ti[2]
    elif p == 1:
        ni[0] ^= tj[0]
        nj[2] ^= ti[2]
    else:
        ni[0] ^= tj[0]
        nj[1] ^= ti[1]
    if not weight_ok(ni, cap) or not weight_ok(nj, cap):
        return False
    terms[i] = ni
    terms[j] = nj
    return True


REMOVED = -1


def shift_after_remove(work, removed):
    for idx, w in enumerate(work):
        if w == removed:
            work[idx] = REMOVED
        elif w != REMOVED and w > removed:
            work[idx] = w - 1


def reduce(terms, touched):
    work = list(touched)
    while work:
        t = work.pop()
        if t == REMOVED or t >= len(terms):
            continue
        if has_zero(terms[t]):
            del terms[t]
            shift_after_remove(work, t)
            continue
        for q in range(len(terms)):
            if q == t:
                continue
            a, b = terms[t], terms[q]
            if a[0] == b[0] and a[1] == b[1]:
                k = 2
            elif a[0] == b[0] and a[2] == b[2]:
                k = 1
            elif a[1] == b[1] and a[2] == b[2]:
                k = 0
            else:
                continue
            nq = list(terms[q])
            nq[k] ^= a[k]
            terms[q] = nq
            del terms[t]
            shift_after_remove(work, t)
            work.append(q - 1 if q > t else q)
            break


def plus_transition(terms, rng, cap) -> bool:
    r = len(terms)
    if r < 2:
        return False
    i = rng.below(r)
    j = rng.below(r)
    if i == j:
        return False
    ti, tj = terms[i], terms[j]
    if ti[0] == tj[0] or ti[1] == tj[1] or ti[2] == tj[2]:
        return False
    t1 = [ti[0] ^ tj[0], ti[1], ti[2]]
    t2 = [tj[0], ti[1] ^ tj[1], tj[2]]
    t3 = [tj[0], ti[1], ti[2] ^ tj[2]]
    if not weight_ok(t1, cap) or not weight_ok(t2, cap) or not weight_ok(t3, cap):
        return False
    terms[i] = t1
    terms[j] = t2
    terms.append(t3)
    reduce(terms, [i, j, len(terms) - 1])
    return True


def walk(start, seed, max_steps, plateau=50_000, slack=3, max_weight=0, target_rank=0, dead_end=True,
         on_dead_end=None):
    """Mirror of flipwalk.rs walk(). `on_dead_end(terms, best_rank)` (testing only, default None) is called at
    every step where a dead end is detected, before the escape move, with the current scheme (which it must not
    modify) and the rank of the best scheme so far."""
    rng = SplitMix64(seed)
    terms = [list(t) for t in start]
    best = [list(t) for t in terms]
    since = 0
    counters = {"flips": 0, "rejected_weight": 0, "plus": 0, "restarts": 0, "dead_ends": 0}
    improvements = []
    # Exact dead-end detection (see flipwalk.rs): stamp[3*i+p] == epoch records that term i had no partner
    # sharing factor p in the current scheme; the epoch advances whenever the scheme may have changed.
    stamp = [0] * (3 * len(terms))
    epoch = 1
    unmatched = 0
    swept = 0
    step = 0
    while step < max_steps and len(best) > target_rank:
        step += 1
        r = len(terms)
        found_dead_end = False
        if r >= 2:
            i = rng.below(r)
            p = rng.below(3)
            key = terms[i][p]
            cands = [q for q in range(r) if q != i and terms[q][p] == key]
            if cands:
                j = cands[rng.below(len(cands))]
                if flip(terms, i, j, p, max_weight):
                    counters["flips"] += 1
                    reduce(terms, [i, j])
                    epoch += 1
                    unmatched = 0
                else:
                    counters["rejected_weight"] += 1
            elif dead_end:
                if len(stamp) < 3 * r:
                    stamp.extend([0] * (3 * r - len(stamp)))
                cell = 3 * i + p
                if stamp[cell] != epoch:
                    stamp[cell] = epoch
                    unmatched += 1
                if unmatched >= r and swept != epoch:  # one deterministic completion sweep per epoch
                    swept = epoch
                    for c in range(3 * r):
                        if stamp[c] == epoch:
                            continue
                        ti, tp = c // 3, c % 3
                        key2 = terms[ti][tp]
                        if any(q != ti and terms[q][tp] == key2 for q in range(r)):
                            break
                        stamp[c] = epoch
                        unmatched += 1
                found_dead_end = unmatched == 3 * r
        if len(terms) < len(best):
            best = [list(t) for t in terms]
            since = 0
            improvements.append((len(best), step))
        else:
            since += 1
        if since >= plateau or found_dead_end:
            if found_dead_end:
                counters["dead_ends"] += 1
                if on_dead_end is not None:
                    on_dead_end(terms, len(best))
            if len(terms) > len(best) + slack:
                terms = [list(t) for t in best]
                counters["restarts"] += 1
                epoch += 1
                unmatched = 0
            elif plus_transition(terms, rng, max_weight):
                counters["plus"] += 1
                epoch += 1
                unmatched = 0
            since = 0
    return {"best": [tuple(t) for t in best], "steps": step, "improvements": improvements, **counters}

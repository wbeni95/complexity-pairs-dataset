"""Counting the n-bit integers with a cheap representation k = X^2 + C, by root groups of equal bit length
(algorithm A3). Polynomial in n.

Definitions as in entry.json: L(v) = binary digits of |v| (L(0) = 1), f_k(X) = L(X) + L(C) + [C < 0] with C = k - X^2,
S_n = {0 <= k < 2^n : min over X of f_k(X) <= n - 4}. Output: (|S_n|, number of root groups processed).

Notation: B = 2^n - 1, v = n - 4, T = isqrt(B) + 1. A root X with w = v - L(X) >= 1 has the unclipped interval
J_X = [X^2 - m, X^2 + s], s = 2^w - 1, m = 2^(w-1) - 1 (w >= 2) or 0 (w = 1). By Lemma B of the entry,
|S_n| = |U| - |U below 0| - |U above B| for U = union of J_X over X = 0..T.

Group l is X in {0, 1} for l = 1 and X in [2^(l-1), 2^l - 1] for l >= 2 (cut at T); w, s and m are constant in it.
The sweep in X order (left ends strictly increase) treats a group [a, b] in O(1) steps: root a by the generic rule;
for X in (a, b], X starts a new component iff X >= t1 = floor((s + m + 2)/2) + 1 (gap to the previous interval of the
group) and X >= t2 = isqrt(E + 1 + m) + 1 (gap to everything before, E = right end of the current component after
root a). Both conditions are monotone, so the roots in (a, max(t1, t2, a + 1)) extend the current component and every
later root of the group starts a component of its own: a whole component of length s + m + 1, except the last root
of the group, whose interval becomes the current component.
Below 0: exactly [-m_1, -1], m_1 the m of group 1. Above B: at most 2 roots X <= T have X^2 + s > B (proof in
PROOFS.md); the roots of a group with X^2 > B - s start at isqrt(B - s) + 1.

Cost: floor(n/2) + 1 groups for n >= 11, O(1) arithmetic operations and at most two integer square roots per group.
The square roots use Newton's iteration, O(log n) steps each (proof in PROOFS.md): O(n log n) word operations.
For n <= 5 no group is processed and the result is 0 = |S_n| (every representation costs at least 2 bits).
"""


def isqrt_newton(q, stats=None):
    """floor(sqrt(q)) for an integer q >= 0 by Newton's iteration from 2^ceil(L(q)/2).

    The iterates never drop below floor(sqrt(q)) and decrease strictly while they are above it, so the first
    non-decreasing step stops the loop at floor(sqrt(q)). stats (optional dict) counts calls and iteration steps.
    """
    if stats is not None:
        stats["isqrt_calls"] = stats.get("isqrt_calls", 0) + 1
        stats["isqrt_max_bits"] = max(stats.get("isqrt_max_bits", 0), q.bit_length())
    if q == 0:
        return 0
    x = 1 << ((q.bit_length() + 1) // 2)
    while True:
        if stats is not None:
            stats["newton_steps"] = stats.get("newton_steps", 0) + 1
        t = x + q // x
        if stats is not None:
            stats["max_value_bits"] = max(stats.get("max_value_bits", 0), t.bit_length())
        y = t // 2
        if y >= x:
            return x
        x = y


def count_groups(n, stats=None):
    """(|S_n|, groups processed). stats (optional dict) receives square-root counts and the number of roots whose
    interval reaches above B."""
    v = n - 4
    B = (1 << n) - 1
    T = isqrt_newton(B, stats) + 1
    closed = 0                        # total size of the finished components
    start = end = None                # current component of the sweep
    below = 0
    tops = []                         # parts above B of the intervals that reach above B
    groups = 0
    l = 1
    while True:
        a = 0 if l == 1 else 1 << (l - 1)
        w = v - l
        if a > T or w < 1:
            break
        b = min((1 << l) - 1, T)
        groups += 1
        m = (1 << (w - 1)) - 1 if w >= 2 else 0
        s = (1 << w) - 1
        if l == 1:
            below = m
        # root a: generic sweep step
        lo, hi = a * a - m, a * a + s
        if start is None:
            start, end = lo, hi
        elif lo > end + 1:
            closed += end - start + 1
            start, end = lo, hi
        elif hi > end:
            end = hi
        if b > a:
            t1 = (s + m + 2) // 2 + 1                     # lo_X > hi_(X-1) + 1  <=>  2X - 1 > s + m + 1
            t2 = isqrt_newton(end + 1 + m, stats) + 1      # lo_X > end + 1       <=>  X^2 > end + 1 + m
            xs = max(a + 1, t1, t2)                       # first root of (a, b] that starts a component
            if xs - 1 >= a + 1:                           # roots a+1 .. min(xs-1, b) extend the component
                h = min(xs - 1, b) ** 2 + s
                if h > end:
                    end = h
            if xs <= b:                                   # roots xs .. b: one interval each
                closed += end - start + 1
                closed += (b - xs) * (s + m + 1)
                start, end = b * b - m, b * b + s
        # roots of this group whose interval reaches above B: X^2 > B - s
        q = B - s
        x0 = a if q < 0 else max(a, isqrt_newton(q, stats) + 1)
        for x in range(x0, b + 1):
            tops.append((max(x * x - m, B + 1), x * x + s))
        if stats is not None:                             # size of the integers handled in this group
            group_values = [start, end, closed, lo, hi, b * b + s, end + 1 + m, q]
            if b > a:
                group_values += [t1, t2, xs, h if xs - 1 >= a + 1 else 0, (b - xs) * (s + m + 1) if xs <= b else 0]
            group_values += [z for pair in tops for z in pair]
            stats["max_value_bits"] = max([stats.get("max_value_bits", 0)]
                                          + [abs(z).bit_length() for z in group_values])
        l += 1
    if stats is not None:
        stats["above_range_roots"] = len(tops)
        stats["groups"] = groups
    if start is None:
        return 0, groups
    closed += end - start + 1
    above = 0                         # union of the parts above B; their left ends are non-decreasing in X
    t_start = t_end = None
    for lo, hi in tops:
        if t_start is None:
            t_start, t_end = lo, hi
        elif lo <= t_end + 1:
            if hi > t_end:
                t_end = hi
        else:
            above += t_end - t_start + 1
            t_start, t_end = lo, hi
    if t_start is not None:
        above += t_end - t_start + 1
    if stats is not None:
        stats["max_value_bits"] = max(stats.get("max_value_bits", 0), closed.bit_length(), above.bit_length())
    return closed - below - above, groups


def count_by_groups(n):
    return count_groups(n)

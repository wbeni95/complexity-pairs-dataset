"""Instances: a list of n integers.

V1 values are drawn from a small range so that ties are common (the subsequence must be STRICTLY
increasing), with some sorted, reversed and constant lists mixed in.

The oracle uses an independent reduction: the longest strictly increasing subsequence of a equals the
longest common subsequence of a and sorted(set(a)), computed by the textbook LCS table.
"""

ORACLE_MAX_N = 400


def generate(n, rng):
    style = rng.random()
    if style < 0.1:
        return sorted(rng.randint(-n, n) for _ in range(n))
    if style < 0.2:
        return sorted((rng.randint(-n, n) for _ in range(n)), reverse=True)
    if style < 0.25:
        return [7] * n
    span = max(1, n // 2)
    return [rng.randint(-span, span) for _ in range(n)]


def check(instance, output):
    if len(instance) > ORACLE_MAX_N:
        return None
    b = sorted(set(instance))
    prev = [0] * (len(b) + 1)
    for x in instance:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            cur[j] = prev[j - 1] + 1 if x == y else max(prev[j], cur[j - 1])
        prev = cur
    return output == prev[-1]


# --- Exact comparison counting for V2 (measure: "reported"; RESEARCH_LOG RL-047/RL-048) -------------

_comparisons = 0


def _val(x):
    return x.v if isinstance(x, CountingKey) else x


class CountingKey:
    """An integer element that counts every comparison made on it (in either operand position)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __lt__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v < _val(other)

    def __le__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v <= _val(other)

    def __gt__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v > _val(other)

    def __ge__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v >= _val(other)

    def __eq__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v == _val(other)

    def __ne__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v != _val(other)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountingKey({self.v!r})"


def generate_scaling(n, rng):
    """A strictly increasing list with random gaps: the worst case for patience sorting.

    The answer is L = n, so the i-th binary search runs over i tails: sum of log2(i) ~ n log2 n steps.
    The enumeration (2^n n inner steps) and the quadratic DP (n(n-1)/2 comparisons) do the same amount
    of work on every input of length n.

    Each element is wrapped in CountingKey, which counts the comparisons between elements that the
    UNCHANGED implementations make; reported_cost() returns that count (the counter is reset here).
    Exact values on this input: subset enumeration n 2^(n-1) - 2^n + 1 (one `<=` per chosen index after
    the first, summed over all masks); quadratic DP n(n-1)/2; patience sorting sum_{j=2..n} floor(log2 j).
    """
    global _comparisons
    a, x = [], 0
    for _ in range(n):
        x += rng.randint(1, 10)
        a.append(CountingKey(x))
    _comparisons = 0
    return a


def reported_cost(output):
    """Number of element comparisons performed since the instance was generated."""
    return _comparisons

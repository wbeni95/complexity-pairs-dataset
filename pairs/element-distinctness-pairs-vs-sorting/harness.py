"""Instances: tuples of n integers.

generate() mixes four kinds so that V1 sees both answers: n distinct values from a range of size 10 n^2 + 10;
the same with one planted duplicate (a copy of one value written over another position); n values drawn
from [0, n) (duplicates almost always, for n >= 2); and distinct values of magnitude up to 10^18 with both
signs.

generate_scaling() returns n distinct values from [-10^9, 10^9): the worst case for the all-pairs scan
(no early exit). The sorting algorithm does Theta(n log n) work on every input. For V2 (measure:
"reported", RESEARCH_LOG RL-047/RL-048) each value is wrapped in CountingKey, which counts every comparison
the UNCHANGED implementations make between input values (==, <=, and the other four operators), and
reported_cost() returns that count: exactly n(n-1)/2 equality tests for the all-pairs scan on these
distinct inputs; merge-sort comparisons plus n - 1 neighbour tests for the sorting algorithm.

The oracle compares len(set(values)) with n (hashing): it shares no code or idea with the two
implementations under test.
"""


def generate(n, rng):
    kind = rng.randrange(4)
    if kind == 0:
        return tuple(rng.sample(range(10 * n * n + 10), n))
    if kind == 1:
        vals = rng.sample(range(10 * n * n + 10), n)
        if n >= 2:
            i, j = rng.sample(range(n), 2)
            vals[j] = vals[i]
        return tuple(vals)
    if kind == 2:
        return tuple(rng.randrange(max(n, 1)) for _ in range(n))
    return tuple(v - 10 ** 18 for v in rng.sample(range(2 * 10 ** 18), n))


def check(values, output):
    return output == (len(set(values)) == len(values))


# --- Exact comparison counting for V2 (measure: "reported") -----------------------------------------

_comparisons = 0


def _val(x):
    return x.v if isinstance(x, CountingKey) else x


class CountingKey:
    """An integer value that counts every comparison made on it (in either operand position)."""
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
    """n distinct values from [-10^9, 10^9), wrapped in CountingKey; resets the comparison counter."""
    global _comparisons
    inst = tuple(CountingKey(v) for v in rng.sample(range(-10 ** 9, 10 ** 9), n))
    _comparisons = 0
    return inst


def reported_cost(output):
    """Number of comparisons between input values performed since the instance was generated."""
    return _comparisons

"""Instances: n integers drawn from [0, n] (duplicates occur, and equal values are not inversions).

V2 counts comparisons (measure: "reported"; RESEARCH_LOG RL-047/RL-048): generate_scaling() draws the same
values as generate() (same distribution, same seeds) and wraps each in CountingKey, which counts every
comparison the UNCHANGED implementations make between elements (<, <=, >, >=, ==, !=). reported_cost()
returns the count since the instance was generated: exactly n(n-1)/2 for the all-pairs scan (one `>` per
pair), and the merge comparisons (`<`) for merge-sort counting.
"""


def generate(n, rng):
    return tuple(rng.randint(0, n) for _ in range(n))


def check(values, output):
    """Independent oracle: a Fenwick (binary indexed) tree over value ranks, Theta(n log n)."""
    ranks = {v: i + 1 for i, v in enumerate(sorted(set(values)))}
    tree = [0] * (len(ranks) + 1)
    count = 0
    for seen, v in enumerate(values):
        r = ranks[v]
        le, i = 0, r          # number of earlier elements <= v
        while i > 0:
            le += tree[i]
            i -= i & -i
        count += seen - le    # earlier elements > v
        i = r
        while i < len(tree):
            tree[i] += 1
            i += i & -i
    return output == count


# --- Exact comparison counting for V2 (measure: "reported") -----------------------------------------

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
    """The values of generate(n, rng), wrapped in CountingKey; resets the comparison counter."""
    global _comparisons
    inst = tuple(CountingKey(x) for x in generate(n, rng))
    _comparisons = 0
    return inst


def reported_cost(output):
    """Number of element comparisons performed since the instance was generated."""
    return _comparisons

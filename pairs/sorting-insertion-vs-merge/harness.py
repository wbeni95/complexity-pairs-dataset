"""Instances: a list of n integers drawn uniformly from [-n, n] (so duplicates and negatives occur).

Uniformly random input is the average case for insertion sort, which is honest for V2 because insertion
sort is Theta(n^2) on average as well as in the worst case, and merge sort is Theta(n log n) on every input.

V2 counts comparisons (measure: "reported"; RESEARCH_LOG RL-047/RL-048 explain why timing cannot resolve a
log factor). generate_scaling() draws the same values as generate() (same distribution, same seeds) but
wraps each one in CountingKey, an integer key that counts every comparison the UNCHANGED implementations
make on it (<, <=, >, >=, ==, !=). reported_cost() returns the number of comparisons since the instance was
generated. Insertion sort compares only with `>`, merge sort only with `<`.

The oracle is Python's built-in sorted(), used here only as a reference, never as an implementation.
"""


def generate(n, rng):
    return [rng.randint(-n, n) for _ in range(n)]


def check(instance, output):
    return isinstance(output, list) and output == sorted(instance)


# --- Exact comparison counting for V2 (measure: "reported") -----------------------------------------

_comparisons = 0


def _val(x):
    return x.v if isinstance(x, CountingKey) else x


class CountingKey:
    """An integer key that counts every comparison made on it (in either operand position)."""
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
    inst = [CountingKey(x) for x in generate(n, rng)]
    _comparisons = 0
    return inst


def reported_cost(output):
    """Number of key comparisons performed since the instance was generated."""
    return _comparisons

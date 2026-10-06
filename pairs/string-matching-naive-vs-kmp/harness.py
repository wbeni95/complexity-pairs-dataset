"""Instances: (text, pattern), text of length n, non-empty pattern of length m.

V1 texts come from small alphabets (and periodic strings) so that matches, overlapping matches and
near-misses are frequent. The oracle counts occurrences with str.find in a loop; it is a reference
only, never an implementation under test.
"""


def generate(n, rng):
    style = rng.random()
    if style < 0.6:
        text = "".join(rng.choice("ab") for _ in range(n))
    elif style < 0.8:
        text = "".join(rng.choice("abc") for _ in range(n))
    else:                                    # periodic text, e.g. "abaabaaba..."
        period = "".join(rng.choice("ab") for _ in range(rng.randint(1, 3)))
        text = (period * (n // len(period) + 1))[:n]
    kind = rng.random()
    if kind < 0.5 and n > 0:                 # a substring of the text: at least one match
        m = rng.randint(1, min(n, 8))
        i = rng.randint(0, n - m)
        pattern = text[i:i + m]
    elif kind < 0.9:                         # a random short pattern
        pattern = "".join(rng.choice("ab") for _ in range(rng.randint(1, 5)))
    else:                                    # longer than the text (when n is small): no match
        pattern = "a" * (n + 1)
    return (text, pattern)


def check(instance, output):
    text, pattern = instance
    count, start = 0, 0
    while True:
        i = text.find(pattern, start)
        if i < 0:
            return output == count
        count += 1
        start = i + 1                        # step one past the match: overlapping occurrences count


# --- Exact character-comparison counting for V2 (measure: "reported"; RESEARCH_LOG RL-047/RL-048) ----
# Characters of a Python str cannot be instrumented, so the scaling instance holds the same characters as
# tuples of CountingChar. The UNCHANGED implementations touch text and pattern only through len(),
# indexing, iteration and ==/!= between characters, so they run on these tuples as on strings, and every
# character comparison goes through CountingChar.

_comparisons = 0


def _val(x):
    return x.c if isinstance(x, CountingChar) else x


class CountingChar:
    """One character that counts every == / != comparison made on it."""
    __slots__ = ("c",)

    def __init__(self, c):
        self.c = c

    def __eq__(self, other):
        global _comparisons
        _comparisons += 1
        return self.c == _val(other)

    def __ne__(self, other):
        global _comparisons
        _comparisons += 1
        return self.c != _val(other)

    def __hash__(self):
        return hash(self.c)

    def __repr__(self):
        return f"CountingChar({self.c!r})"


def generate_scaling(n, rng):
    """Worst case for the naive matcher with m = n // 2: T = a^n, P = a^(m-1) b.

    Every one of the n - m + 1 alignments matches m - 1 characters before failing on the final 'b',
    so the naive matcher does (n - m + 1) m ~ n^2 / 4 comparisons; KMP stays Theta(n + m) = Theta(n).
    Returned as tuples of CountingChar (see above); resets the comparison counter.
    """
    global _comparisons
    m = n // 2
    text = tuple(CountingChar(c) for c in "a" * n)
    pattern = tuple(CountingChar(c) for c in "a" * (m - 1) + "b")
    _comparisons = 0
    return (text, pattern)


def reported_cost(output):
    """Number of character comparisons performed since the instance was generated."""
    return _comparisons

"""Harness for multi-pattern matching: naive matching per pattern vs KMP per pattern vs Aho-Corasick.

Instance (text, patterns): a text and a tuple of non-empty patterns (strings in V1). Output: a tuple with, for every
pattern in the given order, the number of positions where it occurs in the text; overlapping occurrences all count,
and a pattern listed twice gets its count twice.

generate(n, rng): n patterns (n = 0 gives the empty tuple of counts). Texts over {a, b} or {a, b, c}, random or
periodic, of length between 0 and 6n + 6; patterns mix substrings of the text, random short strings, prefixes and
suffixes of one another (e.g. a, aa, aba), duplicates and patterns longer than the text.

check(instance, output) is independent of the implementations: it counts every pattern with str.find in a loop
(stepping one past each match, so overlapping occurrences count) and compares the tuple.

V2 (measure "reported"): generate_scaling(n, rng) is the family with text a^(n^2) and the n patterns
a^(j-1) b, j = 1..n (total pattern length n(n+1)/2), given as tuples of CountingChar, which count every == and !=
between characters; it resets the counter. The implementations touch text and patterns only through len(),
indexing, iteration and ==/!= between characters, so they run unchanged on these tuples. Exact comparison counts
(derived in entry.json, checked in experiments/2026-10-06i_aho_corasick.py):
  naive          n(n+1)(3n^2 - 2n + 2)/6             (n >= 1)
  KMP each       3n^3 - 2n^2 - 5n + 6                (n >= 2)
  Aho-Corasick   4n^2 - 3                            (n >= 1)
                 = (n-1)^2 trie + (3n-5) failure links + (3n^2 - n + 1) scan   (this split for n >= 2)
Proofs of these counts and of all other claims: PROOFS.md.
No counted operation happens inside a CPython built-in.
"""


def generate(n, rng):
    style = rng.random()
    length = rng.randint(0, 6 * n + 6)
    if style < 0.5:
        text = "".join(rng.choice("ab") for _ in range(length))
    elif style < 0.75:
        text = "".join(rng.choice("abc") for _ in range(length))
    else:
        period = "".join(rng.choice("ab") for _ in range(rng.randint(1, 3)))
        text = (period * (length // len(period) + 1))[:length]
    patterns = []
    for _ in range(n):
        kind = rng.random()
        if kind < 0.35 and text:
            m = rng.randint(1, min(len(text), 8))
            i = rng.randint(0, len(text) - m)
            patterns.append(text[i:i + m])
        elif kind < 0.6:
            patterns.append("".join(rng.choice("ab") for _ in range(rng.randint(1, 5))))
        elif kind < 0.8 and patterns:
            base = rng.choice(patterns)
            cut = rng.randint(1, len(base))
            patterns.append(base[:cut] if rng.random() < 0.5 else base[-cut:])
        elif kind < 0.9 and patterns:
            patterns.append(rng.choice(patterns))
        else:
            patterns.append("a" * rng.randint(1, len(text) + 2))
    return (text, tuple(patterns))


def _count_find(text, pattern):
    count, start = 0, 0
    while True:
        i = text.find(pattern, start)
        if i < 0:
            return count
        count += 1
        start = i + 1                       # one past the match: overlapping occurrences count


def check(instance, output):
    text, patterns = instance
    if not isinstance(output, tuple) or len(output) != len(patterns):
        return False
    if any(isinstance(x, bool) or not isinstance(x, int) for x in output):
        return False
    return output == tuple(_count_find(text, p) for p in patterns)


# --- Exact character-comparison counting for V2 (measure: "reported") ---------------------------------------

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

    __hash__ = None

    def __repr__(self):
        return f"CountingChar({self.c!r})"


def scaling_strings(n):
    """The V2 family as plain strings: text a^(n^2), patterns a^(j-1) b for j = 1..n."""
    return "a" * (n * n), tuple("a" * (j - 1) + "b" for j in range(1, n + 1))


def generate_scaling(n, rng):
    """V2 family as tuples of CountingChar (deterministic; rng unused); resets the comparison counter."""
    global _comparisons
    text, patterns = scaling_strings(n)
    inst = (tuple(CountingChar(c) for c in text), tuple(tuple(CountingChar(c) for c in p) for p in patterns))
    _comparisons = 0
    return inst


def reported_cost(output):
    """Number of character comparisons since the scaling instance was generated."""
    return _comparisons

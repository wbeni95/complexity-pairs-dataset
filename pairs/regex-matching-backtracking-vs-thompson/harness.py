"""Instances: (pattern, text) in the dialect of entry.json (symbols a-z and '.', quantifiers '?' and '*', full match).

generate(n, rng): size parameter n means: at most 2n atoms and at most 2n text characters. With probability 1/4
(for n <= 12) the instance is the pathological P_n = ((a?)^n a^n, a^n). Otherwise a random pattern of n atoms over
the symbols {a, b, .} (quantifier none/'?'/'*' with probability 1/2, 1/4, 1/4) and a text over {a, b} of length
<= 2n: half the time uniformly random, half the time sampled from the pattern itself and then possibly mutated, so
that both answers occur.

V1 oracle (check): Python's re.fullmatch, a different engine. The dialect is a subset of Python's syntax with the
same meaning ('.' never meets a newline because texts use only a and b). It is used only as an oracle.

V2 (measure: "reported"): generate_scaling(n, rng) returns the family P_n = ((a?)^n a^n, a^n) with the text made of
CountingChar objects, which count every comparison between a pattern symbol and a text character made by the
UNCHANGED matchers (the comparisons c == text[j]); reported_cost returns the count. Exact counts (proven in
entry.json; checked in experiments/2026-10-07b_regex_counts.py): backtracking (n + 2) 2^(n-1) - 1, memoised
backtracking and Thompson as stated in entry.json.
"""
import re


def _sample_from(atoms, rng):
    out = []
    for c, q in atoms:
        reps = 1 if q == "" else rng.randint(0, 1) if q == "?" else rng.choice((0, 0, 1, 2, 3))
        for _ in range(reps):
            out.append(rng.choice("ab") if c == "." else c)
    return "".join(out)


def generate(n, rng):
    if n <= 12 and rng.random() < 0.25:
        return "a?" * n + "a" * n, "a" * n
    atoms = []
    for _ in range(n):
        c = rng.choice("ab.")
        q = rng.choice(("", "", "?", "*"))
        atoms.append((c, q))
    pattern = "".join(c + q for c, q in atoms)
    if rng.random() < 0.5:
        text = "".join(rng.choice("ab") for _ in range(rng.randint(0, 2 * n)))
    else:
        text = _sample_from(atoms, rng)[:2 * n]
        if text and rng.random() < 0.3:
            i = rng.randrange(len(text))
            text = text[:i] + ("a" if text[i] == "b" else "b") + text[i + 1:]
    return pattern, text


def check(instance, output):
    pattern, text = instance
    return output == (re.fullmatch(pattern, "".join(str(x) for x in text)) is not None)


# --- Exact comparison counting for V2 -----------------------------------------------------------------

_cmps = 0


class CountingChar:
    """A text character that counts every equality test against it (module counter _cmps)."""
    __slots__ = ("ch",)

    def __init__(self, ch):
        self.ch = ch

    def __eq__(self, other):
        global _cmps
        _cmps += 1
        return self.ch == (other.ch if isinstance(other, CountingChar) else other)

    def __hash__(self):
        return hash(self.ch)

    def __str__(self):
        return self.ch

    def __repr__(self):
        return f"CountingChar({self.ch!r})"


def generate_scaling(n, rng):
    """P_n = ((a?)^n a^n, a^n), the text built from CountingChar; resets the comparison counter."""
    global _cmps
    _cmps = 0
    return "a?" * n + "a" * n, tuple(CountingChar("a") for _ in range(n))


def reported_cost(output):
    """Symbol-character comparisons made since the scaling instance was generated."""
    return _cmps

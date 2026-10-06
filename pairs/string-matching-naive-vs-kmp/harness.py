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


def generate_scaling(n, rng):
    """Worst case for the naive matcher with m = n // 2: T = a^n, P = a^(m-1) b.

    Every one of the n - m + 1 alignments matches m - 1 characters before failing on the final 'b',
    so the naive matcher does (n - m + 1) m ~ n^2 / 4 comparisons; KMP stays Theta(n + m) = Theta(n).
    """
    m = n // 2
    return ("a" * n, "a" * (m - 1) + "b")

"""Instances: strings of length n.

generate() mixes six kinds so that V1 sees long palindromes, ties and both parities: random strings over
{a, b}, over {a, b, c} and over 26 letters; n equal letters; a random string over {a, b, c} with a planted
palindrome of random length; and a periodic string (period 1..4 over {a, b}).

generate_scaling() returns n equal letters, the worst case of both quadratic and cubic algorithms (every
substring is a palindrome, so no test stops early and every expansion runs to the string's end).

The oracle shares no code with the implementations. It verifies the claimed answer (L, start) directly:
s[start:start+L] is a palindrome; no window of length L + 1 or L + 2 is a palindrome (any longer palindrome
would contain one, by trimming equal numbers of characters from both ends); and no palindrome of length L
starts before `start`. Cost O(n L) with string slicing.
"""
import string


def generate(n, rng):
    kind = rng.randrange(6)
    if kind == 0:
        return "".join(rng.choice("ab") for _ in range(n))
    if kind == 1:
        return "".join(rng.choice("abc") for _ in range(n))
    if kind == 2:
        return "".join(rng.choice(string.ascii_lowercase) for _ in range(n))
    if kind == 3:
        return "a" * n
    if kind == 4:
        chars = [rng.choice("abc") for _ in range(n)]
        if n:
            length = rng.randint(1, n)
            start = rng.randint(0, n - length)
            for k in range(length // 2):
                chars[start + length - 1 - k] = chars[start + k]
        return "".join(chars)
    period = "".join(rng.choice("ab") for _ in range(rng.randint(1, 4)))
    return (period * (n // len(period) + 1))[:n]


def generate_scaling(n, rng):
    return "a" * n


def _is_pal(w):
    return w == w[::-1]


def check(s, output):
    n = len(s)
    L, start = output
    if n == 0:
        return (L, start) == (0, 0)
    if not (1 <= L and 0 <= start and start + L <= n and _is_pal(s[start:start + L])):
        return False
    for length in (L + 1, L + 2):
        if any(_is_pal(s[i:i + length]) for i in range(n - length + 1)):
            return False
    return not any(_is_pal(s[i:i + L]) for i in range(start))

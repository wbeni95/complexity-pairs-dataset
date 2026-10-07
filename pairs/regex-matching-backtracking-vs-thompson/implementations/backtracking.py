"""Backtracking matcher: depth-first over the choices, consume first.

match(i, j) asks whether atoms[i:] fully match text[j:]. For 'c?' it first tries to consume one character, then
to skip the atom; for 'c*' it first tries to consume one character and stay on the atom, then to leave it.
Nothing is remembered between branches, so the same (i, j) can be re-explored exponentially often: on the
pattern (a?)^n a^n against a^n it makes exactly (n + 2) 2^(n-1) - 1 character comparisons.
Recursion depth is at most len(atoms) + len(text) + 1.
"""
# --- the dialect (identical in every matcher of this entry; see entry.json) ---
SYMBOLS = set("abcdefghijklmnopqrstuvwxyz.")


def parse(pattern):
    """Return the pattern as a tuple of (symbol, quantifier) pairs, quantifier in {'', '?', '*'}."""
    atoms = []
    for ch in pattern:
        if ch in "?*":
            if not atoms or atoms[-1][1]:
                raise ValueError(f"quantifier {ch!r} must follow an unquantified symbol: {pattern!r}")
            atoms[-1] = (atoms[-1][0], ch)
        elif ch in SYMBOLS:
            atoms.append((ch, ""))
        else:
            raise ValueError(f"character {ch!r} is not in the dialect: {pattern!r}")
    return tuple(atoms)


def match_backtracking(instance):
    pattern, text = instance
    atoms = parse(pattern)
    m, n = len(atoms), len(text)

    def char_ok(c, j):
        return c == "." or c == text[j]

    def match(i, j):
        if i == m:
            return j == n
        c, q = atoms[i]
        if q == "":
            return j < n and char_ok(c, j) and match(i + 1, j + 1)
        if q == "?":
            return (j < n and char_ok(c, j) and match(i + 1, j + 1)) or match(i + 1, j)
        # q == "*"
        return (j < n and char_ok(c, j) and match(i, j + 1)) or match(i + 1, j)

    return match(0, 0)

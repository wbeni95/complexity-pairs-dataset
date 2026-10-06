"""The same backtracking recursion, memoised on (atom index, text position).

There are at most (m + 1)(n + 1) distinct subproblems (m atoms, text length n) and each one does O(1) work
besides its recursive calls, so the matcher runs in O(m n). This is the memoisation step of RESEARCH_LOG RL-039:
here, unlike for the cofactor determinant, the natural key has polynomially many values.
Recursion depth is at most m + n + 1.
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


def match_memoized(instance):
    pattern, text = instance
    atoms = parse(pattern)
    m, n = len(atoms), len(text)
    memo = {}

    def char_ok(c, j):
        return c == "." or c == text[j]

    def match(i, j):
        key = (i, j)
        if key in memo:
            return memo[key]
        if i == m:
            result = j == n
        else:
            c, q = atoms[i]
            if q == "":
                result = j < n and char_ok(c, j) and match(i + 1, j + 1)
            elif q == "?":
                result = (j < n and char_ok(c, j) and match(i + 1, j + 1)) or match(i + 1, j)
            else:  # "*"
                result = (j < n and char_ok(c, j) and match(i, j + 1)) or match(i + 1, j)
        memo[key] = result
        return result

    return match(0, 0)

"""Thompson's NFA simulation (Thompson 1968): advance the SET of all reachable states in lock step.

States are atom indices 0..m (m = accepting). The epsilon-closure of state i adds i + 1 when atom i is
optional ('?' or '*'), repeatedly. For each text character, every active state i < m whose symbol matches
moves to i + 1 ('c' or 'c?') or stays at i ('c*'); then the closure is taken. Each step touches at most m + 1
states with O(1) work each, so the cost is O((m + 1)(n + 1)) for m atoms and text length n, with no backtracking.
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


def match_thompson(instance):
    pattern, text = instance
    atoms = parse(pattern)
    m = len(atoms)

    def closure(states):
        """Epsilon-closure in O(m + 1 + len(states)): mark reachable states, then list them in index order
        (no duplicates)."""
        seen = [False] * (m + 1)
        for s in states:
            while not seen[s]:
                seen[s] = True
                if s < m and atoms[s][1] in ("?", "*"):
                    s += 1
                else:
                    break
        return [s for s in range(m + 1) if seen[s]]

    current = closure([0])
    for j in range(len(text)):
        x = text[j]
        nxt = []
        for s in current:
            if s == m:
                continue
            c, q = atoms[s]
            if c == "." or c == x:
                nxt.append(s if q == "*" else s + 1)
        current = closure(nxt)
        if not current:
            return False
    return m in current

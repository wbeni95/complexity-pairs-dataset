"""Optimal LZ77-style parsing with k repeat-offset slots by enumeration of every parse.

Instance (s, k, repmin): s a tuple of integers (the string, n = len(s)), k >= 1 slots, repmin >= 1.
Output: (minimum total cost, number of token evaluations).

Model (entry.json gives it in full). A parse reads s from position 0 to position n and carries a slot tuple
R = (R[0], ..., R[k-1]), initially (1, ..., 1). At position i:
  literal                 cost 9,                      advance 1, R unchanged;
  repeat of slot j, len L cost 3 + j + gamma(L),       needs R[j] <= i, L >= repmin and s[i+t] = s[i+t-R[j]] for t < L;
                                                       R -> (R[j], R[0..j-1], R[j+1..k-1])  (slot j moves to the front);
  new match d, len L      cost 2 + gamma(L-1) + gamma(d), needs 1 <= d <= i, L >= 2 and s[i+t] = s[i+t-d] for t < L;
                                                       R -> (d, R[0..k-2])  (push front, drop the last slot).
gamma(x) = 2 floor(log2 x) + 1, the length of the Elias gamma code of x. Copies may overlap (d < L is allowed).

The enumeration is a depth-first search over all token sequences. A "token evaluation" is one extension of a partial
parse by one token, i.e. one edge of the search tree; this is the operation counted for V2. The match lengths
ml[i][d] are precomputed once (n(n-1)/2 character comparisons, not counted). Proofs (correctness, bounds, the
uncounted work, the stack bound): PROOFS.md in the entry folder, sections 4, 6.4-6.6 and 7.
"""

LITERAL_COST = 9


def gamma_len(x):
    return 2 * (x.bit_length() - 1) + 1


def match_lengths(s):
    """ml[i][d] = largest L with i + L <= n and s[i+t] == s[i+t-d] for all t < L (1 <= d <= i <= n)."""
    n = len(s)
    ml = [[0] * (i + 1) for i in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row, nxt = ml[i], ml[i + 1]
        for d in range(1, i + 1):
            if s[i] == s[i - d]:
                row[d] = 1 + nxt[d]
    return ml


def lz77_slots_enumeration(instance):
    s, k, repmin = instance
    n = len(s)
    ml = match_lengths(s)
    best = None
    evaluations = 0
    stack = [(0, (1,) * k, 0)]
    while stack:
        i, slots, cost = stack.pop()
        if i == n:
            if best is None or cost < best:
                best = cost
            continue
        row = ml[i]
        evaluations += 1                                          # literal
        stack.append((i + 1, slots, cost + LITERAL_COST))
        for j in range(k):                                        # repeats
            r = slots[j]
            if r <= i and row[r] >= repmin:
                moved = (r,) + slots[:j] + slots[j + 1:]
                for length in range(repmin, row[r] + 1):
                    evaluations += 1
                    stack.append((i + length, moved, cost + 3 + j + gamma_len(length)))
        for d in range(1, i + 1):                                 # new matches
            if row[d] >= 2:
                pushed = (d,) + slots[:-1]
                for length in range(2, row[d] + 1):
                    evaluations += 1
                    stack.append((i + length, pushed, cost + 2 + gamma_len(length - 1) + gamma_len(d)))
    return best, evaluations

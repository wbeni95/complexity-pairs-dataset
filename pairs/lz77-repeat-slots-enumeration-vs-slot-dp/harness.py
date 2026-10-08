"""Harness for optimal LZ77-style parsing with k repeat-offset slots: enumeration of all parses vs the DP over
(position, slot contents).

Instance (s, k, repmin): s a tuple of non-negative integers (the string, n = len(s)), k in {1, 2, 3}, repmin in
{1, 2, 3}. Token model and costs: see entry.json (literal 9; repeat of slot j with length L: 3 + j + gamma(L), slot j
moves to the front; new match with distance d and length L: 2 + gamma(L-1) + gamma(d), d is pushed to the front and
the last slot is dropped; initial slots (1, ..., 1); gamma(x) = 2 floor(log2 x) + 1).
Output of both implementations: (minimum total cost, operation count). `equal` compares the costs only.

generate(n, rng) draws k, repmin and one of six string families:
  0  a^n, sometimes with one other symbol at a random position (the worst case of the DP);
  1  random strings over 2, 3 or 4 letters;
  2  a random period of length 1..5 repeated, with about n/6 random substitutions;
  3  "copy" strings: random letters and copies of random earlier substrings, overlapping copies included;
  4  words over a small letter set separated by fresh symbols (each fresh symbol occurs once);
  5  the V2 family x_1 a b x_2 a b ... (x_j fresh), padded with fresh symbols to length n.

check(instance, output) is independent of both implementations: for n <= ORACLE_MAX_N it recomputes the optimum by
a backward memoised recursion V(i, R) = min over tokens of cost + V(next state), with its own match test by direct
character comparison (no table, no forward pass, no prefix grouping). It also rejects a cost above 9n (the all-literal
parse) and outputs that are not a pair of integers. Above ORACLE_MAX_N it returns None. Proof: PROOFS.md, section 8.

V2 (measure "reported"): generate_scaling(n, rng) returns the family F1(m) = x_1 a b x_2 a b ... x_m a b with
m = n // 3 (n is a multiple of 3 on the V2 grid), k = 2 and repmin = 3. Every match token in F1 has length exactly 2,
so with repmin = 3 no repeat token is ever allowed, block j >= 2 can be coded in exactly j ways (two literals, or a new
match of length 2 at distance 3t for t = 1..j-1), and block 1 only by literals. reported_cost(output) = output[1].
Exact counts (proved in PROOFS.md, sections 1-3; checked in tests/test_entry_lz77_repeat_slots.py):
  enumeration   sum_{j=1}^{m} (j-1)! (j+2) token evaluations (any k), m! complete parses;
  slot DP       sum_{j=1}^{m} 3 S(j) + sum_{j=2}^{m} (j-1) G(j) relaxations, with S, G below;
                for k = 2 this is (4m^3 - 15m^2 + 29m - 9)/3.
"""
import math

LITERAL_COST = 9
ORACLE_MAX_N = 24


# --------------------------------------------------------------------------
# Instances for V1
# --------------------------------------------------------------------------

def f1_string(m, pad=0):
    """x_1 a b x_2 a b ... x_m a b with a = 0, b = 1 and fresh x_j = j + 1, then `pad` further fresh symbols."""
    s = []
    for j in range(1, m + 1):
        s += [j + 1, 0, 1]
    s += [m + 2 + t for t in range(pad)]
    return tuple(s)


def _copy_string(n, rng):
    letters = rng.choice((2, 3))
    s = []
    while len(s) < n:
        if len(s) < 2 or rng.random() < 0.3:
            s.append(rng.randrange(letters))
        else:
            d = rng.randint(1, len(s))
            for _ in range(rng.randint(2, 6)):          # overlapping copy when the length exceeds d
                if len(s) == n:
                    break
                s.append(s[-d])
    return s


def _word_string(n, rng):
    words = [tuple(rng.randrange(3) for _ in range(rng.randint(1, 3))) for _ in range(rng.randint(1, 3))]
    s, fresh = [], 10
    while len(s) < n:
        s.append(fresh)
        fresh += 1
        s.extend(rng.choice(words))
    return s[:n]


def generate(n, rng):
    k = rng.choice((1, 2, 3))
    repmin = rng.choice((1, 2, 2, 3))
    kind = rng.randrange(6)
    if kind == 0:
        s = [0] * n
        if n and rng.random() < 0.4:
            s[rng.randrange(n)] = 1
    elif kind == 1:
        letters = rng.choice((2, 3, 4))
        s = [rng.randrange(letters) for _ in range(n)]
    elif kind == 2:
        base = [rng.randrange(3) for _ in range(rng.randint(1, 5))]
        s = [base[i % len(base)] for i in range(n)]
        for _ in range(n // 6):
            s[rng.randrange(n)] = rng.randrange(4)
    elif kind == 3:
        s = _copy_string(n, rng)
    elif kind == 4:
        s = _word_string(n, rng)
    else:
        s = list(f1_string(n // 3, n % 3))
    return (tuple(s), k, repmin)


# --------------------------------------------------------------------------
# Independent oracle
# --------------------------------------------------------------------------

def _gamma(x):
    return 2 * (x.bit_length() - 1) + 1


def oracle_optimum(instance):
    """Backward memoised recursion over (position, slots); match lengths by direct comparison."""
    s, k, repmin = instance
    n = len(s)

    def extent(i, d):
        length = 0
        while i + length < n and s[i + length] == s[i + length - d]:
            length += 1
        return length

    memo = {}

    def value(i, slots):
        if i == n:
            return 0
        key = (i, slots)
        if key in memo:
            return memo[key]
        best = LITERAL_COST + value(i + 1, slots)
        for j, r in enumerate(slots):
            if r <= i:
                moved = (r,) + slots[:j] + slots[j + 1:]
                for length in range(repmin, extent(i, r) + 1):
                    best = min(best, 3 + j + _gamma(length) + value(i + length, moved))
        for d in range(1, i + 1):
            pushed = (d,) + slots[:-1]
            for length in range(2, extent(i, d) + 1):
                best = min(best, 2 + _gamma(length - 1) + _gamma(d) + value(i + length, pushed))
        memo[key] = best
        return best

    return value(0, (1,) * k)


def check(instance, output):
    if not (isinstance(output, tuple) and len(output) == 2):
        return False
    cost, count = output
    if type(cost) is not int or type(count) is not int or count < 0:
        return False
    s, k, repmin = instance
    n = len(s)
    if cost < 0 or cost > LITERAL_COST * n:
        return False
    if n <= ORACLE_MAX_N:
        return cost == oracle_optimum(instance)
    return None


def equal(a, b):
    return a[0] == b[0]


# --------------------------------------------------------------------------
# V2: exact operation counts on the family F1
# --------------------------------------------------------------------------

def generate_scaling(n, rng):
    """F1(n // 3) padded to length n, with k = 2 and repmin = 3 (rng is not used)."""
    return (f1_string(n // 3, n % 3), 2, 3)


def reported_cost(output):
    return output[1]


def enumeration_count_f1(m):
    """Token evaluations of the enumeration on F1(m) with repmin = 3 (any k)."""
    return sum(math.factorial(j - 1) * (j + 2) for j in range(1, m + 1))


def _falling_sum(top, cmax):
    """sum_{c=0}^{cmax} top (top-1) ... (top-c+1)."""
    return sum(math.perm(top, c) for c in range(0, cmax + 1))


def dp_states_f1(j, k):
    """S(j): number of slot tuples at each of the three positions of block j of F1 (repmin = 3)."""
    return 1 if j <= 2 else _falling_sum(j - 2, min(k, j - 2))


def dp_groups_f1(j, k):
    """G(j): number of distinct (k-1)-prefixes among those tuples."""
    return 1 if j <= 2 else _falling_sum(j - 2, min(k - 1, j - 2))


def dp_count_f1(m, k):
    """Relaxations of the slot DP on F1(m) with repmin = 3."""
    return sum(3 * dp_states_f1(j, k) for j in range(1, m + 1)) + sum((j - 1) * dp_groups_f1(j, k)
                                                                    for j in range(2, m + 1))

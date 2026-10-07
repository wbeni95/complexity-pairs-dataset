"""Harness for 3XOR: all triples vs a Patricia trie.

Instances: (w, values) with an integer w >= 1 and a tuple of n integers in [0, 2^w). Output: a triple of indices
(i, j, k) with i < j < k and values[i] ^ values[j] ^ values[k] == 0, or None if no such triple exists. Different
correct algorithms may return different triples, so equal(a, b) compares only whether a triple was found, and
check(instance, output) verifies any returned triple.

generate(n, rng): n <= 2 gives random values (some 0) and always the answer None. For n >= 3 one of five kinds:
  0  small words: w = floor(log2 n) + 1..3, uniform values (mostly yes);
  1  random 64-bit values (almost surely no); half of the time a planted triple values[k] = values[i] ^ values[j];
  2  values of odd Hamming weight, w in 1..64 (always no: the XOR of three odd-weight words has odd weight, so it
     is not 0; duplicates do not change this);
  3  duplicates and zeros on a pool of odd-weight values: either distinct pool values or draws with repetition,
     then 0..3 positions set to 0. Answer: yes iff 0 occurs >= 3 times (0, 0, 0), or 0 occurs and some value
     occurs twice (x, x, 0); otherwise no;
  4  tiny words, w in 1..4 (many repeats and zeros; all three kinds of solution occur).

check(instance, output) is independent of both implementations. A triple must be a tuple of three ints (bool,
float and other types are rejected) with 0 <= i < j < k < n and XOR 0. None is judged by a hash-based Theta(n^2)
pair scan: for every pair i < j it looks up t = values[i] ^ values[j] in a Counter of the values and requires a
third index, discounting i and j when they hold the value t (index multiplicity, as in the 3SUM harness).

V2 (measure "reported"): generate_scaling(n, rng) takes n = 2^(w-1) and returns all w-bit integers of odd Hamming
weight (2^(w-1) of them, so w = log2(n) + 1), in an order shuffled by rng, as CountingInt objects, and resets the
counter. It is a no-instance, so both algorithms run to the end. For every a in the set, {a ^ x} is the set of
even-weight words, and every pair 2t, 2t + 1 holds one even-weight and one odd-weight word, so the merge of the
Patricia-trie algorithm interleaves maximally (2n - 1 steps). CountingInt counts every operation on a value:
^, &, |, >>, <<, ==, !=, <, <=, >, >= and truth tests; bitwise results are CountingInt again, and it has no hash.
Exact counts (derived in entry.json, checked in experiments/2026-10-06i_three_xor.py):
  all triples      (n^3 - n) / 6                    = C(n, 2) XORs + C(n, 3) equality tests
  Patricia trie    7 n^2 + 2 n log2(n) - 3 n
The counts depend on n only, not on the shuffle. No counted operation runs inside a CPython built-in.
"""
from collections import Counter

# --------------------------------------------------------------------------
# Instances for V1
# --------------------------------------------------------------------------


def _odd_weight(x):
    """x with its lowest bit flipped if x has even Hamming weight (a bijection even <-> odd weight)."""
    return x if bin(x).count("1") % 2 else x ^ 1


def _odd_pool(size, w, rng):
    """`size` distinct odd-weight w-bit values (needs 2^(w-1) >= size)."""
    seen, pool = set(), []
    while len(pool) < size:
        v = _odd_weight(rng.randrange(1 << w))
        if v not in seen:
            seen.add(v)
            pool.append(v)
    return pool


def generate(n, rng):
    if n <= 2:
        w = rng.randint(1, 8)
        return (w, tuple(0 if rng.random() < 0.3 else rng.randrange(1 << w) for _ in range(n)))
    kind = rng.randrange(5)
    if kind == 0:
        w = n.bit_length() + rng.randint(0, 2)
        values = [rng.randrange(1 << w) for _ in range(n)]
    elif kind == 1:
        w = 64
        values = [rng.getrandbits(64) for _ in range(n)]
        if rng.random() < 0.5:
            i, j, k = rng.sample(range(n), 3)
            values[k] = values[i] ^ values[j]
    elif kind == 2:
        w = rng.randint(1, 64)
        values = [_odd_weight(rng.randrange(1 << w)) for _ in range(n)]
    elif kind == 3:
        w = rng.randint(n.bit_length() + 2, 64)
        if rng.random() < 0.5:
            values = _odd_pool(n, w, rng)
        else:
            pool = _odd_pool(max(1, n // 2), w, rng)
            values = [rng.choice(pool) for _ in range(n)]
        for pos in rng.sample(range(n), min(n, rng.choice((0, 1, 1, 2, 2, 3)))):
            values[pos] = 0
    else:
        w = rng.randint(1, 4)
        values = [rng.randrange(1 << w) for _ in range(n)]
    return (w, tuple(values))


# --------------------------------------------------------------------------
# Output comparison and independent oracle
# --------------------------------------------------------------------------


def equal(a, b):
    """Correct algorithms may return different triples: compare only whether one was found."""
    return (a is None) == (b is None)


def has_solution(values):
    """Hash-based Theta(n^2) decision: is there a set of three distinct indices whose values XOR to 0?"""
    count = Counter(values)
    n = len(values)
    for i in range(n):
        for j in range(i + 1, n):
            t = values[i] ^ values[j]
            need = 1 + (t == values[i]) + (t == values[j])
            if count[t] >= need:
                return True
    return False


def check(instance, output):
    w, values = instance
    n = len(values)
    if output is None:
        return not has_solution(values)
    if type(output) is not tuple or len(output) != 3:
        return False
    if any(type(x) is not int for x in output):        # rejects bool, float, str, ...
        return False
    i, j, k = output
    if not (0 <= i < j < k < n):
        return False
    return (values[i] ^ values[j] ^ values[k]) == 0


# --------------------------------------------------------------------------
# Exact operation counting for V2 (measure: "reported")
# --------------------------------------------------------------------------

_ops = {"xor": 0, "and_or": 0, "shift": 0, "compare": 0, "truth": 0}


class CountingInt:
    """A non-negative integer that counts every bitwise operation, shift, comparison and truth test on it."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def _op(self, kind, value):
        _ops[kind] += 1
        return CountingInt(value)

    def __xor__(self, o):
        return self._op("xor", self.v ^ self._val(o))

    def __rxor__(self, o):
        return self._op("xor", self._val(o) ^ self.v)

    def __and__(self, o):
        return self._op("and_or", self.v & self._val(o))

    def __rand__(self, o):
        return self._op("and_or", self._val(o) & self.v)

    def __or__(self, o):
        return self._op("and_or", self.v | self._val(o))

    def __ror__(self, o):
        return self._op("and_or", self._val(o) | self.v)

    def __rshift__(self, o):
        return self._op("shift", self.v >> self._val(o))

    def __lshift__(self, o):
        return self._op("shift", self.v << self._val(o))

    def _cmp(self, result):
        _ops["compare"] += 1
        return result

    def __eq__(self, o):
        return self._cmp(self.v == self._val(o))

    def __ne__(self, o):
        return self._cmp(self.v != self._val(o))

    def __lt__(self, o):
        return self._cmp(self.v < self._val(o))

    def __le__(self, o):
        return self._cmp(self.v <= self._val(o))

    def __gt__(self, o):
        return self._cmp(self.v > self._val(o))

    def __ge__(self, o):
        return self._cmp(self.v >= self._val(o))

    __hash__ = None

    def __bool__(self):
        _ops["truth"] += 1
        return self.v != 0

    def __repr__(self):
        return f"CountingInt({self.v})"


def reset_counter():
    for key in _ops:
        _ops[key] = 0


def counts():
    """A copy of the per-kind counters (for experiments)."""
    return dict(_ops)


def odd_weight_words(w):
    """All w-bit integers of odd Hamming weight, ascending (2^(w-1) of them)."""
    return [x for x in range(1 << w) if bin(x).count("1") % 2]


def generate_scaling(n, rng):
    """n = 2^(w-1): all odd-weight w-bit words, shuffled by rng, as CountingInt; resets the counter."""
    if n < 1 or n & (n - 1):
        raise ValueError("the V2 family is defined for n a power of two")
    w = n.bit_length()
    words = odd_weight_words(w)
    rng.shuffle(words)
    inst = (w, tuple(CountingInt(x) for x in words))
    reset_counter()
    return inst


def reported_cost(output):
    """Counted operations on input-derived values since the scaling instance was generated."""
    return sum(_ops.values())

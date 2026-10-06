"""Instances: (n, table) for a Boolean function on N = 2^n points that is promised to be constant or balanced.

Outputs are (answer, queries) with answer in {"constant", "balanced"}; V1 compares answers, V2 fits queries.

generate(n, rng): a random constant function (probability 1/2) or a uniformly random balanced function.
On such instances the deterministic algorithm usually stops after very few queries: a random balanced
function shows two different values early. The claimed cost 2^(n-1) + 1 is a WORST-CASE cost, so V2 uses:

generate_scaling(n, rng): the worst-case instances FOR THE DETERMINISTIC QUERY ORDER 0, 1, 2, ... used in
implementations/classical.py. For that fixed order the algorithm makes exactly 2^(n-1) + 1 queries on
precisely four functions and fewer on every other promise input:
  - the two constant functions (it must see more than half of the table before it may answer "constant");
  - the two balanced functions that are constant on the first half of the order, f(x) = c XOR (top bit of x)
    (the first 2^(n-1) answers agree, and only query number 2^(n-1) + 1 reveals the other value).
experiments/2026-10-07_deutsch_jozsa_checks.py verifies this by exhaustion over all promise inputs for
n = 1..4. A different query order has a different set of worst-case inputs, but by the adversary argument
(see entry.json) every deterministic exact algorithm has some input forcing 2^(n-1) + 1 queries.
"""


def generate(n, rng):
    if n < 1:
        raise ValueError("Deutsch-Jozsa needs n >= 1 (for N = 1 no balanced function exists)")
    N = 1 << n
    if rng.random() < 0.5:
        c = rng.randrange(2)
        return n, tuple([c] * N)
    values = [0] * (N // 2) + [1] * (N // 2)
    rng.shuffle(values)
    return n, tuple(values)


def generate_scaling(n, rng):
    N = 1 << n
    c = rng.randrange(2)
    if rng.random() < 0.5:
        return n, tuple([c] * N)
    return n, tuple(c ^ (x >> (n - 1)) for x in range(N))


def equal(a, b):
    return a[0] == b[0]


def check(instance, output):
    """Independent check against the whole truth table: count the ones."""
    n, table = instance
    ones = sum(table)
    truth = "constant" if ones in (0, len(table)) else "balanced" if 2 * ones == len(table) else None
    if truth is None:
        return None  # not a promise instance; cannot judge
    return output[0] == truth


def reported_cost(output):
    return output[1]

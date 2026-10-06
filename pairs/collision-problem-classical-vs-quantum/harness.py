"""Instances: (n, table) for a uniformly random 2-to-1 function on N = 2^n points.

The domain is split into N/2 pairs by a uniformly random perfect matching, and each pair gets a distinct label
drawn from the codomain {0, ..., 2N - 1}. The codomain has size 2N >= 3N/2, the condition under which the
Aaronson-Shi (2004) proof of the quantum lower bound applies directly (Kutin 2005 and Ambainis 2005 remove the
condition). There is no XOR structure: unlike Simon's problem, the pairs are not cosets {x, x XOR s}.

Outputs are (answer, queries) with answer = (a, b), a < b, f(a) = f(b).
"""


def generate(n, rng):
    if n < 1:
        raise ValueError("the collision problem needs N = 2^n >= 2")
    N = 1 << n
    points = list(range(N))
    rng.shuffle(points)
    labels = rng.sample(range(2 * N), N // 2)
    table = [0] * N
    for i, label in enumerate(labels):
        table[points[2 * i]] = label
        table[points[2 * i + 1]] = label
    return n, tuple(table)


def equal(a, b):
    """The collision problem is a RELATION, not a function: a 2-to-1 function on N points has N/2 collisions,
    and different algorithms legitimately return different ones. Agreement between implementations is
    therefore NOT required; every output is instead verified by check() against the instance."""
    return True


def check(instance, output):
    """Independent check: the two indices are distinct, in range, and have the same value."""
    n, table = instance
    a, b = output[0]
    return 0 <= a < b < len(table) and table[a] == table[b]


def reported_cost(output):
    return output[1]

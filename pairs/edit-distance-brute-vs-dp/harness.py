"""Instances: two random strings of length n over {A, C, G, T}."""


def generate(n, rng):
    return ("".join(rng.choice("ACGT") for _ in range(n)),
            "".join(rng.choice("ACGT") for _ in range(n)))


def check(instance, output):
    a, b = instance
    # Cheap necessary conditions, independent of both algorithms.
    if a == b:
        return output == 0
    return abs(len(a) - len(b)) <= output <= max(len(a), len(b))

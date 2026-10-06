"""Instances: two random strings of length n over {A, C, G, T}."""


def generate(n, rng):
    return ("".join(rng.choice("ACGT") for _ in range(n)),
            "".join(rng.choice("ACGT") for _ in range(n)))


def check(instance, output):
    a, b = instance
    if a == b:
        return output == len(a)
    return 0 <= output <= min(len(a), len(b))

"""Primality harness. Instances are n-bit integers (n = bit length).

The oracle is a sieve of Eratosthenes, independent of every implementation under test.
"""

SIEVE_BITS = 20
_sieve = None
_primes_by_bits = None


def _build():
    global _sieve, _primes_by_bits
    limit = 1 << SIEVE_BITS
    s = bytearray([1]) * limit
    s[0] = s[1] = 0
    for p in range(2, int(limit ** 0.5) + 1):
        if s[p]:
            s[p * p::p] = bytes(len(range(p * p, limit, p)))
    _sieve = s
    _primes_by_bits = {}
    for x in range(2, limit):
        if s[x]:
            _primes_by_bits.setdefault(x.bit_length(), []).append(x)


def generate(n, rng):
    """An n-bit integer; half the time a prime, so both answers get exercised."""
    if n > SIEVE_BITS:
        raise ValueError(f"V1 sizes must be <= {SIEVE_BITS} bits (oracle range)")
    if _sieve is None:
        _build()
    if n <= 1:
        return n
    if rng.random() < 0.5:
        return rng.choice(_primes_by_bits[n])
    return rng.getrandbits(n - 1) | (1 << (n - 1))


def check(instance, output):
    if _sieve is None:
        _build()
    return output == bool(_sieve[instance])


def generate_scaling(n, rng):
    """A random n-bit PRIME: the worst case for trial division."""
    while True:
        x = rng.getrandbits(n - 1) | (1 << (n - 1)) | 1
        if _is_prime_det(x):
            return x


def _is_prime_det(x):
    """Deterministic Miller-Rabin; the first 12 prime bases are exact below 3.3e24 (~81 bits)."""
    if x >= 3_317_044_064_679_887_385_961_981:
        raise ValueError("generate_scaling supports n <= 81 bits")
    bases = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    if x < 2:
        return False
    for p in bases:
        if x % p == 0:
            return x == p
    d, s = x - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in bases:
        y = pow(a, d, x)
        if y in (1, x - 1):
            continue
        for _ in range(s - 1):
            y = y * y % x
            if y == x - 1:
                break
        else:
            return False
    return True

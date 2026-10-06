"""Miller-Rabin probabilistic primality test (Miller 1976, Rabin 1980).

Primes are always accepted. A composite survives one round with probability
<= 1/4, so `rounds` independent random bases give error <= 4^(-rounds).
"""
import random


def is_prime_miller_rabin(N: int, rounds: int = 32) -> bool:
    if N < 4:
        return N in (2, 3)
    if N % 2 == 0:
        return False
    d, s = N - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        a = random.randrange(2, N - 1)
        y = pow(a, d, N)
        if y in (1, N - 1):
            continue
        for _ in range(s - 1):
            y = y * y % N
            if y == N - 1:
                break
        else:
            return False  # a is a witness: N is certainly composite
    return True

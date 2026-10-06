"""Trial division: test odd divisors up to sqrt(N). Theta(sqrt(N)) = Theta(2^(n/2)) for n-bit primes."""


def is_prime_trial(N: int) -> bool:
    if N < 2:
        return False
    if N % 2 == 0:
        return N == 2
    d = 3
    while d * d <= N:
        if N % d == 0:
            return False
        d += 2
    return True

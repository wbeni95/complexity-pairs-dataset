"""AKS primality test, following the six steps of Agrawal, Kayal, Saxena,
"PRIMES is in P", Annals of Mathematics 160 (2004).

Deterministic and unconditional; polynomial in the bit length of N (proofs in ../PROOFS.md).
Written for clarity, not speed. Polynomials mod (X^r - 1, N) are lists of r
coefficients; squaring uses Kronecker substitution (pack into one big integer,
multiply once, unpack), which keeps pure Python tolerable.

In the bounds log2(N)^2 (step 2) and sqrt(phi(r)) log2(N) (step 5) the code uses an exact rational
lam = A / 2^64 with log2(N) <= lam <= bit length of N (_log2_upper, integer arithmetic only) in place of
log2(N), and computes floor(lam^2) and floor(sqrt(phi(r)) lam) exactly. These can exceed the values with
log2(N) (for example at N = 229533671885360152), which the correctness proof, written for any such lam,
allows; a floating-point log2 could make them smaller than the values with log2(N), which it does not.
"""
import math


def is_prime_aks(N: int) -> bool:
    if N < 2:
        return False
    # Step 1: if N = a^b with a > 1, b > 1, N is composite.
    if _is_perfect_power(N):
        return False
    # Step 2: smallest r with ord_r(N) > lam^2, where lam = A / 2^J >= log2(N).
    A, J = _log2_upper(N)
    max_k = (A * A) >> (2 * J)  # floor(lam^2)
    r = 2
    while not (math.gcd(r, N) == 1 and _order_exceeds(N, r, max_k)):
        r += 1
    # Step 3: a nontrivial gcd with some a <= r reveals a factor.
    for a in range(2, min(r, N - 1) + 1):
        if 1 < math.gcd(a, N) < N:
            return False
    # Step 4.
    if N <= r:
        return True
    # Step 5: check (X + a)^N == X^N + a  mod (X^r - 1, N).
    limit = math.isqrt(_totient(r) * A * A) >> J  # floor(sqrt(phi(r)) * lam)
    for a in range(1, limit + 1):
        lhs = _pow_x_plus_a(a, N, r)
        rhs = [0] * r
        rhs[N % r] = 1
        rhs[0] = (rhs[0] + a) % N
        if lhs != rhs:
            return False
    # Step 6.
    return True


def _log2_upper(N: int, J: int = 64) -> tuple[int, int]:
    """(A, J) with log2(N) <= A / 2^J <= bit length of N, for N >= 1, in exact integer arithmetic.

    N = 2^e * y with 1 <= y < 2. Each of the J steps squares y and halves it when the square is >= 2,
    which yields the next binary digit of log2(y); every value is rounded UP to P fraction bits, so the
    digits never undershoot and A / 2^J stays an upper bound.
    """
    e = N.bit_length() - 1
    P = J + 64                    # fraction bits of the fixed-point value Y / 2^P
    Y = -((-N << P) >> e)         # ceil(y * 2^P)
    bits = 0
    for _ in range(J):
        Y = -((-Y * Y) >> P)      # ceil(Y^2 / 2^P)
        bits <<= 1
        if Y >= 2 << P:           # square >= 2: digit 1, then halve (rounding up)
            bits |= 1
            Y = -((-Y) >> 1)
    return (e << J) + bits + 1, J


def _iroot(N: int, b: int) -> int:
    """floor(N ** (1/b)), exactly."""
    lo, hi = 1, 1 << (N.bit_length() // b + 1)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid ** b <= N:
            lo = mid
        else:
            hi = mid - 1
    return lo


def _is_perfect_power(N: int) -> bool:
    for b in range(2, N.bit_length() + 1):
        a = _iroot(N, b)
        if a > 1 and a ** b == N:
            return True
    return False


def _order_exceeds(N: int, r: int, max_k: int) -> bool:
    """True iff N^k mod r != 1 for all 1 <= k <= max_k, i.e. ord_r(N) > max_k."""
    x = 1
    for _ in range(max_k):
        x = x * N % r
        if x == 1:
            return False
    return True


def _totient(r: int) -> int:
    result, m, p = r, r, 2
    while p * p <= m:
        if m % p == 0:
            while m % p == 0:
                m //= p
            result -= result // p
        p += 1
    if m > 1:
        result -= result // m
    return result


def _square_mod(P: list[int], r: int, N: int) -> list[int]:
    """P(X)^2 mod (X^r - 1, N) via Kronecker substitution."""
    wb = ((r * (N - 1) ** 2).bit_length() + 7) // 8 or 1  # bytes per coefficient slot
    packed = int.from_bytes(b"".join(c.to_bytes(wb, "little") for c in P), "little")
    prod = (packed * packed).to_bytes(2 * r * wb, "little")
    c = [int.from_bytes(prod[i * wb:(i + 1) * wb], "little") for i in range(2 * r)]
    return [(c[i] + c[i + r]) % N for i in range(r)]


def _pow_x_plus_a(a: int, N: int, r: int) -> list[int]:
    """(X + a)^N mod (X^r - 1, N), left-to-right square-and-multiply."""
    P = [0] * r
    P[0] = 1
    for bit in bin(N)[2:]:
        P = _square_mod(P, r, N)
        if bit == "1":
            # multiply by (X + a): coefficient i gets a*P[i] + P[i-1]; X^r wraps to 1
            P = [(a * P[i] + P[i - 1]) % N for i in range(r)]
    return P

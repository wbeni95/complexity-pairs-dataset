"""Checks for the proofs of the two primality entries that are too slow for the unit tests
(pairs/primality-trial-vs-aks/PROOFS.md, pairs/primality-miller-rabin-vs-aks/PROOFS.md).

Part 1. The AKS implementation computes its bounds with an exact rational lam >= log2(N) (Lemma A1). Its K equals
        floor(log2(N)^2) for every N in [2, 2^20), and its r and l equal the values computed with the exact
        log2(N) for every N in [2, 2^16). The exact values come from 80-digit decimal arithmetic with a certified
        margin (Python's decimal ln is correctly rounded). Also: N > r for every N in [512, 2^16) (H.4), with the
        largest r per bit length; and K = floor(log2(N)^2) + 1 at N = 229533671885360152 (lam may exceed log2 N).
Part 2. Miller-Rabin: for every odd composite N < 2^14 other than 9, the number of non-witnesses is at most
        phi(N)/4, and a base drawn from {2, ..., N - 2} is a non-witness with probability < 1/4.
Part 3. AKS agrees with a sieve on every N < 2^12, and rejects at least 30 semiprimes whose prime factors both
        exceed r (so that only step 5 can reject them).

Each check prints a line starting with [PASS] or [FAIL]; the exit code is 1 if any check fails.
Run from the repository root:  python experiments/2026-10-07_primality_proof_checks.py
"""
import importlib.util
import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


aks = load("pairs/primality-trial-vs-aks/implementations/aks.py", "checks_aks")
FAILED = []


def report(ok, text):
    print(("[PASS] " if ok else "[FAIL] ") + text, flush=True)
    if not ok:
        FAILED.append(text)


def sieve(limit):
    s = bytearray([1]) * limit
    s[0] = s[1] = 0
    for p in range(2, math.isqrt(limit - 1) + 1):
        if s[p]:
            s[p * p::p] = bytes(len(range(p * p, limit, p)))
    return s


getcontext().prec = 80
LN2 = Decimal(2).ln()
MARGIN = Decimal(10) ** -60


def certified_floor(x):
    f = int(x)
    if x - f < MARGIN or (f + 1) - x < MARGIN:
        raise ArithmeticError(f"value too close to an integer: {x}")
    return f


def exact_log2_parts(N):
    """(floor(log2(N)^2), log2(N) as a Decimal or None for powers of two, exact integer log2 for powers of two)."""
    if N & (N - 1) == 0:
        m = N.bit_length() - 1
        return m * m, None, m
    L = Decimal(N).ln() / LN2
    return certified_floor(L * L), L, None


def find_r(N, K):
    r = K + 2          # r <= K + 1 cannot work: ord_r(N) <= phi(r) <= r - 1
    while not (math.gcd(r, N) == 1 and aks._order_exceeds(N, r, K)):
        r += 1
    return r


def part1():
    bad_k = 0
    for N in range(2, 1 << 20):
        A, J = aks._log2_upper(N)
        if (A * A) >> (2 * J) != exact_log2_parts(N)[0]:
            bad_k += 1
    report(bad_k == 0, f"part 1: code's K == floor(log2(N)^2) for every N in [2, 2^20) ({bad_k} mismatches)")
    bad_r = bad_l = 0
    r_max = 0
    r_max_bits, not_above = {}, []
    for N in range(2, 1 << 16):
        A, J = aks._log2_upper(N)
        K = (A * A) >> (2 * J)
        r = find_r(N, K)
        r_max = max(r_max, r)
        r_max_bits[N.bit_length()] = max(r_max_bits.get(N.bit_length(), 0), r)
        if N >= 512 and N <= r:
            not_above.append(N)
        k_exact, L, m = exact_log2_parts(N)
        if find_r(N, k_exact) != r:
            bad_r += 1
        if N > r:
            phi = aks._totient(r)
            ell = math.isqrt(phi * A * A) >> J
            ell_exact = math.isqrt(phi * m * m) if L is None else certified_floor(Decimal(phi).sqrt() * L)
            bad_l += ell != ell_exact
    report(bad_r == 0 and bad_l == 0,
           f"part 1: code's r and l equal the exact-log2 values for every N in [2, 2^16) "
           f"({bad_r} r mismatches, {bad_l} l mismatches); largest r = {r_max}")
    per_bits = ", ".join(f"{b}: {r_max_bits[b]}" for b in range(10, 17))
    report(not not_above and all(r_max_bits[b] < 1 << (b - 1) for b in range(10, 17)),
           f"part 1: N > r for every N in [512, 2^16) ({len(not_above)} exceptions); largest r per bit length "
           f"{per_bits}")
    N = 229533671885360152
    A, J = aks._log2_upper(N)
    report((A * A) >> (2 * J) == exact_log2_parts(N)[0] + 1,
           f"part 1: lam may exceed log2 N: at N = {N}, K = {(A * A) >> (2 * J)} = floor(log2(N)^2) + 1")


def non_witness_count(N):
    d, s = N - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    count = 0
    for a in range(1, N):
        y = pow(a, d, N)
        if y == 1 or y == N - 1:
            count += 1
            continue
        for _ in range(s - 1):
            y = y * y % N
            if y == N - 1:
                count += 1
                break
    return count


def part2():
    limit = 1 << 14
    prime = sieve(limit)
    phi = list(range(limit))
    for p in range(2, limit):
        if prime[p]:
            for k in range(p, limit, p):
                phi[k] -= phi[k] // p
    bad, tested = [], 0
    for N in range(9, limit, 2):
        if prime[N]:
            continue
        S = non_witness_count(N)
        tested += 1
        ok_phi = N == 9 and S == 2 or N != 9 and 4 * S <= phi[N]
        if not (ok_phi and 4 * (S - 2) < N - 3):
            bad.append(N)
    report(not bad, f"part 2: Miller-Rabin bound on {tested} odd composites N < 2^14 ({len(bad)} failures {bad[:5]})")


def part3():
    prime = sieve(1 << 12)
    wrong = [N for N in range(1 << 12) if aks.is_prime_aks(N) != bool(prime[N])]
    report(not wrong, f"part 3: AKS equals the sieve for every N < 2^12 ({len(wrong)} disagreements {wrong[:5]})")
    small = sieve(2000)
    ps = [p for p in range(300, 2000) if small[p]]
    tested, wrong = 0, []
    for i, p in enumerate(ps):
        for q in ps[i:i + 3]:
            N = p * q
            A, J = aks._log2_upper(N)
            r = find_r(N, (A * A) >> (2 * J))
            if min(p, q) > r:
                tested += 1
                if aks.is_prime_aks(N) is not False:
                    wrong.append(N)
        if tested >= 30:
            break
    report(tested >= 30 and not wrong,
           f"part 3: {tested} semiprimes with both factors above r reported composite ({len(wrong)} wrong)")


if __name__ == "__main__":
    part1()
    part2()
    part3()
    print(f"{'ALL PASS' if not FAILED else str(len(FAILED)) + ' FAILED'}")
    sys.exit(1 if FAILED else 0)

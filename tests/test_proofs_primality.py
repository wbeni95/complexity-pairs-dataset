"""Deterministic checks of pairs/primality-trial-vs-aks/PROOFS.md (trial division, AKS, harness, Bertrand) and
pairs/primality-miller-rabin-vs-aks/PROOFS.md (Miller-Rabin)."""
import importlib.util
import math
import random
import sys
import unittest
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRIAL_DIR = ROOT / "pairs" / "primality-trial-vs-aks"
MR_DIR = ROOT / "pairs" / "primality-miller-rabin-vs-aks"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


aks = load(TRIAL_DIR / "implementations" / "aks.py", "proofs_prim_aks")
trial = load(TRIAL_DIR / "implementations" / "trial_division.py", "proofs_prim_trial")
harness = load(TRIAL_DIR / "harness.py", "proofs_prim_harness")
mr = load(MR_DIR / "implementations" / "miller_rabin.py", "proofs_prim_mr")


def simple_sieve(limit):
    """Primality table for [0, limit), written independently of harness.py."""
    s = [True] * limit
    s[0] = s[1] = False
    i = 2
    while i * i < limit:
        if s[i]:
            for j in range(i * i, limit, i):
                s[j] = False
        i += 1
    return s


PRIME = simple_sieve(1 << 16)


def trial_prime(x):
    if x < 2:
        return False
    if x % 2 == 0:
        return x == 2
    return all(x % d for d in range(3, math.isqrt(x) + 1, 2))


def aks_params(N):
    """K, r and l as computed by steps 2 and 5 of is_prime_aks (r <= K + 1 is skipped: there
    ord_r(N) <= phi(r) <= r - 1 <= K, so the code rejects those r)."""
    A, J = aks._log2_upper(N)
    K = (A * A) >> (2 * J)
    r = K + 2
    while not (math.gcd(r, N) == 1 and aks._order_exceeds(N, r, K)):
        r += 1
    ell = math.isqrt(aks._totient(r) * A * A) >> J
    return A, J, K, r, ell


def order(N, r):
    x, k = N % r, 1
    while x != 1:
        x, k = x * N % r, k + 1
    return k


def capture_locals(fn, code, *args):
    """Run fn(*args); return its result and the locals of the last frame of `code` at its return."""
    seen = {}

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is code:
            seen.clear()
            seen.update(frame.f_locals)

    sys.setprofile(prof)
    try:
        out = fn(*args)
    finally:
        sys.setprofile(None)
    return out, seen


R = lambda n: max(16, n * (n * n + 1) ** 2)   # noqa: E731  (the bound of Lemma A3)

STEP5_SEMIPRIMES = [95477, 96091, 97343, 98587, 99221, 103603, 106829, 111547]


class CountingN(int):
    calls = 0

    def __mod__(self, other):
        CountingN.calls += 1
        return int.__mod__(self, other)


class TrialDivisionTests(unittest.TestCase):
    def test_correct_below_2_16(self):
        self.assertEqual([x for x in range(1 << 16) if trial.is_prime_trial(x)],
                         [x for x in range(1 << 16) if PRIME[x]])

    def test_division_counts(self):
        for N in range(2, 1 << 14):
            CountingN.calls = 0
            trial.is_prime_trial(CountingN(N))
            D = 1 + (math.isqrt(N) - 1) // 2
            if N % 2 and PRIME[N]:
                self.assertEqual(CountingN.calls, D, N)
            else:
                self.assertLessEqual(CountingN.calls, D, N)
        for N in range(3, 1 << 16, 2):
            if PRIME[N]:
                n = N.bit_length()
                D = 1 + (math.isqrt(N) - 1) // 2
                self.assertLess(D, 1 + 2 ** (n / 2 - 1))
                self.assertGreaterEqual(D, math.isqrt(N) / 2)
                self.assertGreaterEqual(math.isqrt(N) / 2, (2 ** ((n - 1) / 2) - 1) / 2)

    def test_v2_instances(self):
        for n in range(26, 41, 2):
            N = harness.generate_scaling(n, random.Random(f"primality-trial-vs-aks|v2|{n}"))
            self.assertEqual(N.bit_length(), n)
            self.assertTrue(trial_prime(N))
            D = 1 + (math.isqrt(N) - 1) // 2
            self.assertGreaterEqual(D, (2 ** ((n - 1) / 2) - 1) / 2)

    def test_locals_have_O_n_bits(self):
        code = trial.is_prime_trial.__code__
        rng = random.Random(24)
        for _ in range(200):
            n = rng.randrange(2, 25)
            N = rng.getrandbits(n - 1) | 1 << (n - 1)
            peak = [0]

            def tracer(frame, event, arg):
                if frame.f_code is code:
                    for v in frame.f_locals.values():
                        if isinstance(v, int):
                            peak[0] = max(peak[0], v.bit_length())
                    return tracer
                return None

            sys.settrace(tracer)
            try:
                trial.is_prime_trial(N)
            finally:
                sys.settrace(None)
            self.assertLessEqual(peak[0], n + 2)


class AKSParameterTests(unittest.TestCase):
    def test_log2_upper(self):
        getcontext().prec = 80
        ln2 = Decimal(2).ln()
        rng = random.Random(400)
        values = list(range(1, 4096)) + [rng.getrandbits(b) | 1 << (b - 1) for b in rng.choices(range(13, 401), k=200)]
        for N in values:
            n = N.bit_length()
            for J in (1, 2, 3, 5, 8):
                A, j = aks._log2_upper(N, J)
                self.assertEqual(j, J)
                self.assertGreaterEqual(1 << A, N ** (1 << J))      # log2 N <= A / 2^J, exactly
                self.assertLessEqual(A, n << J)
            A, J = aks._log2_upper(N)
            self.assertEqual(J, 64)
            self.assertLessEqual(A, n << J)
            self.assertGreaterEqual(Decimal(A) / Decimal(2 ** J) - Decimal(N).ln() / ln2, Decimal(0))



class AKSLemmaTests(unittest.TestCase):
    def test_totient(self):
        limit = 20000
        phi = list(range(limit))
        for p in range(2, limit):
            if phi[p] == p:                                          # p is prime
                for k in range(p, limit, p):
                    phi[k] -= phi[k] // p
        for r in range(1, limit):
            self.assertEqual(aks._totient(r), phi[r], r)
        for r in range(1, 1000):
            self.assertEqual(aks._totient(r), sum(1 for k in range(1, r + 1) if math.gcd(k, r) == 1), r)

    def test_nair(self):
        d = 1
        lcms = [1]
        for m in range(1, 2001):
            d = d * m // math.gcd(d, m)
            lcms.append(d)
            if m >= 7:
                self.assertGreaterEqual(d, 1 << m)
        for m in range(1, 301):
            for k in range(1, m + 1):
                self.assertEqual(lcms[m] % (k * math.comb(m, k)), 0)

    def test_order_lemma(self):
        rng = random.Random(15)
        values = list(range(2, 1 << 12)) + [rng.getrandbits(b) | 1 << (b - 1) for b in rng.choices(range(15, 21), k=300)]
        for N in values:
            A, J, K, r, _ = aks_params(N)
            lam_ceil = -((-A * (K + 1) ** 2) >> J)                   # ceil(lambda (K + 1)^2)
            self.assertEqual(math.gcd(r, N), 1)
            self.assertGreater(order(N, r), K)
            self.assertLessEqual(r, max(16, lam_ceil))
            self.assertLessEqual(max(16, lam_ceil), R(N.bit_length()))
        for B in range(16, 10 ** 6, 997):
            self.assertLessEqual(B ** 0.2 * math.log2(B), B / 2)

    def test_counting_chain(self):
        for B in range(2, 2001):
            self.assertGreater(math.comb(2 * B + 1, B), 1 << (B + 1))
        checked = 0
        for N in range(3, 1 << 14, 2):
            if not PRIME[N]:
                continue
            A, J, K, r, ell = aks_params(N)
            if N <= r:
                continue
            t = order(N, r)                                          # p = N: G = <N mod r>
            self.assertGreater(t * (1 << (2 * J)), A * A)            # t > lambda^2
            B = math.isqrt(t * A * A) >> J                           # floor(sqrt(t) lambda)
            self.assertTrue(2 <= B <= t - 1 and B <= ell < r, N)
            self.assertGreaterEqual(math.comb(t + ell, t - 1), math.comb(2 * B + 1, B))
            self.assertGreater(math.comb(2 * B + 1, B), 1 << (B + 1))
            checked += 1
        self.assertGreater(checked, 1800)

    def test_lower_bound(self):
        self.assertGreater(R(23), 2 ** 22)
        for n in range(24, 5001):
            self.assertLess(R(n), 2 ** (n - 1))
        # the counted part is in AKSCorrectnessTests.test_small_N (every prime N < 600 with N > r)


def poly_trim(a):
    while a and a[-1] == 0:
        a.pop()
    return a


def poly_divmod(a, b, p):
    a, b = poly_trim(list(a)), poly_trim(list(b))
    q = [0] * max(len(a) - len(b) + 1, 1)
    inv = pow(b[-1], p - 2, p)
    while len(a) >= len(b) and a:
        c = a[-1] * inv % p
        k = len(a) - len(b)
        q[k] = c
        for i, bi in enumerate(b):
            a[i + k] = (a[i + k] - c * bi) % p
        poly_trim(a)
    return poly_trim(q), a


def poly_gcd(a, b, p):
    a, b = poly_trim(list(a)), poly_trim(list(b))
    while b:
        a, b = b, poly_divmod(a, b, p)[1]
    inv = pow(a[-1], p - 2, p)
    return [x * inv % p for x in a]


def poly_mul(a, b, p):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] = (out[i + j] + x * y) % p
    return out


def x_pow_minus_1(d, p):
    return [p - 1] + [0] * (d - 1) + [1]


class AKSFieldTests(unittest.TestCase):
    def test_order_r_factor(self):
        for p in (q for q in range(2, 30) if PRIME[q]):
            for r in range(2, 40):
                if r % p == 0:
                    continue
                f = x_pow_minus_1(r, p)
                deriv = [(i * c) % p for i, c in enumerate(f)][1:]
                self.assertEqual(poly_gcd(f, deriv, p), [1])            # squarefree
                lcm = [1]
                for q in (q for q in range(2, r + 1) if PRIME[q] and r % q == 0):
                    g = x_pow_minus_1(r // q, p)
                    lcm = poly_divmod(poly_mul(lcm, g, p), poly_gcd(lcm, g, p), p)[0]
                quotient, rem = poly_divmod(f, lcm, p)
                self.assertEqual(rem, [])
                phi = sum(1 for k in range(1, r + 1) if math.gcd(k, r) == 1)
                self.assertEqual(len(quotient) - 1, phi, (p, r))


class AKSArithmeticTests(unittest.TestCase):
    def test_square_mod(self):
        rng = random.Random(2000)
        for _ in range(2000):
            r = rng.randrange(1, 41)
            N = rng.choice((2, 3, 7, 255, 65537, 2 ** 61 - 1, 10 ** 30 + 57))
            P = [rng.randrange(N) for _ in range(r)]
            want = [0] * r
            for i in range(r):
                for j in range(r):
                    want[(i + j) % r] = (want[(i + j) % r] + P[i] * P[j]) % N
            self.assertEqual(aks._square_mod(P, r, N), want)

    def test_pow_x_plus_a(self):
        for N in range(2, 41):
            for r in range(1, 11):
                for a in range(0, 4):
                    want = [1 % N] + [0] * (r - 1)
                    for _ in range(N):
                        want = [(a * want[i] + want[i - 1]) % N for i in range(r)]
                    self.assertEqual(aks._pow_x_plus_a(a, N, r), want, (N, r, a))


class AKSCorrectnessTests(unittest.TestCase):
    def test_small_N(self):
        """Every N < 600: the answer equals the sieve; the code's K, r and l (read from its locals) equal
        aks_params(N); on primes with N > r, the number of squarings is l * n, l >= (n - 1)^2, r > (n - 1)^2."""
        code = aks.is_prime_aks.__code__
        original = aks._square_mod
        count = [0]

        def counting(P, r, N):
            count[0] += 1
            return original(P, r, N)

        aks._square_mod = counting
        reached = primes_checked = 0
        try:
            for N in range(600):
                count[0] = 0
                out, loc = capture_locals(aks.is_prime_aks, code, N)
                self.assertEqual(out, PRIME[N], N)
                if "r" not in loc:
                    continue
                A, J, K, r, ell = aks_params(N)
                self.assertEqual((loc["max_k"], loc["r"]), (K, r), N)
                if "limit" in loc:
                    self.assertEqual(loc["limit"], ell, N)
                    reached += 1
                if PRIME[N] and N > r:
                    n = N.bit_length()
                    self.assertEqual(count[0], ell * n, N)
                    self.assertGreaterEqual(ell, (n - 1) ** 2)
                    self.assertGreater(r, (n - 1) ** 2)
                    primes_checked += 1
        finally:
            aks._square_mod = original
        self.assertGreater(reached, 50)
        self.assertGreater(primes_checked, 50)

    def test_step5_only_composites(self):
        for N in STEP5_SEMIPRIMES:
            A, J, K, r, ell = aks_params(N)
            self.assertFalse(aks._is_perfect_power(N))
            self.assertTrue(N > r and all(math.gcd(a, N) == 1 for a in range(2, r + 1)), N)
            self.assertFalse(trial_prime(N))
            self.assertFalse(aks.is_prime_aks(N), N)


class AKSSpaceTests(unittest.TestCase):
    @staticmethod
    def size(v):
        if isinstance(v, bool):
            return 1
        if isinstance(v, int):
            return max(1, v.bit_length())
        if isinstance(v, (bytes, bytearray)):
            return 8 * len(v)
        if isinstance(v, list) and all(isinstance(x, int) for x in v):
            return sum(max(1, x.bit_length()) for x in v)
        return 0

    def test_live_size(self):
        target = aks._square_mod.__code__
        filename = aks.__file__
        rng = random.Random(613)
        primes = [rng.choice([q for q in range(1 << (b - 1), 1 << b) if PRIME[q]]) for b in (8, 9, 10, 11, 12, 13)]
        for N in primes + STEP5_SEMIPRIMES[:2]:
            A, J, K, r, ell = aks_params(N)
            n = N.bit_length()
            peak = [0]

            def prof(frame, event, arg):
                if event == "return" and frame.f_code is target:
                    total, f = 0, frame
                    while f is not None:
                        if f.f_code.co_filename == filename:
                            total += sum(self.size(v) for v in f.f_locals.values())
                        f = f.f_back
                    peak[0] = max(peak[0], total)

            sys.setprofile(prof)
            try:
                aks.is_prime_aks(N)
            finally:
                sys.setprofile(None)
            self.assertGreater(peak[0], 0)
            self.assertLessEqual(peak[0], r * (14 * n + 5 * math.log2(r) + 48) + 4096, N)


class HarnessTests(unittest.TestCase):
    def test_psi12_passes_twelve_bases(self):
        p, q = 399165290221, 798330580441
        N = p * q
        self.assertEqual(N, 318665857834031151167461)
        self.assertTrue(trial_prime(p) and trial_prime(q))
        d, s = N - 1, 0
        while d % 2 == 0:
            d //= 2
            s += 1
        for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
            y = pow(a, d, N)
            passes = y in (1, N - 1)
            for _ in range(s - 1):
                if passes:
                    break
                y = y * y % N
                passes = y == N - 1
            self.assertTrue(passes, a)                               # a strong liar for this composite
        with self.assertRaises(ValueError):
            harness._is_prime_det(N)

    def test_sieve(self):
        harness._build()
        self.assertEqual(len(harness._sieve), 1 << 20)
        self.assertEqual([x for x in range(1 << 20) if harness._sieve[x]],
                         [x for x in range(1 << 20) if trial.is_prime_trial(x)])


class BertrandTests(unittest.TestCase):
    def test_chain_and_small_m(self):
        chain = [2, 3, 5, 7, 13, 23, 43, 83, 163, 317, 631]
        self.assertTrue(all(PRIME[q] for q in chain))
        self.assertTrue(all(chain[i] < 2 * chain[i - 1] for i in range(1, len(chain))))
        limit = 2 * 10 ** 5 + 1
        s = simple_sieve(limit)
        count = [0] * limit
        for x in range(1, limit):
            count[x] = count[x - 1] + s[x]
        for m in range(1, 10 ** 5 + 1):
            self.assertGreater(count[2 * m] - count[m], 0, m)

    def test_analytic_step(self):
        g = lambda y: y * y / 3 - (y + 1) * (2 * math.log2(y) + 0.002)            # noqa: E731
        g1 = lambda y: 2 * y / 3 - 2 * math.log2(y) - 0.002 - 2 * (y + 1) / (y * math.log(2))   # noqa: E731
        self.assertGreater(g(32), 11)
        self.assertGreater(g1(32), 8)
        self.assertGreater(2 / 3 - 2 / (32 * math.log(2)), 0.57)
        self.assertLessEqual(1 / (32 ** 2 * math.log(2)), 0.002)


def non_witnesses(N):
    d, s = N - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    out = set()
    for a in range(1, N):
        y = pow(a, d, N)
        if y == 1 or y == N - 1:
            out.add(a)
            continue
        for _ in range(s - 1):
            y = y * y % N
            if y == N - 1:
                out.add(a)
                break
    return out


class FixedBase:
    def __init__(self, a):
        self.a = a

    def randrange(self, lo, hi):
        assert lo <= self.a < hi
        return self.a


class MillerRabinTests(unittest.TestCase):
    def test_round_matches_definition(self):
        saved = mr.random
        try:
            for N in range(5, 401, 2):
                S = non_witnesses(N)
                for a in range(2, N - 1):
                    mr.random = FixedBase(a)
                    self.assertEqual(mr.is_prime_miller_rabin(N, 1), a in S, (N, a))
        finally:
            mr.random = saved
        for N in list(range(4)) + list(range(4, 400, 2)):
            self.assertEqual(mr.is_prime_miller_rabin(N), bool(PRIME[N]))

    def test_primes_pass_every_base(self):
        for N in range(3, 2000, 2):
            if PRIME[N]:
                self.assertEqual(non_witnesses(N), set(range(1, N)))

    def test_three_quarters_bound(self):
        carmichael = [561, 1105, 1729, 2465, 2821, 6601, 8911, 10585, 15841, 29341]
        for N in [x for x in range(9, 2000, 2) if not PRIME[x]] + carmichael:
            S = non_witnesses(N)
            phi = sum(1 for k in range(1, N) if math.gcd(k, N) == 1)
            self.assertTrue({1, N - 1} <= S)
            if N == 9:
                self.assertEqual(S, {1, 8})
            else:
                self.assertLessEqual(4 * len(S), phi, N)
            self.assertLess(4 * (len(S) - 2), N - 3, N)

    def test_locals_have_O_n_bits(self):
        code = mr.is_prime_miller_rabin.__code__
        rng = random.Random(64)
        for _ in range(200):
            n = rng.randrange(3, 65)
            N = rng.getrandbits(n - 1) | 1 << (n - 1) | 1
            peak = [0]

            def tracer(frame, event, arg):
                if frame.f_code is code:
                    for v in frame.f_locals.values():
                        if isinstance(v, int):
                            peak[0] = max(peak[0], v.bit_length())
                    return tracer
                return None

            random.seed(n)
            sys.settrace(tracer)
            try:
                mr.is_prime_miller_rabin(N)
            finally:
                sys.settrace(None)
            self.assertLessEqual(peak[0], max(n, 6))

    def test_corp_constants(self):
        self.assertGreaterEqual(min(0.5 - 3 / 2 ** n for n in range(4, 200)), 5 / 16)
        self.assertGreater(1 - (1 - 5 / 16 * 3 / 4) ** 3, 0.55)


if __name__ == "__main__":
    unittest.main()

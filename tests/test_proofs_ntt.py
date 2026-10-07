"""Checks of the proofs in pairs/polynomial-multiplication-naive-vs-ntt/PROOFS.md (sections 3 to 9).

Every test runs the UNCHANGED implementations on fixed inputs and seeds, over the ranges stated in each test. The
written proofs cover the general statements; these tests re-run their computable facts.
"""
import importlib.util
import math
import random
import tracemalloc
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "polynomial-multiplication-naive-vs-ntt"
P = 998244353


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NAIVE_MOD = load(ENTRY / "implementations" / "naive.py", "proofs_poly_naive")
NTT = load(ENTRY / "implementations" / "ntt.py", "proofs_poly_ntt")


def convolution(A, B):
    if not A or not B:
        return []
    C = [0] * (len(A) + len(B) - 1)
    for i, a in enumerate(A):
        for j, b in enumerate(B):
            C[i + j] = (C[i + j] + a * b) % P
    return C


def peak_bytes(fn, arg):
    tracemalloc.start()
    try:
        base = tracemalloc.get_traced_memory()[0]
        out = fn(arg)
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    del out
    return peak


class ModulusTests(unittest.TestCase):
    """PROOFS.md section 5: p - 1 = 2^23 * 7 * 17; Lucas' certificate with base 3 (3^(p-1) = 1 and 3^((p-1)/q) != 1
    for q = 2, 7, 17) proves that p is prime and that 3 has order p - 1; trial division up to sqrt(p) confirms the
    primality independently; for every L = 2^s, s = 1..23, the code's root 3^((p-1)/L) has order exactly L and its
    square is the root for L/2; 2^24 does not divide p - 1."""

    def test_certificate(self):
        self.assertEqual(P - 1, 2 ** 23 * 7 * 17)
        self.assertEqual(NTT.P, P)
        self.assertEqual(NTT.G, 3)
        self.assertEqual(pow(3, P - 1, P), 1)
        for q in (2, 7, 17):
            self.assertNotEqual(pow(3, (P - 1) // q, P), 1, q)

    def test_trial_division(self):
        self.assertTrue(all(P % d for d in range(2, math.isqrt(P) + 1)))

    def test_roots(self):
        prev = None
        for s in range(1, 24):
            L = 1 << s
            w = pow(3, (P - 1) // L, P)
            self.assertEqual(pow(w, L, P), 1, s)
            self.assertEqual(pow(w, L // 2, P), P - 1, s)
            if prev is not None:
                self.assertEqual(w * w % P, prev, s)
            prev = w
        self.assertNotEqual((P - 1) % (1 << 24), 0)


class TransformTests(unittest.TestCase):
    """PROOFS.md section 6: _ntt(a, invert=False) maps a to its DFT (a_hat[t] = sum_j a[j] w^(j t), w = 3^((p-1)/N)),
    checked on every unit vector (a complete check of the linear map) for N = 1, 2, 4, ..., 64; _ntt(., invert=True)
    inverts it on seeded vectors for N = 1, 2, 4, ..., 1024."""

    def test_dft_on_unit_vectors(self):
        for s in range(7):
            N = 1 << s
            w = pow(3, (P - 1) // N, P)
            for j in range(N):
                a = [int(i == j) for i in range(N)]
                NTT._ntt(a, invert=False)
                self.assertEqual(a, [pow(w, j * t, P) for t in range(N)], (N, j))

    def test_inverse(self):
        for s in range(11):
            N = 1 << s
            rng = random.Random(f"ntt-inv|{N}")
            v = [rng.randrange(P) for _ in range(N)]
            a = list(v)
            NTT._ntt(a, invert=False)
            NTT._ntt(a, invert=True)
            self.assertEqual(a, v, N)


class CorrectnessTests(unittest.TestCase):
    """PROOFS.md sections 4 and 7: both implementations return A * B mod p, n = 0..130, 255, 256, 257, 511, 512, 513,
    on seeded uniform coefficients, and on inputs with planted zero coefficients and with all coefficients
    p - 1 (n <= 130)."""

    def test_products(self):
        for n in list(range(131)) + [255, 256, 257, 511, 512, 513]:
            rng = random.Random(f"ntt-proofs|{n}")
            cases = [(tuple(rng.randrange(P) for _ in range(n)), tuple(rng.randrange(P) for _ in range(n)))]
            if n <= 130:
                cases.append((tuple(rng.choice((0, rng.randrange(P))) for _ in range(n)),
                              tuple(rng.randrange(P) for _ in range(n))))
                cases.append((tuple([P - 1] * n), tuple([P - 1] * n)))
            for A, B in cases:
                want = convolution(A, B)
                self.assertEqual(NAIVE_MOD.polymul_naive((A, B)), want, n)
                self.assertEqual(NTT.polymul_ntt((A, B)), want, n)


class SizeTests(unittest.TestCase):
    """PROOFS.md section 8: polymul_ntt calls _ntt three times on lists of length N, the least power of two >= 2n - 1,
    so 2n - 1 <= N <= 4n - 3 (n >= 2), observed by wrapping the module's _ntt (the code is unchanged), n = 1..300, 1000,
    1025; and the three transforms make exactly (3/2) N log2 N butterflies, counted as executions of the butterfly line
    `u = a[k]` of the unchanged _ntt (sys.settrace), n = 1..64, 300, 1000."""

    def test_sizes(self):
        original = NTT._ntt
        seen = []

        def spy(a, invert):
            seen.append(len(a))
            return original(a, invert)

        NTT._ntt = spy
        try:
            for n in list(range(1, 301)) + [1000, 1025]:
                rng = random.Random(f"ntt-size|{n}")
                A = tuple(rng.randrange(P) for _ in range(n))
                B = tuple(rng.randrange(P) for _ in range(n))
                seen.clear()
                NTT.polymul_ntt((A, B))
                N = 1
                while N < 2 * n - 1:
                    N *= 2
                self.assertEqual(seen, [N, N, N], n)
                if n >= 2:
                    self.assertTrue(2 * n - 1 <= N <= 4 * n - 3, n)
        finally:
            NTT._ntt = original

    def test_butterflies(self):
        import inspect
        import sys
        lines, start = inspect.getsourcelines(NTT._ntt)
        target = start + next(i for i, line in enumerate(lines) if line.strip() == "u = a[k]")
        code = NTT._ntt.__code__
        hits = [0]

        def local(frame, event, arg):
            if event == "line" and frame.f_lineno == target:
                hits[0] += 1
            return local

        def tracer(frame, event, arg):
            return local if frame.f_code is code else None

        for n in list(range(1, 65)) + [300, 1000]:
            rng = random.Random(f"ntt-butterflies|{n}")
            A = tuple(rng.randrange(P) for _ in range(n))
            B = tuple(rng.randrange(P) for _ in range(n))
            hits[0] = 0
            old = sys.gettrace()
            sys.settrace(tracer)
            try:
                NTT.polymul_ntt((A, B))
            finally:
                sys.settrace(old)
            N = 1
            while N < 2 * n - 1:
                N *= 2
            self.assertEqual(hits[0], 3 * (N // 2) * (N.bit_length() - 1), n)


class SpaceTests(unittest.TestCase):
    """PROOFS.md section 9: Theta(n) space. The peak traced allocation during the call (instance built before tracing)
    divided by n is at least 16 and at most 2000, and varies by a factor of at most 1.6 across four doubling sizes (n^2
    would vary by a factor of 8): NTT at n = 256..2048 and 300..2400 (padding), schoolbook at n = 128..1024 and
    150..1200."""

    def test_peaks(self):
        for fn, groups in ((NAIVE_MOD.polymul_naive, ((128, 256, 512, 1024), (150, 300, 600, 1200))),
                           (NTT.polymul_ntt, ((256, 512, 1024, 2048), (300, 600, 1200, 2400)))):
            for sizes in groups:
                per = []
                for n in sizes:
                    rng = random.Random(f"ntt-space|{n}")
                    inst = (tuple(rng.randrange(P) for _ in range(n)), tuple(rng.randrange(P) for _ in range(n)))
                    per.append(peak_bytes(fn, inst) / n)
                self.assertGreaterEqual(min(per), 16, fn.__name__)
                self.assertLessEqual(max(per), 2000, fn.__name__)
                self.assertLessEqual(max(per) / min(per), 1.6, (fn.__name__, per))


if __name__ == "__main__":
    unittest.main()

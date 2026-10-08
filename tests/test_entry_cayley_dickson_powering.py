"""Fast tests for pairs/cayley-dickson-powering-repeated-vs-square-multiply (a few seconds).

The two implementations agree with each other and with check(); check() rejects deliberately wrong outputs; the
exact V2 counts equal the closed forms stated in entry.json; the table product used by the oracle equals the
recursive product; the algebras are not associative (m >= 3) and not alternative (m >= 4); random bracketings of a
power agree (power-associativity).
"""
import importlib.util
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "cayley-dickson-powering-repeated-vs-square-multiply"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "test_cdp_harness")
_REP = _load(ENTRY / "implementations" / "repeated.py", "test_cdp_rep")
REP = _REP.cd_power_repeated
SQM = _load(ENTRY / "implementations" / "square_multiply.py", "test_cdp_sqm").cd_power_square_multiply
P = H.P


def _basis(dim, i):
    return tuple(1 if k == i else 0 for k in range(dim))


def _bracketing(x, e, rng):
    if e == 1:
        return x
    i = rng.randint(1, e - 1)
    return H.table_mul(_bracketing(x, i, rng), _bracketing(x, e - i, rng), P)


class CayleyDicksonPowering(unittest.TestCase):
    def test_agree_and_check(self):
        for n in range(1, 9):
            for t in range(3):
                inst = H.generate(n, random.Random(f"cdp-test|{n}|{t}"))
                a, b = REP(inst), SQM(inst)
                self.assertEqual(a, b)
                self.assertIs(H.check(inst, a), True)
                bad = ((a[0] + 1) % P,) + a[1:]
                self.assertIs(H.check(inst, bad), False)
                self.assertIs(H.check(inst, list(a)), False)

    def test_large_exponent(self):
        for n in (64, 200):
            inst = H.generate(n, random.Random(f"cdp-large|{n}"))
            self.assertIs(H.check(inst, SQM(inst)), True)

    def test_table_product_equals_recursive_product(self):
        rng = random.Random(1)
        for m in range(6):
            dim = 1 << m
            for _ in range(10):
                x = tuple(rng.randrange(P) for _ in range(dim))
                y = tuple(rng.randrange(P) for _ in range(dim))
                self.assertEqual(_REP.cd_mul(x, y, P), H.table_mul(x, y, P))

    def test_not_associative_not_alternative(self):
        for m in (3, 4, 5):
            dim = 1 << m
            a, b, c = _basis(dim, 1), _basis(dim, 2), _basis(dim, 4)
            mul = lambda u, v: H.table_mul(u, v, P)  # noqa: E731
            self.assertEqual(mul(mul(a, b), c), _basis(dim, 7))
            self.assertEqual(mul(a, mul(b, c)), tuple((-v) % P for v in _basis(dim, 7)))
            if m >= 4:
                x = tuple((u + v) % P for u, v in zip(_basis(dim, 1), _basis(dim, 10)))
                y = _basis(dim, 4)
                self.assertNotEqual(mul(mul(x, x), y), mul(x, mul(x, y)))

    def test_power_associative(self):
        rng = random.Random(2)
        for m in (3, 4, 5):
            x = tuple(rng.randrange(P) for _ in range(1 << m))
            for e in range(1, 9):
                ref = REP((x, e, P))
                for _ in range(2):
                    self.assertEqual(_bracketing(x, e, rng), ref)

    def test_closed_form_counts(self):
        for n in range(2, 10):
            inst = H.generate_scaling(n, random.Random(n))
            REP(inst)
            self.assertEqual(H.reported_cost(None), 64 * (2 ** n - 2))
        for n in (2, 3, 16, 100, 300):
            inst = H.generate_scaling(n, random.Random(n))
            SQM(inst)
            self.assertEqual(H.reported_cost(None), 128 * (n - 1))
        rng = random.Random(3)
        for m in (3, 4, 5):
            x = tuple(H.CountingInt(rng.randrange(P)) for _ in range(1 << m))
            for e in (1, 2, 5, 12, 77):
                H._ops["mul"] = 0
                SQM((x, e, P))
                self.assertEqual(H._ops["mul"], 4 ** m * (e.bit_length() - 1 + bin(e).count("1") - 1))


if __name__ == "__main__":
    unittest.main()

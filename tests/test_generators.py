"""Tests for generators/: generated entries must be correct, honestly tagged, and verifiable.

Run:  python -m unittest discover -s tests
"""
import importlib.util
import json
import math
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("linear_recurrence", ROOT / "generators" / "linear_recurrence.py")
linrec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(linrec)


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


class GrowthRateTests(unittest.TestCase):
    def test_known_roots(self):
        phi = (1 + math.sqrt(5)) / 2
        self.assertAlmostEqual(linrec.growth_rate([1, 1]), phi, places=12)
        self.assertAlmostEqual(linrec.growth_rate([7, -3]), phi, places=12)  # depends only on the support
        self.assertAlmostEqual(linrec.growth_rate([1, 1, 1]), 1.839286755214161, places=12)  # tribonacci constant

    def test_root_satisfies_characteristic_polynomial(self):
        for coeffs in ([1, 0, 1], [1, 1, 1, 1], [0, 2, 5]):
            lam = linrec.growth_rate(coeffs)
            k = len(coeffs)
            residual = lam ** k - sum(lam ** (k - i) for i, c in enumerate(coeffs, 1) if c)
            self.assertAlmostEqual(residual, 0.0, places=9)

    def test_rejects_non_exponential_support(self):
        with self.assertRaises(ValueError):
            linrec.growth_rate([0, 0, 3])


class GeneratedEntryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_three_implementations_agree_with_direct_computation(self):
        for coeffs in ([1, 1, 1], [2, 0, 5], [3, 1]):
            d = linrec.write(coeffs, root=self.tmp)
            fns = [load(d / "implementations" / f, f"{f}_{coeffs}").solve for f in ("naive.py", "dp.py", "matrix_power.py")]
            k = len(coeffs)
            a = [0] * (k - 1) + [1]  # reference sequence computed here, independently of the generated code
            for n in range(k, 40):
                a.append(sum(c * a[n - i] for i, c in enumerate(coeffs, 1)) % 2 ** 64)
            for n in range(0, 22):
                self.assertEqual({fn(n) for fn in fns}, {a[n]}, (coeffs, n))
            self.assertEqual(fns[1](39), a[39])
            self.assertEqual(fns[2](39), a[39])

    def test_entry_is_tagged_synthetic_and_schema_valid(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((ROOT / "schema" / "entry.schema.json").read_text(encoding="utf-8"))
        d = linrec.write([1, 0, 1], root=self.tmp)
        entry = json.loads((d / "entry.json").read_text(encoding="utf-8"))
        self.assertEqual(entry["pair_type"], "T7")
        self.assertIn("T7 SYNTHETIC", entry["caveats"])
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(entry)), [])


if __name__ == "__main__":
    unittest.main()

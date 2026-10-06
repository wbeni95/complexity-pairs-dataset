"""Tests for tools/validate.py: the validator must reject wrong claims, not just accept right ones.

Run:  python -m unittest discover -s tests
"""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import validate  # noqa: E402

FIB = Path(validate.REPO) / "pairs" / "fibonacci-naive-vs-dp"
BV = Path(validate.REPO) / "pairs" / "bernstein-vazirani-classical-vs-quantum"


class CostExpressionTests(unittest.TestCase):
    def test_arithmetic(self):
        self.assertAlmostEqual(validate.eval_cost("n**2 * log(n)", 8), 64 * 2.0794415, places=5)
        self.assertEqual(validate.eval_cost("factorial(n - 2)", 6), 24)
        self.assertAlmostEqual(validate.eval_cost("phi**2", 0), 2.6180339887, places=8)

    def test_rejects_code(self):
        for expr in ("__import__('os').system('echo hi')", "n.__class__", "open('x')", "[n]", "lambda: 1"):
            with self.assertRaises((ValueError, SyntaxError), msg=expr):
                validate.eval_cost(expr, 3)


class ValidatorRejectsBadEntries(unittest.TestCase):
    """Builds a throw-away repo layout and points the validator at it."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "pairs").mkdir()
        (self.tmp / "staging").mkdir()
        self.entry_dir = self.tmp / "pairs" / "fibonacci-naive-vs-dp"
        shutil.copytree(FIB, self.entry_dir, ignore=shutil.ignore_patterns("__pycache__"))
        self._old_repo = validate.REPO
        validate.REPO = self.tmp
        validate._module_cache.clear()
        from jsonschema import Draft202012Validator
        with open(validate.SCHEMA_PATH, encoding="utf-8") as f:
            self.schema = Draft202012Validator(json.load(f))

    def tearDown(self):
        validate.REPO = self._old_repo
        validate._module_cache.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def edit_entry(self, fn):
        path = self.entry_dir / "entry.json"
        entry = json.loads(path.read_text(encoding="utf-8"))
        fn(entry)
        path.write_text(json.dumps(entry, indent=2), encoding="utf-8")

    def run_validator(self, scaling=False, entry_dir=None, expect=None):
        args = SimpleNamespace(scaling=scaling, probe=False, static=False, verbose=False)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ok = validate.validate_entry(entry_dir or self.entry_dir, self.schema, args)
        if expect is not None:
            self.assertIn(expect, out.getvalue())
        return ok

    def test_unmodified_copy_passes(self):
        self.assertTrue(self.run_validator())

    def test_wrong_scaling_claim_fails_v2(self):
        # Claim the exponential recursion is quadratic: the fit must catch it.
        def lie(entry):
            entry["algorithms"][0]["harness"]["scaling"] = {"cost": "n**6", "n_values": [18, 20, 22, 24, 26, 28]}
        self.edit_entry(lie)
        self.assertFalse(self.run_validator(scaling=True, expect="vs claimed cost 'n**6'"))

    def test_disagreeing_implementation_fails_v1(self):
        impl = self.entry_dir / "implementations" / "dp.py"
        impl.write_text(impl.read_text(encoding="utf-8").replace("return a", "return a + (n == 13)"), encoding="utf-8")
        self.assertFalse(self.run_validator(expect="disagree"))

    def test_input_mutation_is_rejected(self):
        # Minimal sorting entry: one implementation sorts its input in place.
        d = self.tmp / "pairs" / "sorting-mutation-test"
        (d / "implementations").mkdir(parents=True)
        (d / "README.md").write_text("test", encoding="utf-8")
        (d / "harness.py").write_text(
            "def generate(n, rng):\n    return [rng.randint(0, 9) for _ in range(n)]\n", encoding="utf-8")
        (d / "implementations" / "algs.py").write_text(
            "def copy_sort(xs):\n    return sorted(xs)\n\n"
            "def in_place_sort(xs):\n    xs.sort()\n    return xs\n", encoding="utf-8")
        entry = json.loads((self.entry_dir / "entry.json").read_text(encoding="utf-8"))
        entry["id"] = "sorting-mutation-test"
        entry["verification"]["level"] = "V1"
        entry["test_harness"] = {"module": "harness.py", "v1_sizes": [5, 6], "trials": 2}
        entry["algorithms"] = entry["algorithms"][:2]
        entry["algorithms"][0]["implementation"] = "implementations/algs.py:copy_sort"
        entry["algorithms"][1]["implementation"] = "implementations/algs.py:in_place_sort"
        (d / "entry.json").write_text(json.dumps(entry), encoding="utf-8")
        self.assertFalse(self.run_validator(entry_dir=d, expect="mutated its input"))

    def test_v0_entry_in_pairs_fails(self):
        self.edit_entry(lambda e: e["verification"].update(level="V0"))
        self.assertFalse(self.run_validator(expect="V0 belongs in staging"))

    def test_v1_entry_in_staging_fails(self):
        moved = self.tmp / "staging" / self.entry_dir.name
        shutil.move(str(self.entry_dir), moved)
        self.assertFalse(self.run_validator(entry_dir=moved, expect="staging/ holds V0 entries only"))

    def test_v3_without_proofs_fails(self):
        self.edit_entry(lambda e: e["verification"].update(level="V3"))
        self.assertFalse(self.run_validator(expect="V3 requires verification.proofs"))

    def test_id_must_match_folder(self):
        self.edit_entry(lambda e: e.update(id="something-else"))
        self.assertFalse(self.run_validator(expect="!= folder name"))

    def test_false_query_count_claim_fails(self):
        # Claim the 1-query quantum algorithm needs n queries: the reported-count fit must catch it.
        d = self.tmp / "pairs" / BV.name
        shutil.copytree(BV, d, ignore=shutil.ignore_patterns("__pycache__"))
        path = d / "entry.json"
        entry = json.loads(path.read_text(encoding="utf-8"))
        entry["algorithms"][1]["harness"]["scaling"] = {"cost": "n", "n_values": [1, 2, 4, 8], "measure": "reported"}
        path.write_text(json.dumps(entry), encoding="utf-8")
        self.assertFalse(self.run_validator(scaling=True, entry_dir=d, expect="vs claimed cost 'n'"))

    def test_rival_that_also_fits_fails(self):
        # phi**n vs a rival 1.7**n: alpha against the rival is ln(phi)/ln(1.7) ~ 0.91, inside 0.25 -> not discriminated.
        def add_close_rival(entry):
            entry["algorithms"][0]["harness"]["scaling"]["rivals"] = ["1.7**n"]
        self.edit_entry(add_close_rival)
        self.assertFalse(self.run_validator(scaling=True, expect="claim not discriminated"))

    def test_rival_that_does_not_fit_passes(self):
        # phi**n vs a rival 2**n: alpha against the rival is ln(phi)/ln(2) ~ 0.69 -> rejected, claim stands.
        def add_far_rival(entry):
            entry["algorithms"][0]["harness"]["scaling"]["rivals"] = ["2**n"]
        self.edit_entry(add_far_rival)
        self.assertTrue(self.run_validator(scaling=True))

    def test_t4_without_randomized_algorithm_fails(self):
        self.edit_entry(lambda e: e.update(secondary_tags=["T4"]))
        self.assertFalse(self.run_validator(expect="T4 needs"))

    def test_t9_without_classical_lower_bound_fails(self):
        def claim_t9(entry):
            entry["secondary_tags"] = ["T9"]
            entry["algorithms"][2]["model"] = "quantum"
        self.edit_entry(claim_t9)
        self.assertFalse(self.run_validator(expect="T9 needs a classical lower bound"))

    def test_t7_outside_synthetic_fails(self):
        self.edit_entry(lambda e: e.update(pair_type="T7"))
        self.assertFalse(self.run_validator(expect="belong in synthetic/"))


if __name__ == "__main__":
    unittest.main()

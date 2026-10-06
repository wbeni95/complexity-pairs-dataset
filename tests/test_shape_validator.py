"""The exact shape diagnostic inside tools/validate.py (round 2026-10-06f): informational only.

* integration: the shape result is printed with -v and stored in the record, and never changes a V2 verdict,
  even for a wrong claim (MISMATCH) or when the diagnostic itself crashes;
* the pre-existing output lines are unchanged;
* regression: the V2 verdicts of the exact-count series equal those of ledger run 20261006T143136Z, with the shape
  diagnostic enabled (exact values are compared too when the Python version equals the ledger's).

By default the regression covers every exact-count series with samples == 1 outside the Strassen entry (about a
minute). Set CPAIRS_FULL_REGRESSION=1 to include the randomised series (samples > 1) and the Strassen entry, whose
shape grid reaches n = 512 (about three more minutes).

Run:  python -m unittest discover -s tests
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import platform
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import validate  # noqa: E402

REPO = Path(validate.REPO)
ZETA = REPO / "pairs" / "subset-sum-zeta-transform-naive-vs-yates"
LEDGER = REPO / "ledger" / "runs" / "20261006T143136Z.json"
FULL = os.environ.get("CPAIRS_FULL_REGRESSION") == "1"
SLOW_ENTRIES = {"matrix-multiplication-naive-vs-strassen"}


def schema_validator():
    from jsonschema import Draft202012Validator
    with open(validate.SCHEMA_PATH, encoding="utf-8") as f:
        return Draft202012Validator(json.load(f))


class ShapeInsideValidator(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "pairs").mkdir()
        self.entry_dir = self.tmp / "pairs" / ZETA.name
        shutil.copytree(ZETA, self.entry_dir, ignore=shutil.ignore_patterns("__pycache__"))
        self._old_repo = validate.REPO
        validate.REPO = self.tmp
        validate._module_cache.clear()
        self.schema = schema_validator()

    def tearDown(self):
        validate.REPO = self._old_repo
        validate._module_cache.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def edit_scaling(self, prefix, fn):
        path = self.entry_dir / "entry.json"
        entry = json.loads(path.read_text(encoding="utf-8"))
        alg = next(a for a in entry["algorithms"] if a["name"].startswith(prefix))
        fn(alg["harness"]["scaling"])
        path.write_text(json.dumps(entry, indent=2), encoding="utf-8")

    def run_validator(self, verbose=False, record=False, no_shape=False):
        args = SimpleNamespace(scaling=True, probe=False, static=False, verbose=verbose, no_shape=no_shape)
        recorder = [] if record else None
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ok = validate.validate_entry(self.entry_dir, self.schema, args, recorder)
        return ok, out.getvalue(), (recorder[0] if record else None)

    def test_match_is_printed_and_recorded(self):
        ok, out, rec = self.run_validator(verbose=True, record=True)
        self.assertTrue(ok)
        self.assertIn("shape submask enumeration (naive): [consecutive n=1..12, 12 terms] MATCH", out)
        shapes = [m["shape"] for m in rec["v2"]]
        self.assertEqual([s["category"] for s in shapes], ["MATCH", "MATCH"])
        self.assertIn("x - 3", shapes[0]["found"]["base"])
        json.dumps(rec)  # the record must stay JSON-serialisable

    def test_not_computed_without_verbose_or_record(self):
        with mock.patch.object(validate, "run_shape", side_effect=AssertionError("must not run")):
            ok, out, _ = self.run_validator()
        self.assertTrue(ok)
        self.assertNotIn("shape", out)

    def test_existing_output_lines_unchanged(self):
        _, with_shape, _ = self.run_validator(verbose=True)
        _, without, _ = self.run_validator(verbose=True, no_shape=True)
        norm = lambda s: re.sub(r"\[\d+\.\ds\]", "[t]", s)  # noqa: E731 -- elapsed seconds vary
        kept = [ln for ln in norm(with_shape).splitlines() if not ln.startswith("      shape ")]
        self.assertEqual(kept, norm(without).splitlines())
        self.assertEqual(sum(ln.startswith("      shape ") for ln in with_shape.splitlines()), 2)

    def test_wrong_claim_gives_mismatch_but_v2_still_passes(self):
        self.edit_scaling("submask", lambda sc: sc["shape"].update(expect={"base": "2"}))
        ok, out, rec = self.run_validator(verbose=True, record=True)
        self.assertTrue(ok)
        s = rec["v2"][0]["shape"]
        self.assertEqual((s["category"], s["differs"]), ("MISMATCH", ["base"]))
        self.assertIn("MISMATCH (base)", out)
        self.assertEqual(rec["status"], "OK")

    def test_crash_inside_the_diagnostic_does_not_touch_v2(self):
        from methods import shape as sd
        with mock.patch.object(sd, "run", side_effect=RuntimeError("boom")):
            ok, out, rec = self.run_validator(verbose=True, record=True)
        self.assertTrue(ok)
        self.assertEqual({m["shape"]["reason"] for m in rec["v2"]}, {"internal_error"})

    def test_invalid_block_is_reported_not_failed(self):
        self.edit_scaling("submask", lambda sc: sc["shape"].update(n_range=[3, 1000]))  # 998 terms > 64
        ok, _, rec = self.run_validator(record=True)
        self.assertTrue(ok)
        self.assertEqual(rec["v2"][0]["shape"]["reason"], "invalid_shape_block")

    def test_failing_v2_keeps_failing(self):
        self.edit_scaling("submask", lambda sc: sc.update(cost="2**n"))  # wrong claim: V2 must still fail
        ok, out, rec = self.run_validator(verbose=True, record=True)
        self.assertFalse(ok)
        self.assertIn("vs claimed cost '2**n'", out)
        s = rec["v2"][0]["shape"]
        self.assertEqual((s["category"], s["differs"]), ("MISMATCH", ["base"]))

    def test_no_shape_switch(self):
        _, _, rec = self.run_validator(record=True, no_shape=True)
        self.assertTrue(all("shape" not in m for m in rec["v2"]))


class SkippedWithoutRunningAnything(unittest.TestCase):
    def test_timing_measure_and_missing_block(self):
        # harness/fn None: if anything were run, this would raise
        r = validate.run_shape({"id": "x"}, None, None, {"name": "a"}, None,
                               {"cost": "n", "measure": "time", "shape": {"sequence": "consecutive", "n_range": [1, 9]}}, {})
        self.assertEqual((r["category"], r["reason"]), ("SKIPPED", "timing_measure"))
        r = validate.run_shape({"id": "x"}, None, None, {"name": "a"}, None, {"cost": "n", "measure": "reported"}, {})
        self.assertEqual((r["category"], r["reason"]), ("SKIPPED", "no_shape_block"))
        r = validate.run_shape({"id": "x"}, None, None, {"name": "a"}, None,
                               {"cost": "n", "measure": "reported", "samples": 4,
                                "shape": {"sequence": "consecutive", "n_range": [1, 9]}}, {})
        self.assertEqual((r["category"], r["reason"]), ("UNDETERMINED", "randomised_counts"))


class LedgerCompatibility(unittest.TestCase):
    def test_new_measurements_keep_every_old_key(self):
        old = json.loads(LEDGER.read_text(encoding="utf-8"))
        old_keys = set()
        for e in old["entries"]:
            for m in e.get("v2", []):
                old_keys |= set(m)
                self.assertNotIn("shape", m)  # old files have no shape field; readers must use .get("shape")
        entry = validate.load_entry(ZETA)
        rec = {}
        validate.run_v2(entry, ZETA, False, rec)
        for m in rec["v2"]:
            self.assertTrue(old_keys <= set(m), old_keys - set(m))
            self.assertEqual(set(m) - old_keys, {"shape"})

    def test_run_metadata_names_the_diagnostic(self):
        meta = validate.run_metadata(SimpleNamespace(paths=[], scaling=True, probe=False, static=False, no_shape=False))
        self.assertTrue(meta["shape_diagnostic"]["informational"])
        self.assertEqual(meta["shape_diagnostic"]["version"], 1)


class V2VerdictsUnchanged(unittest.TestCase):
    """Exact-count V2 verdicts (and values) with the shape diagnostic enabled vs ledger 20261006T143136Z."""

    def test_against_ledger(self):
        led = json.loads(LEDGER.read_text(encoding="utf-8"))
        same_python = platform.python_version() == led["run"]["python"]
        checked = 0
        for e in led["entries"]:
            series = [m for m in e.get("v2", []) if m["measure"] == "reported"
                      and (FULL or (m["samples"] == 1 and e["id"] not in SLOW_ENTRIES))]
            if not series:
                continue
            d = REPO / e["path"]
            entry = copy.deepcopy(validate.load_entry(d))
            names = {m["algorithm"] for m in series}
            entry["algorithms"] = [a for a in entry["algorithms"] if a["name"] in names]
            rec = {}
            with contextlib.redirect_stdout(io.StringIO()):
                errors = validate.run_v2(entry, d, False, rec)
            self.assertEqual(errors, [], e["id"])
            got = {m["algorithm"]: m for m in rec["v2"]}
            for m in series:
                g = got[m["algorithm"]]
                with self.subTest(entry=e["id"], algorithm=m["algorithm"]):
                    self.assertEqual(g["passed"], m["passed"])
                    self.assertEqual(g["n_values"], m["n_values"])
                    if same_python:
                        self.assertEqual(g["values"], m["values"])
                    self.assertIn(g["shape"]["category"], ("MATCH", "MISMATCH", "UNDETERMINED", "SKIPPED"))
                checked += 1
        self.assertGreaterEqual(checked, 59 if FULL else 46)


if __name__ == "__main__":
    unittest.main()

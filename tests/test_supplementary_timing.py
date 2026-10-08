"""Supplementary wall-clock timing of exact-count series in tools/validate.py.

Exact counts are this dataset's evidence; wall-clock seconds are recorded next to them, on the same instances, for
comparison with standard benchmarks. The timing must:
* be stored for every series with measure 'reported' when requested, with one value per n;
* never change a V2 verdict or a counted value, even when the timing itself crashes;
* not run unless requested (validate_entry requests it only for --record runs without --no-timing);
* be named in the run metadata.

Run:  python -m unittest discover -s tests
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import validate  # noqa: E402

REPO = Path(validate.REPO)
ZETA = REPO / "pairs" / "subset-sum-zeta-transform-naive-vs-yates"   # two exact-count series
FIB = REPO / "pairs" / "fibonacci-naive-vs-dp"                       # wall-clock series only


def measure(entry_dir, timing):
    entry = validate.load_entry(entry_dir)
    rec = {}
    with contextlib.redirect_stdout(io.StringIO()):
        errors = validate.run_v2(entry, entry_dir, False, rec, shape=False, timing=timing)
    return errors, rec["v2"]


class SupplementaryTiming(unittest.TestCase):
    def test_every_exact_count_series_gets_seconds_per_n(self):
        errors, v2 = measure(ZETA, timing=True)
        self.assertEqual(errors, [])
        reported = [m for m in v2 if m["measure"] == "reported"]
        self.assertEqual(len(reported), 2)
        for m in reported:
            t = m["timing"]
            self.assertTrue(t["informational"])
            self.assertEqual(t["unit"], "seconds")
            self.assertEqual(t["n_values"], m["n_values"])
            self.assertEqual(len(t["values"]), len(m["n_values"]))
            self.assertTrue(all(v > 0 for v in t["values"]))
        json.dumps(v2)  # the record must stay JSON-serialisable

    def test_verdicts_and_counts_unchanged(self):
        _, without = measure(ZETA, timing=False)
        _, with_timing = measure(ZETA, timing=True)
        self.assertTrue(all("timing" not in m for m in without))
        strip = [{k: v for k, v in m.items() if k != "timing"} for m in with_timing]
        self.assertEqual(strip, without)

    def test_crash_inside_the_timing_does_not_touch_v2(self):
        _, without = measure(ZETA, timing=False)
        with mock.patch.object(validate, "time_call", side_effect=RuntimeError("boom")):
            errors, v2 = measure(ZETA, timing=True)
        self.assertEqual(errors, [])
        self.assertEqual({m["timing"]["error"] for m in v2}, {"RuntimeError: boom"})
        self.assertEqual([m["passed"] for m in v2], [m["passed"] for m in without])
        self.assertEqual([m["values"] for m in v2], [m["values"] for m in without])

    def test_wall_clock_series_get_no_second_timing(self):
        _, v2 = measure(FIB, timing=True)
        self.assertTrue(v2)
        self.assertTrue(all(m["measure"] == "time" and "timing" not in m for m in v2))

    def test_not_run_unless_requested(self):
        with mock.patch.object(validate, "supplementary_timing", side_effect=AssertionError("must not run")):
            errors, _ = measure(ZETA, timing=False)
        self.assertEqual(errors, [])

    def test_validate_entry_times_only_recorded_runs(self):
        from jsonschema import Draft202012Validator
        with open(validate.SCHEMA_PATH, encoding="utf-8") as f:
            schema = Draft202012Validator(json.load(f))
        calls = []
        real = validate.run_v2

        def spy(*a, **k):
            calls.append(k.get("timing"))
            return real(*a, **k)

        def args(no_timing=False):
            return SimpleNamespace(scaling=True, probe=False, static=False, verbose=False, no_shape=True,
                                   no_timing=no_timing)
        with mock.patch.object(validate, "run_v2", side_effect=spy), contextlib.redirect_stdout(io.StringIO()):
            validate.validate_entry(ZETA, schema, args(), None)
            validate.validate_entry(ZETA, schema, args(), [])
            validate.validate_entry(ZETA, schema, args(no_timing=True), [])
        self.assertEqual(calls, [False, True, False])

    def test_run_metadata_names_the_timing(self):
        meta = validate.run_metadata(SimpleNamespace(paths=[], scaling=True, probe=False, static=False,
                                                     no_shape=False, no_timing=False))
        self.assertTrue(meta["supplementary_timing"]["enabled"])
        self.assertTrue(meta["supplementary_timing"]["informational"])
        meta = validate.run_metadata(SimpleNamespace(paths=[], scaling=True, probe=False, static=False,
                                                     no_shape=False, no_timing=True))
        self.assertFalse(meta["supplementary_timing"]["enabled"])


if __name__ == "__main__":
    unittest.main()

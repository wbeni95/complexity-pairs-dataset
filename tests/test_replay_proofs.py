"""tools/replay_proofs.py: how listed checks become commands, that every listed check exists, and how a command's
result is judged (exit code and [FAIL] lines)."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import replay_proofs  # noqa: E402
import validate  # noqa: E402


class CommandTests(unittest.TestCase):
    def test_test_files_run_as_unittest_modules(self):
        cmd = replay_proofs.command_for(ROOT / "tests" / "test_replay_proofs.py")
        self.assertEqual(cmd, ("-m", "unittest", "tests.test_replay_proofs"))

    def test_other_files_run_as_scripts_from_the_root(self):
        cmd = replay_proofs.command_for(ROOT / "tools" / "validate.py")
        self.assertEqual(cmd, ("tools/validate.py",))

    def test_entries_also_replay_their_v1_runs(self):
        item = {"slug": "x", "path": ROOT / "pairs" / "x", "kind": "entry",
                "proof": {"documents": ["PROOFS.md"], "checks": ["../../tests/test_replay_proofs.py"], "audit": "RL-103"}}
        cmds = replay_proofs.commands_for(item)
        self.assertEqual(cmds[0], ("tools/validate.py", "pairs/x"))
        self.assertEqual(cmds[1], ("-m", "unittest", "tests.test_replay_proofs"))


class VerdictTests(unittest.TestCase):
    def test_exit_zero_and_no_fail_line_passes(self):
        self.assertEqual(replay_proofs.verdict(0, "[PASS] a\nALL CHECKS PASSED\n"), (True, "PASS"))

    def test_nonzero_exit_fails(self):
        self.assertEqual(replay_proofs.verdict(1, "[PASS] a\n"), (False, "FAIL (exit code 1)"))

    def test_exit_zero_with_a_fail_line_fails(self):
        self.assertEqual(replay_proofs.verdict(0, "[PASS] a\n[FAIL] b: 3 mismatches\nALL CHECKS PASSED\n"),
                         (False, "FAIL (output contains [FAIL] lines)"))

    def test_fail_line_on_the_last_line_without_newline(self):
        self.assertFalse(replay_proofs.verdict(0, "[PASS] a\n[FAIL] b")[0])

    def test_only_lines_that_start_with_the_prefix_count(self):
        self.assertTrue(replay_proofs.verdict(0, "  [FAIL] indented\nsee [FAIL] inside a line\n[FAILED] other\n")[0])
        self.assertEqual(replay_proofs.fail_lines("x\n[FAIL] one\n [FAIL] two\n[FAIL] three\n"),
                         ["[FAIL] one", "[FAIL] three"])


class MainJudgesCommandsTests(unittest.TestCase):
    """main() on one stand-in item whose only command is `python -c CODE`."""

    def run_main(self, code):
        item = {"slug": "stand-in", "path": ROOT, "kind": "theorem", "proof": {}}
        out = io.StringIO()
        with mock.patch.object(replay_proofs, "marked_items", return_value=[item]), \
                mock.patch.object(replay_proofs, "commands_for", return_value=[("-c", code)]), \
                contextlib.redirect_stdout(out):
            rc = replay_proofs.main([])
        return rc, out.getvalue()

    def test_clean_command_passes(self):
        rc, out = self.run_main("print('[PASS] a'); print('ALL CHECKS PASSED')")
        self.assertEqual(rc, 0)
        self.assertIn("1/1 commands passed", out)

    def test_exit_zero_with_fail_line_is_a_failure(self):
        rc, out = self.run_main("print('[PASS] a'); print('[FAIL] b: wrong count')")
        self.assertEqual(rc, 1)
        self.assertIn("FAIL (output contains [FAIL] lines)", out)
        self.assertIn("    [FAIL] b: wrong count", out)
        self.assertIn("items with a failing check: stand-in", out)

    def test_nonzero_exit_is_a_failure(self):
        rc, out = self.run_main("import sys; print('[PASS] a'); sys.exit(3)")
        self.assertEqual(rc, 1)
        self.assertIn("FAIL (exit code 3)", out)


class MarkedItemTests(unittest.TestCase):
    def test_every_marked_item_lists_existing_files_and_a_logged_audit(self):
        for item in replay_proofs.marked_items():
            with self.subTest(item=item["slug"]):
                self.assertEqual(validate.proof_errors(item["proof"], item["path"]), [])


if __name__ == "__main__":
    unittest.main()

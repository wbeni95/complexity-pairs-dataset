"""tools/replay_proofs.py: how listed checks become commands, and that every listed check exists."""
import sys
import unittest
from pathlib import Path

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


class MarkedItemTests(unittest.TestCase):
    def test_every_marked_item_lists_existing_files_and_a_logged_audit(self):
        for item in replay_proofs.marked_items():
            with self.subTest(item=item["slug"]):
                self.assertEqual(validate.proof_errors(item["proof"], item["path"]), [])


if __name__ == "__main__":
    unittest.main()

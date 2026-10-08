"""tools/ci_select.py: shared or unknown changes check everything; an item change checks that item, every item whose
proof, implementation or test harness names the changed file, and one item listing each check that reads it. The
expected selections below are written out by hand from the repository, not recomputed with the selector's rules."""
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import ci_select  # noqa: E402


def sel(*paths):
    return ci_select.select(list(paths))


def mode_of(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        ci_select.main(argv)
    return dict(line.split("=", 1) for line in out.getvalue().splitlines())["mode"]


class FullRunTests(unittest.TestCase):
    def test_shared_and_unknown_paths(self):
        for path in ("tools/validate.py", "schema/entry.schema.json", "lib/qsim.py", "requirements.txt",
                     ".github/workflows/validate.yml", "theorems/meta.schema.json", "tests/proof_space.py",
                     "tests/_proof_trace.py", ".gitattributes", "some-new-top-level-file.txt", "methods/x.py",
                     "experiments/2026-10-06c_analysis.py"):  # an experiment that no proof and no check names
            with self.subTest(path=path):
                s = sel("README.md", path)
                self.assertEqual((s["mode"], s["sources"]), ("full", True))

    def test_removed_item_folder(self):
        self.assertEqual(sel("pairs/no-such-entry-folder/entry.json")["mode"], "full")

    def test_unreadable_item_gives_a_full_run_not_a_crash(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "pairs" / "x").mkdir(parents=True)
            (tmp / "pairs" / "x" / "entry.json").write_text('{"id": "x",', encoding="utf-8")
            self.assertEqual(ci_select.select(["pairs/x/entry.json"], tmp)["mode"], "full")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_each_full_event_on_its_own(self):
        # a valid base and no change: only the event or the ref can make these runs full
        self.assertEqual(mode_of(["--event", "push", "--ref", "refs/heads/main", "--base", "HEAD", "--head", "HEAD"]),
                         "docs")
        for argv in (["--event", "schedule"], ["--event", "workflow_dispatch"],
                     ["--event", "push", "--ref", "refs/tags/v9.9.9"]):
            with self.subTest(argv=argv):
                self.assertEqual(mode_of(argv + ["--base", "HEAD", "--head", "HEAD"]), "full")

    def test_unknown_base(self):
        for base in ("", "0" * 40, "f" * 40):
            with self.subTest(base=base):
                self.assertEqual(mode_of(["--event", "push", "--ref", "refs/heads/main", "--base", base]), "full")


class GitDiffTests(unittest.TestCase):
    """changed_files on a throw-away repository: renames come as a removal plus an addition, and non-ASCII paths come
    unquoted."""

    def setUp(self):
        if shutil.which("git") is None:
            self.skipTest("git not available")
        self.tmp = Path(tempfile.mkdtemp())
        self.git("init", "-q")
        (self.tmp / "pairs" / "a").mkdir(parents=True)
        (self.tmp / "pairs" / "a" / "entry.json").write_text("{}", encoding="utf-8")
        (self.tmp / "notes").mkdir()
        self.base = self.commit("base")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=self.tmp,
                              capture_output=True, text=True, check=True).stdout.strip()

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def test_rename_and_non_ascii(self):
        (self.tmp / "pairs" / "a").rename(self.tmp / "pairs" / "b")
        (self.tmp / "notes" / "é.md").write_text("x", encoding="utf-8")
        head = self.commit("change")
        with mock.patch.object(ci_select, "REPO", self.tmp):
            got = ci_select.changed_files(self.base, head)
        self.assertEqual(sorted(got), ["notes/é.md", "pairs/a/entry.json", "pairs/b/entry.json"])


class SelectiveTests(unittest.TestCase):
    def test_documentation_alone(self):
        s = sel("README.md", "RESEARCH_LOG.md", "notes/x.md", "ledger/runs/x.json", "CITATION.cff", "theorems/README.md",
                "notes/é.md")
        self.assertEqual((s["mode"], s["entries"], s["slugs"], s["sources"]), ("docs", [], [], False))

    def test_one_entry(self):
        s = sel("pairs/fibonacci-naive-vs-dp/entry.json")
        self.assertEqual((s["mode"], s["entries"], s["sources"]), ("items", ["pairs/fibonacci-naive-vs-dp"], True))
        self.assertIn("fibonacci-naive-vs-dp", s["slugs"])

    def test_theorem_notes_are_replayed_not_validated(self):
        s = sel("theorems/binary-powering-exactness-in-magmas/meta.json")
        self.assertEqual((s["entries"], s["slugs"]), ([], ["binary-powering-exactness-in-magmas"]))

    def test_unmarked_items_are_not_replayed(self):
        # staging/ entries cannot carry the check mark (validate.py), so any staged entry is an unmarked item
        folder = next(d for d in sorted((ROOT / "staging").iterdir()) if (d / "entry.json").is_file())
        s = sel(f"staging/{folder.name}/entry.json")
        self.assertIn(f"staging/{folder.name}", s["entries"])
        self.assertNotIn(folder.name, s["slugs"])


class CrossFolderTests(unittest.TestCase):
    """Reads across folders that exist in this repository, each found by reading the code."""

    CASES = [
        # (changed path, entry whose V1/V2 must run or None, marked item that must be replayed, why)
        ("pairs/primality-trial-vs-aks/harness.py", "pairs/primality-miller-rabin-vs-aks",
         "primality-miller-rabin-vs-aks", "its test_harness.module is ../primality-trial-vs-aks/harness.py"),
        ("pairs/matrix-multiplication-naive-vs-strassen/PROOFS.md", "pairs/boolean-matrix-multiplication-naive-vs-strassen",
         "boolean-matrix-multiplication-naive-vs-strassen", "its proof.documents names that file"),
        ("pairs/assignment-brute-vs-hungarian/implementations/hungarian.py", None, "hungarian-exact-iteration-count",
         "its verify.py loads that implementation"),
        ("theorems/no-integral-form-z-half-schemes/data/3x3x6_tensor.mpl", None, "per-term-2-integrality-z-half-schemes",
         "its verify.py reads the data/ folder of that note"),
        ("experiments/2026-10-07b_count_v2_helpers.py", None, "sorting-insertion-vs-merge",
         "its check experiments/2026-10-07b_count_v2_sorting.py loads that helper"),
        ("pairs/element-distinctness-pairs-vs-sorting/entry.json", None, "longest-palindromic-substring",
         "its check experiments/2026-10-07_oracle_controls.py loads that entry"),
    ]

    def test_cases(self):
        for path, entry, slug, why in self.CASES:
            with self.subTest(path=path):
                s = sel(path)
                self.assertEqual(s["mode"], "items")
                if entry:
                    self.assertIn(entry, s["entries"], why)
                self.assertIn(slug, s["slugs"], why)


class WorkflowTests(unittest.TestCase):
    def test_unit_tests_always_run_in_full(self):
        text = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        self.assertIn("python -m unittest discover -s tests", text)
        self.assertNotIn("$TESTS", text)
        self.assertIn("python tools/make_charts.py --check", text)


if __name__ == "__main__":
    unittest.main()

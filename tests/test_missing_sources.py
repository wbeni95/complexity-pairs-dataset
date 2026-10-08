"""The generated README section "Sources we could not read" and the `missing_sources` field in index.json.

The section lists every source named in an item's provenance.missing_sources (entries and theorem notes), one row
per source, after the tables of the generated README block. It must:
* have the exact format below, with the item link, the provenance label, the full reference with its DOI/URL link,
  why the source could not be read, and what reading it would decide;
* be absent when no item lists missing sources (so the README is unchanged);
* be deterministic: rebuilding gives the same bytes, and `build_index.py --check` passes after a build;
* come with `missing_sources` in each item's provenance in index.json.

The build is tested on a synthetic item in a temporary copy of the repository layout. These tests need only the
standard library; with jsonschema installed they also check that the synthetic fixtures are valid items.

Run:  python -m unittest discover -s tests
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_index  # noqa: E402
import validate  # noqa: E402

try:
    import jsonschema
except ImportError:  # the section itself needs only the standard library
    jsonschema = None

FIB = ROOT / "pairs" / "fibonacci-naive-vs-dp"
NOTE = ROOT / "theorems" / "knuth-window-concave-length-weights"
HEADING = "### Sources we could not read"
INTRO = ("These items are marked 🟡⏳ undetermined (or ⏳ pending) because a source that might already contain the "
         "result could not be read. If you have access to one of these sources and can tell us whether it contains the "
         "result, or know an open-access copy, please open an issue.")

S_DOI = {"authors": "A. Author and B. Author", "year": 1982, "title": "On a recurrence", "venue": "J. Example 3(1)",
         "doi": "10.5555/example.1982", "status": "publisher site refused automated access",
         "needed_for": "whether the lemma on concave weights is already stated there"}
S_URL = {"authors": "C. Author", "year": 1961, "title": "A thesis", "venue": "PhD thesis, Example University",
         "url": "https://example.org/thesis", "status": "not consultable until 2050",
         "needed_for": "whether the theorem is already proved there"}
S_BOTH = {"authors": "D. Author", "year": 2001, "title": "Pipes | and  spaces", "venue": "Proc. Example",
          "doi": "10.5555/both", "url": "https://example.org/both", "status": "no open-access copy found",
          "needed_for": "whether the bound | is tight"}

ROW_DOI = ("A. Author and B. Author (1982). *On a recurrence*. J. Example 3(1). "
           "[doi:10.5555/example.1982](https://doi.org/10.5555/example.1982)")
ROW_URL = "C. Author (1961). *A thesis*. PhD thesis, Example University. [https://example.org/thesis](https://example.org/thesis)"
ROW_BOTH = ("D. Author (2001). *Pipes \\| and spaces*. Proc. Example. [doi:10.5555/both](https://doi.org/10.5555/both) "
            "[https://example.org/both](https://example.org/both)")

LITERATURE_PENDING = {"class": "literature", "bases": ["Base 1999"], "pending": True,
                      "pending_note": "A detail could not be verified in the closest source.", "missing_sources": [S_DOI]}
UNDETERMINED = {"class": "undetermined", "bases": [], "pending": True,
                "pending_note": "Two sources that might contain the result could not be read.",
                "missing_sources": [S_URL, S_BOTH]}


def section_lines(readme: str) -> list[str]:
    start = readme.index(HEADING)
    end = readme.index(build_index.TABLE_END, start)
    return readme[start:end].rstrip("\n").split("\n")


class SectionFormatTests(unittest.TestCase):
    ITEMS = [
        {"title": "Entry A", "path": "pairs/entry-a", "provenance": LITERATURE_PENDING},
        {"title": "Entry B", "path": "pairs/entry-b", "provenance": {"class": "own"}},
        {"title": "Note C", "path": "theorems/note-c", "provenance": UNDETERMINED},
    ]

    def test_exact_format(self):
        expected = "\n".join([
            HEADING,
            "",
            INTRO,
            "",
            "| Item | Label | Source | Status | What it would decide |",
            "|---|---|---|---|---|",
            f"| [Entry A](pairs/entry-a) | ⏳ Pending | {ROW_DOI} | publisher site refused automated access | "
            "whether the lemma on concave weights is already stated there |",
            f"| [Note C](theorems/note-c) | 🟡⏳ Undetermined (may be our own result) | {ROW_URL} | "
            "not consultable until 2050 | whether the theorem is already proved there |",
            f"| [Note C](theorems/note-c) | 🟡⏳ Undetermined (may be our own result) | {ROW_BOTH} | "
            "no open-access copy found | whether the bound \\| is tight |",
        ])
        self.assertEqual(build_index.missing_sources_section(self.ITEMS), expected)

    def test_absent_without_missing_sources(self):
        self.assertEqual(build_index.missing_sources_section([]), "")
        self.assertEqual(build_index.missing_sources_section([self.ITEMS[1]]), "")
        self.assertEqual(build_index.missing_sources_section(
            [{"title": "X", "path": "p/x", "provenance": {k: v for k, v in LITERATURE_PENDING.items()
                                                          if k != "missing_sources"}}]), "")

    def test_intro_asks_for_an_issue_not_for_copies(self):
        text = build_index.missing_sources_section(self.ITEMS)
        self.assertIn(INTRO, text)
        self.assertNotIn("send", text.split("| Item |")[0].lower())

    def test_deterministic(self):
        self.assertEqual(build_index.missing_sources_section(copy.deepcopy(self.ITEMS)),
                         build_index.missing_sources_section(self.ITEMS))


class GeneratedReadmeTests(unittest.TestCase):
    """build_index.main on a temporary copy: the real README.md, one entry and one theorem note."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        shutil.copy2(ROOT / "README.md", self.tmp / "README.md")
        (self.tmp / "pairs").mkdir()
        shutil.copytree(FIB, self.tmp / "pairs" / FIB.name, ignore=shutil.ignore_patterns("__pycache__"))
        (self.tmp / "theorems" / NOTE.name).mkdir(parents=True)
        shutil.copy2(NOTE / "meta.json", self.tmp / "theorems" / NOTE.name / "meta.json")
        self.entry_path = self.tmp / "pairs" / FIB.name / "entry.json"
        self.meta_path = self.tmp / "theorems" / NOTE.name / "meta.json"
        self.patches = [mock.patch.object(build_index, "REPO", self.tmp), mock.patch.object(validate, "REPO", self.tmp)]
        for p in self.patches:
            p.start()
        # Start every test from a fixed provenance without missing sources, independent of the real note's label.
        bases = json.loads(self.meta_path.read_text(encoding="utf-8"))["provenance"].get("bases", [])
        self.set_provenance(self.meta_path, {"class": "literature", "bases": bases, "pending": True,
                                             "pending_note": "Fixture: a source that might cover the result could not be read."})

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def set_provenance(self, path, prov):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["provenance"] = prov
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        if jsonschema is not None:  # the fixture must be a valid item
            schema_path = ROOT / ("schema/entry.schema.json" if path.name == "entry.json" else "theorems/meta.schema.json")
            jsonschema.validate(data, json.loads(schema_path.read_text(encoding="utf-8")))
        self.assertEqual(validate.provenance_errors(prov), [])

    def build(self, *argv) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return build_index.main(list(argv))

    def outputs(self) -> tuple[bytes, bytes]:
        return (self.tmp / "README.md").read_bytes(), (self.tmp / "index.json").read_bytes()

    def test_absent_without_missing_sources(self):
        self.assertEqual(self.build(), 0)
        readme = (self.tmp / "README.md").read_text(encoding="utf-8")
        self.assertNotIn(HEADING, readme)
        index = json.loads((self.tmp / "index.json").read_text(encoding="utf-8"))
        for item in index["entries"] + index["theorems"]:
            self.assertNotIn("missing_sources", item["provenance"])
        self.assertEqual(self.build("--check"), 0)

    def test_present_with_missing_sources(self):
        self.set_provenance(self.entry_path, LITERATURE_PENDING)
        self.set_provenance(self.meta_path, UNDETERMINED)
        self.assertEqual(self.build(), 0)
        readme = (self.tmp / "README.md").read_text(encoding="utf-8")
        entry_title = json.loads(self.entry_path.read_text(encoding="utf-8"))["title"]
        note_title = json.loads(self.meta_path.read_text(encoding="utf-8"))["title"]
        self.assertEqual(section_lines(readme), [
            HEADING,
            "",
            INTRO,
            "",
            "| Item | Label | Source | Status | What it would decide |",
            "|---|---|---|---|---|",
            f"| [{entry_title}](pairs/{FIB.name}) | ⏳ Pending | {ROW_DOI} | publisher site refused automated access | "
            "whether the lemma on concave weights is already stated there |",
            f"| [{note_title}](theorems/{NOTE.name}) | 🟡⏳ Undetermined (may be our own result) | {ROW_URL} | "
            "not consultable until 2050 | whether the theorem is already proved there |",
            f"| [{note_title}](theorems/{NOTE.name}) | 🟡⏳ Undetermined (may be our own result) | {ROW_BOTH} | "
            "no open-access copy found | whether the bound \\| is tight |",
        ])
        # after every table, inside the generated block, before the hand-written rest of the README
        self.assertLess(readme.index("### Theorems ("), readme.index(HEADING))
        self.assertLess(readme.index(HEADING), readme.index(build_index.TABLE_END))
        self.assertLess(readme.index(build_index.TABLE_END), readme.index("## License"))
        # the theorems table shows the yellow label, with its own hourglass and no separate pending flag
        table_row = next(line for line in readme.split("\n")
                         if line.startswith(f"| [{note_title}](theorems/{NOTE.name})") and "`python " in line)
        self.assertIn("🟡⏳ Undetermined (may be our own result) | `python ", table_row)
        self.assertNotIn("Pending", table_row)
        # index.json carries the sources with each item's provenance
        index = json.loads((self.tmp / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["entries"][0]["provenance"]["missing_sources"], [S_DOI])
        self.assertEqual(index["theorems"][0]["provenance"]["missing_sources"], [S_URL, S_BOTH])

    def test_deterministic(self):
        self.set_provenance(self.entry_path, LITERATURE_PENDING)
        self.set_provenance(self.meta_path, UNDETERMINED)
        self.assertEqual(self.build("--check"), 1)  # stale before the first build
        self.assertEqual(self.build(), 0)
        first = self.outputs()
        self.assertEqual(self.build("--check"), 0)
        self.assertEqual(self.build(), 0)
        self.assertEqual(self.outputs(), first)

    def test_removing_the_sources_restores_the_readme(self):
        self.assertEqual(self.build(), 0)
        before = self.outputs()
        original = self.meta_path.read_text(encoding="utf-8")
        self.set_provenance(self.meta_path, UNDETERMINED)
        self.assertEqual(self.build(), 0)
        self.assertNotEqual(self.outputs()[0], before[0])
        self.meta_path.write_text(original, encoding="utf-8", newline="\n")
        self.assertEqual(self.build(), 0)
        self.assertEqual(self.outputs(), before)


if __name__ == "__main__":
    unittest.main()

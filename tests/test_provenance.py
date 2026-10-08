"""Provenance labels: schema field, validator rules and index badges, for entries and theorem notes."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import jsonschema  # noqa: E402

import build_index  # noqa: E402
import validate  # noqa: E402

SCHEMA = json.loads((ROOT / "schema" / "entry.schema.json").read_text(encoding="utf-8"))
META_SCHEMA = json.loads((ROOT / "theorems" / "meta.schema.json").read_text(encoding="utf-8"))


def provenance_schema(schema):
    """The `provenance` subschema with the $defs it refers to (missing_source), so that it validates on its own."""
    return {"$schema": schema["$schema"], "$defs": schema["$defs"], **schema["properties"]["provenance"]}


PROV_SCHEMA = provenance_schema(SCHEMA)
META_PROV_SCHEMA = provenance_schema(META_SCHEMA)

SOURCE_DOI = {"authors": "A. Author and B. Author", "year": 1982, "title": "On a recurrence",
              "venue": "J. Example 3(1)", "doi": "10.5555/example.1982",
              "status": "publisher site refused automated access",
              "needed_for": "whether the lemma on concave weights is already stated there"}
SOURCE_URL = {"authors": "C. Author", "year": 1961, "title": "A thesis", "venue": "PhD thesis, Example University",
              "url": "https://example.org/thesis", "status": "not consultable until 2050",
              "needed_for": "whether the theorem is already proved there"}
UNDETERMINED = {"class": "undetermined", "bases": ["Base 1999"], "pending": True,
                "pending_note": "The closest source could not be read; see missing_sources.",
                "missing_sources": [SOURCE_DOI]}


class ProvenanceSchemaTests(unittest.TestCase):
    def ok(self, prov, schema=PROV_SCHEMA):
        jsonschema.validate(prov, schema)

    def bad(self, prov, schema=PROV_SCHEMA):
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(prov, schema)

    def test_accepts_the_three_classes(self):
        for cls in ("literature", "own", "own-extension"):
            self.ok({"class": cls, "bases": ["Some Author 2001"]})

    def test_rejects_unknown_class_and_fields(self):
        self.bad({"class": "mine"})
        self.bad({"class": "own", "extra": 1})
        self.bad({"bases": ["x y z"]})

    def test_both_schemas_accept_undetermined_with_missing_sources(self):
        for schema in (PROV_SCHEMA, META_PROV_SCHEMA):
            self.ok(UNDETERMINED, schema)
            self.ok({**UNDETERMINED, "missing_sources": [SOURCE_DOI, SOURCE_URL, {**SOURCE_DOI, "url": "https://x.org/a"}]},
                    schema)
            self.ok({"class": "literature", "bases": ["Base 1999"], "pending": True,
                     "pending_note": "A detail could not be verified.", "missing_sources": [SOURCE_URL]}, schema)

    def test_both_schemas_reject_malformed_missing_sources(self):
        no_link = {k: v for k, v in SOURCE_DOI.items() if k != "doi"}
        malformed = [no_link, {**SOURCE_DOI, "isbn": "978-0"}, {**SOURCE_DOI, "doi": "doi:10.5555/x"},
                     {**SOURCE_URL, "url": "example.org/thesis"}, {**SOURCE_DOI, "year": "1982"},
                     {**SOURCE_DOI, "status": "paywall"}, {**SOURCE_DOI, "needed_for": ""}]
        malformed += [{k: v for k, v in SOURCE_DOI.items() if k != field}
                      for field in ("authors", "year", "title", "venue", "status", "needed_for")]
        for schema in (PROV_SCHEMA, META_PROV_SCHEMA):
            self.bad({**UNDETERMINED, "missing_sources": []}, schema)
            for item in malformed:
                with self.subTest(item=item):
                    self.bad({**UNDETERMINED, "missing_sources": [item]}, schema)


class ProvenanceRuleTests(unittest.TestCase):
    def test_absent_is_fine(self):
        self.assertEqual(validate.provenance_errors(None), [])

    def test_extension_needs_a_base(self):
        self.assertTrue(validate.provenance_errors({"class": "own-extension"}))
        self.assertEqual(validate.provenance_errors({"class": "own-extension", "bases": ["Base 1999"]}), [])

    def test_pending_needs_a_note_and_vice_versa(self):
        self.assertTrue(validate.provenance_errors({"class": "literature", "pending": True}))
        self.assertTrue(validate.provenance_errors({"class": "literature", "pending_note": "Source X not accessible"}))
        self.assertEqual(validate.provenance_errors(
            {"class": "literature", "pending": True, "pending_note": "Source X was not accessible"}), [])

    def test_pending_is_never_an_own_label(self):
        for cls in ("own", "own-extension"):
            prov = {"class": cls, "bases": ["Base 1999"], "pending": True, "pending_note": "Source X was not accessible"}
            self.assertTrue(validate.provenance_errors(prov), cls)
            self.assertTrue(validate.provenance_errors({**prov, "missing_sources": [SOURCE_DOI]}), cls)

    def test_undetermined_with_pending_note_and_missing_sources_passes(self):
        self.assertEqual(validate.provenance_errors(UNDETERMINED), [])
        self.assertEqual(validate.provenance_errors({**UNDETERMINED, "bases": []}), [])

    def test_undetermined_needs_pending_note_and_missing_sources(self):
        for field in ("pending", "pending_note", "missing_sources"):
            prov = {k: v for k, v in UNDETERMINED.items() if k != field}
            with self.subTest(without=field):
                errors = validate.provenance_errors(prov)
                self.assertTrue(any("'undetermined'" in e and field in e.split("lacking:")[1] for e in errors), errors)
        self.assertTrue(validate.provenance_errors({**UNDETERMINED, "pending": False}))
        self.assertTrue(validate.provenance_errors({**UNDETERMINED, "missing_sources": []}))

    def test_missing_sources_need_pending(self):
        for cls in ("literature", "undetermined", "own", "own-extension"):
            prov = {"class": cls, "bases": ["Base 1999"], "missing_sources": [SOURCE_DOI]}
            with self.subTest(cls=cls):
                self.assertTrue(any("'missing_sources' given" in e for e in validate.provenance_errors(prov)))
        self.assertEqual(validate.provenance_errors(
            {"class": "literature", "bases": ["Base 1999"], "pending": True,
             "pending_note": "A detail could not be verified.", "missing_sources": [SOURCE_DOI]}), [])


class NoteRulesMatchValidatorTests(unittest.TestCase):
    """Theorem notes are checked by meta.schema.json and by validate.provenance_errors (tests/test_proof_mark.py).
    The schema's provenance rules must give the same verdict as the validator on every case."""

    CASES = [
        {"class": "literature", "bases": ["Base 1999"]},
        {"class": "own", "bases": []},
        {"class": "own-extension", "bases": ["Base 1999"]},
        {"class": "own-extension", "bases": []},
        {"class": "literature", "bases": ["Base 1999"], "pending": True, "pending_note": "Source X was not accessible"},
        {"class": "literature", "bases": ["Base 1999"], "pending": True, "pending_note": "Source X was not accessible",
         "missing_sources": [SOURCE_DOI]},
        {"class": "literature", "bases": ["Base 1999"], "missing_sources": [SOURCE_DOI]},
        {"class": "literature", "bases": ["Base 1999"], "pending": True},
        {"class": "literature", "bases": ["Base 1999"], "pending_note": "Source X was not accessible"},
        {"class": "own", "bases": [], "pending": True, "pending_note": "Source X was not accessible"},
        {"class": "own-extension", "bases": ["Base 1999"], "pending": True, "pending_note": "Source X was not accessible"},
        {"class": "own", "bases": [], "missing_sources": [SOURCE_DOI]},
        UNDETERMINED,
        {**UNDETERMINED, "bases": []},
        {**UNDETERMINED, "pending": False},
        {k: v for k, v in UNDETERMINED.items() if k != "pending"},
        {k: v for k, v in UNDETERMINED.items() if k != "pending_note"},
        {k: v for k, v in UNDETERMINED.items() if k != "missing_sources"},
    ]

    def test_same_verdict(self):
        meta = json.loads((ROOT / "theorems" / "knuth-window-concave-length-weights" / "meta.json")
                          .read_text(encoding="utf-8"))
        for prov in self.CASES:
            with self.subTest(prov=prov):
                note = copy.deepcopy(meta)
                note["provenance"] = prov
                schema_ok = jsonschema.Draft202012Validator(META_SCHEMA).is_valid(note)
                self.assertEqual(schema_ok, validate.provenance_errors(prov) == [])


class BadgeTests(unittest.TestCase):
    def test_badges(self):
        self.assertEqual(build_index.provenance_badge({"class": "literature"}), "")
        self.assertIn("Own result", build_index.provenance_badge({"class": "own"}))
        self.assertIn("Own extension", build_index.provenance_badge({"class": "own-extension", "bases": ["b"]}))
        self.assertIn("Pending", build_index.provenance_badge({"class": "literature", "pending": True}))

    def test_exact_labels(self):
        self.assertEqual(build_index.provenance_badge({"class": "own"}), " 🟠 Own result")
        self.assertEqual(build_index.provenance_badge({"class": "own-extension", "bases": ["b"]}), " 🟠 Own extension")
        self.assertEqual(build_index.provenance_badge({"class": "literature", "pending": True}), " ⏳ Pending")
        self.assertEqual(build_index.provenance_badge(UNDETERMINED), " 🟡⏳ Undetermined (may be our own result)")

    def test_undetermined_shows_one_hourglass_and_combines_with_the_check_mark(self):
        badge = build_index.provenance_badge(UNDETERMINED, True)
        self.assertEqual(badge, " ✅ Proved · 🟡⏳ Undetermined (may be our own result)")
        self.assertEqual(badge.count("⏳"), 1)
        self.assertNotIn("Pending", badge)
        self.assertEqual(build_index.provenance_badge({"class": "literature", "pending": True}, True),
                         " ✅ Proved · ⏳ Pending")


if __name__ == "__main__":
    unittest.main()

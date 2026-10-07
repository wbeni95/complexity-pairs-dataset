"""Provenance labels: schema field, validator rules and index badges."""
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
PROV_SCHEMA = SCHEMA["properties"]["provenance"]


class ProvenanceSchemaTests(unittest.TestCase):
    def ok(self, prov):
        jsonschema.validate(prov, PROV_SCHEMA)

    def bad(self, prov):
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(prov, PROV_SCHEMA)

    def test_accepts_the_three_classes(self):
        for cls in ("literature", "own", "own-extension"):
            self.ok({"class": cls, "bases": ["Some Author 2001"]})

    def test_rejects_unknown_class_and_fields(self):
        self.bad({"class": "mine"})
        self.bad({"class": "own", "extra": 1})
        self.bad({"bases": ["x y z"]})


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


class BadgeTests(unittest.TestCase):
    def test_badges(self):
        self.assertEqual(build_index.provenance_badge({"class": "literature"}), "")
        self.assertIn("Own result", build_index.provenance_badge({"class": "own"}))
        self.assertIn("Own extension", build_index.provenance_badge({"class": "own-extension", "bases": ["b"]}))
        self.assertIn("Pending", build_index.provenance_badge({"class": "literature", "pending": True}))


if __name__ == "__main__":
    unittest.main()

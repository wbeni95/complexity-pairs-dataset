"""The green check mark (✅ Proved): schema field, validator rules, index badge, and the theorem-note metadata."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import jsonschema  # noqa: E402

import build_index  # noqa: E402
import validate  # noqa: E402

ENTRY_SCHEMA = json.loads((ROOT / "schema" / "entry.schema.json").read_text(encoding="utf-8"))
META_SCHEMA = json.loads((ROOT / "theorems" / "meta.schema.json").read_text(encoding="utf-8"))
NOTE_DIR = ROOT / "theorems" / "knuth-window-concave-length-weights"
GOOD = {"documents": ["README.md"], "checks": ["verify.py"], "audit": "RL-097"}


class ProofSchemaTests(unittest.TestCase):
    def test_both_schemas_accept_a_complete_field(self):
        for schema in (ENTRY_SCHEMA, META_SCHEMA):
            jsonschema.validate(GOOD, schema["properties"]["proof"])

    def test_both_schemas_reject_incomplete_fields(self):
        for schema in (ENTRY_SCHEMA, META_SCHEMA):
            sub = schema["properties"]["proof"]
            for bad in ({"documents": ["README.md"], "checks": ["verify.py"]},
                        {"documents": [], "checks": ["verify.py"], "audit": "RL-097"},
                        {**GOOD, "audit": "RL97"},
                        {**GOOD, "extra": True}):
                with self.assertRaises(jsonschema.ValidationError):
                    jsonschema.validate(bad, sub)


class ProofRuleTests(unittest.TestCase):
    def test_absent_is_fine(self):
        self.assertEqual(validate.proof_errors(None, NOTE_DIR), [])

    def test_existing_files_and_logged_audit_pass(self):
        self.assertEqual(validate.proof_errors(GOOD, NOTE_DIR), [])

    def test_missing_or_escaping_files_fail(self):
        self.assertTrue(validate.proof_errors({**GOOD, "documents": ["PROOFS-missing.md"]}, NOTE_DIR))
        self.assertTrue(validate.proof_errors({**GOOD, "checks": ["../../../outside.py"]}, NOTE_DIR))

    def test_unlogged_audit_fails(self):
        self.assertTrue(validate.proof_errors({**GOOD, "audit": "RL-99999"}, NOTE_DIR))

    def test_staged_entries_cannot_carry_the_mark(self):
        entry_dir = next(d for d in sorted((ROOT / "staging").iterdir()) if (d / "entry.json").is_file())
        entry = json.loads((entry_dir / "entry.json").read_text(encoding="utf-8"))
        entry["proof"] = {"documents": ["README.md"], "checks": ["README.md"], "audit": "RL-097"}
        errors, _ = validate.static_checks(entry, entry_dir, jsonschema.Draft202012Validator(ENTRY_SCHEMA))
        self.assertTrue(any("staging/" in e and "check mark" in e for e in errors), errors)


class BadgeTests(unittest.TestCase):
    def test_check_mark_comes_first_and_combines(self):
        self.assertEqual(build_index.provenance_badge({"class": "literature"}, True), " ✅ Proved")
        self.assertEqual(build_index.provenance_badge({"class": "own"}, True), " ✅ Proved · 🟠 Own result")
        self.assertEqual(build_index.provenance_badge({"class": "own"}), " 🟠 Own result")


class TheoremMetaTests(unittest.TestCase):
    """Every note's meta.json is valid, matches its folder, and its verify script and proof files exist."""

    def test_every_note(self):
        notes = sorted((ROOT / "theorems").glob("*/meta.json"))
        self.assertTrue(notes)
        for meta_path in notes:
            with self.subTest(note=meta_path.parent.name):
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                jsonschema.validate(meta, META_SCHEMA)
                self.assertEqual(meta["id"], meta_path.parent.name)
                script = meta["verify"].split()[1]
                self.assertTrue((ROOT / script).is_file(), script)
                self.assertTrue((meta_path.parent / "README.md").is_file())
                self.assertEqual(validate.provenance_errors(meta["provenance"]), [])
                self.assertEqual(validate.proof_errors(meta.get("proof"), meta_path.parent), [])


if __name__ == "__main__":
    unittest.main()

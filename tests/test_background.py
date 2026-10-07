"""The optional `background` field: schema shape and its rendering in generated READMEs."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import jsonschema  # noqa: E402

import build_index  # noqa: E402

SCHEMA = json.loads((ROOT / "schema" / "entry.schema.json").read_text(encoding="utf-8"))
BG = SCHEMA["properties"]["background"]


class BackgroundSchemaTests(unittest.TestCase):
    def test_accepts_statement_with_source(self):
        jsonschema.validate([{"statement": "The decision version is NP-complete.", "source": "Karp 1972"}], BG)

    def test_rejects_missing_source_or_extra_keys(self):
        for bad in ([{"statement": "The decision version is NP-complete."}],
                    [{"statement": "The decision version is NP-complete.", "source": "Karp 1972", "proof": "x"}],
                    [{"statement": "short", "source": "Karp 1972"}]):
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.validate(bad, BG)


class BackgroundRenderingTests(unittest.TestCase):
    def test_generated_readme_shows_background_under_its_own_heading(self):
        entry_dir = next(d for d in sorted((ROOT / "staging").iterdir()) if (d / "entry.json").is_file())
        entry = json.loads((entry_dir / "entry.json").read_text(encoding="utf-8"))
        entry = copy.deepcopy(entry)
        entry["background"] = [{"statement": "No polynomial-time algorithm is known.", "source": "Example 2000"}]
        text = build_index.entry_readme(entry)
        self.assertIn("**Background** (cited; not claims of this entry", text)
        self.assertIn("- No polynomial-time algorithm is known. (Example 2000)", text)


if __name__ == "__main__":
    unittest.main()

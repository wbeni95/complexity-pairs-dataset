"""Experiment (RESEARCH_LOG RL-077): export a rank-47 scheme of the new-found class (RL-071) in the
Kauers-Moosbauer '.exp' text format, round-trip check it, and compute its factor-rank profile.

Format, as read by experiments/2026-10-07b_sources.py (parse_scheme): one product per line,
'(a11+a23)*(b12)*(c31+c44)', 1-based indices; a_ij <-> project bit 4(i-1)+(j-1); b_jk likewise;
c_rs <-> project bit 4(r-1)+(s-1), i.e. the third factor is written in the project's (k, i) order, as all
published Kauers-Moosbauer 4x4x4 GF(2) files are (research/2026-10-06c_novelty_audit.md).

Also exports RL-054's scheme (equivalent to a published Kauers-Moosbauer scheme, RL-070) the same way.

Checks: (1) the exported text parses back (with the audit's own parser) to exactly the same term set;
(2) both exact verifiers accept the parsed scheme; (3) the factor-rank profile of the representative and of
the other four saved schemes of the class are identical.

Run from the repository root:  python experiments/2026-10-06c_export_exp.py
"""
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import equivalence, gf2mm  # noqa: E402

spec = importlib.util.spec_from_file_location("src07b", ROOT / "experiments" / "2026-10-07b_sources.py")
SRC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SRC)

CLASS_DIR = ROOT / "search" / "schemes" / "rust-2026-10-06c"
REPRESENTATIVE = CLASS_DIR / "4x4x4_rank47_seed618.json"
OUT = CLASS_DIR / "4x4x4_rank47_seed618.exp"


def factor_text(mask: int, letter: str) -> str:
    entries = [f"{letter}{b // 4 + 1}{b % 4 + 1}" for b in range(16) if mask >> b & 1]
    return "(" + "+".join(entries) + ")"


def to_exp(terms) -> str:
    return "\n".join(f"{factor_text(a, 'a')}*{factor_text(b, 'b')}*{factor_text(c, 'c')}" for a, b, c in terms) + "\n"


def parse_back(text: str):
    terms = []
    for A, B, C in SRC.parse_scheme(text):
        a = sum(1 << (4 * i + j) for (i, j), v in A.items() if v % 2)
        b = sum(1 << (4 * j + k) for (j, k), v in B.items() if v % 2)
        c = sum(1 << (4 * r + s) for (r, s), v in C.items() if v % 2)
        terms.append((a, b, c))
    return terms


fmt, terms, doc = gf2mm.load_scheme(REPRESENTATIVE)
assert tuple(fmt) == (4, 4, 4) and len(terms) == 47
text = to_exp(terms)
back = parse_back(text)
print("round trip identical term set:", sorted(back) == sorted(terms))
print("verify:", gf2mm.verify(fmt, back), " verify_explicit:", gf2mm.verify_explicit(fmt, back))
OUT.write_text(text, encoding="ascii", newline="\n")
print("wrote", OUT.relative_to(ROOT).as_posix(), f"({len(text.splitlines())} products)")

profiles = {}
for p in sorted(CLASS_DIR.glob("4x4x4_rank47_*.json")):
    _, t, _ = gf2mm.load_scheme(p)
    profiles[p.name] = equivalence.factor_rank_profile(t, 4)
print("class members with identical factor-rank profile:", len(set(profiles.values())) == 1, sorted(profiles))
prof = dict(profiles[REPRESENTATIVE.name])
print("factor-rank profile of the class (sorted rank triple -> number of terms):", {"".join(map(str, k)): v for k, v in sorted(prof.items())}, "total", sum(prof.values()))

rl054_path = ROOT / "search" / "schemes" / "rust-2026-10-07" / "4x4x4_rank47_seed8.json"
_, rl054, _ = gf2mm.load_scheme(rl054_path)
p054 = dict(equivalence.factor_rank_profile(rl054, 4))
print("RL-054 scheme profile (for comparison):", {"".join(map(str, k)): v for k, v in sorted(p054.items())}, "total", sum(p054.values()))
out054 = rl054_path.with_suffix(".exp")
text054 = to_exp(rl054)
assert sorted(parse_back(text054)) == sorted(rl054) and gf2mm.verify((4, 4, 4), parse_back(text054))
out054.write_text(text054, encoding="ascii", newline="\n")
print("wrote", out054.relative_to(ROOT).as_posix(), "(round trip and verify OK)")

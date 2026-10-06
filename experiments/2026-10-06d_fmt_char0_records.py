#!/usr/bin/env python3
"""Experiment (research/2026-10-06d_exotic_formats.md, section 2.3): are the general-ring records of the target
formats usable over GF(2) as they stand?

Three published schemes, downloaded from Perminov's collection (github.com/dronperminov/FastMatrixMultiplication @
64f58a5e, the files named as sources in its schemes/status.json; cached in $FMT_CACHE like 2026-10-06d_fmt_records.py):
  * (2,4,5) rank 32, schemes/known/tensor/2x4x5_tensor.mpl (Sedoglavic's catalogue format; the catalogue cites
    AlphaEvolve 2025 for 32);
  * (3,3,6) rank 40, schemes/known/tensor/3x3x6_tensor.mpl (the catalogue cites Smirnov 2013 for 40);
  * (2,5,6) rank 47, schemes/known/alpha_evolve/2x5x6_m47_mod0.json (AlphaEvolve 2025, integer coefficients).
For each: exact verification over Q (Fractions), and the reduction mod 2 of 2-experiments/2026-10-06d_fmt_records.py
(to_gf2: per-factor rescaling by powers of 2; a term whose scalar then has negative 2-adic valuation makes the scheme
"not 2-integral as it stands"), followed by gf2mm.verify and gf2mm.verify_explicit.

Run from the repository root: FMT_CACHE=<dir> ./.venv/Scripts/python experiments/2026-10-06d_fmt_char0_records.py
RESULT (2026-10-06): printed; see the report.
"""
import hashlib
import importlib.util
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm  # noqa: E402

spec = importlib.util.spec_from_file_location("rec", ROOT / "experiments" / "2026-10-06d_fmt_records.py")
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)

BASE = "https://raw.githubusercontent.com/dronperminov/FastMatrixMultiplication/64f58a5e40806bc47847b11dd8aceec043fa895d/schemes/known/"
FILES = {"2x4x5": ((2, 4, 5), BASE + "tensor/2x4x5_tensor.mpl"),
         "3x3x6": ((3, 3, 6), BASE + "tensor/3x3x6_tensor.mpl"),
         "2x5x6": ((2, 5, 6), BASE + "alpha_evolve/2x5x6_m47_mod0.json")}

MAT = re.compile(r"Matrix\((\d+),\s*(\d+),\s*\[(.*?)\]\)", re.S)


def parse_triads(text):
    body = text[text.index("TriadSet"):]
    terms = []
    for tri in body.split("Triad([")[1:]:
        mats = []
        for rows, cols, data in MAT.findall(tri):
            vals = [Fraction(x.strip()) for x in re.sub(r"[\[\]]", " ", data).replace(" ", "").split(",") if x.strip()]
            assert len(vals) == int(rows) * int(cols)
            mats.append({(r, c): vals[r * int(cols) + c] for r in range(int(rows)) for c in range(int(cols))
                         if vals[r * int(cols) + c] != 0})
        assert len(mats) == 3
        terms.append((Fraction(1), mats[0], mats[1], mats[2]))  # C given as p x n: entry (k, i)
    return terms


def parse_perminov_json(text, fmt):
    d = json.loads(text)
    n, m, p = fmt
    terms = []
    for u, v, w in zip(d["u"], d["v"], d["w"]):
        a = {(x // m, x % m): Fraction(c) for x, c in enumerate(u) if c}
        b = {(y // p, y % p): Fraction(c) for y, c in enumerate(v) if c}
        c = {(z // n, z % n): Fraction(cc) for z, cc in enumerate(w) if cc}  # w: linear form of C^T, entry (k, i)
        terms.append((Fraction(1), a, b, c))
    return terms


def main():
    for key, (fmt, url) in FILES.items():
        rec.URL[key] = url
        data = rec.get(key)
        text = data.decode("utf-8")
        terms = parse_perminov_json(text, fmt) if url.endswith(".json") else parse_triads(text)
        q_ok = rec.verify_rational(fmt, terms, True)
        dens = sorted({x.denominator for t in terms for f in t[1:] for x in f.values()})
        g = rec.to_gf2(fmt, terms, True)
        gf2 = None if g is None else (len(g), gf2mm.verify(fmt, g), gf2mm.verify_explicit(fmt, g) if g else None)
        print(f"{key}: {len(terms)} terms; valid over Q: {q_ok}; denominators {dens}; sha256 "
              f"{hashlib.sha256(data).hexdigest()[:16]}...")
        if g is None:
            print("   mod 2: not 2-integral as it stands (a term has negative 2-adic valuation after rescaling)")
        else:
            print(f"   mod 2: {gf2[0]} non-zero terms; verify {gf2[1]}; verify_explicit {gf2[2]}")
    # Catalogue constructions for (4,6,6) and (2,3,6): Kronecker products of integer schemes, valid over GF(2).
    lib = sorted((ROOT / "search" / "schemes" / "rust-2026-10-07b").glob("2x3x3_rank15_seed1.json"))[0]
    f233, t233, _ = gf2mm.load_scheme(lib)
    fmt, terms = gf2mm.kron_scheme((2, 2, 2), gf2mm.strassen_scheme(), f233, t233)
    print(f"Strassen (x) {lib.name}: format {fmt}, rank {len(terms)}, verify {gf2mm.verify(fmt, terms)}")
    fmt, terms = gf2mm.kron_scheme((1, 1, 2), gf2mm.standard_scheme((1, 1, 2)), f233, t233)
    print(f"<1,1,2:2> (x) {lib.name}: format {fmt}, rank {len(terms)}, verify {gf2mm.verify(fmt, terms)}")


if __name__ == "__main__":
    main()

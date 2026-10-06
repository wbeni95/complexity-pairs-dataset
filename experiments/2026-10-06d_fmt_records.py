#!/usr/bin/env python3
"""Experiment (research/2026-10-06d_exotic_formats.md, section 2): best known ranks of matrix multiplication
formats (n, m, p), 2 <= n <= m <= p <= 6, over GF(2) and over general rings, from checked sources.

Sources (all downloads cached outside the repository in $FMT_CACHE, default <system temp>/cpd-2026-10-06d,
keyed by sha1(url); one connection, >= 1.5 s between requests, User-Agent of the project's research agent):
  KM   Kauers & Moosbauer, flips repository (github.com/jakobmoosbauer/flips @ e31a0a0f, archive download),
       solutions/<nmp>-<rank>-mod<0|2>.exp. Parsed and VERIFIED here.
  KW   Kauers (and Wood), meta-flip-graph repository (github.com/mkauers/matrix-multiplication @ 12c26b29, archive
       download), <nmp>/k*.exp, rational coefficients. Parsed; each file is reduced to GF(2) when it is
       2-integral (see to_gf2) and VERIFIED here; validity over Q is checked exactly as well.
  AIH  Arai, Ichikawa & Hukushima, adaptive flip graphs (github.com/Yamato-Arai/adap @ fe7b2040), data/*.m.
  MP   Moosbauer & Poole, flip graphs with symmetry (github.com/jakobmoosbauer/symmetric-flips @ 3e2d4dd8),
       schemes/*.txt (GF(2) versions and lifted versions).
  AT   AlphaTensor (github.com/google-deepmind/alphatensor @ 1949163d, algorithms/factorizations_f2.npz), the
       parser of experiments/2026-10-07b_sources.py (read without numpy).
  CAT  Sedoglavic's catalogue, https://fmm.univ-lille.fr/ (rank and reference per format; general rings; the
       page does not mark characteristic-2-only schemes).
  MMC  Matrix Multiplication Catalog, https://solven.eu/matmulcatalog/catalog.json (minimum rank per field,
       non-commutative schemes only; F2 / Z / Q claims, not re-verified here).
  PER  Perminov, FastMatrixMultiplication @ 64f58a5e, schemes/status.json (best ZT / Z / Q rank per format;
       claims, not re-verified here). Integer (Z, ZT) schemes are valid over every commutative ring, hence
       give GF(2) upper bounds too.
Lower bounds: the flattening bound max(nm, mp, pn) is computed (it holds over every field); a few better
bounds are listed as [recalled] (not checked here) in RECALLED_LOWER.

Run from the repository root:
  FMT_CACHE=<dir> ./.venv/Scripts/python experiments/2026-10-06d_fmt_records.py
Output: printed table and search/runs/2026-10-06d_records.json.

RESULT (2026-10-06 run): see the report, section 2. Every GF(2) value in the "verified" column comes from a
scheme file that passed gf2mm.verify here (and gf2mm.verify_explicit for formats with nmp <= 100).
"""
from __future__ import annotations

import collections
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import sys
import tempfile
import time
import urllib.request
import zipfile
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm  # noqa: E402

CACHE = Path(os.environ.get("FMT_CACHE", Path(tempfile.gettempdir()) / "cpd-2026-10-06d")) / "http"
UA = "complexity-pairs-dataset research agent (https://github.com/wbeni95/complexity-pairs-dataset)"

URL = {
    "KM": "https://codeload.github.com/jakobmoosbauer/flips/zip/e31a0a0f0d2577cee5da047ca7dcae0c61992e40",
    "KW": "https://codeload.github.com/mkauers/matrix-multiplication/zip/12c26b29a5458e173813911fb4f2c2865fba841e",
    "AIH": "https://codeload.github.com/Yamato-Arai/adap/zip/fe7b20408a329815c0431115b5d1861f2b564a65",
    "MP": "https://codeload.github.com/jakobmoosbauer/symmetric-flips/zip/3e2d4dd8acf831ef65c7c6b13ed787330e1e3483",
    "AT": "https://raw.githubusercontent.com/google-deepmind/alphatensor/1949163da3bef7e3eb268a3ac015fd1c2dbfc767/"
          "algorithms/factorizations_f2.npz",
    "CAT": "https://fmm.univ-lille.fr/",
    "MMC": "https://solven.eu/matmulcatalog/catalog.json",
    "PER": "https://raw.githubusercontent.com/dronperminov/FastMatrixMultiplication/"
           "64f58a5e40806bc47847b11dd8aceec043fa895d/schemes/status.json",
}

FORMATS = [(n, m, p) for n in range(2, 7) for m in range(n, 7) for p in range(m, 7)]

# [recalled] lower bounds (not checked in this session; statements as remembered, sources named for checking).
RECALLED_LOWER = {
    (2, 2, 2): (7, "Winograd 1971; Hopcroft-Kerr 1971 [recalled]; over GF(2) also our exhaustive check (RL-036)"),
    (2, 2, 3): (11, "Alekseyev 1985 [recalled]"),
    (2, 2, 4): (14, "Alekseev-Smirnov 2013 [recalled]"),
    (3, 3, 3): (19, "Blaser 2003, doi:10.1016/S0885-064X(02)00007-9 [DOI OK, value recalled]"),
    (4, 4, 4): (28, "Blaser 1999 (5/2)n^2 - 3n, doi:10.1109/SFFCS.1999.814576 [title OK, lower-order term recalled]"),
    (5, 5, 5): (48, "Blaser 1999 (5/2)n^2 - 3n [recalled]"),
    (6, 6, 6): (72, "Blaser 1999 (5/2)n^2 - 3n [recalled]"),
}

_last = [0.0]


def get(key: str) -> bytes:
    url = URL[key]
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / hashlib.sha1(url.encode()).hexdigest()
    if not path.exists():
        wait = 1.5 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
            path.write_bytes(r.read())
        _last[0] = time.time()
    data = path.read_bytes()
    SHA[key] = hashlib.sha256(data).hexdigest()
    return data


SHA: dict = {}


# --------------------------------------------------------------------------------------------- parsing

TOP = re.compile(r"\s*(?:(\()|([abc]\d\d)|(/\s*\d+)|(\d+)|([+\-*]))")


def _split_groups(line: str):
    """Split '(f1)*(f2)*(f3)[/d]', '(f1) (f2) (f3)', 'k*(f1)*a12*(f3)' etc. into (scalar, [f1, f2, f3]).
    A bare variable outside parentheses is a factor of its own; numbers and signs outside parentheses go into
    the term's scalar."""
    groups, scalar, pos = [], Fraction(1), 0
    while pos < len(line):
        mt = TOP.match(line, pos)
        if not mt:
            if line[pos:].strip() == "":
                break
            raise ValueError(f"unexpected text {line[pos:pos + 12]!r}")
        if mt.group(1):  # parenthesised factor: find the matching ')'
            depth, k = 0, mt.start(1)
            while True:
                if line[k] == "(":
                    depth += 1
                elif line[k] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            groups.append(line[mt.start(1) + 1:k])
            pos = k + 1
            continue
        if mt.group(2):
            groups.append(mt.group(2))
        elif mt.group(3):
            scalar /= int(mt.group(3)[1:].strip())
        elif mt.group(4):
            scalar *= int(mt.group(4))
        elif mt.group(5) == "-":
            scalar = -scalar
        pos = mt.end()
    return scalar, groups


VAR = re.compile(r"([+-]?)\s*(\d+(?:/\d+)?)?\s*\*?\s*([abc])(\d)(\d)")


def parse_factor(text: str, letter: str) -> dict:
    t = text.replace(" ", "")
    out = collections.defaultdict(Fraction)
    pos = 0
    for mt in VAR.finditer(t):
        if mt.group(3) != letter:
            raise ValueError(f"expected {letter}, got {mt.group(3)}")
        coef = Fraction(mt.group(2)) if mt.group(2) else Fraction(1)
        if mt.group(1) == "-":
            coef = -coef
        out[(int(mt.group(4)) - 1, int(mt.group(5)) - 1)] += coef
        pos = mt.end()
    if pos == 0:
        raise ValueError("empty factor")
    return {k: v for k, v in out.items() if v != 0}


def parse_exp(text: str):
    """Parse a scheme in the .exp text format; returns a list of (scalar, a, b, c) with dict factors."""
    terms = []
    for line in text.splitlines():
        line = line.strip().rstrip(";")
        if not line or line.startswith("#"):
            continue
        scalar, groups = _split_groups(line)
        while len(groups) == 1 and re.search(r"[abc]\d\d.*[abc]\d\d", groups[0]):  # '-(a*(b)*(c))'
            s2, groups = _split_groups(groups[0])
            scalar *= s2
        if len(groups) != 3:
            raise ValueError(f"cannot split into three factors: {line[:60]}")
        terms.append((scalar,) + tuple(parse_factor(g, L) for g, L in zip(groups, "abc")))
    return terms


def parse_mathematica(text: str, fmt):
    """Arai et al. data files: {{{A},{B},{C}}, ...} with A n x m, B m x p, C p x n (0/1 entries)."""
    import ast
    data = ast.literal_eval(text.replace("{", "[").replace("}", "]").replace("\n", ""))
    terms = []
    for A, B, C in data:
        a = {(i, j): Fraction(v) for i, row in enumerate(A) for j, v in enumerate(row) if v}
        b = {(j, k): Fraction(v) for j, row in enumerate(B) for k, v in enumerate(row) if v}
        c = {(k, i): Fraction(v) for k, row in enumerate(C) for i, v in enumerate(row) if v}
        terms.append((Fraction(1), a, b, c))
    return terms


def infer_format(terms):
    n = 1 + max(i for t in terms for (i, j) in t[1])
    m = 1 + max(max(j for t in terms for (i, j) in t[1]), max(j for t in terms for (j, k) in t[2]))
    p = 1 + max(k for t in terms for (j, k) in t[2])
    return n, m, p


def _v2(x: Fraction) -> int:
    if x == 0:
        return 10**9
    v, num, den = 0, abs(x.numerator), x.denominator
    while num % 2 == 0:
        num //= 2
        v += 1
    while den % 2 == 0:
        den //= 2
        v -= 1
    return v


def to_gf2(fmt, terms, c_ki: bool = True):
    """Reduce a rational scheme mod 2. Each factor is scaled by a power of 2 so that its coefficients are
    2-adic units or 2-adically divisible; the term scalar absorbs the powers. A term whose scalar has positive
    2-adic valuation vanishes mod 2; a negative valuation makes the scheme not 2-integral in this form (None).
    Returns bitmask terms (alpha bit i*m+j, beta bit j*p+k, gamma bit k*n+i) or None."""
    n, m, p = fmt
    out = []
    for s, a, b, c in terms:
        va, vb, vc = (min(_v2(x) for x in f.values()) for f in (a, b, c))
        vs = _v2(s) + va + vb + vc
        if vs < 0:
            return None
        if vs > 0:
            continue
        def bits(f, v, enc):
            x = 0
            for key, coef in f.items():
                if _v2(coef) == v:  # odd after scaling
                    x ^= 1 << enc(*key)
            return x
        A = bits(a, va, lambda i, j: i * m + j)
        B = bits(b, vb, lambda j, k: j * p + k)
        if c_ki:
            C = bits(c, vc, lambda k, i: k * n + i)
        else:
            C = bits(c, vc, lambda i, k: k * n + i)
        if A and B and C:
            out.append((A, B, C))
    return out


def verify_rational(fmt, terms, c_ki: bool = True) -> bool:
    """Exact Brent check over Q (Fractions), sparse: sum of scalar * a (x) b (x) c equals T<n,m,p>."""
    n, m, p = fmt
    acc = collections.defaultdict(Fraction)
    for s, a, b, c in terms:
        for (i1, j1), x in a.items():
            for (j2, k2), y in b.items():
                xy = s * x * y
                for key, z in c.items():
                    k3, i3 = key if c_ki else (key[1], key[0])
                    acc[(i1, j1, j2, k2, k3, i3)] += xy * z
    for key, v in acc.items():
        i1, j1, j2, k2, k3, i3 = key
        want = 1 if (j1 == j2 and k2 == k3 and i3 == i1) else 0
        if v != want:
            return False
    count_ones = sum(1 for key, v in acc.items() if v == 1)
    return count_ones == n * m * p


def check_gf2(fmt, terms, explicit: bool):
    ok = gf2mm.verify(fmt, terms)
    if ok and explicit:
        ok = gf2mm.verify_explicit(fmt, terms)
    return ok


def canon(fmt):
    return tuple(sorted(fmt))


def permute_to(fmt_sorted, fmt, terms):
    """Return the format as given; ranks are invariant under permutations of (n, m, p)."""
    return fmt


# --------------------------------------------------------------------------------------------- sources

def load_sources_module():
    spec = importlib.util.spec_from_file_location("src07b", ROOT / "experiments" / "2026-10-07b_sources.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def verified_files(records):
    """KM, KW, AIH, MP archives: parse and verify every scheme file of an in-range format."""
    want = set(FORMATS)
    for key, pattern in (("KM", r"/solutions/(\d)(\d)(\d)-(\d+)-(mod[02]a?)\.exp$"),
                         ("KW", r"/(\d)(\d)(\d)/(k[0-9a-f]+)\.exp$"),
                         ("AIH", r"/data/(\d)(\d)(\d)_(\d+)\.m$"),
                         ("MP", r"/schemes/(\d)(\d)(\d)m(\d+)(_lifted)?\.txt$")):
        z = zipfile.ZipFile(io.BytesIO(get(key)))
        n_files = n_ok = 0
        for name in sorted(z.namelist()):
            mt = re.search(pattern, name)
            if not mt:
                continue
            fmt = tuple(int(x) for x in mt.groups()[:3])
            if canon(fmt) not in want:
                continue
            n_files += 1
            text = z.read(name).decode("utf-8", errors="replace")
            try:
                terms = parse_mathematica(text, fmt) if key == "AIH" else parse_exp(text)
            except Exception as e:  # noqa: BLE001
                print(f"  {key} {name.split('/', 1)[1]}: PARSE FAILED ({e})")
                continue
            fmt_in = infer_format(terms)
            if fmt_in != fmt:
                print(f"  {key} {name.split('/', 1)[1]}: indices give format {fmt_in}, name says {fmt}")
                fmt = fmt_in
            explicit = fmt[0] * fmt[1] * fmt[2] <= 100
            res = {"source": key, "file": name.split("/", 1)[1], "format": fmt, "terms_in_file": len(terms)}
            gf2_rank = None
            for c_ki in (True, False):
                g = to_gf2(fmt, terms, c_ki)
                if g is not None and check_gf2(fmt, g, explicit):
                    gf2_rank = len(g)
                    res["c_convention"] = "(k,i)" if c_ki else "(i,k)"
                    break
            res["gf2_rank"] = gf2_rank
            res["gf2_verifier"] = ("verify+verify_explicit" if explicit else "verify") if gf2_rank else None
            ints = all(x.denominator == 1 for t in terms for f in t[1:] for x in f.values()) and \
                all(t[0].denominator == 1 for t in terms)
            res["integer_coefficients"] = ints
            res["valid_over_Q"] = any(verify_rational(fmt, terms, c) for c in (True, False)) \
                if key != "AIH" and not (key == "MP" and not mt.group(5)) and not (key == "KM" and "mod2" in mt.group(5)) \
                else None
            n_ok += gf2_rank is not None
            records.append(res)
        print(f"  {key}: {n_files} in-range files, {n_ok} verified over GF(2) (sha256 {SHA[key][:16]}...)")


def alphatensor(records, src):
    z = zipfile.ZipFile(io.BytesIO(get("AT")))
    for name in z.namelist():
        fmt = tuple(int(x) for x in name[:-4].split(","))
        if canon(fmt) not in set(FORMATS):
            continue
        n, m, p = fmt
        (ru, R), u = src._npy(z.read(name))[0]
        (rv, _), v = src._npy(z.read(name))[1]
        (rw, _), w = src._npy(z.read(name))[2]
        terms = []
        for r_ in range(R):
            a = sum(1 << x for x in range(ru) if u[x * R + r_] % 2)
            b = sum(1 << y for y in range(rv) if v[y * R + r_] % 2)
            c = sum(1 << zz for zz in range(rw) if w[zz * R + r_] % 2)
            if a and b and c:
                terms.append((a, b, c))
        ok = check_gf2(fmt, terms, n * m * p <= 100)
        records.append({"source": "AT", "file": f"factorizations_f2.npz:{name}", "format": fmt,
                        "terms_in_file": R, "gf2_rank": len(terms) if ok else None,
                        "gf2_verifier": ("verify+verify_explicit" if n * m * p <= 100 else "verify") if ok else None})
    print(f"  AT: GF(2) factorizations read (sha256 {SHA['AT'][:16]}...)")


def catalogue():
    t = get("CAT").decode("utf-8", errors="replace")
    out = {}
    for fmt in FORMATS:
        rows = []
        for perm in sorted(set(__import__("itertools").permutations(fmt))):
            fid = "x".join(map(str, perm))
            mt = re.search(r'<tr id="%s"(.*?)</tr>' % fid, t, flags=re.S)
            if mt:
                cells = re.findall(r'<td data-col="(\w+)">(.*?)</td>', mt.group(1), flags=re.S)
                d = {k: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", v)).replace("&nbsp;", " ").strip()
                     for k, v in cells}
                try:
                    rows.append((int(d.get("fast_tensor_rank")), fid, d.get("description", "")[:140]))
                except (TypeError, ValueError):
                    pass
        if rows:
            out[fmt] = min(rows)
    print(f"  CAT: {len(out)} of {len(FORMATS)} formats have a row (sha256 {SHA['CAT'][:16]}...)")
    return out


def mmc():
    d = json.loads(get("MMC"))
    best = collections.defaultdict(dict)
    for s in d["schemes"]:
        f = canon(s["format"])
        if f not in set(FORMATS) or s.get("commutative"):
            continue
        for fld in s.get("fields", []):
            cur = best[f].get(fld)
            if cur is None or s["rank"] < cur[0]:
                best[f][fld] = (s["rank"], s.get("source"))
    print(f"  MMC: {len(best)} formats (sha256 {SHA['MMC'][:16]}...)")
    return best


def perminov():
    d = json.loads(get("PER"))
    out = {}
    for fmt in FORMATS:
        key = "x".join(map(str, fmt))
        if key in d:
            out[fmt] = d[key]["ranks"]
    print(f"  PER: {len(out)} formats (sha256 {SHA['PER'][:16]}...)")
    return out


def threshold_rank(fmt) -> int:
    """Largest r with 3 log r / log(nmp) < log2 7 (a rank that beats Strassen's exponent via symmetrisation)."""
    N = fmt[0] * fmt[1] * fmt[2]
    r = int((N ** (math.log2(7) / 3))) + 2
    while 3 * math.log(r) / math.log(N) >= math.log2(7):
        r -= 1
    return r


def main():
    print(f"cache: <FMT_CACHE>/http ({len(FORMATS)} formats)")
    src = load_sources_module()
    records = []
    verified_files(records)
    alphatensor(records, src)
    cat, mm, per = catalogue(), mmc(), perminov()
    table = []
    for fmt in FORMATS:
        rs = [r for r in records if canon(r["format"]) == fmt and r.get("gf2_rank")]
        best_v = min((r["gf2_rank"] for r in rs), default=None)
        best_src = sorted({f"{r['source']}:{r['file'].split('/')[-1]}" for r in rs if r["gf2_rank"] == best_v})
        q_rs = [r for r in records if canon(r["format"]) == fmt and r.get("valid_over_Q")]
        best_q_v = min((r["terms_in_file"] for r in q_rs), default=None)
        z_rs = [r for r in q_rs if r.get("integer_coefficients")]
        best_z_v = min((r["terms_in_file"] for r in z_rs), default=None)
        mmc_f = mm.get(fmt, {})
        prr = per.get(fmt, {})
        claims_int = [x for x in (prr.get("Z"), prr.get("ZT"), mmc_f.get("Z", (None,))[0]) if x]
        gf2_claim = min([x for x in [best_v, mmc_f.get("F2", (None,))[0]] + claims_int if x], default=None)
        general = min([x for x in [cat.get(fmt, (None,))[0], prr.get("Q"), prr.get("Z"), prr.get("ZT"),
                                   best_q_v, mmc_f.get("Q", (None,))[0]] if x], default=None)
        flat = max(fmt[0] * fmt[1], fmt[1] * fmt[2], fmt[2] * fmt[0])
        rec_lb = RECALLED_LOWER.get(fmt)
        row = {
            "format": fmt, "naive": fmt[0] * fmt[1] * fmt[2],
            "gf2_verified_here": best_v, "gf2_verified_sources": best_src,
            "gf2_best_incl_claims": gf2_claim,
            "mmc_F2": mmc_f.get("F2"), "mmc_Z": mmc_f.get("Z"), "mmc_Q": mmc_f.get("Q"),
            "perminov": prr, "catalogue": cat.get(fmt),
            "Q_verified_here": best_q_v, "Z_verified_here": best_z_v,
            "general_best": general,
            "lower_flattening": flat, "lower_recalled": rec_lb,
            "threshold_beat_log2_7": threshold_rank(fmt),
            "exponent_at_gf2_best": round(3 * math.log(gf2_claim) / math.log(fmt[0] * fmt[1] * fmt[2]), 5)
            if gf2_claim else None,
        }
        table.append(row)
    print("\nformat   naive  GF2(verified here; sources)            GF2 best incl. claims  general best  "
          "CAT  PER(Q/Z/ZT)  MMC(F2/Z/Q)  LB(flat; recalled)  r* (beats log2 7)")
    for r in table:
        cat_s = r["catalogue"][0] if r["catalogue"] else "-"
        p = r["perminov"]
        per_s = f"{p.get('Q', '-')}/{p.get('Z', '-')}/{p.get('ZT', '-')}" if p else "-"
        mm_s = "/".join(str(r[k][0]) if r[k] else "-" for k in ("mmc_F2", "mmc_Z", "mmc_Q"))
        lb = f"{r['lower_flattening']}" + (f"; {r['lower_recalled'][0]}" if r["lower_recalled"] else "")
        print(f"{'x'.join(map(str, r['format'])):7s} {r['naive']:5d}  {str(r['gf2_verified_here']):>4s} "
              f"{','.join(r['gf2_verified_sources'])[:44]:44s} {str(r['gf2_best_incl_claims']):>5s}  "
              f"{str(r['general_best']):>6s}  {str(cat_s):>4s}  {per_s:12s} {mm_s:12s} {lb:18s} "
              f"{r['threshold_beat_log2_7']}")
    out = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "sha256": SHA, "urls": URL, "records": records,
           "table": table}
    path = ROOT / "search" / "runs" / "2026-10-06d_records.json"
    path.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"\nwrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

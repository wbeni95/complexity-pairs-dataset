"""Experiment (research/2026-10-07b_search_formats.md, section 1): best known ranks of small matrix
multiplication formats over GF(2) and over general rings, from verified sources.

What it does (run 2026-10-06; network access needed):
  1. DOIs of the cited papers, checked with tools/check_sources.lookup_doi (Crossref, then DataCite).
  2. Downloads the published scheme files of Kauers & Moosbauer, "Flip Graphs for Matrix Multiplication"
     (data repository https://github.com/jakobmoosbauer/flips, folder solutions/, file names
     "<n><m><p>-<rank>-mod<0|2>.exp"; mod2 = characteristic two, mod0 = arbitrary ground fields), parses
     them, and VERIFIES them ourselves:
       * over GF(2) (coefficients reduced mod 2, zero terms dropped) with both exact verifiers of
         search/gf2mm.py (verify and verify_explicit), and
       * for mod0 files, over the integers with exact integer arithmetic (an independent check written here).
     A file that verifies proves that a scheme of that rank exists in that setting. It does not prove that no
     better scheme is known; that comes from the catalogues in steps 3 and 4.
  3. Sedoglavic's catalogue (https://fmm.univ-lille.fr/): the best rank and the cited reference of each
     format, parsed from the HTML table (rows <tr id="NxMxP">). The catalogue does not mark
     characteristic-2-only schemes (no "Z/2", "GF(2)" or "characteristic" annotation on the page), so it is
     used for general rings only.
  4. The "Matrix Multiplication Catalog" (https://solven.eu/matmulcatalog, catalog.json, which lists the
     fields in which each stored scheme is valid, including F2): minimum rank per format and field.
  5. AlphaTensor's published GF(2) factorizations (github.com/google-deepmind/alphatensor,
     algorithms/factorizations_f2.npz), read WITHOUT numpy (the .npy format is parsed by hand; object arrays
     are unpickled by a restricted unpickler that accepts only numpy's array/dtype reconstructors) and verified
     with both exact verifiers.
  6. The MMC's cited-bounds.json (rank claims without factor matrices): non-commutative claims for our formats
     (result: only (2,2,2) 7, (3,3,3) 23 twice and (4,4,4) 49, none below the table).

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_sources.py

RESULT (2026-10-06): see the report's best-known-rank table. In short: all 13 downloaded Kauers-Moosbauer
files verify (GF(2): all 13 with both verifiers; Z: all 11 mod0 files). The 4x4x4 rank-47 file verifies over
GF(2) only; the 4x4x5 rank-60 file verifies over GF(2) only. All 20 AlphaTensor GF(2) factorizations verify
(convention c_ki), among them 4x4x4 rank 47, 3x4x5 rank 47 and 4x4x5 rank 63. No source consulted lists a 4x4x4
scheme of rank below 47 over GF(2).
"""
import ast
import collections
import io
import pickle
import struct
import zipfile
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from check_sources import lookup_doi  # noqa: E402
from search import gf2mm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {"User-Agent": "complexity-pairs-dataset source check"}
DOIS = [
    ("10.1038/s41586-022-05172-4", "AlphaTensor (Fawzi et al. 2022)"),
    ("10.1145/3597066.3597120", "Kauers & Moosbauer, Flip Graphs for Matrix Multiplication (ISSAC 2023)"),
    ("10.1137/0120004", "Hopcroft & Kerr 1971"),
    ("10.1134/S0965542513120129", "Smirnov 2013, bilinear complexity and practical algorithms"),
    ("10.1007/BF02165411", "Strassen 1969"),
    ("10.1090/S0002-9904-1976-13988-2", "Laderman 1976"),
]
FLIPS = "https://raw.githubusercontent.com/jakobmoosbauer/flips/main/solutions/"
FILES = ["223-11-mod0", "224-14-mod0", "233-15-mod0", "234-20-mod0", "244-26-mod0", "334-29-mod0",
         "335-36-mod0", "344-38-mod0", "345-47-mod0", "444-47-mod2", "444-49-mod0", "445-60-mod2", "445-62-mod0"]
FORMATS = ["2x2x2", "2x2x3", "2x2x4", "2x3x3", "2x3x4", "2x4x4", "3x3x3", "3x3x4", "3x3x5", "3x4x4", "3x4x5",
           "4x4x4", "4x4x5"]


def get(url: str) -> str:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def split_top(line: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in line:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "*" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    merged, carry = [], ""
    for p in parts:  # a bare numeric coefficient at top level multiplies the next factor
        if re.fullmatch(r"\s*[+-]?\d+\s*", p):
            carry += p.strip() + "*"
        else:
            merged.append(carry + p)
            carry = ""
    return merged


TERM = re.compile(r"([+-]?)\s*(?:(\d+)\s*\*\s*)?([abc])(\d)(\d)")


def parse_factor(text: str, letter: str) -> dict:
    t = text.strip()
    sign = 1
    if t.startswith("-("):
        sign, t = -1, t[1:]
    m = re.fullmatch(r"([+-]?\d+)\*\((.*)\)", t)
    scale = 1
    if m:
        scale, t = int(m.group(1)), "(" + m.group(2) + ")"
    if t.startswith("(") and t.endswith(")"):
        t = t[1:-1]
    if "/" in t:
        raise ValueError("fraction")
    out = {}
    for s, c, v, i, j in TERM.findall(t):
        if v != letter:
            raise ValueError(f"expected {letter}, got {v}")
        coef = scale * sign * (-1 if s == "-" else 1) * (int(c) if c else 1)
        out[(int(i) - 1, int(j) - 1)] = out.get((int(i) - 1, int(j) - 1), 0) + coef
    return {k: v for k, v in out.items() if v != 0}


def parse_scheme(text: str):
    terms = []
    for line in text.splitlines():
        line = line.strip().rstrip(";").replace(" ", "")
        if not line:
            continue
        fs = split_top(line)
        if len(fs) != 3:
            raise ValueError(f"cannot split into three factors: {line[:80]}")
        terms.append(tuple(parse_factor(f, L) for f, L in zip(fs, "abc")))
    return terms


def integer_verify(fmt, terms, c_transposed: bool) -> bool:
    n, m, p = fmt
    acc = collections.defaultdict(int)
    for A, B, C in terms:
        for x, ca in A.items():
            for y, cb in B.items():
                for z, cc in C.items():
                    acc[(x, y, z)] += ca * cb * cc
    want = {}
    for i in range(n):
        for j in range(m):
            for k in range(p):
                want[((i, j), (j, k), (i, k) if c_transposed else (k, i))] = 1
    got = {k: v for k, v in acc.items() if v != 0}
    return got == want


def to_gf2(fmt, terms, c_transposed: bool):
    n, m, p = fmt
    out = []
    for A, B, C in terms:
        a = sum(1 << (i * m + j) for (i, j), v in A.items() if v % 2)
        b = sum(1 << (j * p + k) for (j, k), v in B.items() if v % 2)
        c = 0
        for (r, s), v in C.items():
            if v % 2:
                k, i = (s, r) if c_transposed else (r, s)
                c |= 1 << (k * n + i)
        if a and b and c:
            out.append((a, b, c))
    return out


def check_flips():
    print("\n## Kauers-Moosbauer flip-graph solution files (downloaded and verified here)")
    for name in FILES:
        fmt = tuple(int(ch) for ch in name.split("-")[0])
        rank, mod = int(name.split("-")[1]), name.split("-")[2]
        text = get(FLIPS + name + ".exp")
        terms = parse_scheme(text)
        line = f"{name}: format {fmt}, products in file {len(terms)} (file name says {rank})"
        for ct in (False, True):  # c indexed (k,i) as in the cyclic convention, or (i,k)
            g = to_gf2(fmt, terms, ct)
            ok2 = gf2mm.verify(fmt, g)
            okx = gf2mm.verify_explicit(fmt, g) if ok2 else False
            okz = integer_verify(fmt, terms, ct)
            if ok2 or okz:
                line += (f" | c-index {'(i,k)' if ct else '(k,i)'}: GF(2) rank {len(g)} verify={ok2} "
                         f"verify_explicit={okx}; over Z: {okz}")
        print(line)


def check_catalogue():
    print("\n## Sedoglavic catalogue (fmm.univ-lille.fr), parsed rows")
    t = get("https://fmm.univ-lille.fr/")
    for kw in ("Z/2Z", "GF(2)", "characteristic"):
        print(f"  occurrences of {kw!r} on the page: {t.count(kw)}")
    for f in FORMATS:
        m = re.search(r'<tr id="%s"(.*?)</tr>' % f, t, flags=re.S)
        if not m:
            print(f"  {f}: no row of its own on the main page")
            continue
        cells = re.findall(r'<td data-col="(\w+)">(.*?)</td>', m.group(1), flags=re.S)
        d = {k: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", v)).replace("&nbsp;", " ").strip() for k, v in cells}
        print(f"  {f}: rank {d.get('fast_tensor_rank')}  (naive {d.get('classical_tensor_rank')})  "
              f"reference: {d.get('description')}")


def check_mmc():
    print("\n## Matrix Multiplication Catalog (solven.eu/matmulcatalog/catalog.json): minimum rank per field")
    d = json.loads(get("https://solven.eu/matmulcatalog/catalog.json"))
    want = {tuple(int(x) for x in f.split("x")) for f in FORMATS}
    best = collections.defaultdict(dict)
    for s in d["schemes"]:
        f = tuple(sorted(s["format"]))
        if f not in want:
            continue
        for fld in s.get("fields", []):
            cur = best[f].get(fld)
            if cur is None or s["rank"] < cur[0]:
                best[f][fld] = (s["rank"], s.get("source"), s.get("verified"), s.get("commutative"))
    for f in sorted(want):
        b = best.get(f, {})
        print(f"  {f}: " + "; ".join(f"{k}: rank {v[0]} ({v[1]}, verified={v[2]}, commutative={v[3]})"
                                    for k, v in sorted(b.items()) if k in ("F2", "Z", "Q")))


ALPHATENSOR_F2 = "https://raw.githubusercontent.com/google-deepmind/alphatensor/main/algorithms/factorizations_f2.npz"


class _Stub:
    """Minimal stand-in for numpy.ndarray / numpy.dtype while unpickling without numpy."""

    def __init__(self, *args):
        self.args = args
        self.state = None

    def __setstate__(self, state):
        self.state = state


def _stub_reconstruct(cls, shape, typecode):
    return _Stub()


class _NoNumpyUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module.startswith("numpy") and name == "_reconstruct":
            return _stub_reconstruct
        if module.startswith("numpy") and name in ("ndarray", "dtype"):
            return _Stub
        raise pickle.UnpicklingError(f"refusing to load {module}.{name}")


def _array_from_stub(s):
    _, shape, dtype, fortran, raw = s.state
    if dtype.args[0] != "i8" or fortran:
        raise ValueError(f"unexpected dtype {dtype.args} / fortran={fortran}")
    vals = list(struct.unpack("<%dq" % (len(raw) // 8), raw))
    return shape, vals


def _npy(data: bytes):
    """Parse one .npy member: returns a list of (shape, flat int values) for its factor matrices."""
    assert data[:6] == b"\x93NUMPY"
    hl = int.from_bytes(data[8:10], "little")
    header = ast.literal_eval(data[10:10 + hl].decode("latin1"))
    body = data[10 + hl:]
    if header["descr"] == "<i8":
        three, rows, rank = header["shape"]
        vals = list(struct.unpack("<%dq" % (len(body) // 8), body))
        size = rows * rank
        return [((rows, rank), vals[k * size:(k + 1) * size]) for k in range(three)]
    if header["descr"] == "|O":
        obj = _NoNumpyUnpickler(io.BytesIO(body)).load()
        _, shape, dtype, fortran, items = obj.state
        return [_array_from_stub(it) for it in items]
    raise ValueError(f"unexpected header {header}")


def alphatensor_scheme(key: str):
    """AlphaTensor's GF(2) factorization for key 'n,m,p' as our (alpha, beta, gamma) bitmask terms (c_ki)."""
    with urllib.request.urlopen(urllib.request.Request(ALPHATENSOR_F2, headers=UA), timeout=60) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    n, m, p = (int(x) for x in key.split(","))
    ((ru, R), u), ((rv, _), v), ((rw, _), w) = _npy(z.read(key + ".npy"))
    terms = []
    for r_ in range(R):
        a = sum(1 << x for x in range(ru) if u[x * R + r_] % 2)
        b = sum(1 << y for y in range(rv) if v[y * R + r_] % 2)
        c = sum(1 << zz for zz in range(rw) if w[zz * R + r_] % 2)  # row-major (k, i) = our bit k*n + i
        if a and b and c:
            terms.append((a, b, c))
    return terms


def check_alphatensor():
    print("\n## AlphaTensor published GF(2) factorizations (factorizations_f2.npz), verified here")
    with urllib.request.urlopen(urllib.request.Request(ALPHATENSOR_F2, headers=UA), timeout=60) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    for name in z.namelist():
        fmt = tuple(int(x) for x in name[:-4].split(","))
        n, m, p = fmt
        mats = _npy(z.read(name))
        (ru, R), u = mats[0]
        (rv, _), v = mats[1]
        (rw, _), w = mats[2]
        line = f"{name[:-4]}: factor shapes {(ru, rv, rw)} x rank {R}"
        for ct in (False, True):
            terms = []
            for r_ in range(R):
                a = sum(1 << x for x in range(ru) if u[x * R + r_] % 2)
                b = sum(1 << y for y in range(rv) if v[y * R + r_] % 2)
                c = 0
                for zz in range(rw):
                    if w[zz * R + r_] % 2:
                        if ct:  # w indexed (i, k), row-major i*p + k -> our bit k*n + i
                            i, k = divmod(zz, p)
                        else:   # w indexed (k, i), row-major k*n + i
                            k, i = divmod(zz, n)
                        c |= 1 << (k * n + i)
                if a and b and c:
                    terms.append((a, b, c))
            try:
                ok = gf2mm.verify(fmt, terms)
            except Exception:  # noqa: BLE001
                ok = False
            if ok:
                line += (f" | w-index {'(i,k)' if ct else '(k,i)'}: GF(2) rank {len(terms)} verify=True "
                         f"verify_explicit={gf2mm.verify_explicit(fmt, terms)}")
        print(line)


def check_mmc_cited():
    print("\n## MMC cited-bounds.json (rank claims without factor matrices): non-commutative claims for our formats")
    d = json.loads(get("https://solven.eu/matmulcatalog/cited-bounds.json"))
    want = {tuple(int(x) for x in f.split("x")) for f in FORMATS}
    n = 0
    for it in d.get("entries", []):
        f = tuple(sorted(it.get("format", [])))
        if f in want and not it.get("commutative"):
            n += 1
            print(f"  {f}: field {it.get('field')}, rank {it.get('rank')}, source {it.get('source')}")
    print(f"  ({n} such claims among {len(d.get('entries', []))} entries)")


def check_dois():
    print("## DOIs (Crossref / DataCite)")
    for doi, what in DOIS:
        print(f"  {doi}  [{what}]  ->  {lookup_doi(doi)}")


if __name__ == "__main__":
    check_dois()
    check_flips()
    check_catalogue()
    check_mmc()
    check_mmc_cited()
    check_alphatensor()

"""Novelty audit, step 1 (research/2026-10-06c_novelty_audit.md): collect every publicly available 4x4x4 rank-47
matrix multiplication scheme over GF(2) that we could find, convert it to the project's convention and verify it.

Project convention (search/gf2mm.py): T<4,4,4> = sum a_ij (x) b_jk (x) c_ki over GF(2); alpha bit i*4+j,
beta bit j*4+k, gamma bit k*4+i, i.e. the third factor is indexed (k, i). Every source is converted twice, once
reading its third factor as indexed (k, i) and once as (i, k) (transposed). The convention that passes the exact
verifier is recorded; for every source exactly one of the two passes (checked and printed). Accepted schemes then
also pass the second, independent exact verifier `verify_explicit`.

Sources (the git ones are pinned to the commit that was current on 2026-10-06):
  AT   AlphaTensor, github.com/google-deepmind/alphatensor @ 1949163d, algorithms/factorizations_f2.npz key
       '4,4,4' (CC BY 4.0 for data, per the repository README). The same repository's nonequivalence/ file
       holds 14,236 rank-49 factorizations in standard arithmetic (header checked here), not rank 47.
  KMg  Kauers & Moosbauer, github.com/jakobmoosbauer/flips @ e31a0a0f, solutions/444-47-mod2.exp
       (the README puts the program under GPL-3; no license is stated for the data).
  KMn  Kauers & Moosbauer, arXiv:2210.04045 ("another non-equivalent solution"), electronic version
       http://www.algebra.uni-linz.ac.at/people/mkauers/matrix-mult/s47.exp (no license stated).
  KW   Kauers' web directory http://www.algebra.uni-linz.ac.at/people/mkauers/matrix-mult/solutions/444/47/*/ and
       .../444/x47/*/ (every j*.exp file; directory listings crawled; no license or description stated).
  FM   N. F. Zaru, github.com/big-brain-zaru/FastMatrixF2 @ 5fd32f68 (MIT), every results/**/*rank47*.json
       (bit 4i+j, a (i,j), b (j,k), c (k,i) according to its README).
  MMC  Matrix Multiplication Catalog, https://solven.eu/matmulcatalog/catalog.json: every 4x4x4 entry with field
       F2 and rank 47 (its 'multiplications' and 'elements' strings are parsed).
Other places searched without a 4x4x4 rank-47 GF(2) scheme are listed in the report (Sedoglavic's catalogue,
Arai et al.'s repository, Perminov's repositories, Moosbauer-Poole's symmetric-flips, khoruzhii/flip-cpd,
khoruzhii/lita, MerlijnW70/fmm-schemes).

Downloads are cached (never in the repository): directory $NOVELTY_CACHE, default <system temp>/cpd-2026-10-06c.
Output: <cache>/collected.json (the converted, verified schemes with provenance and SHA-256 of each raw file).
Third-party scheme files are NOT added to the repository; rerun this script to re-download them.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-06c_collect.py
Deterministic given the downloaded files (the Kauers web directory is not versioned; its manifest hash is printed).

RESULT (run 2026-10-06, console copy search/runs/2026-10-06c_collect.console.txt): 99,129 files accepted
(AT 1, KMg 1, KMn 1, FM 5, MMC 1, Kauers web directory 19 + 99,101); every file verifies in exactly one reading,
always with the third factor indexed (k, i) as published; all 99,129 also pass verify_explicit. They are only 25
distinct term sets (the 99,101 x47 files are 4 term sets in many line orders). AlphaTensor publishes no second
4x4x4 rank-47 file (factorizations_r 4,4,4 has rank 49; nonequivalence/ is (14236, 49, 3, 16)).
Details: research/2026-10-06c_novelty_audit.md, section 1.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE = Path(os.environ.get("NOVELTY_CACHE", Path(tempfile.gettempdir()) / "cpd-2026-10-06c"))
UA = {"User-Agent": "complexity-pairs-dataset novelty audit (research use; polite crawler, cached)"}
FMT = (4, 4, 4)

AT_SHA = "1949163da3bef7e3eb268a3ac015fd1c2dbfc767"
KM_SHA = "e31a0a0f0d2577cee5da047ca7dcae0c61992e40"
FM_SHA = "5fd32f680acf2a7708ea6a2d40d10f7e7537957c"
AT_F2 = f"https://raw.githubusercontent.com/google-deepmind/alphatensor/{AT_SHA}/algorithms/factorizations_f2.npz"
AT_NONEQ = (f"https://raw.githubusercontent.com/google-deepmind/alphatensor/{AT_SHA}/"
            "nonequivalence/alphatensor_14236_factorizations.npz")
KM_FILE = f"https://raw.githubusercontent.com/jakobmoosbauer/flips/{KM_SHA}/solutions/444-47-mod2.exp"
KAUERS = "http://www.algebra.uni-linz.ac.at/people/mkauers/matrix-mult/"
FM_RAW = f"https://raw.githubusercontent.com/big-brain-zaru/FastMatrixF2/{FM_SHA}/"
FM_TREE = f"https://api.github.com/repos/big-brain-zaru/FastMatrixF2/git/trees/{FM_SHA}?recursive=1"
MMC = "https://solven.eu/matmulcatalog/catalog.json"


# --------------------------------------------------------------------------------------------- download cache

def fetch(url: str) -> bytes:
    """GET with an on-disk cache keyed by the URL (sha1). Retries on transient errors."""
    key = hashlib.sha1(url.encode()).hexdigest()
    path = CACHE / "http" / key
    if path.exists():
        return path.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read()
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(data)
            tmp.replace(path)
            with open(CACHE / "http" / "index.tsv", "a", encoding="utf-8") as f:
                f.write(f"{key}\t{url}\t{len(data)}\n")
            return data
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:  # noqa: PERF203
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"unreachable: {url} ({last})")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_07b():
    spec = importlib.util.spec_from_file_location("src07b", ROOT / "experiments/2026-10-07b_sources.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SRC = _load_07b()  # reuse the tested parsers of the previous round (exp format, .npy without numpy)


# --------------------------------------------------------------------------------------------- conversions

def transpose4(x: int) -> int:
    """Transpose a 4x4 bit matrix (bit 4r+c -> bit 4c+r)."""
    out = 0
    for r in range(4):
        for c in range(4):
            if (x >> (4 * r + c)) & 1:
                out |= 1 << (4 * c + r)
    return out


def both_conventions(terms_ki):
    """terms read with the third factor indexed (k, i) [as given], and with it read as (i, k) [transposed]."""
    return {"c(k,i)": list(terms_ki), "c(i,k)": [(a, b, transpose4(c)) for a, b, c in terms_ki]}


def accept(label: str, terms_ki, record: dict, out: list, log: list):
    """Try both readings of the third factor; keep the one that verifies (exactly one is expected)."""
    passing = []
    for conv, terms in both_conventions(terms_ki).items():
        try:
            ok = gf2mm.verify(FMT, terms)
        except ValueError:
            ok = False
        if ok:
            passing.append((conv, terms))
    if len(passing) != 1:
        log.append(f"{label}: {len(passing)} conventions pass verify -> NOT accepted")
        return False
    conv, terms = passing[0]
    rec = dict(record)
    rec.update({"id": label, "source_c_index": conv if conv == "c(k,i)" else "c(i,k) (transposed on import)",
                "rank": len(terms), "verify": True, "terms": sorted(list(t) for t in terms)})
    out.append(rec)
    return True


def parse_exp_text(text: str):
    """.exp format '(a11+a12)*(b21)*(c11+c22)' -> terms with the third factor read as written (c_rs -> bit 4r+s).
    Coefficients are reduced mod 2; a term with a zero factor is dropped (none occurred)."""
    raw = SRC.parse_scheme(text)
    terms = []
    for A, B, C in raw:
        a = sum(1 << (4 * i + j) for (i, j), v in A.items() if v % 2)
        b = sum(1 << (4 * j + k) for (j, k), v in B.items() if v % 2)
        c = sum(1 << (4 * r + s) for (r, s), v in C.items() if v % 2)
        if a and b and c:
            terms.append((a, b, c))
    return terms, len(raw)


# --------------------------------------------------------------------------------------------- sources

def src_alphatensor(out, log):
    data = fetch(AT_F2)
    z = zipfile.ZipFile(io.BytesIO(data))
    keys = sorted(n[:-4] for n in z.namelist())
    log.append(f"AT factorizations_f2.npz: sha256 {sha256(data)}; keys with format 4,4,4: "
               f"{[k for k in keys if k == '4,4,4']} (of {len(keys)} keys)")
    ((ru, R), u), ((rv, _), v), ((rw, _), w) = SRC._npy(z.read("4,4,4.npy"))
    terms = []
    for r_ in range(R):
        a = sum(1 << x for x in range(ru) if u[x * R + r_] % 2)
        b = sum(1 << y for y in range(rv) if v[y * R + r_] % 2)
        c = sum(1 << q for q in range(rw) if w[q * R + r_] % 2)  # w flattened row-major as written
        if a and b and c:
            terms.append((a, b, c))
    accept("AT", terms, {"source": "AlphaTensor (Fawzi et al. 2022)", "url": AT_F2, "file_sha256": sha256(data),
                         "license": "CC BY 4.0 (data), per repository README"}, out, log)
    # the standard-arithmetic file: rank of its 4,4,4 factorization (expected 49, i.e. no second rank-47 there)
    rd = fetch(AT_F2.replace("factorizations_f2.npz", "factorizations_r.npz"))
    zr = zipfile.ZipFile(io.BytesIO(rd))
    if "4,4,4.npy" in zr.namelist():
        mats = SRC._npy(zr.read("4,4,4.npy"))
        log.append(f"AT factorizations_r.npz (sha256 {sha256(rd)}): key 4,4,4 has rank {mats[0][0][1]} "
                   f"(standard arithmetic)")
    # the nonequivalence collection: read only the .npy header (shape, dtype)
    nd = fetch(AT_NONEQ)
    zz = zipfile.ZipFile(io.BytesIO(nd))
    for name in zz.namelist():
        with zz.open(name) as f:
            head = f.read(256)
        hl = int.from_bytes(head[8:10], "little")
        log.append(f"AT nonequivalence/{name}: header {head[10:10 + hl].decode('latin1').strip()} "
                   f"(sha256 of npz {sha256(nd)}) -> rank-49 factorizations, not rank 47")


def src_km_github(out, log):
    data = fetch(KM_FILE)
    terms, nraw = parse_exp_text(data.decode())
    log.append(f"KMg 444-47-mod2.exp: {nraw} products, sha256 {sha256(data)}")
    accept("KMg", terms, {"source": "Kauers & Moosbauer, flips repository (ISSAC 2023 data)", "url": KM_FILE,
                          "file_sha256": sha256(data), "license": "none stated for data (program GPL-3)"}, out, log)


def src_km_note(out, log):
    url = KAUERS + "s47.exp"
    data = fetch(url)
    terms, nraw = parse_exp_text(data.decode())
    log.append(f"KMn s47.exp: {nraw} products, sha256 {sha256(data)}")
    accept("KMn", terms, {"source": "Kauers & Moosbauer, arXiv:2210.04045, electronic version", "url": url,
                          "file_sha256": sha256(data), "license": "none stated"}, out, log)


ROW = re.compile(r'<a href="([^"]+)">[^<]*</a></td><td align="right">([^<]*)</td><td align="right">\s*([^<]*)</td>')


def listing(url):
    html = fetch(url).decode("utf-8", errors="replace")
    return [(h, d.strip(), s.strip()) for h, d, s in ROW.findall(html) if not h.startswith("/")]


def src_kauers_web(out, log):
    entries = []
    for coll in ("47", "x47"):
        base = f"{KAUERS}solutions/444/{coll}/"
        subdirs = [h for h, _, _ in listing(base) if re.fullmatch(r"[0-9a-f]{2}/", h)]
        with ThreadPoolExecutor(max_workers=4) as ex:
            lists = list(ex.map(lambda d: (d, listing(base + d)), subdirs))
        n = 0
        for d, rows in lists:
            for h, date, size in rows:
                if re.fullmatch(r"j[0-9a-f]+\.exp(-[a-z0-9]+)?", h):  # incl. 4 variant files -s1 -s2 -w1 -w2
                    entries.append((coll, base + d + h, date, size))
                    n += 1
        log.append(f"KW 444/{coll}: {len(subdirs)} subdirectories, {n} .exp files listed")
    entries.sort()
    with ThreadPoolExecutor(max_workers=4) as ex:
        blobs = list(ex.map(lambda e: fetch(e[1]), entries))
    manifest = hashlib.sha256()
    nacc = 0
    for (coll, url, date, size), data in zip(entries, blobs):
        manifest.update(f"{url}\t{sha256(data)}\n".encode())
        try:
            terms, nraw = parse_exp_text(data.decode())
        except ValueError as e:
            log.append(f"KW {url}: parse error {e}")
            continue
        name = url.rsplit("/", 1)[1].replace(".exp", "")
        if nraw != 47:
            log.append(f"KW {url}: {nraw} products (not 47), skipped")
            continue
        nacc += accept(f"KW-{coll}/{name}", terms,
                       {"source": f"Kauers web directory solutions/444/{coll}/", "url": url, "listed_date": date,
                        "file_sha256": sha256(data), "license": "none stated"}, out, log)
    log.append(f"KW: {len(entries)} files downloaded, {nacc} accepted (verify passes in exactly one convention); "
               f"manifest sha256 {manifest.hexdigest()}")


def src_fastmatrixf2(out, log):
    tree = json.loads(fetch(FM_TREE).decode())
    paths = sorted(t["path"] for t in tree["tree"]
                   if t["type"] == "blob" and t["path"].startswith("results/") and "rank47" in t["path"]
                   and t["path"].endswith(".json") and "analysis" not in t["path"])
    log.append(f"FM: rank-47 JSON files in results/: {paths}")
    for p in paths:
        data = fetch(FM_RAW + p)
        doc = json.loads(data.decode())
        bm = doc.get("scheme_bitmasks")
        if not bm:
            log.append(f"FM {p}: no scheme_bitmasks (keys {sorted(doc)[:10]}), skipped")
            continue
        if tuple(doc.get("format", [])) != FMT:
            log.append(f"FM {p}: format {doc.get('format')}, skipped")
            continue
        terms = [tuple(int(x) for x in t) for t in bm]
        accept(f"FM/{p.rsplit('/', 1)[1][:-5]}", terms,
               {"source": "Zaru, FastMatrixF2 repository (Zenodo 10.5281/zenodo.22823115)", "url": FM_RAW + p,
                "file_sha256": sha256(data), "license": "MIT"}, out, log)


def src_mmc(out, log):
    data = fetch(MMC)
    d = json.loads(data.decode())
    hits = [s for s in d["schemes"] if sorted(s["format"]) == [4, 4, 4] and s["rank"] == 47 and "F2" in s["fields"]]
    log.append(f"MMC catalog.json (sha256 {sha256(data)}): {len(hits)} entries 4x4x4 rank 47 F2: "
               f"{[(h['source'], h['file']) for h in hits]}")
    for h in hits:
        mults, elems = h["multiplications"], h["elements"]  # lists of strings in catalog.json
        if isinstance(mults, str):
            mults = json.loads(mults.replace("'", '"'))
        if isinstance(elems, str):
            elems = json.loads(elems.replace("'", '"'))
        a = {}
        b = {}
        for line in mults:
            name, rhs = line.split("=", 1)
            r = int(name.strip()[1:])
            left, right = SRC.split_top(rhs.replace(" ", ""))
            A = SRC.parse_factor(left, "a")
            B = SRC.parse_factor(right, "b")
            a[r] = sum(1 << (4 * i + j) for (i, j), v in A.items() if v % 2)
            b[r] = sum(1 << (4 * j + k) for (j, k), v in B.items() if v % 2)
        c = {r: 0 for r in a}
        for line in elems:
            name, rhs = line.split("=", 1)
            i, k = int(name.strip()[1]) - 1, int(name.strip()[2]) - 1  # c_ik = entry (i, k) of C = AB
            for tok in re.findall(r"([+-]?)\s*m(\d+)", rhs):
                c[int(tok[1])] ^= 1 << (4 * k + i)  # our gamma is indexed (k, i)
        terms = [(a[r], b[r], c[r]) for r in sorted(a) if a[r] and b[r] and c[r]]
        accept(f"MMC/{h['source']}", terms, {"source": f"Matrix Multiplication Catalog ({h['source']})",
                                              "url": MMC + " :: " + h["file"], "file_sha256": sha256(data),
                                              "license": "not stated in catalog.json"}, out, log)


def _vx(terms):
    return gf2mm.verify_explicit(FMT, [tuple(t) for t in terms])


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    print(f"cache: {CACHE}")
    out, log = [], []
    for fn in (src_alphatensor, src_km_github, src_km_note, src_fastmatrixf2, src_mmc, src_kauers_web):
        t0 = time.time()
        n0 = len(log)
        fn(out, log)
        log.append(f"[{fn.__name__} done in {time.time() - t0:.1f} s]")
        print("\n".join(log[n0:]), flush=True)
    t0 = time.time()
    with Pool(3) as pool:
        vx = pool.map(_vx, [r["terms"] for r in out], chunksize=64)
    for r, ok in zip(out, vx):
        r["verify_explicit"] = ok
    print(f"verify_explicit on {len(out)} accepted schemes: {sum(vx)} pass, {len(vx) - sum(vx)} fail "
          f"({time.time() - t0:.1f} s)")
    by_src = {}
    for r in out:
        by_src.setdefault(r["id"].split("/")[0], []).append(r)
    for k, rs in sorted(by_src.items()):
        convs = sorted({r["source_c_index"] for r in rs})
        print(f"  {k}: {len(rs)} schemes, rank(s) {sorted({r['rank'] for r in rs})}, "
              f"third factor as published: {convs}")
    # exact duplicates (same set of terms, i.e. the same scheme up to term order)
    seen = {}
    for r in out:
        seen.setdefault(tuple(map(tuple, r["terms"])), []).append(r["id"])
    dups = [v for v in seen.values() if len(v) > 1]
    print(f"distinct term sets: {len(seen)} among {len(out)} accepted schemes; groups of identical term sets: "
          f"{len(dups)}")
    for v in dups[:20]:
        print(f"  identical: {v[:6]}{' ...' if len(v) > 6 else ''}")
    (CACHE / "collected.json").write_text(json.dumps(out), encoding="utf-8")
    print(f"wrote {CACHE / 'collected.json'}")


if __name__ == "__main__":
    main()

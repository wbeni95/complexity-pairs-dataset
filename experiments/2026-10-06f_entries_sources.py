"""Experiment (research/2026-10-06f_new_entries.md): registry check of every source cited by the entries added
in round 2026-10-06f.

For each source with a DOI: Crossref record (title, year, volume, issue, pages), else DataCite (title, year).
For each arXiv id: the arXiv API (title, year). The comparison uses tools/check_sources.py's own rules
(title_matches: >= 70% word overlap; year within 1 for DOIs, 3 for arXiv; parse_venue/detail_mismatches for
volume, issue and page range), so a source that passes here also passes tools/check_sources.py.

Network etiquette: one connection at a time, at most 1 request per second to Crossref/DataCite and 1 per 3 s to
arXiv, User-Agent identifying the project. Results are cached in memory only.

Run from the repository root:  .venv/Scripts/python.exe experiments/2026-10-06f_entries_sources.py
Prints one line per source and a summary; exit status 1 if any source has a problem.
RESULT: see the report, section "Citation checks" (the printed table is copied there).
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_sources import detail_mismatches, parse_venue, title_matches  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = "complexity-pairs-dataset research agent (https://github.com/wbeni95/complexity-pairs-dataset)"
ATOM = "{http://www.w3.org/2005/Atom}"
_last = {"crossref": 0.0, "arxiv": 0.0}

# (entries citing it, source dict exactly as written into entry.json)
SOURCES = [
    # --- Horn-SAT ---
    ("horn", {"authors": "Dowling, W. F.; Gallier, J. H.", "year": 1984,
              "title": "Linear-time algorithms for testing the satisfiability of propositional Horn formulae",
              "venue": "The Journal of Logic Programming 1(3), 267-284", "doi": "10.1016/0743-1066(84)90014-1"}),
    ("horn", {"authors": "Horn, A.", "year": 1951, "title": "On sentences which are true of direct unions of algebras",
              "venue": "Journal of Symbolic Logic 16(1), 14-21", "doi": "10.2307/2268661"}),
    ("horn, xor", {"authors": "Schaefer, T. J.", "year": 1978, "title": "The complexity of satisfiability problems",
                   "venue": "Proceedings of the 10th Annual ACM Symposium on Theory of Computing (STOC 1978), 216-226",
                   "doi": "10.1145/800133.804350"}),
    ("horn", {"authors": "Cook, S. A.", "year": 1971, "title": "The complexity of theorem-proving procedures",
              "venue": "Proceedings of the 3rd Annual ACM Symposium on Theory of Computing (STOC 1971), 151-158",
              "doi": "10.1145/800157.805047"}),
    ("horn", {"authors": "Minoux, M.", "year": 1988,
              "title": "LTUR: a simplified linear-time unit resolution algorithm for Horn formulae and computer implementation",
              "venue": "Information Processing Letters 29(1), 1-12", "doi": "10.1016/0020-0190(88)90124-X"}),
    # --- XOR-SAT ---
    ("xor", {"authors": "Creignou, N.; Hermann, M.", "year": 1996,
             "title": "Complexity of generalized satisfiability counting problems",
             "venue": "Information and Computation 125(1), 1-12", "doi": "10.1006/inco.1996.0016"}),
    ("xor", {"authors": "Valiant, L. G.", "year": 1979, "title": "The complexity of enumeration and reliability problems",
             "venue": "SIAM Journal on Computing 8(3), 410-421", "doi": "10.1137/0208032"}),
    # --- Boolean matrix multiplication ---
    ("bmm", {"authors": "Fischer, M. J.; Meyer, A. R.", "year": 1971,
             "title": "Boolean matrix multiplication and transitive closure",
             "venue": "12th Annual Symposium on Switching and Automata Theory (SWAT 1971), 129-131",
             "doi": "10.1109/SWAT.1971.4"}),
    ("bmm", {"authors": "Munro, I.", "year": 1971,
             "title": "Efficient determination of the transitive closure of a directed graph",
             "venue": "Information Processing Letters 1(2), 56-58", "doi": "10.1016/0020-0190(71)90006-8"}),
    ("bmm", {"authors": "Strassen, V.", "year": 1969, "title": "Gaussian elimination is not optimal",
             "venue": "Numerische Mathematik 13, 354-356", "doi": "10.1007/BF02165411"}),
    ("bmm", {"authors": "Warshall, S.", "year": 1962, "title": "A theorem on Boolean matrices",
             "venue": "Journal of the ACM 9(1), 11-12", "doi": "10.1145/321105.321107"}),
    # --- OR / AND convolution ---
    ("orconv", {"authors": "Björklund, A.; Husfeldt, T.; Kaski, P.; Koivisto, M.", "year": 2007,
                "title": "Fourier meets Möbius: fast subset convolution",
                "venue": "Proceedings of the 39th ACM Symposium on Theory of Computing (STOC 2007), 67-74",
                "doi": "10.1145/1250790.1250801"}),
    ("orconv", {"authors": "Kennes, R.", "year": 1992, "title": "Computational aspects of the Mobius transformation of graphs",
                "venue": "IEEE Transactions on Systems, Man, and Cybernetics 22(2), 201-223", "doi": "10.1109/21.148425"}),
    # --- Hamiltonian cycles (sub-agent entry) ---
    ("hc", {"authors": "Kohn, S.; Gottlieb, A.; Kohn, M.", "year": 1977,
            "title": "A generating function approach to the traveling salesman problem",
            "venue": "Proceedings of the 1977 Annual Conference (ACM '77)", "doi": "10.1145/800179.810218"}),
    ("hc", {"authors": "Karp, R. M.", "year": 1982,
            "title": "Dynamic programming meets the principle of inclusion and exclusion",
            "venue": "Operations Research Letters 1(2), 49-51", "doi": "10.1016/0167-6377(82)90044-X"}),
    ("hc", {"authors": "Bax, E. T.", "year": 1993, "title": "Inclusion and exclusion algorithm for the Hamiltonian path problem",
            "venue": "Information Processing Letters 47(4), 203-207", "doi": "10.1016/0020-0190(93)90033-6"}),
    ("hc", {"authors": "Held, M.; Karp, R. M.", "year": 1962, "title": "A dynamic programming approach to sequencing problems",
            "venue": "Journal of the Society for Industrial and Applied Mathematics 10(1), 196-210", "doi": "10.1137/0110015"}),
    ("hc", {"authors": "Bellman, R.", "year": 1962, "title": "Dynamic programming treatment of the travelling salesman problem",
            "venue": "Journal of the ACM 9(1), 61-63", "doi": "10.1145/321105.321111"}),
    ("hc, mis", {"authors": "Karp, R. M.", "year": 1972, "title": "Reducibility among combinatorial problems",
                 "venue": "Complexity of Computer Computations, Plenum, 85-103", "doi": "10.1007/978-1-4684-2001-2_9"}),
    # --- MIS on bounded pathwidth (sub-agent entry) ---
    ("mis", {"authors": "Arnborg, S.; Proskurowski, A.", "year": 1989,
             "title": "Linear time algorithms for NP-hard problems restricted to partial k-trees",
             "venue": "Discrete Applied Mathematics 23(1), 11-24", "doi": "10.1016/0166-218X(89)90031-0"}),
    ("mis", {"authors": "Bodlaender, H. L.", "year": 1996,
             "title": "A linear-time algorithm for finding tree-decompositions of small treewidth",
             "venue": "SIAM Journal on Computing 25(6), 1305-1317", "doi": "10.1137/S0097539793251219"}),
    ("mis", {"authors": "Robertson, N.; Seymour, P. D.", "year": 1983, "title": "Graph minors. I. Excluding a forest",
             "venue": "Journal of Combinatorial Theory, Series B 35(1), 39-61", "doi": "10.1016/0095-8956(83)90079-5"}),
    # --- planar perfect matchings (sub-agent entry) ---
    ("planar", {"authors": "Kasteleyn, P. W.", "year": 1961,
                "title": "The statistics of dimers on a lattice: I. The number of dimer arrangements on a quadratic lattice",
                "venue": "Physica 27(12), 1209-1225", "doi": "10.1016/0031-8914(61)90063-5"}),
    ("planar", {"authors": "Temperley, H. N. V.; Fisher, M. E.", "year": 1961,
                "title": "Dimer problem in statistical mechanics-an exact result",
                "venue": "Philosophical Magazine 6(68), 1061-1063", "doi": "10.1080/14786436108243366"}),
    ("planar", {"authors": "Valiant, L. G.", "year": 1979, "title": "The complexity of computing the permanent",
                "venue": "Theoretical Computer Science 8(2), 189-201", "doi": "10.1016/0304-3975(79)90044-6"}),
    ("planar", {"authors": "Bareiss, E. H.", "year": 1968,
                "title": "Sylvester's identity and multistep integer-preserving Gaussian elimination",
                "venue": "Mathematics of Computation 22(103), 565-578", "doi": "10.1090/S0025-5718-1968-0226829-0"}),
    ("planar", {"authors": "Elkies, N.; Kuperberg, G.; Larsen, M.; Propp, J.", "year": 1992,
                "title": "Alternating-sign matrices and domino tilings (Part I)",
                "venue": "Journal of Algebraic Combinatorics 1(2), 111-132", "doi": "10.1023/A:1022420103267",
                "arxiv": "math/9201305"}),
]


def _get(url: str, kind: str) -> bytes | None:
    gap = 3.0 if kind == "arxiv" else 1.05
    wait = _last[kind] + gap - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            _last[kind] = time.monotonic()
            return data
        except urllib.error.HTTPError as e:
            _last[kind] = time.monotonic()
            if e.code == 404:
                return None
            time.sleep(5 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            _last[kind] = time.monotonic()
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"unreachable: {url}")


def crossref(doi: str) -> dict | None:
    raw = _get("https://api.crossref.org/works/" + urllib.parse.quote(doi), "crossref")
    if raw is None:
        return None
    msg = json.loads(raw)["message"]
    year = None
    for key in ("published-print", "published-online", "issued"):
        parts = msg.get(key, {}).get("date-parts")
        if parts and parts[0] and parts[0][0]:
            year = parts[0][0]
            break
    return {"title": (" ".join(msg.get("title") or []) + " " + " ".join(msg.get("subtitle") or [])).strip(),
            "year": year, "volume": msg.get("volume"), "issue": msg.get("issue"), "page": msg.get("page"),
            "container": " ".join(msg.get("container-title") or [])}


def datacite(doi: str) -> dict | None:
    raw = _get("https://api.datacite.org/dois/" + urllib.parse.quote(doi), "crossref")
    if raw is None:
        return None
    a = json.loads(raw)["data"]["attributes"]
    return {"title": " ".join(t.get("title", "") for t in a.get("titles") or []).strip(),
            "year": a.get("publicationYear"), "volume": None, "issue": None, "page": None, "container": "DataCite"}


def arxiv(aid: str) -> tuple[str, int] | None:
    raw = _get("https://export.arxiv.org/api/query?id_list=" + aid, "arxiv")
    root = ET.fromstring(raw)
    for entry in root.findall(f"{ATOM}entry"):
        title = " ".join(entry.findtext(f"{ATOM}title", "").split())
        year = entry.findtext(f"{ATOM}published", "")[:4]
        if title and year.isdigit():
            return title, int(year)
    return None


def main() -> int:
    problems = 0
    for tag, s in SOURCES:
        label = f"[{tag}] {s['authors'].split(';')[0]} {s['year']}"
        if "doi" in s:
            rec = crossref(s["doi"]) or datacite(s["doi"])
            if rec is None:
                problems += 1
                print(f"NOT FOUND   {label}: doi {s['doi']}")
            else:
                ok_t = title_matches(s["title"], rec["title"])
                ok_y = rec["year"] is None or abs(rec["year"] - s["year"]) <= 1
                bad = detail_mismatches(parse_venue(s.get("venue", ""), s["year"]), rec)
                status = "OK" if ok_t and ok_y and not bad else "MISMATCH"
                problems += status != "OK"
                print(f"{status:<11} {label}: doi {s['doi']}\n"
                      f"            registered: {rec['title']!r} ({rec['year']}), {rec['container']} "
                      f"vol {rec['volume']} issue {rec['issue']} pages {rec['page']}"
                      + (f"\n            details: {'; '.join(bad)}" if bad else ""))
        if "arxiv" in s:
            found = arxiv(s["arxiv"])
            ok = found is not None and title_matches(s["title"], found[0]) and abs(found[1] - s["year"]) <= 3
            problems += not ok
            print(f"{'OK' if ok else 'MISMATCH':<11} {label}: arXiv {s['arxiv']} -> {found}")
    print(f"\n{len(SOURCES)} sources, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

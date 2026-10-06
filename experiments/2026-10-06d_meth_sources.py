#!/usr/bin/env python3
"""Identifier checks for the literature cited in research/2026-10-06d_methodology.md.

Question: does every DOI / arXiv id that the methodology report cites exist, and do the registered title and
year match what the report says?

Method:
  * DOIs: Crossref (`api.crossref.org/works/<doi>`), DataCite as a fallback. At most 1 request per second.
  * arXiv ids: the arXiv API (`export.arxiv.org/api/query?id_list=...`), one id per request, at most one request
    every 3 seconds (arXiv's own guideline). One connection, no parallelism.
  * User-Agent: "complexity-pairs-dataset research agent (https://github.com/wbeni95/complexity-pairs-dataset)".
  * Title comparison: tools/check_sources.title_matches (>= 70 % word overlap, imported read-only).
  * Responses are cached outside the repository ($METH_SOURCES_CACHE, default <system temp>/cpd-2026-10-06d-meth),
    so a rerun does not query again.

Only titles and years are compared. A line "OK" means the identifier exists with that title and year; it does
NOT mean the paper's content was re-read.

Output: one line per identifier: OK / TITLE-MISMATCH / YEAR-MISMATCH / NOT-FOUND, and a summary.
Provenance: external (Crossref, DataCite, arXiv), deterministic in its inputs.

Outcome (2026-10-06, final run, 117 identifiers): 114 OK, 1 OK-NO-YEAR (10.1109/CCC.2003.1214419: title matches,
Crossref stores no year), 2 TITLE-MISMATCH because Crossref stores an EMPTY title for two Theory of Computing DOIs
(10.4086/toc.2006.v002a001, 10.4086/toc.2013.v009a004); their arXiv versions (quant-ph/0409116, 1011.3245) were
added and match. Four guessed DOIs were wrong on the first runs (they belong to other papers) and were replaced by
the records found with Crossref bibliographic search: Graffiti 1988 (90226-9 -> 90199-9), Siggers 2010
(0082-z -> 0082-3), Reichardt SODA 2011 (.43 -> .44), Kannan-Lenstra-Lovasz 1988 (0917832-6 -> 0917831-4).

Usage (repository root):
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe experiments/2026-10-06d_meth_sources.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from check_sources import title_matches  # noqa: E402

UA = "complexity-pairs-dataset research agent (https://github.com/wbeni95/complexity-pairs-dataset)"
ATOM = "{http://www.w3.org/2005/Atom}"
CACHE = Path(os.environ.get(
    "METH_SOURCES_CACHE", Path(tempfile.gettempdir()) / "cpd-2026-10-06d-meth" / "sources_cache.json"))

# (identifier, cited year, cited title). "arXiv:" prefix marks arXiv ids; everything else is a DOI.
SOURCES = [
    # ---- Area 1: discovery with an exact verifier / program search / experimental mathematics
    ("10.1145/36206.36194", 1987, "Superoptimizer: a look at the smallest program"),
    ("10.1145/2451116.2451150", 2013, "Stochastic superoptimization"),
    ("10.1038/s41586-022-05172-4", 2022, "Discovering faster matrix multiplication algorithms with reinforcement learning"),
    ("10.1038/s41586-023-06004-9", 2023, "Faster sorting algorithms discovered using deep reinforcement learning"),
    ("10.1145/3597066.3597120", 2023, "Flip graphs for matrix multiplication"),
    ("10.1016/j.jsc.2020.10.003", 2021, "New ways to multiply 3 x 3-matrices"),
    ("10.1038/s41586-023-06924-6", 2024, "Mathematical discoveries from program search with large language models"),
    ("arXiv:2506.13131", 2025, "AlphaEvolve: A coding agent for scientific and algorithmic discovery"),
    ("10.1561/2500000010", 2017, "Program Synthesis"),
    ("10.1109/FMCAD.2013.6679385", 2013, "Syntax-guided synthesis"),
    ("10.1126/science.1165893", 2009, "Distilling free-form natural laws from experimental data"),
    ("10.1126/sciadv.aay2631", 2020, "AI Feynman: A physics-inspired method for symbolic regression"),
    ("10.1073/pnas.1517384113", 2016, "Discovering governing equations from data by sparse identification of nonlinear dynamical systems"),
    ("arXiv:2207.01018", 2022, "Symbolic Regression is NP-hard"),
    ("10.1090/S0025-5718-99-00995-3", 1999, "Analysis of PSLQ, an integer relation finding algorithm"),
    ("10.1007/BF01457454", 1982, "Factoring polynomials with rational coefficients"),
    ("10.1090/S0025-5718-97-00856-9", 1997, "On the rapid computation of various polylogarithmic constants"),
    ("10.1145/178365.178368", 1994, "GFUN: a Maple package for the manipulation of generating and holonomic functions in one variable"),
    ("10.1109/TIT.1969.1054260", 1969, "Shift-register synthesis and BCH decoding"),
    ("10.1038/s41586-021-03229-4", 2021, "Generating conjectures on fundamental constants with the Ramanujan Machine"),
    ("10.1016/0012-365X(88)90199-9", 1988, "On conjectures of Graffiti"),
    ("10.1038/s41586-021-04086-x", 2021, "Advancing mathematics by guiding human intuition with AI"),
    ("arXiv:2104.14516", 2021, "Constructions in combinatorics via neural networks"),
    ("10.1016/S0195-6698(80)80051-5", 1980, "Differentiably finite power series"),
    ("10.1016/0021-8693(89)90222-6", 1989, "D-finite power series"),
    ("10.1007/978-3-7091-0445-3", 2011, "The Concrete Tetrahedron"),
    # ---- Area 2: structure that implies polynomial time / hardness theories
    ("10.1007/BF01584082", 1971, "Matroids and the greedy algorithm"),
    ("10.1007/BF02579273", 1981, "The ellipsoid method and its consequences in combinatorial optimization"),
    ("10.1006/jctb.2000.1989", 2000, "A combinatorial algorithm minimizing submodular functions in strongly polynomial time"),
    ("10.1145/502090.502096", 2001, "A combinatorial strongly polynomial algorithm for minimizing submodular functions"),
    ("10.1016/0095-8956(80)90075-1", 1980, "Decomposition of regular matroids"),
    ("10.1016/0890-5401(90)90043-H", 1990, "The monadic second-order logic of graphs. I. Recognizable sets of finite graphs"),
    ("10.1137/S0097539793251219", 1996, "A linear-time algorithm for finding tree-decompositions of small treewidth"),
    ("10.1016/0166-218X(89)90031-0", 1989, "Linear time algorithms for NP-hard problems restricted to partial k-trees"),
    ("10.1145/800133.804350", 1978, "The complexity of satisfiability problems"),
    ("10.1145/263867.263489", 1997, "Closure properties of constraints"),
    ("10.1016/S0304-3975(97)00230-2", 1998, "On the algebraic structure of combinatorial problems"),
    ("10.1137/S0097539794266766", 1998, "The computational structure of monotone monadic SNP and constraint satisfaction: a study through Datalog and group theory"),
    ("10.1109/FOCS.2017.37", 2017, "A dichotomy theorem for nonuniform CSPs"),
    ("10.1109/FOCS.2017.38", 2017, "A proof of CSP dichotomy conjecture"),
    ("10.1145/3402029", 2020, "A proof of the CSP dichotomy conjecture"),
    ("10.1007/s00012-010-0082-3", 2010, "A strong Mal'cev condition for locally finite varieties omitting the unary type"),
    ("10.1016/0095-8956(90)90132-J", 1990, "On the complexity of H-coloring"),
    ("10.1006/inco.1996.0016", 1996, "Complexity of generalized satisfiability counting problems"),
    ("10.1145/2528400", 2013, "The complexity of the counting constraint satisfaction problem"),
    ("10.1137/100811258", 2013, "An effective dichotomy for the counting constraint satisfaction problem"),
    ("10.1016/0304-3975(79)90044-6", 1979, "The complexity of computing the permanent"),
    ("10.1016/0031-8914(61)90063-5", 1961, "The statistics of dimers on a lattice"),
    ("10.1080/14786436108243366", 1961, "Dimer problem in statistical mechanics-an exact result"),
    ("10.1137/070682575", 2008, "Holographic algorithms"),
    ("10.1016/j.jcss.2010.06.005", 2011, "Holographic algorithms: from art to science"),
    ("10.1145/800157.805047", 1971, "The complexity of theorem-proving procedures"),
    ("10.1006/jcss.2000.1727", 2001, "On the complexity of k-SAT"),
    ("10.1006/jcss.2001.1774", 2001, "Which problems have strongly exponential complexity?"),
    ("10.1016/0925-7721(95)00022-2", 1995, "On a class of O(n^2) problems in computational geometry"),
    ("10.1145/3186893", 2018, "Subcubic equivalences between path, matrix, and triangle problems"),
    ("10.1137/15M1053128", 2018, "Edit distance cannot be computed in strongly subquadratic time (unless SETH is false)"),
    ("10.1016/j.tcs.2005.09.023", 2005, "A new algorithm for optimal 2-constraint satisfaction and its implications"),
    ("10.1145/321864.321877", 1975, "On the structure of polynomial time reducibility"),
    ("10.1016/0743-1066(84)90014-1", 1984, "Linear-time algorithms for testing the satisfiability of propositional Horn formulae"),
    # ---- Area 3: recognising the shape of a cost from data
    ("10.1145/1287624.1287681", 2007, "Measuring empirical computational complexity"),
    ("10.1017/CBO9780511843747", 2012, "A Guide to Experimental Algorithmics"),
    ("10.1145/2254064.2254076", 2012, "Input-sensitive profiling"),
    ("10.1017/CBO9780511801655", 2009, "Analytic Combinatorics"),
    ("10.1007/978-1-4020-9927-4", 2009, "Polygons, Polyominoes and Polycubes"),
    ("10.1214/aos/1176344136", 1978, "Estimating the dimension of a model"),
    ("10.1109/TAC.1974.1100705", 1974, "A new look at the statistical model identification"),
    ("10.1016/0022-247X(85)90209-4", 1985, "Resurrecting the asymptotics of linear recurrences"),
    ("10.1137/S0895479892230031", 1994, "A uniform approach for the fast computation of matrix-type Padé approximants"),
    ("10.1145/1008861.1008865", 1980, "A general method for solving divide-and-conquer recurrences"),
    ("arXiv:math/0501379", 2005, "On the non-holonomic character of logarithms, powers, and the nth prime function"),
    ("10.1287/moor.2.2.103", 1977, "New finite pivoting rules for the simplex method"),
    ("10.1090/S0025-5718-1988-0917831-4", 1988, "Polynomial factorization and nonrandomness of bits of algebraic and some transcendental numbers"),
    # ---- Area 4: quantum questions
    ("10.1145/502090.502097", 2001, "Quantum lower bounds by polynomials"),
    ("10.1007/BF01263419", 1994, "On the degree of boolean functions as real polynomials"),
    ("10.1145/129712.129758", 1992, "On the degree of polynomials that approximate symmetric Boolean functions (preliminary version)"),
    ("10.1006/jcss.2002.1826", 2002, "Quantum lower bounds by quantum arguments"),
    ("10.1145/1250790.1250867", 2007, "Negative weights make adversaries stronger"),
    ("10.4086/toc.2006.v002a001", 2006, "All quantum adversary methods are equivalent"),
    ("arXiv:quant-ph/0409116", 2004, "All quantum adversary methods are equivalent"),
    ("10.1137/1.9781611973082.44", 2011, "Reflections for quantum query algorithms"),
    ("10.1109/FOCS.2011.75", 2011, "Quantum query complexity of state conversion"),
    ("10.1109/CCC.2003.1214419", 2003, "Quantum query complexity and semi-definite programming"),
    ("10.1007/s00453-013-9826-8", 2015, "On exact quantum query complexity"),
    ("10.1145/2488608.2488721", 2013, "Superlinear advantage for exact quantum algorithms"),
    ("10.1016/S0304-3975(01)00144-X", 2002, "Complexity measures and decision tree complexity: a survey"),
    ("10.4007/annals.2019.190.3.6", 2019, "Induced subgraphs of hypercubes and a proof of the Sensitivity Conjecture"),
    ("10.1145/3406325.3451047", 2021, "Degree vs. approximate degree and quantum implications of Huang's sensitivity theorem"),
    ("10.1145/3106234", 2017, "Separations in query complexity based on pointer functions"),
    ("10.1145/2897518.2897644", 2016, "Separations in query complexity using cheat sheets"),
    ("10.1145/2746539.2746547", 2015, "Forrelation: a problem that optimally separates quantum from classical computing"),
    ("10.1145/3530258", 2022, "Oracle separation of BQP and PH"),
    ("10.1098/rspa.2010.0301", 2011, "Classical simulation of commuting quantum computations implies collapse of the polynomial hierarchy"),
    ("10.4086/toc.2013.v009a004", 2013, "The computational complexity of linear optics"),
    ("arXiv:1011.3245", 2010, "The computational complexity of linear optics"),
    ("arXiv:quant-ph/9807006", 1998, "The Heisenberg representation of quantum computers"),
    ("10.1103/PhysRevA.70.052328", 2004, "Improved simulation of stabilizer circuits"),
    ("10.1137/S0097539700377025", 2002, "Quantum circuits that can be simulated classically in polynomial time"),
    ("10.1103/PhysRevA.65.032325", 2002, "Classical simulation of noninteracting-fermion quantum circuits"),
    ("10.1098/rspa.2008.0189", 2008, "Matchgates and classical simulation of quantum circuits"),
    ("10.1103/PhysRevLett.91.147902", 2003, "Efficient classical simulation of slightly entangled quantum computations"),
    ("10.1098/rspa.2002.1097", 2003, "On the role of entanglement in quantum-computational speed-up"),
    ("10.1137/050644756", 2008, "Simulating quantum computation by contracting tensor networks"),
    ("10.1145/3313276.3316310", 2019, "A quantum-inspired classical algorithm for recommendation systems"),
    ("10.1145/3549524", 2022, "Sampling-based sublinear low-rank matrix arithmetic framework for dequantizing quantum machine learning"),
    ("10.1038/nphys3272", 2015, "Read the fine print"),
    ("10.1145/237814.237866", 1996, "A fast quantum mechanical algorithm for database search"),
    ("10.1137/S0097539796300933", 1997, "Strengths and weaknesses of quantum computing"),
    ("10.1103/PhysRevA.60.2746", 1999, "Grover's quantum searching algorithm is optimal"),
    ("10.1145/1008731.1008735", 2004, "Quantum lower bounds for the collision and the element distinctness problems"),
    ("10.1137/0220062", 1991, "CREW PRAMs and decision trees"),
    ("10.1109/SFCS.1977.24", 1977, "Probabilistic computations: toward a unified measure of complexity"),
    ("10.1007/BF01192527", 1995, "On rank vs. communication complexity"),
    ("arXiv:quant-ph/0403168", 2004, "Exact quantum query complexity for total Boolean functions"),
    ("arXiv:1302.1235", 2013, "Exact quantum query complexity of EXACT and THRESHOLD"),
    ("10.1137/S0097539796298637", 1997, "On the power of quantum computation"),
    ("10.1137/S0097539795293172", 1997, "Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum computer"),
]


def _load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


_last = {"crossref": 0.0, "arxiv": 0.0}


def _get(url: str, kind: str) -> bytes | None:
    gap = 3.05 if kind == "arxiv" else 1.05
    for attempt in range(3):
        wait = _last[kind] + gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last[kind] = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            ra = e.headers.get("Retry-After", "")
            time.sleep(min(int(ra) if ra.isdigit() else 5 * 2 ** attempt, 60))
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(3 * (attempt + 1))
    return b"__UNREACHABLE__"


def lookup(ident: str, cache: dict) -> dict:
    if ident in cache:
        return cache[ident]
    rec: dict = {"found": False}
    if ident.startswith("arXiv:"):
        aid = ident[len("arXiv:"):]
        raw = _get("https://export.arxiv.org/api/query?id_list=" + urllib.parse.quote(aid), "arxiv")
        if raw and raw != b"__UNREACHABLE__":
            root = ET.fromstring(raw)
            for entry in root.findall(f"{ATOM}entry"):
                title = " ".join(entry.findtext(f"{ATOM}title", "").split())
                pub = entry.findtext(f"{ATOM}published", "")
                if title and pub:
                    rec = {"found": True, "title": title, "year": int(pub[:4]), "registry": "arXiv"}
        elif raw == b"__UNREACHABLE__":
            rec = {"found": False, "unreachable": True}
    else:
        raw = _get("https://api.crossref.org/works/" + urllib.parse.quote(ident), "crossref")
        if raw and raw != b"__UNREACHABLE__":
            msg = json.loads(raw)["message"]
            year = None
            for key in ("published-print", "published-online", "issued"):
                parts = msg.get(key, {}).get("date-parts")
                if parts and parts[0] and parts[0][0]:
                    year = parts[0][0]
                    break
            title = (" ".join(msg.get("title") or []) + " " + " ".join(msg.get("subtitle") or [])).strip()
            rec = {"found": True, "title": title, "year": year, "registry": "Crossref",
                   "container": " ".join(msg.get("container-title") or [])}
        else:
            raw = _get("https://api.datacite.org/dois/" + urllib.parse.quote(ident), "crossref")
            if raw and raw != b"__UNREACHABLE__":
                attrs = json.loads(raw)["data"]["attributes"]
                title = " ".join(t.get("title", "") for t in attrs.get("titles") or []).strip()
                rec = {"found": True, "title": title, "year": attrs.get("publicationYear"), "registry": "DataCite"}
    if not rec.get("unreachable"):
        cache[ident] = rec
    return rec


def main() -> int:
    cache = _load_cache()
    counts: dict[str, int] = {}
    for ident, year, title in SOURCES:
        rec = lookup(ident, cache)
        _save_cache(cache)
        if not rec.get("found"):
            status = "UNREACHABLE" if rec.get("unreachable") else "NOT-FOUND"
            detail = ""
        else:
            t_ok = title_matches(title, rec["title"])
            y_ok = rec.get("year") is None or abs(int(rec["year"]) - year) <= 0
            if t_ok and y_ok:
                status = "OK" if rec.get("year") is not None else "OK-NO-YEAR"
            elif t_ok:
                status = "YEAR-MISMATCH"
            else:
                status = "TITLE-MISMATCH"
            detail = f"  [{rec['registry']}: {rec['title'][:110]!r}, {rec.get('year')}]"
        counts[status] = counts.get(status, 0) + 1
        print(f"{status:15s} {ident:38s} {year}  {title[:70]}{detail if status != 'OK' else ''}")
    print("\nsummary:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())), f"(total {len(SOURCES)})")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())

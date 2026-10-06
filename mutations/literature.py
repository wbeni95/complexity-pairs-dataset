"""References for the mutation pilot and their verification against Crossref / DataCite / arXiv.

Every DOI or arXiv id below was written from memory ([recalled]) and is only labelled [DOI OK] / [arXiv id OK] after
`verify_all()` found a record whose title matches (tools/check_sources.title_matches, imported unchanged) and whose
year is within one of the cited year. Entries without an identifier stay [recalled].

Etiquette (RL-073 and the brief): one connection, sequential requests, at most 1 request per second to Crossref and
DataCite and at most 1 per 3 seconds to arXiv, with an identifying User-Agent. Nothing is crawled.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
USER_AGENT = "complexity-pairs-dataset research agent (https://github.com/wbeni95/complexity-pairs-dataset)"
ATOM = "{http://www.w3.org/2005/Atom}"

REFS = {
    "strassen1969": dict(authors="Strassen, V.", year=1969, title="Gaussian elimination is not optimal",
                         doi="10.1007/BF02165411"),
    "fischer-meyer1971": dict(authors="Fischer, M. J.; Meyer, A. R.", year=1971,
                              title="Boolean matrix multiplication and transitive closure", doi="10.1109/SWAT.1971.4"),
    "munro1971": dict(authors="Munro, I.", year=1971,
                      title="Efficient determination of the transitive closure of a directed graph",
                      doi="10.1016/0020-0190(71)90006-8"),
    "yuval1976": dict(authors="Yuval, G.", year=1976,
                      title="An algorithm for finding all shortest paths using N^2.81 infinite-precision multiplications",
                      doi="10.1016/0020-0190(76)90085-5"),
    "warshall1962": dict(authors="Warshall, S.", year=1962, title="A theorem on Boolean matrices",
                         doi="10.1145/321105.321107"),
    "floyd1962": dict(authors="Floyd, R. W.", year=1962, title="Algorithm 97: Shortest path", doi="10.1145/367766.368168"),
    "lehmann1977": dict(authors="Lehmann, D. J.", year=1977, title="Algebraic structures for transitive closure",
                        doi="10.1016/0304-3975(77)90056-1"),
    "mohri2002": dict(authors="Mohri, M.", year=2002,
                      title="Semiring frameworks and algorithms for shortest-distance problems",
                      note="Journal of Automata, Languages and Combinatorics 7(3); no DOI"),
    "pollack1960": dict(authors="Pollack, M.", year=1960, title="The maximum capacity through a network",
                        doi="10.1287/opre.8.5.733"),
    "vassilevska-williams-yuster2009": dict(authors="Vassilevska, V.; Williams, R.; Yuster, R.", year=2009,
                                            title="All pairs bottleneck paths and max-min matrix products in truly "
                                                  "subcubic time", doi="10.4086/toc.2009.v005a009",
                                            note="Theory of Computing 5. Crossref holds the DOI without a title, so "
                                                 "the title cannot be checked; the STOC 2007 version is verified."),
    "vassilevska-williams-yuster2007": dict(authors="Vassilevska, V.; Williams, R.; Yuster, R.", year=2007,
                                            title="All-pairs bottleneck paths for general graphs in truly sub-cubic "
                                                  "time", doi="10.1145/1250790.1250876",
                                            note="DOI found by a Crossref bibliographic query on 2026-10-06 "
                                                 "(experiments/2026-10-06d_mut_literature.py)"),
    "duan-pettie2009": dict(authors="Duan, R.; Pettie, S.", year=2009,
                            title="Fast algorithms for (max, min)-matrix multiplication and bottleneck shortest paths",
                            doi="10.1137/1.9781611973068.43",
                            note="first recalled as ...068.42, which Crossref resolves to a different paper "
                                 "('Inserting a Vertex into a Planar Graph'); corrected by a Crossref query"),
    "williams2018": dict(authors="Williams, R. R.", year=2018,
                         title="Faster all-pairs shortest paths via circuit complexity", doi="10.1137/15M1024524"),
    "dijkstra1959": dict(authors="Dijkstra, E. W.", year=1959, title="A note on two problems in connexion with graphs",
                         doi="10.1007/BF01386390"),
    "camerini1978": dict(authors="Camerini, P. M.", year=1978,
                         title="The min-max spanning tree problem and some extensions",
                         doi="10.1016/0020-0190(78)90030-3"),
    "edmonds1971": dict(authors="Edmonds, J.", year=1971, title="Matroids and the greedy algorithm",
                        doi="10.1007/BF01584082"),
    "karp1972": dict(authors="Karp, R. M.", year=1972, title="Reducibility among combinatorial problems",
                     doi="10.1007/978-1-4684-2001-2_9"),
    "valiant1979": dict(authors="Valiant, L. G.", year=1979, title="The complexity of computing the permanent",
                        doi="10.1016/0304-3975(79)90044-6"),
    "kuhn1955": dict(authors="Kuhn, H. W.", year=1955, title="The Hungarian method for the assignment problem",
                     doi="10.1002/nav.3800020109"),
    "pollard1971": dict(authors="Pollard, J. M.", year=1971, title="The fast Fourier transform in a finite field",
                        doi="10.1090/S0025-5718-1971-0301966-0"),
    "cooley-tukey1965": dict(authors="Cooley, J. W.; Tukey, J. W.", year=1965,
                             title="An algorithm for the machine calculation of complex Fourier series",
                             doi="10.1090/S0025-5718-1965-0178586-1"),
    "bellman1962": dict(authors="Bellman, R.", year=1962,
                        title="Dynamic programming treatment of the travelling salesman problem",
                        doi="10.1145/321105.321111"),
    "held-karp1962": dict(authors="Held, M.; Karp, R. M.", year=1962,
                          title="A dynamic programming approach to sequencing problems", doi="10.1137/0110015"),
    "knuth1971": dict(authors="Knuth, D. E.", year=1971, title="Optimum binary search trees", doi="10.1007/BF00264289"),
    "yao1980": dict(authors="Yao, F. F.", year=1980, title="Efficient dynamic programming using quadrangle inequalities",
                    doi="10.1145/800141.804691"),
    "bender-farach-colton2000": dict(authors="Bender, M. A.; Farach-Colton, M.", year=2000,
                                     title="The LCA problem revisited", doi="10.1007/10719839_9"),
    "shamos-hoey1975": dict(authors="Shamos, M. I.; Hoey, D.", year=1975, title="Closest-point problems",
                            doi="10.1109/SFCS.1975.8"),
    "preparata-shamos1985": dict(authors="Preparata, F. P.; Shamos, M. I.", year=1985,
                                 title="Computational Geometry: An Introduction", doi="10.1007/978-1-4612-1098-6"),
    "gondran-minoux2008": dict(authors="Gondran, M.; Minoux, M.", year=2008,
                               title="Graphs, Dioids and Semirings: New Models and Algorithms",
                               doi="10.1007/978-0-387-75450-5"),
    "kruskal1956": dict(authors="Kruskal, J. B.", year=1956,
                        title="On the shortest spanning subtree of a graph and the traveling salesman problem",
                        doi="10.1090/S0002-9939-1956-0078686-7"),
    "prim1957": dict(authors="Prim, R. C.", year=1957, title="Shortest connection networks and some generalizations",
                     doi="10.1002/j.1538-7305.1957.tb01515.x"),
    "bentley1984": dict(authors="Bentley, J.", year=1984, title="Programming pearls: algorithm design techniques",
                        doi="10.1145/358234.381162"),
    "karatsuba-ofman1962": dict(authors="Karatsuba, A.; Ofman, Yu.", year=1962,
                                title="Multiplication of many-digital numbers by automatic computers",
                                note="Doklady Akad. Nauk SSSR 145(2); no DOI"),
    "ryser1963": dict(authors="Ryser, H. J.", year=1963, title="Combinatorial Mathematics", note="book; no DOI"),
    "yates1937": dict(authors="Yates, F.", year=1937, title="The design and analysis of factorial experiments",
                      note="Imperial Bureau of Soil Science; no DOI"),
    "kirchhoff1847": dict(authors="Kirchhoff, G.", year=1847,
                          title="Ueber die Auflösung der Gleichungen, auf welche man bei der Untersuchung der linearen "
                                "Vertheilung galvanischer Ströme geführt wird", doi="10.1002/andp.18471481202"),
    "garey-johnson1979": dict(authors="Garey, M. R.; Johnson, D. S.", year=1979,
                              title="Computers and Intractability: A Guide to the Theory of NP-Completeness",
                              note="book; no DOI"),
    "knuth-taocp2": dict(authors="Knuth, D. E.", year=1997, title="The Art of Computer Programming, Vol. 2: "
                         "Seminumerical Algorithms (3rd ed.), section 4.6.3", note="book; no DOI"),
    "hu1961": dict(authors="Hu, T. C.", year=1961, title="The maximum capacity route problem", doi="10.1287/opre.9.6.898"),
}


def _title_matches():
    spec = importlib.util.spec_from_file_location("cpairs_tools_check_sources", REPO / "tools" / "check_sources.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(REPO / "tools"))
    stdout = sys.stdout
    spec.loader.exec_module(mod)
    sys.stdout = stdout
    return mod.title_matches


_last = {"crossref": 0.0, "datacite": 0.0, "arxiv": 0.0}
_GAP = {"crossref": 1.05, "datacite": 1.05, "arxiv": 3.05}


def _get(url: str, service: str) -> bytes | None:
    wait = _last[service] + _GAP[service] - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    finally:
        _last[service] = time.monotonic()


def _crossref(doi):
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
    title = (" ".join(msg.get("title") or []) + " " + " ".join(msg.get("subtitle") or [])).strip()
    return title, year


def _datacite(doi):
    raw = _get("https://api.datacite.org/dois/" + urllib.parse.quote(doi), "datacite")
    if raw is None:
        return None
    attrs = json.loads(raw)["data"]["attributes"]
    return " ".join(t.get("title", "") for t in attrs.get("titles") or []).strip(), attrs.get("publicationYear")


def _arxiv(aid):
    raw = _get("https://export.arxiv.org/api/query?id_list=" + aid, "arxiv")
    root = ET.fromstring(raw)
    for entry in root.findall(f"{ATOM}entry"):
        title = " ".join(entry.findtext(f"{ATOM}title", "").split())
        year = int(entry.findtext(f"{ATOM}published", "0000")[:4])
        return title, year
    return None


def verify_all(keys=None) -> list[dict]:
    match = _title_matches()
    rows = []
    for key, ref in REFS.items():
        if keys and key not in keys:
            continue
        row = {"key": key, **ref, "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        try:
            if "doi" in ref:
                found = _crossref(ref["doi"])
                service = "crossref"
                if found is None:
                    found = _datacite(ref["doi"])
                    service = "datacite"
                if found is None:
                    row["status"] = "DOI NOT FOUND"
                else:
                    t, y = found
                    row.update(found_title=t, found_year=y, service=service)
                    ok_t = bool(t) and match(ref["title"], t)
                    ok_y = y is not None and abs(int(y) - ref["year"]) <= 1
                    row["status"] = "DOI OK" if (ok_t and ok_y) else f"MISMATCH (title {ok_t}, year {ok_y})"
            elif "arxiv" in ref:
                found = _arxiv(ref["arxiv"])
                if found is None:
                    row["status"] = "ARXIV NOT FOUND"
                else:
                    t, y = found
                    row.update(found_title=t, found_year=y, service="arxiv")
                    row["status"] = "arXiv id OK" if match(ref["title"], t) else "MISMATCH"
            else:
                row["status"] = "recalled (no identifier)"
        except Exception as e:  # noqa: BLE001
            row["status"] = f"ERROR {type(e).__name__}: {e}"
        rows.append(row)
    return rows


def label(key: str, rows_by_key: dict) -> str:
    r = rows_by_key.get(key)
    if r is None:
        return "[recalled]"
    s = r["status"]
    if s == "DOI OK":
        return "[DOI OK]"
    if s == "arXiv id OK":
        return "[arXiv id OK]"
    return "[recalled]"


def _strip(s):
    return re.sub(r"\s+", " ", s)

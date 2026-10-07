"""Experiment (research/2026-10-06i_new_entries.md): registry check of every source cited by the entries
added in round 2026-10-06i (linear ordering, multi-pattern matching, 3XOR).

For each DOI: Crossref record (title, year, volume, issue, pages), else DataCite (title, year). For each arXiv id:
the arXiv API (title, year), and the abstract is printed for the arXiv sources whose content the entries cite
(SHOW_ABSTRACT). The comparison uses tools/check_sources.py's own rules (title_matches: >= 70% word overlap; year
within 1 for DOIs, 3 for arXiv; parse_venue/detail_mismatches for volume, issue and page range).

Network etiquette: one connection at a time, at most 1 request per second to Crossref/DataCite and 1 per 3 s to
arXiv, User-Agent identifying the project.

Run from the repository root:  .venv/Scripts/python.exe experiments/2026-10-06i_sources.py
Prints one line per source and a summary; exit status 1 if any source has a problem.
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
SHOW_ABSTRACT = {"1804.11086", "1305.3827"}


def _load_sources():
    """Every source of the three entries, exactly as written in their entry.json files."""
    out, seen = [], {}
    for entry in ("linear-ordering-enumeration-vs-subset-dp", "multi-pattern-matching-naive-vs-aho-corasick",
                  "three-xor-all-triples-vs-patricia-trie"):
        path = ROOT / "pairs" / entry / "entry.json"
        if not path.is_file():  # an entry folder that is not present in this checkout is skipped
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for s in data["sources"]:
            key = s.get("doi") or s.get("arxiv") or s["title"]
            if key in seen:
                seen[key][0].append(entry.split("-")[0])
                continue
            seen[key] = ([entry.split("-")[0]], s)
            out.append(seen[key])
    return [(", ".join(tags), s) for tags, s in out]


SOURCES = _load_sources()


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


def arxiv_full(aid: str):
    raw = _get("https://export.arxiv.org/api/query?id_list=" + aid, "arxiv")
    root = ET.fromstring(raw)
    for entry in root.findall(f"{ATOM}entry"):
        title = " ".join(entry.findtext(f"{ATOM}title", "").split())
        year = entry.findtext(f"{ATOM}published", "")[:4]
        summary = " ".join(entry.findtext(f"{ATOM}summary", "").split())
        if title and year.isdigit():
            return title, int(year), summary
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
            found = arxiv_full(s["arxiv"])
            ok = found is not None and title_matches(s["title"], found[0]) and abs(found[1] - s["year"]) <= 3
            problems += not ok
            print(f"{'OK' if ok else 'MISMATCH':<11} {label}: arXiv {s['arxiv']} -> {found[:2] if found else None}")
            if found and s["arxiv"] in SHOW_ABSTRACT:
                print(f"            abstract: {found[2]}")
    print(f"\n{len(SOURCES)} sources, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

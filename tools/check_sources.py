#!/usr/bin/env python3
"""Check that every cited DOI / arXiv id exists and matches the cited title and year, and, where the
venue string gives them, the volume, issue and page range registered with Crossref.

Queries the public Crossref and arXiv APIs (network required). Sources without a
DOI or arXiv id (books cited by ISBN, old proceedings) are listed as unchecked.

Usage:
  python tools/check_sources.py            # all entries
  python tools/check_sources.py pairs/fibonacci-naive-vs-dp
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import REPO, discover_entries, load_entry  # noqa: E402

USER_AGENT = "complexity-pairs-dataset/0.1 (source checker)"
ATOM = "{http://www.w3.org/2005/Atom}"


def _get(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            # 429 / 503: honour Retry-After, else back off exponentially.
            retry_after = e.headers.get("Retry-After", "")
            time.sleep(min(int(retry_after) if retry_after.isdigit() else 5 * 2 ** attempt, 60))
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"unreachable: {url}")


def _words(s: str) -> set[str]:
    s = re.sub(r"<[^>]+>|\$[^$]*\$", " ", s.lower())  # drop markup and TeX
    return {w for w in re.findall(r"[a-z0-9]+", s) if len(w) > 2}


def title_matches(cited: str, found: str) -> bool:
    a, b = _words(cited), _words(found)
    if not a or not b:
        return False
    overlap = len(a & b)
    return overlap / len(a) >= 0.7 or overlap / len(b) >= 0.7


def lookup_doi(doi: str) -> tuple[str, int | None] | None:
    """Crossref first; DataCite for DOIs it does not hold (e.g. LIPIcs, Zenodo)."""
    return crossref(doi) or datacite(doi)


def datacite(doi: str) -> tuple[str, int | None] | None:
    raw = _get("https://api.datacite.org/dois/" + urllib.parse.quote(doi))
    if raw is None:
        return None
    attrs = json.loads(raw)["data"]["attributes"]
    title = " ".join(t.get("title", "") for t in attrs.get("titles") or [])
    return title.strip(), attrs.get("publicationYear")


def crossref(doi: str) -> tuple[str, int | None] | None:
    rec = crossref_record(doi)
    return None if rec is None else (rec["title"], rec["year"])


_crossref_cache: dict[str, dict | None] = {}


def crossref_record(doi: str) -> dict | None:
    """Title, year, volume, issue and pages as registered with Crossref (None if Crossref does not hold the DOI)."""
    if doi in _crossref_cache:
        return _crossref_cache[doi]
    raw = _get("https://api.crossref.org/works/" + urllib.parse.quote(doi))
    rec = None
    if raw is not None:
        msg = json.loads(raw)["message"]
        year = None
        for key in ("published-print", "published-online", "issued"):
            parts = msg.get(key, {}).get("date-parts")
            if parts and parts[0] and parts[0][0]:
                year = parts[0][0]
                break
        rec = {
            "title": (" ".join(msg.get("title") or []) + " " + " ".join(msg.get("subtitle") or [])).strip(),
            "year": year,
            "volume": msg.get("volume"),
            "issue": msg.get("issue"),
            "page": msg.get("page"),
        }
    _crossref_cache[doi] = rec
    return rec


def parse_venue(venue: str, year: int) -> dict:
    """Extract volume, issue and page range from venue strings such as 'Journal of the ACM 21(1), 168-173'.

    A number equal to a plausible year (e.g. 'STOC 1996, 212-219') is not taken as a volume.
    """
    out = {}
    pages = re.findall(r",\s*(\d+)\s*[-\u2013]\s*(\d+)\s*(?:\(|$|;)", venue)
    if pages:
        out["first_page"], out["last_page"] = pages[-1]
    m = re.search(r"(?<![\w.])(\d{1,4})\((\d+(?:[-\u2013]\d+)?)\)", venue)
    if m:
        out["volume"], out["issue"] = m.group(1), m.group(2)
    else:
        m = re.search(r"(?<![\w.(])(\d{1,4}),\s*\d+\s*[-\u2013]\s*\d+", venue)
        if m:
            out["volume"] = m.group(1)
    if out.get("volume") and (int(out["volume"]) == year or int(out["volume"]) >= 1900):
        out.pop("volume")
        out.pop("issue", None)
    return out


def detail_mismatches(cited: dict, rec: dict) -> list[str]:
    """Compare parsed venue details with the Crossref record; only fields present on both sides count."""
    problems = []
    norm = lambda x: str(x).strip().lstrip("0").replace("\u2013", "-")  # noqa: E731
    if "volume" in cited and rec.get("volume") and norm(cited["volume"]) != norm(rec["volume"]):
        problems.append(f"volume {cited['volume']} vs Crossref {rec['volume']}")
    if "issue" in cited and rec.get("issue") and norm(cited["issue"]) != norm(rec["issue"]):
        problems.append(f"issue {cited['issue']} vs Crossref {rec['issue']}")
    if "first_page" in cited and rec.get("page"):
        parts = re.split(r"[-\u2013]", rec["page"])
        if norm(cited["first_page"]) != norm(parts[0]):
            problems.append(f"first page {cited['first_page']} vs Crossref {rec['page']}")
        elif len(parts) > 1 and norm(cited["last_page"]) != norm(parts[-1]):
            problems.append(f"last page {cited['last_page']} vs Crossref {rec['page']}")
    return problems


def arxiv_batch(ids: list[str]) -> dict[str, tuple[str, int]]:
    out = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        raw = _get("https://export.arxiv.org/api/query?max_results=50&id_list=" + ",".join(chunk))
        root = ET.fromstring(raw)
        for entry in root.findall(f"{ATOM}entry"):
            aid = entry.findtext(f"{ATOM}id", "").rsplit("/abs/", 1)[-1]
            aid = re.sub(r"v\d+$", "", aid)
            title = " ".join(entry.findtext(f"{ATOM}title", "").split())
            year = int(entry.findtext(f"{ATOM}published", "0000")[:4])
            out[aid] = (title, year)
        time.sleep(3)  # arXiv API etiquette
    return out


if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to a legacy code page
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str]) -> int:
    entries = [(d, load_entry(d)) for d in discover_entries(argv or None)]
    arxiv_ids = sorted({s["arxiv"] for _, e in entries for s in e["sources"] if "arxiv" in s})
    arxiv_down = False
    try:
        arxiv = arxiv_batch(arxiv_ids) if arxiv_ids else {}
    except RuntimeError as e:
        print(f"warning: arXiv API unavailable ({e}); arXiv ids left unchecked")
        arxiv, arxiv_down = {}, True

    problems = unchecked = checked = details_checked = 0
    for entry_dir, entry in entries:
        rel = entry_dir.relative_to(REPO)
        for s in entry["sources"]:
            label = f"{rel}: {s['authors'].split(';')[0]} {s['year']}"
            results = []
            if "doi" in s:
                rec = crossref_record(s["doi"])
                if rec is not None:
                    cited = parse_venue(s.get("venue", ""), s["year"])
                    if cited:
                        details_checked += 1
                        bad = detail_mismatches(cited, rec)
                        if bad:
                            problems += 1
                            print(f"[DETAIL MISMATCH] {label}: doi {s['doi']}: " + "; ".join(bad))
                    if not rec["title"]:
                        # Crossref holds the DOI but no title (happens for some journals): accept only if
                        # the year and the cited volume + first page all agree with the record.
                        ok = (rec["year"] is not None and abs(rec["year"] - s["year"]) <= 1 and cited.get("volume")
                              and cited.get("first_page") and not detail_mismatches(cited, rec))
                        checked += 1
                        if not ok:
                            problems += 1
                            print(f"[UNVERIFIABLE] {label}: doi {s['doi']}: Crossref has no title, and volume/page/year do not confirm it")
                    else:
                        results.append(("doi " + s["doi"], (rec["title"], rec["year"])))
                else:
                    results.append(("doi " + s["doi"], datacite(s["doi"])))
            if "arxiv" in s and not arxiv_down:
                results.append(("arXiv " + s["arxiv"], arxiv.get(s["arxiv"])))
            if not results:
                unchecked += 1
                continue
            for what, found in results:
                checked += 1
                if found is None:
                    problems += 1
                    print(f"[NOT FOUND] {label}: {what}")
                    continue
                title, year = found
                ok_title = title_matches(s["title"], title)
                # arXiv year is the preprint year; journal versions often appear 1-3 years later.
                slack = 3 if what.startswith("arXiv") else 1
                ok_year = year is None or abs(year - s["year"]) <= slack
                if not (ok_title and ok_year):
                    problems += 1
                    print(f"[MISMATCH] {label}: {what}\n      cited: {s['title']!r} ({s['year']})\n      found: {title!r} ({year})")
    print(f"\n{checked} identifiers checked ({details_checked} also on volume/issue/pages), {problems} problem(s), "
          f"{unchecked} source(s) without DOI/arXiv (not checkable)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

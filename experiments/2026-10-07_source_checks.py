"""Source check (2026-10-07 quantum entries): do the candidate DOIs exist, and do title, year, volume, issue
and pages match what the new entries cite?

Queries the public Crossref API (DataCite as fallback) through tools/check_sources.py. This is NOT
deterministic in the same sense as the simulation experiments: it depends on the external registries
(provenance label "external"). It prints, for every candidate DOI, what the registry holds, so that the
cited venue strings can be compared by eye and by tools/check_sources.py <entry> afterwards.

Outcome (first run, 2026-10-07): all 17 candidate DOIs exist; titles, years, volumes, issues and pages match
the cited ones, except that Crossref holds no title for the two Theory of Computing DOIs (confirmed on the
journal's site instead). The Boyer-Brassard-Hoyer-Tapp DOI was found by bibliographic search (first hit) and then
verified. Details: research/2026-10-07_quantum_entries.md, section "Sources".

Run from the repository root:  PYTHONIOENCODING=utf-8 python experiments/2026-10-07_source_checks.py [--arxiv]
(--arxiv adds the two batched arXiv API queries used for abstracts; omitted by default because of rate limits.)
"""
import json
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_sources import _get, crossref_record, lookup_doi  # noqa: E402

CANDIDATES = [
    # (what we want to cite, candidate DOI)
    ("Deutsch & Jozsa 1992, Proc. R. Soc. A 439, 553-558", "10.1098/rspa.1992.0167"),
    ("Cleve, Ekert, Macchiavello, Mosca 1998, Proc. R. Soc. A 454, 339-354", "10.1098/rspa.1998.0164"),
    ("Brassard, Hoyer, Tapp 1998, LATIN '98", "10.1007/BFb0054319"),
    ("Aaronson & Shi 2004, J. ACM 51(4), 595-605", "10.1145/1008731.1008735"),
    ("Ambainis 2007, SIAM J. Comput. 37(1), 210-239", "10.1137/S0097539705447311"),
    ("Aaronson & Ambainis 2015, STOC (Forrelation)", "10.1145/2746539.2746547"),
    ("Harrow, Hassidim, Lloyd 2009, PRL 103, 150502", "10.1103/PhysRevLett.103.150502"),
    ("Aaronson 2015, Nature Physics 11, 291-293 (Read the fine print)", "10.1038/nphys3272"),
    ("Chia et al. 2022, J. ACM 69(5)", "10.1145/3549524"),
    ("Raz & Tal 2019, STOC (BQP vs PH)", "10.1145/3313276.3316315"),
    ("Raz & Tal 2022, J. ACM (BQP vs PH)", "10.1145/3530258"),
    ("Kutin 2005, Theory of Computing 1 (collision, small range) [guess]", "10.4086/toc.2005.v001a002"),
    ("Ambainis 2005, Theory of Computing 1 (collision/ED, small range) [guess]", "10.4086/toc.2005.v001a003"),
    ("Bennett, Bernstein, Brassard, Vazirani 1997, SIAM J. Comput. 26(5)", "10.1137/S0097539796300933"),
    ("Simon 1997, SIAM J. Comput. 26(5)", "10.1137/S0097539796298637"),
    ("Grover 1996, STOC", "10.1145/237814.237866"),
    ("Beals, Buhrman, Cleve, Mosca, de Wolf 2001, J. ACM 48(4) [report only]", "10.1145/502090.502097"),
]

for what, doi in CANDIDATES:
    rec = crossref_record(doi)
    if rec is None:
        print(f"{what}\n    {doi}: not in Crossref; DataCite -> {lookup_doi(doi)}")
        continue
    print(f"{what}\n    {doi}: {rec['title']!r} ({rec['year']}), vol {rec['volume']}, "
          f"issue {rec['issue']}, pages {rec['page']}")

# Boyer, Brassard, Hoyer, Tapp 1998 (Fortschritte der Physik 46): the DOI is not known in advance, so ask
# Crossref's bibliographic search and print the top hits; the chosen DOI is then checked like the others.
query = urllib.parse.quote("Tight bounds on quantum searching Boyer Brassard Hoyer Tapp Fortschritte der Physik")
raw = _get(f"https://api.crossref.org/works?query.bibliographic={query}&rows=5")
for item in json.loads(raw)["message"]["items"]:
    print("search hit:", item.get("DOI"), "|", " ".join(item.get("title") or []), "|",
          " ".join(item.get("container-title") or []), "|", item.get("volume"), item.get("issue"), item.get("page"))

# --- Follow-up checks run inline during the session, kept here for the record (2026-10-07) ---
from check_sources import datacite  # noqa: E402

BBHT = "10.1002/(SICI)1521-3978(199806)46:4/5<493::AID-PROP493>3.0.CO;2-P"
print("BBHT chosen DOI:", crossref_record(BBHT))
# Outcome: 'Tight Bounds on Quantum Searching' (1998), vol 46, issue 4-5, pages 493-505.
for doi in ("10.4086/toc.2005.v001a002", "10.4086/toc.2005.v001a003"):
    print("DataCite", doi, "->", datacite(doi))
# Outcome: None for both (not registered with DataCite). Crossref holds year 2005, volume 1, pages 29-36 / 37-46
# but no title; titles confirmed on theoryofcomputing.org/articles/v001a002 and v001a003 (WebFetch, 2026-10-07):
# Kutin, "Quantum Lower Bound for the Collision Problem with Small Range"; Ambainis, "Polynomial Degree and
# Lower Bounds in Quantum Complexity: Collision and Element Distinctness with Small Range".

if "--arxiv" in sys.argv:  # opt-in: two batched arXiv API calls (rate limits); titles, years and abstracts
    import time
    import xml.etree.ElementTree as ET
    from check_sources import ATOM
    for ids in ("quant-ph/9607014,quant-ph/9705002,quant-ph/9605034,1411.5729,0811.3171,quant-ph/9708016,"
                "quant-ph/0311001,quant-ph/0111102,quant-ph/0112086",
                "1910.06151,1811.04909,1811.04852"):
        root = ET.fromstring(_get("https://export.arxiv.org/api/query?max_results=20&id_list=" + ids))
        for entry in root.findall(ATOM + "entry"):
            print(entry.findtext(ATOM + "id"), "|", " ".join(entry.findtext(ATOM + "title", "").split()))
            print("   ", " ".join(entry.findtext(ATOM + "summary", "").split()))
        time.sleep(3)

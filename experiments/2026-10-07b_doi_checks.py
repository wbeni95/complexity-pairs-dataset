#!/usr/bin/env python3
"""DOI checks for the 2026-10-07b batch entries written by the coordinating agent (XOR convolution, zeta
transform, regex matching, NAND-tree evaluation).

What it does: resolves each DOI with tools/check_sources.lookup_doi (Crossref, then DataCite) and prints the
Crossref record (title, year, volume, issue, pages), so that the venue strings in the entries can be compared
with what the registry holds. Network required; results depend on the registries, not on randomness.

Outcome: recorded in research/2026-10-07b_new_candidates.md (section "DOIs"). A DOI whose registered title does
not match the intended work, or that does not resolve, is dropped from the entries.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from check_sources import crossref_record, lookup_doi  # noqa: E402

DOIS = {
    # XOR convolution
    "Fino & Algazi 1976 (FWHT)": "10.1109/TC.1976.1674569",
    "Bernstein & Vazirani 1997": "10.1137/S0097539796300921",
    # zeta transform
    "Bjorklund, Husfeldt, Kaski, Koivisto 2007 (STOC)": "10.1145/1250790.1250801",
    # regex
    "Thompson 1968": "10.1145/363347.363387",
    # NAND tree
    "Saks & Wigderson 1986": "10.1109/SFCS.1986.44",
    "Snir 1985": "10.1016/0304-3975(85)90024-6",
    "Farhi, Goldstone, Gutmann 2008": "10.4086/toc.2008.v004a008",
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        DOIS = {d: d for d in sys.argv[1:]}
    for label, doi in DOIS.items():
        try:
            print(f"{label}: {doi}")
            print("   lookup_doi:", lookup_doi(doi))
            print("   crossref  :", crossref_record(doi))
        except Exception as e:  # noqa: BLE001
            print("   ERROR", type(e).__name__, e)

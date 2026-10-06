"""Source check (network): which statements about Lawler 1976 and Bjorklund-Husfeldt-Koivisto 2009, cited in
pairs/chromatic-number-subset-dp-vs-inclusion-exclusion, are actually in readable sources?

Lawler's paper (IPL 5(3), 1976) and the published SIAM version of BHK could not be read (publisher pages
returned HTTP 403). Two open versions were read instead:
  * Eppstein, "Small maximal independent sets and faster exact graph coloring", JGAA 7(2), 131-140 (2003),
    doi:10.7155/jgaa.00064, PDF at jgaa.info;
  * the authors' open-access version of BHK (linked by Semantic Scholar as the open-access PDF).
The script downloads both PDFs, extracts text crudely (FlateDecode streams, Tj/TJ string operators; maths
symbols come out garbled) and prints the passages around the keywords. Nothing is stored in the repository.

Outcome (2026-10-07):
  * Eppstein's abstract and introduction: Lawler's chromatic-number algorithm is a DP over induced subgraphs
    that lists the maximal independent sets, with running time "O((1 + 3^(1/3))^n)". The exponent comes out
    garbled as "\\(\\(1 + 3" in the extraction. The bound "follows from an upper bound of 3^(n/3) on the number
    of maximal independent sets ... due to Moon and Moser".
  * BHK (authors' version): the abstract gives "2^n n^O(1) time" for Chromatic Number, among others. Formula (1.1)
    reads: N can be covered with k sets from F iff sum_{X subset N} (-1)^|X| a(X)^k > 0. Section 1.3 says the
    subset DP "goes back at least to Lawler" and that its running time "is never worse than within a
    polynomial factor of sum_{S in F} 2^(n-|S|) <= ... = 3^n". Table 1.2 lists "2.4423 Find chi Lawler". Section 4.1
    has Lemma 7 (chi(G) <= k iff c_k > 0), Proposition 1 ("Chromatic Number can be solved in
    O(2^n n k polylog(nk)) time and O(2^n n) space") and recurrence (4.1), a(X) = a(X u {v}) + a(X u N(v)) + 1.
    Proposition 7 gives O(2.2461^n) time in polynomial space.
These are the statements the entry relies on. Statements not found this way were dropped. That covers the exact
polynomial factor of Lawler's bound and Eppstein's improved base, which the extraction garbled.

Run from the repository root (needs network):  python experiments/2026-10-07_source_text_checks.py
"""
import re
import sys
import urllib.request
import zlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCES = {
    "Eppstein 2003 (JGAA)": ("https://jgaa.info/index.php/jgaa/article/download/paper64/2898",
                             ["Lawler", "Moon"]),
    "Bjorklund-Husfeldt-Koivisto (authors' version)": ("http://www.cs.helsinki.fi/u/mkhkoivi/publications/sicomp-200Y.pdf",
                                                       ["Abstract", "goes back at least to Lawler", "Find \\037 Lawler",
                                                        "Proposition 1", "Proposition 7", "Lemma 7"]),
}


def pdf_text(data):
    pages = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            s = zlib.decompress(m.group(1))
        except zlib.error:
            continue
        if b"TJ" not in s and b"Tj" not in s:
            continue
        line = []
        for a, b in re.findall(rb"\[(.*?)\]\s*TJ|\((.*?)\)\s*Tj", s, re.S):
            w = ""
            for p, num in re.findall(rb"\(((?:\\.|[^\\)])*)\)|(-?\d+\.?\d*)", a or b):
                if p:
                    w += p.decode("latin-1")
                elif num and float(num) < -200:
                    w += " "
            line.append(w)
        pages.append(" ".join(line))
    return "\n".join(pages)


for label, (url, keywords) in SOURCES.items():
    req = urllib.request.Request(url, headers={"User-Agent": "complexity-pairs-dataset/0.1 (source check)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        text = pdf_text(resp.read())
    print(f"=== {label}: {len(text)} characters extracted")
    for kw in keywords:
        i = text.find(kw)
        print(f"--- [{kw}] " + ("NOT FOUND" if i < 0 else text[max(0, i - 200): i + 500].replace("\n", " ")))

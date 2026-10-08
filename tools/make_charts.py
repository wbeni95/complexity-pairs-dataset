#!/usr/bin/env python3
"""Draw the front-page charts of README.md as SVG files in docs/img/, each in a light and a dark version.

Every number in a chart comes from the repository:
  - "items": one square per entry and theorem note, coloured by provenance, with a tick on each item marked ✅.
    tools/build_index.py writes it together with index.json, so it always matches the data;
  - "comparisons-n1000": the exact comparison counts proved in PROOFS.md of the three merge-cost entries, at n = 1000;
  - "steps-and-time": the counts and the wall-clock seconds of the recorded run LEDGER_RUN for the maximum merge cost
    entry (counts are the evidence; seconds are supplementary data);
  - "same-time-bigger-inputs": the wall-clock seconds of LEDGER_RUN for the three algorithms of the X^2 + C entry.
The script asserts that the counts measured in LEDGER_RUN equal the proved closed forms before it draws them.

  python tools/make_charts.py           # write the three charts that do not depend on index.json
  python tools/make_charts.py --check   # exit 1 if one of them differs from what the script would write
"""
from __future__ import annotations

import argparse
import html
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IMG = "docs/img"
LEDGER_RUN = "20261008T085246Z"
MERGE_LARGER = "max-merge-cost-larger-part-cubic-dp-vs-endpoint-dp"
SQUARE_OFFSET = "square-plus-offset-count-enumeration-vs-intervals-vs-groups"


def cubic(n: int) -> int:
    """Comparisons of the cubic interval DP (PROOFS.md section 5 of the three merge-cost entries)."""
    return n * (n + 1) * (2 * n + 1) // 6


def endpoint(n: int) -> int:
    """Comparisons of the endpoint DP (PROOFS.md section 5 of the two maximum merge entries)."""
    return n * (3 * n - 1) // 2


PALETTES = {
    "light": dict(fg="#1f2328", muted="#59636e", grid="#d8dee4", own="#c4501b", old="#8c959f", und="#c99a06",
                  known="#4a6782", syn="#a9b6c3", cited="#8c959f", mid="#4a6782"),
    "dark": dict(fg="#e6edf3", muted="#9198a1", grid="#30363d", own="#f0883e", old="#6e7681", und="#e3b341",
                 known="#7d9cbc", syn="#4b5a69", cited="#6e7681", mid="#7d9cbc"),
}
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"

# provenance groups of the "items" chart, in drawing order: (key, legend text, filled square)
ITEM_GROUPS = [
    ("own", "Our own results and extensions", True),
    ("und", "Undetermined: may be our own", True),
    ("known", "Known results, proved again here", True),
    ("syn", "Synthetic examples (not counted as pairs)", True),
    ("cited", "Known results, cited only (not yet checked)", False),
]


def fmt(x: int) -> str:
    return f"{x:,}".replace(",", " ")


def sup(k: int) -> str:
    return "".join("⁰¹²³⁴⁵⁶⁷⁸⁹"[int(c)] if c.isdigit() else "⁻" for c in str(k))


def svg_open(w: int, h: int, label: str, p: dict) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{html.escape(label)}" font-family="{FONT}">'
            f'<style>text{{fill:{p["fg"]};font-size:13px}} .m{{fill:{p["muted"]};font-size:12px}} '
            f'.v{{font-family:{MONO};font-size:12px}} .h{{font-size:15px;font-weight:600}}</style>')


def item_group(location: str, cls: str) -> str:
    """Group of one item in the "items" chart: own and undetermined items by provenance (wherever they are), other
    items in staging or synthetic by folder, the rest as known results."""
    if cls in ("own", "own-extension"):
        return "own"
    if cls == "undetermined":
        return "und"
    if location == "staging":
        return "cited"
    if location == "synthetic":
        return "syn"
    return "known"


def tick_colour(fill: str) -> str:
    """White on dark squares, near-black on light ones (relative luminance of the square's colour)."""
    lin = [(c / 255) / 12.92 if c <= 10 else (((c / 255) + 0.055) / 1.055) ** 2.4
           for c in (int(fill[i:i + 2], 16) for i in (1, 3, 5))]
    return "#1f2328" if 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2] > 0.3 else "#ffffff"


def in_range(values, lo: float, hi: float, what: str) -> None:
    """Refuse to draw a value outside a fixed axis range."""
    bad = [v for v in values if not lo <= v <= hi]
    if bad:
        raise SystemExit(f"{what}: values {bad} lie outside the axis range [{lo:g}, {hi:g}]")


def items_svg(items: list[tuple[str, bool]], p: dict) -> str:
    """One square per item. items: (group key, proved) pairs; drawn group by group in ITEM_GROUPS order."""
    order = [g for g, _, _ in ITEM_GROUPS]
    items = sorted(items, key=lambda it: (order.index(it[0]), not it[1]))
    counts = {g: sum(1 for k, _ in items if k == g) for g in order}
    cols, sz, gap, top = 12, 24, 5, 34
    rows = max(1, math.ceil(len(items) / cols))
    gw = cols * (sz + gap) - gap
    W, H = 760, top + rows * (sz + gap) + 16
    out = [svg_open(W, H, f"{len(items)} items, one square each, coloured by whose result it is", p),
           f'<text x="0" y="18" class="h">{len(items)} items, one square each</text>'
           f'<text x="{gw + 28}" y="18" class="m">tick = proved here, with a check anyone can run</text>']
    filled = {g: f for g, _, f in ITEM_GROUPS}
    for i, (g, proved) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = c * (sz + gap), top + r * (sz + gap)
        if filled[g]:
            out.append(f'<rect x="{x}" y="{y}" width="{sz}" height="{sz}" rx="3" fill="{p[g]}"/>')
        else:
            out.append(f'<rect x="{x + 0.75}" y="{y + 0.75}" width="{sz - 1.5}" height="{sz - 1.5}" rx="3" fill="none" '
                       f'stroke="{p[g]}" stroke-width="1.5" stroke-dasharray="3 2"/>')
        if proved:
            out.append(f'<path d="M{x + 7} {y + 12.5} l3.6 3.6 l6.6 -7.2" fill="none" stroke="{tick_colour(p[g])}" stroke-width="2" '
                       f'stroke-linecap="round" stroke-linejoin="round"/>')
    lx = gw + 28
    for j, (g, label, f) in enumerate(ITEM_GROUPS):
        y = top + 6 + j * 26
        sw = (f'<rect x="{lx}" y="{y}" width="14" height="14" rx="2" fill="{p[g]}"/>' if f else
              f'<rect x="{lx + 0.75}" y="{y + 0.75}" width="12.5" height="12.5" rx="2" fill="none" stroke="{p[g]}" '
              f'stroke-width="1.5" stroke-dasharray="3 2"/>')
        out.append(sw + f'<text x="{lx + 22}" y="{y + 12}" class="v">{counts[g]:>2}</text>'
                        f'<text x="{lx + 46}" y="{y + 12}">{html.escape(label)}</text>')
    out.append("</svg>")
    return "".join(out) + "\n"


def comparisons_svg(p: dict) -> str:
    n = 1000
    rows = [("Maximum merge cost (larger part)", "and maximum total imbalance: same counts", cubic(n), endpoint(n)),
            ("Minimum merge cost (smaller part)", "closed form instead of a DP", cubic(n), n)]
    W, L, R, top, bh = 760, 250, 150, 40, 20
    sx = lambda v: L + (W - L - R) * math.log10(v) / 9  # noqa: E731
    in_range([v for r in rows for v in r[2:]], 1, 10 ** 9, "comparisons chart")
    H = top + len(rows) * 78 + 34
    out = [svg_open(W, H, "Comparisons for n = 1000 merges (1001 piles), previous exact method versus ours, logarithmic scale", p),
           f'<text x="0" y="18" class="h">Comparisons for n = 1000 merges (1001 piles)</text>'
           f'<text x="{W}" y="18" text-anchor="end" class="m">exact counts, proved in each entry · logarithmic scale</text>']
    for k in range(0, 10, 3):
        x = sx(10 ** k)
        out.append(f'<line x1="{x:.1f}" y1="{top - 6}" x2="{x:.1f}" y2="{H - 30}" stroke="{p["grid"]}"/>'
                   f'<text x="{x:.1f}" y="{H - 12}" text-anchor="middle" class="m">10{sup(k)}</text>')
    for i, (name, sub, old, new) in enumerate(rows):
        y = top + i * 78
        out.append(f'<text x="{L - 12}" y="{y + 15}" text-anchor="end">{html.escape(name)}</text>'
                   f'<text x="{L - 12}" y="{y + 33}" text-anchor="end" class="m">{html.escape(sub)}</text>'
                   f'<rect x="{L}" y="{y}" width="{sx(old) - L:.1f}" height="{bh}" rx="2" fill="{p["old"]}"/>'
                   f'<text x="{sx(old) + 8:.1f}" y="{y + 15}" class="v">{fmt(old)}</text>'
                   f'<rect x="{L}" y="{y + bh + 4}" width="{max(sx(new) - L, 3):.1f}" height="{bh}" rx="2" fill="{p["own"]}"/>'
                   f'<text x="{max(sx(new), L + 3) + 8:.1f}" y="{y + bh + 19}" class="v">{fmt(new)}</text>'
                   f'<text x="{W}" y="{y + bh + 19}" text-anchor="end" font-weight="600" fill="{p["own"]}">'
                   f'{fmt(round(old / new))}× fewer</text>')
    lg = top + len(rows) * 78 - 14
    out.append(f'<rect x="{L}" y="{lg}" width="12" height="12" rx="2" fill="{p["old"]}"/>'
               f'<text x="{L + 18}" y="{lg + 11}" class="m">cubic interval DP (every split)</text>'
               f'<rect x="{L + 230}" y="{lg}" width="12" height="12" rx="2" fill="{p["own"]}"/>'
               f'<text x="{L + 248}" y="{lg + 11}" class="m">our method</text></svg>')
    return "".join(out) + "\n"


def load_ledger(repo: Path = REPO) -> dict:
    """{entry id: {algorithm name: V2 record}} of LEDGER_RUN, after checking the merge counts against PROOFS.md."""
    run = json.loads((repo / "ledger" / "runs" / f"{LEDGER_RUN}.json").read_text(encoding="utf-8"))
    led = {e["id"]: {m["algorithm"]: m for m in e.get("v2") or []} for e in run["entries"]}
    led["_python"] = run["run"]["python"]
    for name, f in (("cubic interval DP (every split)", cubic), ("endpoint DP (two candidate splits per row)", endpoint)):
        m = led[MERGE_LARGER][name]
        if [int(v) for v in m["values"]] != [f(n) for n in m["n_values"]]:
            raise SystemExit(f"{LEDGER_RUN}: measured counts of '{name}' differ from the proved closed form")
    return led


def steps_time_svg(led: dict, p: dict) -> str:
    mc = led[MERGE_LARGER]["cubic interval DP (every split)"]
    me = led[MERGE_LARGER]["endpoint DP (two candidate splits per row)"]
    W, H = 760, 330
    ns = [16, 32, 64, 128, 256, 512]
    out = [svg_open(W, H, "Maximum merge cost: comparisons and measured seconds versus n, cubic DP and endpoint DP", p)]
    for x0, title, kind in ((0, "Steps: counted comparisons", "count"), (395, "Time: measured seconds", "seconds")):
        L, Rr, top, bot = x0 + 52, x0 + 350, 44, H - 70
        lo, hi = (3, 6) if kind == "count" else (-4, 0)
        lx = lambda n: L + (Rr - L) * (math.log2(n) - 4) / 5  # noqa: E731
        ly = lambda v: bot - (bot - top) * (math.log10(v) - lo) / (hi - lo)  # noqa: E731
        out.append(f'<text x="{x0}" y="18" class="h">{title}</text>')
        for k in range(lo, hi + 1):
            y = ly(10 ** k)
            out.append(f'<line x1="{L}" y1="{y:.1f}" x2="{Rr}" y2="{y:.1f}" stroke="{p["grid"]}"/>'
                       f'<text x="{L - 8}" y="{y + 4:.1f}" text-anchor="end" class="m">10{sup(k)}</text>')
        for n in ns:
            out.append(f'<text x="{lx(n):.1f}" y="{bot + 18}" text-anchor="middle" class="m">{n}</text>')
        out.append(f'<text x="{(L + Rr) / 2:.0f}" y="{bot + 36}" text-anchor="middle" class="m">n (merges; n + 1 piles)</text>')
        for m, f, key in ((mc, cubic, "old"), (me, endpoint, "own")):
            pts = list(zip(m["n_values"], m["values"] if kind == "count" else m["timing"]["values"]))
            in_range([v for _, v in pts], 10 ** lo, 10 ** hi, f"steps-and-time chart, {kind}")
            in_range([n for n, _ in pts], 16, 512, "steps-and-time chart, n")
            if kind == "count":
                grid = [2 ** (t / 2) for t in range(8, 19)]  # n = 16 .. 512 in half-octave steps
                d = " L".join(f"{lx(n):.1f},{ly(f(n)):.1f}" for n in grid if top <= ly(f(n)) <= bot)
                out.append(f'<path d="M{d}" fill="none" stroke="{p[key]}" stroke-width="2"/>')
            else:
                d = " L".join(f"{lx(n):.1f},{ly(v):.1f}" for n, v in pts)
                out.append(f'<path d="M{d}" fill="none" stroke="{p[key]}" stroke-width="1.5" stroke-dasharray="4 3"/>')
            out += [f'<circle cx="{lx(n):.1f}" cy="{ly(v):.1f}" r="4" fill="{p[key]}"/>' for n, v in pts]
        note = "lines: proved formulas · dots: recorded run" if kind == "count" else f"one core, CPython {led['_python']}"
        out.append(f'<text x="{Rr}" y="{top - 10}" text-anchor="end" class="m">{note}</text>')
    out.append(f'<rect x="52" y="{H - 14}" width="12" height="12" rx="2" fill="{p["old"]}"/>'
               f'<text x="70" y="{H - 4}" class="m">cubic interval DP</text>'
               f'<rect x="200" y="{H - 14}" width="12" height="12" rx="2" fill="{p["own"]}"/>'
               f'<text x="218" y="{H - 4}" class="m">endpoint DP (ours)</text></svg>')
    return "".join(out) + "\n"


def same_time_svg(led: dict, p: dict) -> str:
    sq = led[SQUARE_OFFSET]
    series = [("enumeration of all k", sq["enumeration of all k with three candidate roots"], "old", -10, "end"),
              ("one interval per root", sq["sweep over one interval per root"], "mid", 10, "start"),
              ("root groups (ours)", sq["root groups of equal bit length"], "own", 10, "start")]
    W, H, L, Rr, top, bot, lo, hi = 760, 290, 60, 600, 44, 240, -6, -1
    lx = lambda n: L + (Rr - L) * math.log2(n / 6) / math.log2(64)  # noqa: E731
    ly = lambda v: bot - (bot - top) * (math.log10(v) - lo) / (hi - lo)  # noqa: E731
    out = [svg_open(W, H, "Measured seconds versus n for three exact counting algorithms", p),
           f'<text x="0" y="18" class="h">Counting n-bit integers that have a cheap X² + C form</text>'
           f'<text x="{W}" y="18" text-anchor="end" class="m">measured seconds, one core, recorded run</text>']
    for k in range(lo, hi + 1):
        y = ly(10 ** k)
        out.append(f'<line x1="{L}" y1="{y:.1f}" x2="{Rr}" y2="{y:.1f}" stroke="{p["grid"]}"/>'
                   f'<text x="{L - 8}" y="{y + 4:.1f}" text-anchor="end" class="m">10{sup(k)} s</text>')
    for n in (6, 12, 24, 48, 96, 192, 384):
        out.append(f'<text x="{lx(n):.1f}" y="{bot + 18}" text-anchor="middle" class="m">{n}</text>')
    out.append(f'<text x="{(L + Rr) / 2:.0f}" y="{bot + 38}" text-anchor="middle" class="m">n (bits; logarithmic axis)</text>')
    for label, m, key, dx, anchor in series:
        pts = list(zip(m["n_values"], m["timing"]["values"]))
        in_range([v for _, v in pts], 10 ** lo, 10 ** hi, "same-time chart, seconds")
        in_range([n for n, _ in pts], 6, 384, "same-time chart, n")
        out.append(f'<path d="M' + " L".join(f"{lx(n):.1f},{ly(v):.1f}" for n, v in pts)
                   + f'" fill="none" stroke="{p[key]}" stroke-width="2"/>')
        out += [f'<circle cx="{lx(n):.1f}" cy="{ly(v):.1f}" r="3.5" fill="{p[key]}"/>' for n, v in pts]
        n_last, v_last = pts[-1]
        out.append(f'<text x="{lx(n_last) + dx:.1f}" y="{ly(v_last) + 4:.1f}" text-anchor="{anchor}" fill="{p[key]}" '
                   f'font-weight="600">{html.escape(label)}</text>'
                   f'<text x="{lx(n_last) + dx:.1f}" y="{ly(v_last) + 20:.1f}" text-anchor="{anchor}" class="m">'
                   f'n = {n_last}: {v_last * 1000:.1f} ms</text>')
    out.append("</svg>")
    return "".join(out) + "\n"


def static_charts(repo: Path = REPO) -> dict[Path, str]:
    """The charts that depend only on PROOFS.md formulas and LEDGER_RUN: {path: SVG text}."""
    led = load_ledger(repo)
    out = {}
    for theme, p in PALETTES.items():
        out[repo / IMG / f"comparisons-n1000-{theme}.svg"] = comparisons_svg(p)
        out[repo / IMG / f"steps-and-time-{theme}.svg"] = steps_time_svg(led, p)
        out[repo / IMG / f"same-time-bigger-inputs-{theme}.svg"] = same_time_svg(led, p)
    return out


def items_charts(items: list[tuple[str, bool]], repo: Path) -> dict[Path, str]:
    """The "items" chart in both themes (called by tools/build_index.py)."""
    return {repo / IMG / f"items-{theme}.svg": items_svg(items, p) for theme, p in PALETTES.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="do not write; exit 1 if a chart is stale")
    args = ap.parse_args(argv)
    outputs = static_charts()
    stale = [p for p, text in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    if args.check:
        for p in stale:
            print(f"stale: {p.relative_to(REPO).as_posix()}  (run python tools/make_charts.py)")
        return 1 if stale else 0
    for p in stale:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(outputs[p], encoding="utf-8", newline="\n")
        print(f"wrote {p.relative_to(REPO).as_posix()}")
    if not stale:
        print("everything up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())

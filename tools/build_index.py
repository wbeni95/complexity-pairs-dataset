#!/usr/bin/env python3
"""Build index.json, the pairs table in README.md, and generated per-entry READMEs.

After the tables, the generated part of README.md lists, under "Sources we could not read", every source named in
an item's provenance.missing_sources; that section is omitted when no item has one.

Per-entry README.md files are generated only when missing or when they carry the
GENERATED marker; hand-written READMEs are left alone.

Output is deterministic (no timestamps) so CI can check freshness:
  python tools/build_index.py           # write files
  python tools/build_index.py --check   # exit 1 if anything is stale
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import LEVELS, REPO, discover_entries, load_entry, location_of  # noqa: E402

GENERATED = "<!-- generated from entry.json by tools/build_index.py; edit entry.json, not this file -->"
TABLE_START = "<!-- PAIRS-TABLE:START -->"
TABLE_END = "<!-- PAIRS-TABLE:END -->"
PAIR_TAGS = ("T1", "T2", "T3", "T4", "T5", "T8", "T9")  # tags that record a real asymptotic improvement
TAG_NAMES = {
    "T1": "exp → poly",
    "T2": "naive-exp → poly",
    "T3": "poly → faster poly",
    "T4": "randomized ↔ deterministic",
    "T5": "quantum → classical",
    "T6": "open / unpaired",
    "T7": "synthetic",
    "T8": "super-poly → faster super-poly",
    "T9": "quantum separation (query model)",
}


def summarize(entry_dir: Path, entry: dict) -> dict:
    level = entry["verification"]["level"]
    loc = location_of(entry_dir)
    tags = [entry["pair_type"], *entry.get("secondary_tags", [])]
    return {
        "id": entry["id"],
        "title": entry["title"],
        "path": entry_dir.relative_to(REPO).as_posix(),
        "location": loc,
        "pair_type": entry["pair_type"],
        "secondary_tags": entry.get("secondary_tags", []),
        "level": level,
        "validated": (loc == "pairs" and LEVELS.index(level) >= 1 and "T7" not in tags
                      and any(t in PAIR_TAGS for t in tags)),
        "lower_bounds": entry.get("lower_bounds", []),
        "has_quantum_algorithm": any(a["model"] == "quantum" for a in entry["algorithms"]),
        "algorithms": [
            {"name": a["name"], "model": a["model"], "time_complexity": a["time_complexity"],
             "implemented": bool(a.get("implementation"))}
            for a in entry["algorithms"]
        ],
        "sources": len(entry["sources"]),
        "provenance": entry.get("provenance", {"class": "literature"}),
        "proved": bool(entry.get("proof")),
    }


PROVENANCE_BADGE = {
    "own": "🟠 Own result",
    "own-extension": "🟠 Own extension",
    # yellow dot: probably our own finding; hourglass: a source that might contain it could not be read
    "undetermined": "🟡⏳ Undetermined (may be our own result)",
}
PENDING_BADGE = "⏳ Pending"
PROVED_BADGE = "✅ Proved"


def provenance_badge(prov: dict, proved: bool = False) -> str:
    """Green check mark for items whose every claim has a written proof here plus checks; orange label for the
    project's own results; yellow label (with the hourglass) for probable own results whose literature check could
    not be finished; a pending flag where a source could not be checked."""
    parts = [PROVED_BADGE] if proved else []
    if prov.get("class") in PROVENANCE_BADGE:
        parts.append(PROVENANCE_BADGE[prov["class"]])
    if prov.get("pending") and prov.get("class") != "undetermined":  # the undetermined label carries the hourglass
        parts.append(PENDING_BADGE)
    return (" " + " · ".join(parts)) if parts else ""


MISSING_SOURCES_HEADING = "### Sources we could not read"
MISSING_SOURCES_INTRO = (
    "These items are marked 🟡⏳ undetermined (or ⏳ pending) because a source that might already contain the result "
    "could not be read. If you have access to one of these sources and can tell us whether it contains the result, "
    "or know an open-access copy, please open an issue."
)


def _cell(text) -> str:
    """Text for one Markdown table cell: a single line, with literal pipes escaped."""
    return " ".join(str(text).split()).replace("|", "\\|")


def missing_source_ref(s: dict) -> str:
    """One unread source, in the reference style of the generated entry READMEs, with its DOI and/or URL link."""
    ref = f"{_cell(s['authors'])} ({s['year']}). *{_cell(s['title'])}*. {_cell(s['venue'])}."
    if s.get("doi"):
        ref += f" [doi:{_cell(s['doi'])}](https://doi.org/{s['doi'].replace('|', '%7C')})"
    if s.get("url"):
        ref += f" [{_cell(s['url'])}]({s['url'].replace('|', '%7C')})"
    return ref


def missing_sources_section(items: list[dict]) -> str:
    """The README section listing every unread source of every item (entry or theorem note), one row per source, in
    the order given; empty when no item lists missing sources."""
    lines = []
    for it in items:
        prov = it["provenance"]
        for s in prov.get("missing_sources", []):
            lines.append(f"| [{_cell(it['title'])}]({it['path']}) | {provenance_badge(prov).strip()} | "
                         f"{missing_source_ref(s)} | {_cell(s['status'])} | {_cell(s['needed_for'])} |")
    if not lines:
        return ""
    return "\n".join([MISSING_SOURCES_HEADING, "", MISSING_SOURCES_INTRO, "",
                      "| Item | Label | Source | Status | What it would decide |",
                      "|---|---|---|---|---|", *lines])


def discover_theorems() -> list[dict]:
    """Notes under theorems/<slug>/ (meta.json + README.md + verify.py): results that are not complexity pairs."""
    out = []
    for meta in sorted((REPO / "theorems").glob("*/meta.json")):
        m = json.loads(meta.read_text(encoding="utf-8"))
        out.append({
            "id": m["id"],
            "title": m["title"],
            "path": meta.parent.relative_to(REPO).as_posix(),
            "provenance": m.get("provenance", {"class": "literature"}),
            "proved": bool(m.get("proof")),
            "verify": m.get("verify", ""),
        })
    return out


def build_index(rows: list[dict], theorems: list[dict] | None = None) -> dict:
    count = lambda pred: sum(1 for r in rows if pred(r))  # noqa: E731
    theorems = theorems or []
    return {
        "schema": "schema/entry.schema.json",
        "counts": {
            "entries": len(rows),
            "validated_pairs": count(lambda r: r["validated"]),
            "open_problems_T6": count(lambda r: "T6" in [r["pair_type"], *r["secondary_tags"]]),
            "quantum_separations_T9_in_pairs": count(lambda r: "T9" in [r["pair_type"], *r["secondary_tags"]]
                                                     and r["location"] == "pairs"),
            "synthetic_T7": count(lambda r: r["pair_type"] == "T7"),
            "with_quantum_algorithm": count(lambda r: r["has_quantum_algorithm"]),
            "by_level": {lv: count(lambda r, lv=lv: r["level"] == lv) for lv in LEVELS},
            "by_type": {t: count(lambda r, t=t: r["pair_type"] == t) for t in TAG_NAMES},
            "proved_entries": count(lambda r: r["proved"]),
            "theorems": len(theorems),
            "proved_theorems": sum(1 for th in theorems if th["proved"]),
        },
        "entries": rows,
        "theorems": theorems,
    }


def short_complexity(text: str) -> str:
    """Leading bound of a complexity string: cut at the first top-level '; ', ', ', ': ', '. ' or ' ('."""
    depth = 0
    for i, ch in enumerate(text):
        if ch in "([":
            if depth == 0 and ch == "(" and text[i - 1:i] == " ":
                return text[:i - 1]
            depth += 1
        elif ch in ")]":
            depth = max(depth - 1, 0)
        elif depth == 0 and text[i:i + 2] in ("; ", ", ", ": ", ". "):
            return text[:i]
    return text


def readme_table(rows: list[dict], theorems: list[dict] | None = None) -> str:
    def fmt_algos(r):
        return "<br>".join(
            f"{a['name']}: {short_complexity(a['time_complexity'])}"
            + (" ⚛" if a["model"] == "quantum" else "")
            for a in r["algorithms"]
        )

    def table(sel):
        lines = ["| Entry | Type | Level | Algorithms (time: leading bound; exact statement in each entry) |",
                 "|---|---|---|---|"]
        for r in sel:
            tags = r["pair_type"] + ("+" + "+".join(r["secondary_tags"]) if r["secondary_tags"] else "")
            lines.append(f"| [{r['title']}]({r['path']}){provenance_badge(r['provenance'], r['proved'])} | {tags} | {r['level']} | {fmt_algos(r)} |")
        return "\n".join(lines)

    idx = build_index(rows, theorems)["counts"]
    verified = [r for r in rows if r["location"] == "pairs"]
    staging = [r for r in rows if r["location"] == "staging"]
    synthetic = [r for r in rows if r["location"] == "synthetic"]
    parts = [
        f"**{idx['validated_pairs']} validated pairs** (V1+, tagged T1–T5, T8 or T9) · "
        f"{idx['open_problems_T6']} open problems (T6) · {idx['quantum_separations_T9_in_pairs']} quantum query separations in pairs/ (T9) · "
        f"{idx['by_level']['V0']} staged (V0) · {idx['with_quantum_algorithm']} with a quantum algorithm (⚛) · "
        f"{idx['proved_entries']} entries and {idx['proved_theorems']} theorem notes proved here (✅)",
        "",
        "### Verified (`pairs/`, V1+)",
        "",
        table(verified),
        "",
        "### Staging (`staging/`, V0: cited, not independently checked)",
        "",
        table(staging),
    ]
    if synthetic:
        parts += ["", "### Synthetic (`synthetic/`, T7: not counted)", "", table(synthetic)]
    if theorems:
        lines = ["| Theorem | Verify |", "|---|---|"]
        for th in theorems:
            lines.append(f"| [{th['title']}]({th['path']}){provenance_badge(th['provenance'], th['proved'])} | `{th['verify']}` |")
        parts += ["", "### Theorems (`theorems/`: results that are not complexity pairs)", "", "\n".join(lines)]
    # after every table, in the order of the tables above; omitted when no item lists missing sources
    unread = missing_sources_section(verified + staging + synthetic + (theorems or []))
    if unread:
        parts += ["", unread]
    return "\n".join(parts)


def entry_readme(entry: dict) -> str:
    tags = entry["pair_type"] + "".join(f", {t}" for t in entry.get("secondary_tags", []))
    out = [
        GENERATED,
        f"# {entry['title']}",
        "",
        f"**Type:** {tags} ({TAG_NAMES[entry['pair_type']]}) · **Verification:** {entry['verification']['level']}",
        "",
        f"**Problem.** {entry['problem_statement']}",
        "",
        f"**Input.** {entry['input']['parameter']} Size: {entry['input']['size_measure']}",
        "",
        "| Algorithm | Model | Time | Space |",
        "|---|---|---|---|",
    ]
    for a in entry["algorithms"]:
        name = a["name"]
        if a.get("implementation"):
            name = f"[{name}]({a['implementation'].split(':')[0]})"
        out.append(f"| {name} | {a['model']} | {a['time_complexity']} | {a['space_complexity']} |")
    out += ["", f"**Relationship.** {entry['relationship']}", ""]
    if entry["caveats"]:
        out += [f"**Caveats.** {entry['caveats']}", ""]
    if entry["notes"]:
        out += [f"**Notes.** {entry['notes']}", ""]
    if entry.get("background"):
        out += ["**Background** (cited; not claims of this entry, and not covered by the check mark).", ""]
        out += [f"- {item['statement']} ({item['source']})" for item in entry["background"]]
        out.append("")
    out += [f"**Verification.** {entry['verification']['method']}", "", "**Sources.**", ""]
    for s in entry["sources"]:
        ref = f"- {s['authors']} ({s['year']}). *{s['title']}*."
        if s.get("venue"):
            ref += f" {s['venue']}."
        if s.get("doi"):
            ref += f" [doi:{s['doi']}](https://doi.org/{s['doi']})"
        if s.get("arxiv"):
            ref += f" [arXiv:{s['arxiv']}](https://arxiv.org/abs/{s['arxiv']})"
        if s.get("isbn"):
            ref += f" ISBN {s['isbn']}"
        out.append(ref)
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="do not write; exit 1 if outputs are stale")
    args = ap.parse_args(argv)

    entries = [(d, load_entry(d)) for d in discover_entries()]
    rows = sorted((summarize(d, e) for d, e in entries), key=lambda r: (r["location"] != "pairs", r["pair_type"], r["id"]))
    theorems = discover_theorems()
    outputs: dict[Path, str] = {
        REPO / "index.json": json.dumps(build_index(rows, theorems), indent=2, ensure_ascii=False) + "\n",
    }

    readme_path = REPO / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    if TABLE_START not in readme or TABLE_END not in readme:
        print(f"README.md lacks {TABLE_START} / {TABLE_END} markers", file=sys.stderr)
        return 2
    head, rest = readme.split(TABLE_START, 1)
    _, tail = rest.split(TABLE_END, 1)
    outputs[readme_path] = f"{head}{TABLE_START}\n{readme_table(rows, theorems)}\n{TABLE_END}{tail}"

    for d, e in entries:
        p = d / "README.md"
        if not p.exists() or p.read_text(encoding="utf-8").startswith(GENERATED):
            outputs[p] = entry_readme(e)

    stale = [p for p, text in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    if args.check:
        for p in stale:
            print(f"stale: {p.relative_to(REPO).as_posix()}  (run python tools/build_index.py)")
        return 1 if stale else 0
    for p in stale:
        p.write_text(outputs[p], encoding="utf-8", newline="\n")
        print(f"wrote {p.relative_to(REPO).as_posix()}")
    if not stale:
        print("everything up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""The front page of README.md: own-first tables, the generated at-a-glance block, the charts and every number of the
worked example, each pinned to the data it comes from (index.json, the PROOFS.md closed forms, the recorded run)."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_index  # noqa: E402
import make_charts  # noqa: E402
import savings_scenario  # noqa: E402
import validate  # noqa: E402

README = (ROOT / "README.md").read_text(encoding="utf-8")
IMG = ROOT / make_charts.IMG


def real_items():
    entries = [(d, validate.load_entry(d)) for d in validate.discover_entries()]
    rows = [build_index.summarize(d, e) for d, e in entries]
    return rows, build_index.discover_theorems()


class OwnFirstTests(unittest.TestCase):
    def test_order_is_own_then_undetermined_then_rest_and_stable(self):
        items = [{"id": i, "provenance": {"class": c}} for i, c in enumerate(
            ["literature", "undetermined", "own", "literature", "own-extension", "undetermined", "own"])]
        self.assertEqual([it["id"] for it in build_index.own_first(items)], [2, 4, 6, 1, 5, 0, 3])

    def test_readme_tables_list_own_results_first(self):
        start = README.index(build_index.TABLE_START)
        for heading in ("### Verified (", "### Theorems ("):
            i = README.index(heading, start)
            j = README.index("\n\n", README.index("|---", i))
            labels = [("own" if "🟠" in line else "und" if "🟡⏳" in line else "rest")
                      for line in README[i:j].splitlines() if line.startswith("| [")]
            rank = {"own": 0, "und": 1, "rest": 2}
            self.assertEqual(labels, sorted(labels, key=rank.get), heading)
            self.assertIn("own", labels)


class GlanceTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.theorems = real_items()
        self.block = build_index.glance_block(self.rows, self.theorems)

    def test_rows_add_up_to_the_totals(self):
        body = [line for line in self.block.splitlines() if line.startswith("| ") and "**Total**" not in line][1:]
        self.assertEqual(len(body), len(build_index.GLANCE_ROWS))
        nums = [[c.strip() for c in line.strip("|").split("|")[1:]] for line in body]
        entries = sum(int(n[0]) for n in nums)
        notes = sum(int(n[1]) for n in nums if n[1] != "–")
        proved = sum(int(n[2].split(" of ")[0]) for n in nums)
        self.assertEqual((entries, notes), (len(self.rows), len(self.theorems)))
        self.assertEqual(proved, sum(r["proved"] for r in self.rows) + sum(t["proved"] for t in self.theorems))
        self.assertIn(f"| **Total** | **{entries}** | **{notes}** | **{proved} of {entries + notes}** |", self.block)

    def test_groups(self):
        groups = [g for g, _, _ in build_index.glance_items(self.rows, self.theorems)]
        own = sum(r["provenance"]["class"] in ("own", "own-extension") for r in self.rows + self.theorems)
        self.assertEqual(groups.count("own"), own)
        rest = lambda r: r["provenance"]["class"] not in ("own", "own-extension", "undetermined")  # noqa: E731
        self.assertEqual(groups.count("cited"), sum(r["location"] == "staging" and rest(r) for r in self.rows))
        self.assertEqual(groups.count("syn"), sum(r["location"] == "synthetic" and rest(r) for r in self.rows))

    def test_readme_carries_the_block(self):
        self.assertIn(f"{build_index.GLANCE_START}\n{self.block}\n{build_index.GLANCE_END}", README)

    def test_items_chart_has_one_square_per_item_and_one_tick_per_proved_item(self):
        items = [(g, pr) for g, pr, _ in build_index.glance_items(self.rows, self.theorems)]
        for theme in make_charts.PALETTES:
            svg = (IMG / f"items-{theme}.svg").read_text(encoding="utf-8")
            self.assertEqual(svg, make_charts.items_svg(items, make_charts.PALETTES[theme]))
            squares = len(re.findall(r'<rect [^>]*width="(?:24|22.5)"', svg))
            self.assertEqual(squares, len(items))
            self.assertEqual(svg.count("<path "), sum(pr for _, pr in items))


class ChartTests(unittest.TestCase):
    def test_recorded_counts_equal_the_proved_formulas(self):
        make_charts.load_ledger()  # raises SystemExit otherwise

    def test_load_ledger_rejects_a_count_that_differs(self):
        real = make_charts.endpoint
        try:
            make_charts.endpoint = lambda n: real(n) + 1
            with self.assertRaises(SystemExit):
                make_charts.load_ledger()
        finally:
            make_charts.endpoint = real

    def test_chart_labels_match_the_data(self):
        fmt = make_charts.fmt
        led = make_charts.load_ledger()
        sq = led[make_charts.SQUARE_OFFSET]
        for theme in make_charts.PALETTES:
            comp = (IMG / f"comparisons-n1000-{theme}.svg").read_text(encoding="utf-8")
            for label in (fmt(333833500), fmt(1499500), fmt(1000), "223× fewer", f"{fmt(333834)}× fewer"):
                self.assertIn(label, comp)
            self.assertEqual(make_charts.cubic(1000), 333833500)
            self.assertEqual(make_charts.endpoint(1000), 1499500)
            steps = (IMG / f"steps-and-time-{theme}.svg").read_text(encoding="utf-8")
            self.assertIn(f"one core, CPython {led['_python']}", steps)
            same = (IMG / f"same-time-bigger-inputs-{theme}.svg").read_text(encoding="utf-8")
            for m in sq.values():
                n, t = m["n_values"][-1], m["timing"]["values"][-1]
                self.assertIn(f"n = {n}: {t * 1000:.1f} ms", same)


def coords(svg):
    """Data marks of a chart: every (x, y) of every path and circle."""
    pts = []
    for d in re.findall(r'<path d="([^"]+)"', svg):
        nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)]
        if d.startswith("M") and " l" not in d:  # absolute polylines only (the ticks of the items chart are relative)
            pts += list(zip(nums[0::2], nums[1::2]))
    pts += [(float(x), float(y)) for x, y in re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)"', svg)]
    return pts


class ChartGeometryTests(unittest.TestCase):
    def test_data_marks_stay_inside_the_gridlines(self):
        for name in ("steps-and-time", "same-time-bigger-inputs"):
            for theme in make_charts.PALETTES:
                svg = (IMG / f"{name}-{theme}.svg").read_text(encoding="utf-8")
                ys = [float(y1) for y1, y2 in re.findall(r'<line x1="[\d.]+" y1="([\d.]+)" x2="[\d.]+" y2="([\d.]+)"', svg)
                      if y1 == y2]
                lo, hi = min(ys), max(ys)
                pts = coords(svg)
                self.assertTrue(pts, name)
                for x, y in pts:
                    self.assertTrue(lo - 0.5 <= y <= hi + 0.5, f"{name}-{theme}: mark at y = {y} outside [{lo}, {hi}]")

    def test_axis_guard_refuses_out_of_range_values(self):
        with self.assertRaises(SystemExit):
            make_charts.in_range([1e-7], 1e-6, 1e-1, "test")

    def test_ticks_are_readable(self):
        self.assertEqual(make_charts.tick_colour("#ffffff"), "#1f2328")
        self.assertEqual(make_charts.tick_colour("#000000"), "#ffffff")

    def test_own_items_stay_own_wherever_they_are(self):
        self.assertEqual(make_charts.item_group("staging", "own"), "own")
        self.assertEqual(make_charts.item_group("synthetic", "undetermined"), "und")
        self.assertEqual(make_charts.item_group("staging", "literature"), "cited")


class UnitOfNTests(unittest.TestCase):
    """In the three merge entries n is the number of merges; the row has n + 1 piles."""

    def test_entries_define_n_as_merges(self):
        for slug in (make_charts.MERGE_LARGER, "max-merge-imbalance-cubic-dp-vs-endpoint-dp",
                     "min-merge-cost-smaller-part-cubic-dp-vs-closed-form"):
            entry = validate.load_entry(ROOT / "pairs" / slug)
            self.assertIn("number of merges", entry["input"]["parameter"], slug)

    def test_front_page_says_merges(self):
        flat = " ".join(README.split())
        self.assertNotRegex(flat, r"n = 1000 piles")
        self.assertIn("n = 1000 merges (1001 piles)", flat)
        for theme in make_charts.PALETTES:
            self.assertIn("n = 1000 merges (1001 piles)", (IMG / f"comparisons-n1000-{theme}.svg").read_text(encoding="utf-8"))
            self.assertIn("n (merges; n + 1 piles)", (IMG / f"steps-and-time-{theme}.svg").read_text(encoding="utf-8"))


class ReadmeNumberTests(unittest.TestCase):
    def test_worked_example_numbers_come_from_the_tool(self):
        r = savings_scenario.scenario(1000, 10_000, 15.0, 0.15, 1.8)
        expected = [
            f"{r['ns_per_comparison_old']:.0f} ns (cubic DP), {r['ns_per_comparison_new']:.0f} ns (endpoint DP)",
            f"| Compute time saved | {r['core_hours_per_day']:,.0f} core-hours | {r['core_hours_per_day'] * 365:,.0f} core-hours |",
            f"| Energy saved | {r['kwh_per_day']:.1f} kWh | {r['kwh_per_day'] * 365:,.0f} kWh |",
            f"| Electricity cost saved | ${r['cost_per_day']:.2f} | ${r['cost_per_day'] * 365:,.0f} |",
            f"| Cooling water saved | {r['water_l_per_day']:,.0f} L | {r['water_l_per_day'] * 365:,.0f} L |",
            f"ratio of comparisons ({r['ratio']:.0f}× at n = 1000)",
            f"about {int(r['seconds_old'] // 60)} min {r['seconds_old'] % 60:.0f} s with the cubic DP and about "
            f"{r['seconds_new']:.1f} s with the endpoint DP",
            f"(n = {r['rate_measured_at_n'][0]} and n = {r['rate_measured_at_n'][1]})",
            f"ledger/runs/{make_charts.LEDGER_RUN}.json",
        ]
        flat = " ".join(README.split())
        for text in expected:
            self.assertIn(" ".join(text.split()), flat)

    def test_less_time_paragraph_matches_the_recorded_run(self):
        sq = make_charts.load_ledger()[make_charts.SQUARE_OFFSET]
        flat = " ".join(README.split())
        for name, words in (("enumeration of all k with three candidate roots", "listing every candidate takes"),
                            ("sweep over one interval per root", "one interval per root takes"),
                            ("root groups of equal bit length", "root-group method takes")):
            m = sq[name]
            n, t = m["n_values"][-1], m["timing"]["values"][-1]
            self.assertIn(f"{words} {t * 1000:.1f} ms at n = {n}", flat)

    def test_scenario_tool_runs(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(savings_scenario.main([]), 0)
        self.assertIn("333,833,500", out.getvalue())
        self.assertIn("1,499,500", out.getvalue())


if __name__ == "__main__":
    unittest.main()

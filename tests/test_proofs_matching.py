"""Checks for pairs/bipartite-matching-kuhn-vs-hopcroft-karp/PROOFS.md, sections 5-12.

Kuhn: each search succeeds iff an augmenting path starts at its root, failed roots stay without augmenting paths,
and the final matching has none. Hopcroft-Karp: at every phase the BFS target and layers match an independent
alternating BFS, the paths found are vertex-disjoint shortest augmenting paths that no shortest path avoids, the
shortest length grows by at least 2 (with a sensitivity control for the maximality check), and the number of
phases respects the bound of Theorem HK. The matching states
are read from the running code with sys.settrace (the code is unchanged). Also: the Kuhn count on G_k padded with
isolated vertices, the Edmonds-matrix oracle, the unit-capacity flow correspondence, and the space bounds. All inputs
come from fixed seeds. Runs in a few seconds.
"""
import importlib.util
import math
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "bipartite-matching-kuhn-vs-hopcroft-karp"
sys.path.insert(0, str(REPO / "tests"))

from proof_space import peak_words  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _load(E / "harness.py", "tp_bm_h")
KUHN_FILE = E / "implementations" / "kuhn.py"
HK_FILE = E / "implementations" / "hopcroft_karp.py"
KUHN = _load(KUHN_FILE, "tp_bm_k").matching_kuhn
HK = _load(HK_FILE, "tp_bm_hk").matching_hopcroft_karp
EK = _load(REPO / "pairs" / "max-flow-edmonds-karp-vs-dinic" / "implementations" / "edmonds_karp.py",
           "tp_bm_ek").max_flow_edmonds_karp


def _line_of(path, text):
    for k, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip() == text:
            return k
    raise AssertionError(f"line {text!r} not found in {path}")


def trace_lines(func, graph, impl_file, func_name, lines):
    """Run func(graph); at each listed line record (line, copies of selected locals); also the final locals."""
    target = str(Path(impl_file).resolve())
    events, final = [], {}

    def snap(loc):
        return {k: (list(v) if isinstance(v, list) else v) for k, v in loc.items()
                if k in ("match_l", "match_r", "root", "dist", "target", "size")}

    def local(frame, event, arg):
        if event == "line" and frame.f_lineno in lines:
            events.append((frame.f_lineno, snap(frame.f_locals)))
        elif event == "return":
            final.update(snap(frame.f_locals))
            final["value"] = arg
        return local

    def glob(frame, event, arg):
        if frame.f_code.co_name == func_name and str(Path(frame.f_code.co_filename).resolve()) == target:
            return local
        return None

    sys.settrace(glob)
    try:
        func(graph)
    finally:
        sys.settrace(None)
    return events, final


def levels(graph, match_l, match_r):
    """lambda(x): BFS level of left vertex x in the digraph x -> match_r[v] (v in adj[x], v matched)."""
    n_left, n_right, adj = graph
    lam = [None] * n_left
    frontier = [x for x in range(n_left) if match_l[x] == -1]
    for x in frontier:
        lam[x] = 0
    t = 0
    while frontier:
        nxt = []
        for x in frontier:
            for v in adj[x]:
                w = match_r[v]
                if w != -1 and lam[w] is None:
                    lam[w] = t + 1
                    nxt.append(w)
        frontier = nxt
        t += 1
    return lam


def shortest_augmenting(graph, match_l, match_r, roots=None, banned=frozenset()):
    """Length (edges) of a shortest augmenting path from the given free left roots avoiding `banned`, or None."""
    n_left, n_right, adj = graph
    if roots is None:
        roots = [x for x in range(n_left) if match_l[x] == -1]
    frontier = [x for x in roots if ("L", x) not in banned]
    seen = set(frontier)
    t = 0
    while frontier:
        nxt = []
        for x in frontier:
            for v in adj[x]:
                if ("R", v) in banned:
                    continue
                w = match_r[v]
                if w == -1:
                    return 2 * t + 1
                if ("L", w) not in banned and w not in seen:
                    seen.add(w)
                    nxt.append(w)
        frontier = nxt
        t += 1
    return None


def path_union(rng):
    """Disjoint paths whose first greedy phase tends to pick the wrong edges (many Hopcroft-Karp phases)."""
    adj, n_right = [], 0
    for _ in range(rng.randint(1, 5)):
        j = rng.randint(1, 7)
        R = list(range(n_right, n_right + j))
        n_right += j
        block = [(R[i - 2], R[i - 1]) for i in range(2, j + 1)] + [(R[0],)]
        if rng.random() < 0.5:
            block = [tuple(reversed(b)) for b in block]
        adj.extend(block)
    return len(adj), n_right, tuple(adj)


def instances(tag, count):
    rng = random.Random(f"tp-bm|{tag}")
    for t in range(count):
        kind = t % 3
        if kind == 0:
            yield H.generate(rng.randint(0, 40), rng)
        elif kind == 1:
            yield path_union(rng)
        else:
            yield H.adversarial(rng.randint(1, 3))


def matched_vertices(match_l, match_r):
    return {("L", x) for x, v in enumerate(match_l) if v != -1} | {("R", v) for v, x in enumerate(match_r) if x != -1}


class MatchingProofChecks(unittest.TestCase):
    def test_kuhn_searches(self):
        start = _line_of(KUHN_FILE, "seen = [False] * n_right")
        for graph in instances("kuhn", 240):
            n_left = graph[0]
            events, final = trace_lines(KUHN, graph, KUHN_FILE, "matching_kuhn", {start})
            self.assertEqual(len(events), n_left)
            states = [e[1] for e in events] + [final]
            failed = []
            for r in range(n_left):
                before, after = states[r], states[r + 1]
                root = before["root"]
                self.assertEqual(root, r)
                self.assertEqual(before["match_l"][root], -1)                      # the root is free
                for x in failed:                                                   # persistence (Lemma K4)
                    self.assertIsNone(shortest_augmenting(graph, before["match_l"], before["match_r"], [x]))
                has_path = shortest_augmenting(graph, before["match_l"], before["match_r"], [root]) is not None
                grew = sum(v != -1 for v in after["match_l"]) == sum(v != -1 for v in before["match_l"]) + 1
                same = after["match_l"] == before["match_l"]
                self.assertTrue(grew if has_path else same, (graph, r))           # Lemmas K2, K3
                if not has_path:
                    failed.append(root)
            self.assertIsNone(shortest_augmenting(graph, final["match_l"], final["match_r"]))
            self.assertEqual(final["value"], sum(v != -1 for v in final["match_l"]))

    def test_hopcroft_karp_phases(self):
        phase_start = _line_of(HK_FILE, "dist = [INF] * n_left")
        after_bfs = _line_of(HK_FILE, "ptr = [0] * n_left")
        phases_seen = 0
        for graph in instances("hk", 240):
            n_left, n_right, adj = graph
            V = n_left + n_right
            events, final = trace_lines(HK, graph, HK_FILE, "matching_hopcroft_karp", {phase_start, after_bfs})
            starts = [e[1] for e in events if e[0] == phase_start] + [final]
            bfs = [e[1] for e in events if e[0] == after_bfs]
            phases = len(starts) - 1                     # one BFS pass per loop body, the last one finds nothing
            self.assertEqual(len(bfs), phases - 1)
            bound = min(i + V // (2 * i + 2) for i in range(0, V + 1)) + 1 if V else 1
            self.assertLessEqual(phases, bound, graph)
            if V:
                self.assertLess(phases, math.sqrt(2 * V) + 1, graph)
            prev = None
            for p in range(phases):
                M_l, M_r = starts[p]["match_l"], starts[p]["match_r"]
                ell = shortest_augmenting(graph, M_l, M_r)
                if p == phases - 1:
                    self.assertIsNone(ell)                                         # final phase: none left
                    continue
                self.assertIsNotNone(ell)
                if prev is not None:
                    self.assertGreaterEqual(ell, prev + 2)                         # Lemma HK4
                prev = ell
                target, dist = bfs[p]["target"], bfs[p]["dist"]
                self.assertEqual(2 * target - 1, ell)                              # Lemma HK1
                lam = levels(graph, M_l, M_r)
                for x in range(n_left):
                    if lam[x] is not None and lam[x] <= target:
                        self.assertEqual(dist[x], lam[x])
                    else:
                        self.assertEqual(dist[x], n_left + n_right + 1)
                N_l, N_r = starts[p + 1]["match_l"], starts[p + 1]["match_r"]
                banned = {("L", x) for x in range(n_left) if M_l[x] != N_l[x]} | \
                         {("R", v) for v in range(n_right) if M_r[v] != N_r[v]}
                M_edges = {(x, v) for x, v in enumerate(M_l) if v != -1}
                N_edges = {(x, v) for x, v in enumerate(N_l) if v != -1}
                diff = M_edges ^ N_edges
                r = len(N_edges) - len(M_edges)
                self.assertGreaterEqual(r, 1)
                self.assertEqual(len(diff), r * ell)                               # r paths of ell edges (HK2)
                # every component of the symmetric difference is an M-augmenting path
                nodes = {("L", x) for x, _ in diff} | {("R", v) for _, v in diff}
                self.assertEqual(len(nodes), r * (ell + 1))
                self.assertEqual(len(nodes - matched_vertices(M_l, M_r)), 2 * r)
                # maximality (HK3): no shortest M-augmenting path avoids the vertices of the paths found
                self.assertNotEqual(shortest_augmenting(graph, M_l, M_r, banned=frozenset(banned)), ell)
                # sensitivity control: un-banning one found path must expose a shortest path again
                comp, todo = set(), [next(iter(nodes))]
                while todo:
                    node = todo.pop()
                    if node in comp:
                        continue
                    comp.add(node)
                    for x, v in diff:
                        if node == ("L", x) or node == ("R", v):
                            todo.extend((("L", x), ("R", v)))
                self.assertEqual(len(comp), ell + 1)
                self.assertEqual(shortest_augmenting(graph, M_l, M_r, banned=frozenset(banned - comp)), ell)
                phases_seen += 1
            self.assertEqual(final["value"], sum(v != -1 for v in final["match_l"]))
            self.assertEqual(final["value"], KUHN(graph))
        self.assertGreater(phases_seen, 300)

    def test_kuhn_count_on_padded_family(self):
        for k in range(1, 6):
            expected = (7 * k ** 6 + 9 * k ** 4 + 11 * k ** 2 - 3 * k) // 6
            n_left, n_right, adj = H.adversarial(k)
            for pad_right in (0, 1, 3, 7):
                for pad_left in (0, 2):
                    lists = tuple(H.CountingNeighbours(nb) for nb in adj + ((),) * pad_left)
                    H._scans = 0
                    KUHN((n_left + pad_left, n_right + pad_right, lists))
                    self.assertEqual(H._scans, expected, (k, pad_left, pad_right))

    def test_edmonds_oracle(self):
        P = H.P
        s, m = 4, P                                            # Lucas-Lehmer test for 2^61 - 1
        for _ in range(61 - 2):
            s = (s * s - 2) % m
        self.assertEqual(s, 0)
        self.assertLess(160 / (P - 1), 1e-15)
        checked = 0
        for a in range(0, 4):
            for b in range(0, 4):
                for mask in range(1 << (a * b)):
                    adj = tuple(tuple(v for v in range(b) if mask >> (u * b + v) & 1) for u in range(a))
                    graph = (a, b, adj)
                    self.assertIs(H.check(graph, KUHN(graph)), True, graph)
                    checked += 1
        self.assertEqual(checked, sum(1 << (a * b) for a in range(4) for b in range(4)))

    def test_unit_capacity_flow(self):
        rng = random.Random("tp-bm|flow")
        for t in range(150):
            n_left, n_right, adj = H.generate(rng.randint(0, 40), rng)
            s, t_ = n_left + n_right, n_left + n_right + 1
            edges = tuple((s, u, 1) for u in range(n_left)) + \
                tuple((u, n_left + v, 1) for u in range(n_left) for v in adj[u]) + \
                tuple((n_left + v, t_, 1) for v in range(n_right))
            self.assertEqual(EK((n_left + n_right + 2, s, t_, edges)), KUHN((n_left, n_right, adj)))

    def test_space(self):
        for graph in instances("space", 60):
            n_left, n_right, _ = graph
            _, pk = peak_words(KUHN, (graph,), KUHN_FILE)
            _, ph = peak_words(HK, (graph,), HK_FILE)
            self.assertTrue(n_left + n_right <= pk <= 3 * n_left + 2 * n_right, (graph, pk))
            self.assertTrue(n_left + n_right <= ph <= 5 * n_left + n_right, (graph, ph))


if __name__ == "__main__":
    unittest.main()

"""Probe for pairs/max-flow-edmonds-karp-vs-dinic: how do the two implementations scale on the random dense
networks of generate_scaling (G(n, 0.5), capacities 1..100, s = 0, t = n - 1), compared with their
worst-case bounds V E^2 = Theta(n^5) and V^2 E = Theta(n^4)?

Part 1 (deterministic): number of Edmonds-Karp augmentations and of Dinic phases / augmentations on the
V2-seeded instances (random.Random(f"{entry_id}|v2|{n}")), to explain the measured growth.
Part 2 (timing, console): validator-style fits against the claimed bounds and against lower powers.

Run from the repository root:  python experiments/2026-10-07_max_flow_probe.py

Outcome (2026-10-07). Part 1 (deterministic): for n = 20, 40, 80, 160 (E = 191, 770, 3182, 12754) Edmonds-Karp made
21, 40, 87, 176 augmentations (V E = 3820 ... 2040640) and Dinic needed 4, 3, 2, 3 phases (same 21, 40, 87, 176
augmentations). Part 2 (console, n = 20..160): Edmonds-Karp alpha = 0.558 vs n^5, 0.924 vs n^3, 1.402 vs n^2;
Dinic alpha = 0.479 vs n^4, 0.638 vs n^3, 0.965 vs n^2. The timings are irregular (e.g. EK 0.19 ms at n = 30 and
1.15 ms at n = 40), probably because the BFS stops when t is reached and the work varies by instance (not investigated).
Conclusion: random dense networks are far from both worst cases; INCONCLUSIVE, entry stays at V1.
"""
import importlib.util
import random
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("probe_helpers", ROOT / "experiments" / "2026-10-07_probe_helpers.py")
ph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph)

E = "max-flow-edmonds-karp-vs-dinic"
H = ph.harness_of(E)


def residual(network):
    n, s, t, edges = network
    to, cap, adj = [], [], [[] for _ in range(n)]
    for u, v, c in edges:
        adj[u].append(len(to)); to.append(v); cap.append(c)
        adj[v].append(len(to)); to.append(u); cap.append(0)
    return n, s, t, to, cap, adj


def ek_augmentations(network):
    n, s, t, to, cap, adj = residual(network)
    count = flow = 0
    while True:
        par = [-1] * n
        par[s] = -2
        q = deque([s])
        while q and par[t] == -1:
            u = q.popleft()
            for e in adj[u]:
                if cap[e] > 0 and par[to[e]] == -1:
                    par[to[e]] = e
                    q.append(to[e])
        if par[t] == -1:
            return flow, count
        b, v = None, t
        while v != s:
            e = par[v]; b = cap[e] if b is None else min(b, cap[e]); v = to[e ^ 1]
        v = t
        while v != s:
            e = par[v]; cap[e] -= b; cap[e ^ 1] += b; v = to[e ^ 1]
        flow += b
        count += 1


def dinic_counts(network):
    n, s, t, to, cap, adj = residual(network)
    phases = augs = flow = 0
    while True:
        level = [-1] * n
        level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for e in adj[u]:
                if cap[e] > 0 and level[to[e]] == -1:
                    level[to[e]] = level[u] + 1
                    q.append(to[e])
        if level[t] == -1:
            return flow, phases, augs
        phases += 1
        it, path, u = [0] * n, [], s
        while True:
            if u == t:
                f = min(cap[e] for e in path)
                for e in path:
                    cap[e] -= f; cap[e ^ 1] += f
                flow += f; augs += 1; path = []; u = s
                continue
            arcs = adj[u]
            while it[u] < len(arcs) and not (cap[arcs[it[u]]] > 0 and level[to[arcs[it[u]]]] == level[u] + 1):
                it[u] += 1
            if it[u] < len(arcs):
                path.append(arcs[it[u]]); u = to[arcs[it[u]]]
            else:
                if not path:
                    break
                e = path.pop(); u = to[e ^ 1]; it[u] += 1


print("Part 1: counts on the V2-seeded G(n, 0.5) instances")
for n in (20, 40, 80, 160):
    g = H.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
    m = len(g[3])
    f1, aug = ek_augmentations(g)
    f2, phases, daug = dinic_counts(g)
    assert f1 == f2
    print(f"  n={n}: E={m}, flow={f1}; Edmonds-Karp augmentations {aug} (V E = {n * m}); "
          f"Dinic phases {phases}, augmentations {daug}", flush=True)

print("Part 2: timing on generate_scaling")
ns = [20, 30, 40, 60, 80, 120, 160]
for cost in ("n**5", "n**3", "n**2"):
    ph.probe(E, "implementations/edmonds_karp.py:max_flow_edmonds_karp", "generate_scaling", cost, ns, label=f"Edmonds-Karp vs {cost}")
for cost in ("n**4", "n**3", "n**2"):
    ph.probe(E, "implementations/dinic.py:max_flow_dinic", "generate_scaling", cost, ns, label=f"Dinic vs {cost}")

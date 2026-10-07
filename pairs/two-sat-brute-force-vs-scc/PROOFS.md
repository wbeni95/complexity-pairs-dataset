# Proofs: 2-SAT, brute force vs Aspvall–Plass–Tarjan

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code)
about its problem and its two algorithms, from first principles and from the code in this folder. Sections 1 and 2
prove the exact operation counts, for every size of their domains. Sections 3 to 9 prove the rest: the correctness
of brute force, the implication graph and the satisfiability criterion, the correctness of the iterative Tarjan
search as implemented, the time and space bounds, the brute-force worst case for every m ≥ 1, the invariance of the
brute-force count under renaming, and the caveats. Each proof is followed by the deterministic scripts or tests that
check it and the ranges they check; a check covers only those ranges, the proofs cover the general statements. The
NP-completeness of 3-SAT is not a claim of this entry; it is listed in the `background` field of `entry.json` with its
source, and nothing below depends on it. Citations give credit; they are never part of a proof.

## Counting convention

`harness.py`, class `CountingLit`: every arithmetic method (`__abs__`, `__neg__`, `__add__`, `__sub__`, `__mul__`,
`__and__`, `__rshift__`, `__xor__` and the reflected forms such as `__rmul__`, `__rrshift__`) adds 1 to the module
counter `_ops` through `_arith` and returns a new `CountingLit`; every comparison adds 1 through `_cmp` and returns a
plain bool; `__index__` (also used as `__int__`), `__hash__` and `__bool__` each add 1. `generate_scaling(n, rng)`
raises for n < 3, otherwise returns (n, clauses) for the family W_n with every literal a `CountingLit`, and sets
`_ops = 0`; `reported_cost(output)` returns `_ops`. So the domain of both counts is n ≥ 3.

A binary operation with a `CountingLit` operand counts 1 (with a plain left operand the int method returns
`NotImplemented` and Python calls the reflected method); `x == y` with a plain int x and a `CountingLit` y also
counts 1 (through the reflected `__eq__`). Reading or writing a list element at a `CountingLit` position calls
`__index__` (1 count); at a plain int position nothing counts. Plain: the loop variables `root` (from `range`), `i`,
the mask, `counter`, `num_comps`, and the values stored in `index`, `low`, `on_stack`, `comp`.

**The family W_n** (`_family(n)`), in this order: the star clauses (x1 ∨ x_j) for j = 2, …, n; the core
(x2 ∨ x3), (x2 ∨ ¬x3), (¬x2 ∨ x3), (¬x2 ∨ ¬x3); the chain (¬x_j ∨ x_{j+1}) for j = 1, …, n − 1; m = 2n + 2
clauses of two literals. The core alone is unsatisfiable (every value of (x2, x3) falsifies one of its clauses).

## 1. Brute force: (n + 7)2^(n−1) + 2 literal evaluations, 3(n + 7)2ⁿ + 12 operations

**Statement.** For every n ≥ 3, `two_sat_brute_force` on W_n makes exactly (n + 7)2^(n−1) + 2 literal evaluations
and 3(n + 7)2ⁿ + 12 counted operations (6 per evaluation).

**Proof.** *Six operations per evaluation:* `((mask >> (abs(lit) - 1)) & 1) == (lit > 0)` makes `__abs__`,
`__sub__`, `__rrshift__` (plain mask on the left), `__and__`, `__gt__` and the final `__eq__` (returning a plain
bool); nothing else in the loop counts. W_n is unsatisfiable, so all 2ⁿ masks are examined; each scans the clauses
in order, each clause until a true literal, and stops at the first falsified clause. The chain is never reached,
because the core falsifies every mask that reaches it.

*Masks with x1 true (2^(n−1)).* Each star clause is satisfied by its first literal: n − 1 evaluations. The core
then costs, for (x2, x3) = (1, 1): 1 + 1 + 2 + 2 = 6 (it fails at (¬x2 ∨ ¬x3)); (1, 0): 1 + 1 + 2 = 4 (fails at
(¬x2 ∨ x3)); (0, 1): 2 + 2 = 4 (fails at (x2 ∨ ¬x3)); (0, 0): 2 (fails at (x2 ∨ x3)). Each pair occurs for
2^(n−3) masks: 16 · 2^(n−3) = 2^(n+1). In all (n − 1)2^(n−1) + 2^(n+1).

*Masks with x1 false (2^(n−1)).* Star clause (x1 ∨ x_j) costs 2 evaluations and fails iff x_j is false, so the
scan stops at the first j ≥ 2 with x_j false, after 2(j − 1) evaluations; 2^(n−j) masks have that first j. The
single mask with x2 = … = x_n true passes all star clauses (2(n − 1)) and then costs 6 in the core. Using
Σ_{i=1..N} i·2^(−i) = 2 − (N + 2)2^(−N) with N = n − 1:
Σ_{j=2..n} 2(j − 1)2^(n−j) = 2^n · Σ_{i=1..n−1} i·2^(−i) = 2^(n+1) − 2n − 2, so this half costs
2^(n+1) − 2n − 2 + 2(n − 1) + 6 = 2^(n+1) + 2.

Total (n − 1)2^(n−1) + 2^(n+1) + 2^(n+1) + 2 = (n + 7)2^(n−1) + 2 evaluations, and 6 times that is 3(n + 7)2ⁿ + 12.

**Check.** `experiments/2026-10-07b_two_sat_counts.py` (n = 3..16). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "2-SAT brute 3(n+7)2^n+12": n = 3..16 (includes the V2 sizes n = 8, 10, …, 16; n < 3 raises, as
stated). `experiments/2026-10-07_count_proof_checks.py`, group `sat`, line "2-SAT brute: x1 true (n-1)2^(n-1) +
2^(n+1), x1 false 2^(n+1) + 2 evaluations, 6 operations each": n = 3..14.

## 2. Aspvall–Plass–Tarjan: 49(n + 2) (building 28n + 28, Tarjan search 21n + 70)

**Statement.** For every n ≥ 3, `two_sat_scc` on W_n makes exactly 49(n + 2) counted operations: 14 per clause to
build the implication graph (28n + 28), and 21n + 70 in the iterative Tarjan search, split as stated in
`entry.json`: adjacency-list reads 3n + 11, index tests 4n + 4, tree-edge updates 3n + 6, on-stack tests 3n + 2,
low updates on the 11 edges into the stack 33, low updates of parents 3n + 4, root tests 2n + 4, pops 3n + 6.

**Proof.** *Building (14 per clause).* `_node(lit)` makes `abs(lit)`, `- 1`, `2 * v` (through `__rmul__`),
`lit < 0` and the addition of that bool (5), and returns a `CountingLit`. Each clause has two literals, so `a` and
`b` cost 10, and `adj[a ^ 1]`, `adj[b ^ 1]` cost `__xor__` and `__index__` each (4). Total 14(2n + 2) = 28n + 28.
The adjacency lists hold the `CountingLit` nodes `a`, `b`.

*The implication graph.* Write P_v = 2(v − 1) for x_v and N_v = 2v − 1 for ¬x_v. Clause (a ∨ b) appends b to
`adj[a ^ 1]` and then a to `adj[b ^ 1]`. In the order the code builds them, the lists are:
N1: P2, P3, …, P_n; N2: P1, P3, N3, N1; N3: P1, P2, N2, N2; N_j (4 ≤ j ≤ n): P1, N_{j−1}; P1: P2;
P2: P3, N3, P3; P3: P2, N2, and P4 if n ≥ 4; P_j (4 ≤ j ≤ n − 1): P_{j+1}; P_n (n ≥ 4): none. That is 4n + 4 = 2m
edges.

*The search.* The roots are the plain ints 0, 1, …, 2n − 1; every other node is reached through an adjacency list,
so it is a `CountingLit`. From root P1 (= 0) the search runs:
1. P1 → P2 → P3 (tree edges). At P3 the edge to P2 meets a node on the stack; P3 → N2 (tree).
2. At N2 the edges to P1 and P3 meet the stack; N2 → N3 (tree). All four edges of N3 meet the stack; N3 finishes
   (low 0, not a root).
3. N2 → N1 (tree). The edges of N1 to P2, P3 meet the stack; for n ≥ 4, N1 → P4 → P5 → … → P_n (tree edges); these
   finish in reverse order, each as a singleton component (its low stays its own index), so P4, …, P_n are popped;
   the edges of N1 to P5, …, P_n then find nodes no longer on the stack. N1 finishes (low 1), then N2 (low 0).
4. Back at P3, the edge to P4 (n ≥ 4) finds a node off the stack; P3 finishes. At P2 the edges to N3 and P3 meet
   the stack; P2 finishes; P1 finishes and pops the component {N1, N3, N2, P3, P2, P1}.
5. The later roots N_4, …, N_n (in this order; every other node is visited) each read their two edges, to P1 and
   N_{j−1}, both visited and off the stack, and pop themselves.

So the tree edges are P1P2, P2P3, P3N2, N2N3, N2N1, N1P4 and P4P5, …, P_{n−1}P_n: n + 2 of them (for n = 3 the
first five). The 11 non-tree edges that meet the stack are P3→P2, N2→P1, N2→P3, the four edges of N3, N1→P2,
N1→P3, P2→N3 and the second P2→P3. The other 3n + 2 − 11 non-tree edges find nodes off the stack.

*Counting, event by event.* (Counting nodes: P2, P3, N2, N3, N1, P4, …, P_n, that is n + 2 nodes.)
- `edges = adj[v]` runs once per iteration of the work loop, deg(v) + 1 times per node, and counts only at counting
  v: (3 + 1) + (deg P3 + 1) + 5 + 5 + n + 2(n − 4) + 1 with deg P3 = 3 for n ≥ 4 gives 3n + 11; for n = 3,
  4 + 3 + 5 + 5 + 3 = 20 = 3n + 11 as well.
- `index[w] == -1` once per edge, w always counting: 4n + 4.
- A tree edge adds `index[w] = low[w] = counter` (2) and `on_stack[w] = True` (1): 3(n + 2).
- A non-tree edge adds `on_stack[w]` (1): (4n + 4) − (n + 2) = 3n + 2.
- An edge that meets the stack adds `low[v] = min(low[v], index[w])`: 3 at a counting v (read, read, write); all 11
  such edges leave counting nodes: 33.
- Finishing a node with a parent adds `low[u] = min(low[u], low[v])`: 3 if the parent u is counting, 1 if it is
  the plain root (only P2, parent P1): 3(n + 1) + 1 = 3n + 4.
- `low[v] == index[v]` costs 2 at each of the n + 2 counting nodes and nothing at the plain roots: 2n + 4.
- Popping a counting node w costs `on_stack[w] = False`, `comp[w] = num_comps` and `w == v` (3); popping a plain
  root costs nothing. Counting pops: the n − 3 singletons P4, …, P_n and the 5 counting members of the big
  component: 3(n − 3) + 15 = 3n + 6.

The sum is (3 + 4 + 3 + 3 + 3 + 2 + 3)n + (11 + 4 + 6 + 2 + 33 + 4 + 4 + 6) = 21n + 70. The final loop compares
`comp[0] == comp[1]` on plain ints; P1 and N1 lie in the same component, so it returns `None` at once. Total
28n + 28 + 21n + 70 = 49(n + 2).

**Check.** `experiments/2026-10-07b_two_sat_counts.py` (the V2 sizes). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "APT 49(n+2)": n = 3..300 and the V2 sizes n = 1000, 2000, 4000, 8000, 16000, 32000 (n < 3
raises, as stated); line "APT split: build 28n+28, Tarjan DFS 21n+70": n = 3..59.
`experiments/2026-10-07_count_proof_checks.py`, group `sat`, line "2-SAT Aspvall-Plass-Tarjan: build 28n+28 and the
eight Tarjan categories (sum 21n+70)": n = 3..119, each counted operation attributed to its source line.

## Conventions for sections 3 to 9

A formula is (n, clauses); a clause is a tuple of 0, 1 or 2 non-zero integers (v for x_v, −v for ¬x_v) and means the
disjunction of its literals; an empty clause is false, and a unit clause (l) is the same constraint as (l ∨ l). An
assignment is identified with its mask (bit v − 1 is the value of x_v). For a literal l, ¬l is −l. m is the number
of clauses.

Time is counted in the unit-cost word model: an executed line whose operands have O(1) words costs O(1), and building a
list of k entries costs O(k). O and Θ are the usual asymptotic bounds over the inputs: a bound may fail on at most
finitely many inputs, never on an infinite family; where a size parameter can be 0 (m), the bounds carry an explicit + 1
or the hypothesis m ≥ 1, so that no infinite family of inputs violates them. Space counts the input (measured as n + m
numbers, as in `input.size_measure`), the working storage and the output, in words.

## 3. Brute force: correctness

**Statement** (`algorithms[0].correctness`; `brute_force.py` docstring). `two_sat_brute_force` returns None iff the
formula is unsatisfiable, and otherwise a satisfying assignment (the one with the smallest mask).

**Proof.** The test `((mask >> (abs(lit) - 1)) & 1) == (lit > 0)` is true iff the literal is true under the mask. The
literal loop breaks at the first true literal; its `else` branch runs iff the clause is false (including an empty
clause) and moves on to the next mask; the clause loop's `else` branch runs iff every clause is true, and then the
function returns the assignment read off the mask. Masks are tried in increasing order, so the function returns the
satisfying mask with the smallest value, or None iff there is none. ∎

**Check.** `tests/test_proofs_two_sat.py`, `test_correctness_and_components`: on every formula with n = 3 made of at
most 3 distinct clauses from the 28 clauses with at most two literals (3683 formulas) and on 800 seeded random 2-CNF
formulas (n = 1..25, unit and empty clauses included), the output for n ≤ 10 is None exactly when no mask satisfies
the formula, and otherwise satisfies every clause. Also the validator's V1 battery.

## 4. The implication graph

**Statement** (`algorithms[1].idea`; `aspvall_plass_tarjan.py` docstring, step 1). The graph built by `two_sat_scc`
has the 2n literals as nodes and, for each clause (l₁ ∨ l₂) (with l₁ = l₂ for a unit clause), the two edges
¬l₁ → l₂ and ¬l₂ → l₁: 2m edges. Along every edge, and hence along every path, a satisfying assignment that makes the
start literal true makes the end literal true.

**Proof.** `_node(lit)` = 2(|lit| − 1) + [lit < 0], so x_v is node 2(v − 1), ¬x_v is node 2(v − 1) + 1, and the node
of ¬l is the node of l with its lowest bit flipped, `node ^ 1`. For a clause, `a = _node(clause[0])` and
`b = _node(clause[-1])` (the same literal for a unit clause), and the code appends b to `adj[a ^ 1]` and a to
`adj[b ^ 1]`: the edges ¬l₁ → l₂ and ¬l₂ → l₁. (An empty clause makes the function return None before the graph is
used; the formula is then unsatisfiable.) The clause l₁ ∨ l₂ is true under an assignment iff ¬l₁ true implies l₂
true, iff ¬l₂ true implies l₁ true; so each edge is an implication that every satisfying assignment respects, and by
induction so is every path. ∎

## 5. The satisfiability criterion and the assignment

**Statement** (`algorithms[1].correctness`, `idea`; docstring, step 3). Let comp be any numbering of the nodes that
gives the nodes of one strongly connected component (SCC) the same number, different SCCs different numbers, and
satisfies comp[u] ≥ comp[v] for every edge u → v (section 6 shows that the code computes such a numbering). Then the
formula is unsatisfiable iff some x_v and ¬x_v lie in the same SCC; otherwise the assignment "x_v true iff
comp[x_v] < comp[¬x_v]" satisfies every clause. Hence `two_sat_scc` returns None iff the formula is unsatisfiable, and
otherwise a satisfying assignment.

**Proof.** If x_v and ¬x_v lie in one SCC, there are paths x_v ⇝ ¬x_v and ¬x_v ⇝ x_v; by section 4 a satisfying
assignment would make ¬x_v true if x_v is true and x_v true if ¬x_v is true, which is impossible. Otherwise
comp[x_v] ≠ comp[¬x_v] for every v, and under the stated assignment a literal l is true iff comp[l] < comp[¬l] (for
l = ¬x_v: ¬x_v is true iff x_v is false iff comp[x_v] > comp[¬x_v]). Suppose a clause (l₁ ∨ l₂) were false:
comp[l₁] > comp[¬l₁] and comp[l₂] > comp[¬l₂]. The edges ¬l₁ → l₂ and ¬l₂ → l₁ give comp[¬l₁] ≥ comp[l₂] and
comp[¬l₂] ≥ comp[l₁], so comp[l₁] > comp[¬l₁] ≥ comp[l₂] > comp[¬l₂] ≥ comp[l₁], a contradiction (for a unit clause
l₁ = l₂ the same chain is shorter). The code's final loop returns None iff some comp[2v] = comp[2v + 1], that is iff
x_{v+1} and ¬x_{v+1} share an SCC (section 6), and otherwise returns (comp[2v] < comp[2v + 1])_{v<n}, the stated
assignment. With the empty-clause case of section 4 this proves the last sentence. ∎

The criterion is Aspvall, Plass and Tarjan's (1979); the proof above is this project's.

**Check.** `test_correctness_and_components` (the formulas of section 3): None exactly when some x and ¬x reach each
other in the independently built implication graph (and, for n ≤ 10, exactly when no mask satisfies the formula);
otherwise the output satisfies every clause and equals (comp[2v] < comp[2v + 1])_v.

## 6. Tarjan's search as implemented: the components and their order

**Statement** (`algorithms[1].correctness`; docstring, step 2). The iterative search in `two_sat_scc` gives every node
w the number comp[w] of the popping step that removes it from `stack`; each popping step removes exactly one SCC, so
comp has the properties required in section 5: it is constant on SCCs, different on different SCCs, and
comp[u] ≥ comp[v] for every edge u → v (the components are emitted in reverse topological order).

Notation. d(v) = `index[v]`, the discovery number. A node is *active* while an entry (v, i) for it is on `work`; it
*finishes* when that entry is popped. The *head* of an SCC is its node with the smallest d.

**Lemma 6.1 (the search).** (a) Every node is discovered exactly once (by the outer loop, as a root, or along an edge),
with d = 0, 1, 2, … in discovery order; when discovered it is pushed on `stack` and on `work`. Every entry of `adj[v]`
is examined exactly once, while (v, i) is on top of `work`, and v finishes after its last entry. (b) The active nodes,
from the bottom of `work` to the top, form a path r = u₀ → u₁ → … → u_k in which each u_{j+1} was discovered along an
edge of u_j (a *tree edge*); only the top node examines edges. (c) Call the nodes reachable from v by tree edges its
descendants, and T(v) = {v} ∪ descendants. Then w ∈ T(v) iff w is discovered while v is active; such a w ≠ v finishes
before v. (d) When v finishes, every out-neighbour of v has been discovered. (e) `stack` lists its nodes in increasing
order of d.

*Proof.* (a), (b): each iteration of the `while work` loop looks at the top entry (v, i); if i < len(adj[v]) it
advances the entry to (v, i + 1) and examines w = adj[v][i], pushing w on `work` (and on `stack`) if w is
undiscovered; otherwise it pops (v, i). A popped node is never pushed again because its `index` is no longer −1, and
the outer loop starts a new root only when `work` is empty and only at an undiscovered node. (c): if w is discovered
while v is active, the top of `work` at that moment is v or lies above v on the path (b), so w's tree parent, and
hence w, is in T(v). Conversely a descendant is discovered while its tree parent is on top, which by induction
happens while v is active. A node pushed above v on `work` is popped before v. (d): every edge v → w is examined
before v finishes, and an undiscovered w is discovered then. (e): nodes are pushed in discovery order and removed only
in segments from the top. ∎

**Lemma 6.2 (white path).** If at the time v is discovered there is a path v → u₁ → … → u_k whose nodes u_j are all
undiscovered, then u₁, …, u_k ∈ T(v). In particular every SCC C lies in T(h) for its head h.

*Proof.* By induction on j, u_{j−1} ∈ T(v) (u₀ = v), so u_{j−1} finishes no later than v; when it finishes, u_j has
been discovered (6.1 (d)), and it was undiscovered when v was discovered, so u_j was discovered while v was active and
lies in T(v) (6.1 (c)). For an SCC C with head h, when h is discovered every other node of C is undiscovered, and
every node of C is reached from h by a path inside C. ∎

**Lemma 6.3 (low values).** When v finishes, `low[v]` is the minimum of d(v) and of the values d(w) over all
examinations of an edge x → w with x ∈ T(v) at which w was already discovered and on `stack`.

*Proof.* `low[v]` starts at d(v) and changes only while v is active: by `low[v] = min(low[v], index[w])` when v
examines an edge to a discovered node on `stack`, and by `low[v] = min(low[v], low[c])` when a tree child c
finishes. By induction over the finishing order, `low[c]` is then the minimum stated for c, and d(c) > d(v); the
descendants of v are v's children and their descendants. ∎

**Theorem 6.4.** Each run of the popping loop removes exactly one SCC from `stack`, at the finish of its head; a node
that is not a head pops nothing when it finishes. Hence every SCC is popped exactly once, and comp is constant on
SCCs and different on different SCCs.

*Proof.* Induction over the finishing events. Assume the statement for all nodes that finish before time τ. Then
(*): at any time σ ≤ τ, a discovered node w is on `stack` iff the head of its SCC has not finished before σ (nodes
leave `stack` only by popping, and every earlier popping removed exactly the SCC of a head at its finish). Let v
finish at τ, and C be its SCC.

(i) v is the head of C. If `low[v]` < d(v), then by 6.3 some edge x → w with x ∈ T(v) was examined at a time σ < τ
when w was on `stack` and d(w) < d(v). By (*) the head h′ of w's SCC had not finished at σ; d(h′) ≤ d(w) < d(v), so
h′ was active at σ, as was v (x was the top node, and v is x or an ancestor of x). Both lie on the path of active nodes
(6.1 (b)) and h′ was discovered first, so h′ is an ancestor of v. Then w ⇝ h′ (same SCC), h′ ⇝ v and v ⇝ x (tree
edges) and x → w, so w ∈ C with d(w) < d(v), contradicting that v is the head. So `low[v]` = d(v), and the popping
loop removes the nodes of `stack` from the top down to v, which by 6.1 (e) are the nodes on `stack` with d ≥ d(v).
They are exactly C. Every node of C lies in T(v) (6.2), is discovered before τ and was not popped before τ (every
earlier popping removed the SCC of another head), so C is on `stack` with d ≥ d(v). Conversely let y be on `stack` at
τ with d(y) ≥ d(v), and h_y the head of y's SCC; y was discovered while v was active, so y ∈ T(v), and by (*) h_y has
not finished before τ. If d(h_y) > d(v), then h_y (discovered no later than y) was discovered while v was active, so
h_y ∈ T(v) ∖ {v} and finished before τ, which is impossible. If d(h_y) < d(v), then h_y was active at τ together with
v, so it is an ancestor of v, and v ⇝ y ⇝ h_y ⇝ v puts y in C. If d(h_y) = d(v), then h_y = v and y ∈ C.

(ii) v is not the head of C. Let h be the head; d(h) < d(v) and v ∈ T(h) (6.2), so h is an ancestor of v and is
active until after τ. Take a path from v to h; all its nodes lie in C. Let w be its first node outside T(v) (h is
outside), and x its predecessor (x ∈ T(v)). When x examined the edge x → w (before τ), w was already discovered,
since otherwise it would have become a child of x and lie in T(v); and as w ∉ T(v), it was not discovered while v was
active, so d(w) < d(v). The head of w's SCC is h, which had not finished, so by (*) w was on `stack`. By 6.3,
`low[v]` ≤ d(w) < d(v), and no popping happens at v's finish.

This proves the statement for v. Every node finishes, so every SCC is popped exactly once; comp[w] is the number of
SCCs popped before w's. ∎

**Theorem 6.5 (reverse topological order).** For every edge u → v with u and v in different SCCs, comp[u] > comp[v].

*Proof.* Let h_u, h_v be the heads of the two SCCs. We show that h_v finishes before h_u, so v's SCC is popped first
(6.4). Consider the moment σ when u examines the edge u → v; u is active, and so is h_u, an ancestor of u (6.2).
- v undiscovered at σ: v becomes a child of u, so v ∈ T(h_u). If d(h_v) > d(h_u), then h_v was discovered while h_u was
  active (no later than v), so h_v ∈ T(h_u) ∖ {h_u} finishes before h_u. If d(h_v) < d(h_u), then at σ h_v is
  discovered but has not finished (its finish pops v's SCC, which needs v on `stack`), so h_v is active and, being
  discovered before h_u, an ancestor of u; then u → v ⇝ h_v ⇝ u puts u in v's SCC, a contradiction.
- v active at σ: then v is an ancestor of u (it lies below the top node u on `work`), so v ⇝ u → v, a contradiction.
- v finished before σ: if v's SCC was popped before σ, h_v finished before σ, hence before h_u. Otherwise h_v has not
  finished at σ (6.4), so it is active and, as h_v ≠ u, an ancestor of u; then u → v ⇝ h_v ⇝ u, a contradiction. ∎

Together, 6.4 and 6.5 give the numbering that section 5 needs, so `two_sat_scc` is correct. The method is Tarjan's
(1972); the proof above is this project's.

**Check.** `test_correctness_and_components` (the formulas of section 3, with the search's final `comp` read by a line
tracer): comp[u] = comp[v] exactly when u and v reach each other in the independently built implication graph,
comp[u] ≥ comp[v] for every edge u → v, and the numbers are 0, 1, … without gaps.

## 7. Aspvall–Plass–Tarjan: time, space and the uncounted work

**Statement** (`algorithms[1].time_complexity`, `space_complexity`; `relationship`; `verification.method`,
`caveats`). `two_sat_scc` runs in O(n + m) time on every input and in Θ(n + m) time on every input without an empty
clause (an empty clause ends the build pass at once); Θ(n) on W_n. Its working storage is O(n + m), and the space is
Θ(n + m) with the input counted. With `CountingLit` literals every examined edge costs at least one counted operation,
and the work that is not accompanied by a counted operation (creating the arrays of 2n entries, the outer loop over
the 2n roots and the accesses at the roots, which are plain integers from `range`, the final loop over the n
variables, and O(1) setup) is O(n + 1).

**Proof.** Build pass: creating `adj` costs O(n); each clause costs O(1), and an empty clause returns at once.
Search: by 6.1 (a) each of the 2n nodes is discovered once, pushed once on `work` and on `stack`, finishes once and is
popped from `stack` once; each of the 2m adjacency entries is examined once. Every iteration of the `while work` loop
either examines an entry or finishes a node, so there are 2m + 2n iterations of O(1) work each besides the popping
loop, whose iterations total 2n. The outer loop has 2n iterations, the arrays have 2n entries, and the final loop n
iterations. Total O(n + m). Without an empty clause the build pass reads all m clauses and creates 2n lists, so the
time is also Ω(n + m); on W_n, m = 2n + 2 gives Θ(n) (the exact count 49(n + 2) is section 2). Working storage: `adj`
(2n lists, 2m entries), `index`, `low`, `on_stack`, `comp` (2n each), `stack` and `work` (at most 2n entries each).
Counted operations: the adjacency entries are the `CountingLit` values returned by `_node`, so the test
`index[w] == -1` calls `w.__index__` for every examined entry; finishing or popping a node reached along an edge costs
counted accesses as well (section 2). Only the root accesses (`index[root] != -1`, `index[root] = low[root]`,
`on_stack[root]`, the finish and pop of a root) and the final loop use plain integers, and the arrays are created
without counted operations: O(1) per root, per array entry and per variable, plus O(1), so O(n + 1) in all. ∎

**Check.** `test_search_work_and_space` (500 seeded random 2-CNF formulas, n = 1..40): the edge examination runs
exactly 2m times, discoveries (roots and tree edges), finishes and pops exactly 2n times each, `stack` and `work`
never exceed 2n entries, `adj` holds 2m entries, the number of executed lines lies between 2m and 30m + 60n + 30, and
with `CountingLit` literals there are at least 14m + 2m counted operations (14 per clause in the build pass, section
2, and one per examined edge). `test_empty_clause_stops_the_build`: with an empty first clause no further clause is
read (k = 10, 100, 1000 following clauses).

## 8. Brute force: bounds, the worst case for every m ≥ 1, invariance under renaming

**Statement** (`algorithms[0].time_complexity`, `space_complexity`, `correctness`; `caveats`). (a) Brute force makes
at most 2ⁿ·2m literal evaluations and runs in O(2ⁿ·(m + 1)) time on every input. (b) On W_n it runs in
Θ(2ⁿ·n) = Θ(2ⁿ·m) time. (c) For every n ≥ 3 and every m ≥ 4, the unsatisfiable formula R_{n,m} made of m − 4 copies of
(x1 ∨ x2) followed by the core makes exactly (4m − 1)2^(n−2) literal evaluations for m ≥ 5 (2^(n+2) for m = 4), at
least m·2^(n−2). For every n ≥ 1 and m ≥ 2 the unsatisfiable list Q_{n,m} of m − 1 copies of (x1) followed by (¬x1)
makes exactly (m + 1)2^(n−1) literal evaluations, and for m = 1 the empty clause makes one clause scan per mask. So
Θ(2ⁿ·m) is the worst case for every n ≥ 1 and m ≥ 1. With distinct clauses at most 4n clauses (as tuples) contain
the literal x1.
(d) The brute-force count of an unsatisfiable formula, in particular of W_n, does not change when variables are
renamed and negated. (e) A uniformly random assignment falsifies a fixed clause on two distinct variables with
probability 1/4. (f) The space is Θ(n + m): the input, O(1) extra words and the output.

**Proof.** (a) At most 2ⁿ masks, at most m clauses scanned per mask, at most 2 evaluations per clause; with m = 0 the
first mask is returned after O(n) steps.

(b) By section 1 the count is (n + 7)2^(n−1) + 2 evaluations, and every scanned clause of W_n costs at least one, so
the time is Θ(2ⁿ·n), and m = 2n + 2.

(c) R_{n,m} contains the core, so it is unsatisfiable and every mask is examined. Masks with x1 true: each copy costs
1 evaluation, and the core costs 2, 4, 4, 6 for (x2, x3) = (0, 0), (0, 1), (1, 0), (1, 1) (section 1), so this half
costs (m − 4)2^(n−1) + 16·2^(n−3). Masks with x1 false, m ≥ 5: if x2 is false the first copy fails after 2
evaluations; if x2 is true every copy costs 2, and then (x2 ∨ x3) and (x2 ∨ ¬x3) cost 1 each and (¬x2 ∨ x3) costs 2
(it fails if x3 is false), and otherwise (¬x2 ∨ ¬x3) costs 2 more and fails: 2(m − 4) + 4 or 2(m − 4) + 6. This half
costs 2·2^(n−2) + (2(m − 4) + 5)2^(n−2). The sum is 2^(n−2)(2(m − 4) + 8 + 2 + 2(m − 4) + 5) = (4m − 1)2^(n−2). For
m = 4 every mask costs 2, 4, 4 or 6 in the core: 2^(n+2) in all. Both are at least m·2^(n−2), and at most 2ⁿ·2m by
(a). Q_{n,m}: a mask with x1 true passes the m − 1 copies with one evaluation each and fails at (¬x1) after one
more (m in all); a mask with x1 false fails at the first copy (one); so (m + 1)2^(n−1) ≥ m·2^(n−1) evaluations. The
empty clause is false at once, so every mask is examined with one clause scan. A clause that contains
x1 is (x1) or a pair with x1 in one of its two positions and one of the 2n literals in the other: at most
1 + 2n + 2n − 1 = 4n tuples ((x1, x1) is counted in both positions).

(d) A renaming with negations maps x_v to s_v·x_{π(v)} for a permutation π and signs s_v = ±1, and a literal l to
φ(l) accordingly. For an assignment α define α′ by α′(x_{π(v)}) = α(x_v) if s_v = 1 and ¬α(x_v) otherwise; α ↦ α′ is
a bijection of {0, 1}ⁿ, and φ(l) is true under α′ iff l is true under α. Both formulas are unsatisfiable, so every
assignment is examined; the scan of φ(F) under α′ evaluates, clause by clause and literal by literal, literals with
the same truth values as the scan of F under α, so it makes the same number of evaluations, and each evaluation costs
6 counted operations whatever the literal (section 1). Summing over the bijection gives equal totals.

(e) The clause is false iff both literals are false; the two variables are distinct, so under a uniformly random
assignment these are two independent events of probability 1/2.

(f) Besides the input, brute force keeps the mask and loop variables (O(1) words) and builds the output of n
values. ∎

**Check.** `test_brute_force_worst_case_every_m` (n = 3..9, m = 4..30; evaluations counted exactly with `CountingLit`,
6 operations each): the exact counts above, at least m·2^(n−2) and at most 2ⁿ·2m; and Q_{n,m} exactly (m + 1)2^(n−1)
(n = 1..7, m = 2..30). `test_renaming_invariance`: W_n under 5 seeded signed permutations for each n = 3..10
costs 3(n + 7)2ⁿ + 12 operations, and 300 seeded random unsatisfiable formulas (n = 1..7) cost the same before and
after a random signed permutation.
`test_random_clause_falsified_with_probability_quarter`: every clause on two distinct variables, n = 2..6, is false
under exactly a quarter of the masks. `test_brute_force_space_and_distinct_clauses`: every local variable of brute
force is an integer or part of the input (200 seeded formulas), and exactly 4n tuples of at most two literals contain
x1 (n = 1..6).

## 9. The remaining claims

- *Relationship: "2-SAT is in P".* Aspvall–Plass–Tarjan decides satisfiability and returns a satisfying assignment in
  O(n + m) time (sections 5 to 7); brute force is exponential on W_n (section 8 (b)). "A clause is a pair of
  implications": section 4.
- *The V1 oracle (`harness.py`, `check`).* An assignment is accepted only after it is verified against every clause.
  None is accepted only with a certificate: an empty clause; for n ≤ 12 an exhaustive search; for larger n paths
  x ⇝ ¬x and ¬x ⇝ x in the implication graph, found by breadth-first search, which prove unsatisfiability by the
  argument of sections 4 and 5. (Kosaraju's algorithm only locates the variable x; if it finds none, the assignment
  it suggests is verified clause by clause and refutes None.)
- *Measured, not proved:* the fit values α (including α = 0.958 for the bare n·2ⁿ), the counts with random clauses
  in front of the core (their growth like 2ⁿ, α = 1.004 against 2ⁿ, is a measurement on the experiment's seeded
  instances), and the V1 agreement on 60 formulas are results of the recorded runs
  (`experiments/2026-10-07b_two_sat_counts.py`, `tools/validate.py --scaling`).

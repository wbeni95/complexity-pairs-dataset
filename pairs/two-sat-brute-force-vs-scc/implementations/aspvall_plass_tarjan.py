"""Decide 2-SAT in linear time (Aspvall, Plass & Tarjan 1979): implication graph + strongly connected components.

Formula: (n, clauses), variables 1..n, each clause a tuple of 0, 1 or 2 non-zero integers (DIMACS literals:
v means x_v, -v means NOT x_v). An empty clause is unsatisfiable; a unit clause (a) is read as (a OR a).

1. Implication graph on 2n nodes (node 2(v-1) is x_v, node 2(v-1)+1 is NOT x_v, so node ^ 1 is the negation).
   A clause (a OR b) gives the two edges NOT a -> b and NOT b -> a: 2m edges in total.
2. Strongly connected components with Tarjan's algorithm (1972), written ITERATIVELY with an explicit work stack,
   so the depth of the depth-first search is not limited by Python's recursion limit. Tarjan's algorithm emits
   the components in reverse topological order of the condensation (a component is emitted only after every
   component reachable from it).
3. The formula is unsatisfiable iff some x_v and NOT x_v lie in the same component. Otherwise setting x_v true
   iff comp[x_v] comes AFTER comp[NOT x_v] in topological order, i.e. iff comp[x_v] < comp[NOT x_v] in Tarjan's
   emission numbering, satisfies every clause (Aspvall, Plass & Tarjan 1979).

Time Theta(n + m), space Theta(n + m). Returns a tuple of n booleans or None.
"""


def _node(lit):
    v = abs(lit) - 1
    return 2 * v + (lit < 0)


def two_sat_scc(formula):
    n, clauses = formula
    num_nodes = 2 * n
    adj = [[] for _ in range(num_nodes)]
    for clause in clauses:
        if len(clause) == 0:
            return None
        a = _node(clause[0])
        b = _node(clause[-1])                  # equals a for a unit clause
        adj[a ^ 1].append(b)
        adj[b ^ 1].append(a)

    index = [-1] * num_nodes                   # DFS discovery number, -1 = not yet visited
    low = [0] * num_nodes                      # lowlink
    on_stack = [False] * num_nodes
    comp = [-1] * num_nodes                    # component number in emission order
    stack = []                                 # Tarjan's stack of nodes in unfinished components
    counter = 0
    num_comps = 0
    for root in range(num_nodes):
        if index[root] != -1:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack[root] = True
        work = [(root, 0)]                     # (node, position of the next out-edge to examine)
        while work:
            v, i = work[-1]
            edges = adj[v]
            if i < len(edges):
                work[-1] = (v, i + 1)
                w = edges[i]
                if index[w] == -1:             # tree edge: descend
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on_stack[w] = True
                    work.append((w, 0))
                elif on_stack[w]:              # edge into the current DFS path's components
                    low[v] = min(low[v], index[w])
            else:                              # all out-edges of v done: finish v
                work.pop()
                if work:
                    u = work[-1][0]
                    low[u] = min(low[u], low[v])
                if low[v] == index[v]:         # v is the root of a component: pop it
                    while True:
                        w = stack.pop()
                        on_stack[w] = False
                        comp[w] = num_comps
                        if w == v:
                            break
                    num_comps += 1

    assignment = []
    for v in range(n):
        if comp[2 * v] == comp[2 * v + 1]:
            return None
        assignment.append(comp[2 * v] < comp[2 * v + 1])
    return tuple(assignment)

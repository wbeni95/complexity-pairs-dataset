"""Aho-Corasick: one automaton for all patterns, one pass over the text.

1. Trie of the patterns. Each node keeps its children as a list of (character, child) pairs, scanned linearly; with
   an alphabet of sigma characters a lookup costs at most sigma character comparisons.
2. Failure links in breadth-first order: fail(v) is the node of the longest proper suffix of v's string that is
   also a trie node.
3. Scan: from the current state, follow failure links until a child for the next text character exists (or the
   root is reached), take it, and count one visit of the resulting state. The state after reading a text prefix is
   the longest suffix of that prefix that is a trie node.
4. Pattern p ends at a text position iff p's node lies on the failure chain of the state reached there, so the
   occurrences of p are the visits summed over p's subtree of the failure tree: add each node's visits to its
   failure parent in reverse breadth-first order.
Every failure-link step in the scan lowers the depth of the state, and each text character raises it by at most
one, so the scan makes at most 2N lookups; building takes O(L) lookups (amortised in the same way along each
pattern). With a fixed alphabet and at least one pattern: Theta(N + L) character comparisons, independent of the
number of occurrences (with no patterns nothing is compared).
"""
from collections import deque


def _child(children, node, c):
    for ch, nxt in children[node]:
        if ch == c:
            return nxt
    return -1


def count_occurrences_aho_corasick(instance):
    text, patterns = instance
    children = [[]]                          # node 0 is the root
    ends = []
    for pattern in patterns:
        node = 0
        for c in pattern:
            nxt = _child(children, node, c)
            if nxt < 0:
                nxt = len(children)
                children.append([])
                children[node].append((c, nxt))
            node = nxt
        ends.append(node)
    fail = [0] * len(children)
    order = []                               # breadth-first order of the non-root nodes
    queue = deque()
    for ch, v in children[0]:
        queue.append(v)
    while queue:
        u = queue.popleft()
        order.append(u)
        for ch, v in children[u]:
            if u != 0:
                f = fail[u]
                while True:
                    w = _child(children, f, ch)
                    if w >= 0:
                        fail[v] = w
                        break
                    if f == 0:
                        fail[v] = 0
                        break
                    f = fail[f]
            queue.append(v)
    visits = [0] * len(children)
    state = 0
    for c in text:
        while True:
            w = _child(children, state, c)
            if w >= 0:
                state = w
                break
            if state == 0:
                break
            state = fail[state]
        visits[state] += 1
    for v in reversed(order):
        visits[fail[v]] += visits[v]
    return tuple(visits[e] for e in ends)

"""3XOR with a Patricia trie: deterministic, O(n^2 + n w) word operations.

Input: (w, values), values a tuple of n integers in [0, 2^w) (the precondition matters: the trie looks only at bits
w-1..0). Output: indices (i, j, k) with i < j < k and values[i] ^ values[j] ^ values[k] == 0, or None.

Which triples can exist. If v1 ^ v2 ^ v3 = 0 at three distinct indices, then either two values are equal, which
forces the third to be 0 (all three are 0 if all are equal), or the three values are pairwise distinct, and then
none of them is 0 (v3 = 0 would give v1 = v2). The algorithm handles the three cases in turn:

1. Scan for zeros (n equality tests). Value 0 at >= 3 indices: return the first three.
2. Build a Patricia (path-compressed binary) trie over the indices of the nonzero values: split the current group
   by bit w-1, then w-2, ...; a bit on which the group does not split is skipped (no node), a split creates a
   branching node (bit 0 to the left, bit 1 to the right). A group of size 1 stops at once; a group that runs out
   of bits holds equal values. The leaves, from left to right, are the distinct nonzero values D in ascending
   order, each with the list of its indices. Cost O(n w) bit tests.
3. Value 0 at 1 or 2 indices and some nonzero value x at >= 2 indices: (x, x, 0) is a solution.
4. For each a in D, an in-order walk of the trie that takes the right child first at every branching node whose
   bit is set in a lists a ^ x for x in D in ascending order (two leaves are ordered by their highest differing
   bit, the bit of their lowest common ancestor, and XOR with a reverses their order exactly when a has that
   bit). Merging this list with D (also ascending) finds a common value c = a ^ b if one exists. 0 is not in D,
   so a ^ a = 0 never matches, and a, b, c are three distinct nonzero values. Cost O(|D|) per a: the trie has
   |D| leaves and |D| - 1 branching nodes, and the merge is linear.

No sorting routine, dictionary, set or hash of an input value is used: every operation on a value is a bit test,
XOR or comparison written out here, so operation counts do not depend on CPython built-ins.
"""


def _order3(i, j, k):
    """The three (plain integer) indices in increasing order."""
    if i > j:
        i, j = j, i
    if j > k:
        j, k = k, j
    if i > j:
        i, j = j, i
    return (i, j, k)


def _build(values, group, bit, leaves):
    """Patricia trie over the indices in `group` (all values agree on the bits above `bit`).

    Returns a leaf (a plain int: the first index of a value) or a branching node (mask, left, right). Leaves are
    appended to `leaves` (lists of indices of equal values) from left to right, i.e. in ascending value order.

    Written with an explicit stack instead of recursion, so the trie depth (up to min(n, w) branching levels) is not
    limited by Python's recursion limit. It performs the same bit tests in the same order as the recursive form:
    the 0-subtree is built completely before the 1-subtree.
    """
    done = []                                   # finished subtrees, in construction order
    todo = [(group, bit)]                       # (group, bit) = build a subtree; (mask,) = assemble a node
    while todo:
        task = todo.pop()
        if len(task) == 1:                      # both children are finished: assemble the branching node
            right = done.pop()
            left = done.pop()
            done.append((task[0], left, right))
            continue
        group, bit = task
        while True:
            if len(group) == 1 or bit < 0:
                leaves.append(group)
                done.append(group[0])
                break
            mask = 1 << bit
            zero, one = [], []
            for i in group:
                if values[i] & mask:
                    one.append(i)
                else:
                    zero.append(i)
            bit -= 1
            if zero and one:
                todo.append((mask,))
                todo.append((one, bit))
                todo.append((zero, bit))        # popped first: the 0-subtree is built first
                break
            group = zero or one                 # no split at this bit: skip it (path compression)
    return done[0]


def _xor_ascending(root, a, values):
    """[(a ^ values[r], r) for every leaf r], in ascending order of a ^ values[r]."""
    out = []
    stack = [root]
    while stack:
        node = stack.pop()
        if isinstance(node, int):                  # leaf: its representative index
            out.append((a ^ values[node], node))
        else:
            mask, left, right = node
            if a & mask:                           # a has this bit: XOR swaps the two subtrees' order
                stack.append(left)
                stack.append(right)
            else:
                stack.append(right)
                stack.append(left)
    return out


def three_xor_patricia_trie(instance):
    w, values = instance
    n = len(values)
    zeros, nonzero = [], []
    for i in range(n):
        if values[i] == 0:
            zeros.append(i)
        else:
            nonzero.append(i)
    if len(zeros) >= 3:
        return (zeros[0], zeros[1], zeros[2])
    if not nonzero:
        return None
    leaves = []
    root = _build(values, nonzero, w - 1, leaves)
    if zeros:
        for group in leaves:
            if len(group) >= 2:
                return _order3(group[0], group[1], zeros[0])
    reps = [group[0] for group in leaves]          # one index per distinct nonzero value, ascending by value
    dvals = [values[r] for r in reps]
    m = len(reps)
    for a_rep in reps:
        xs = _xor_ascending(root, values[a_rep], values)
        i = j = 0
        while i < m and j < m:
            c = xs[i][0]
            if c == dvals[j]:
                return _order3(a_rep, xs[i][1], reps[j])
            if c < dvals[j]:
                i += 1
            else:
                j += 1
    return None

"""Harness for first-match rule ordering: enumeration of all k! orders vs dynamic programming over subsets.

Instance (k, match, cost, default), all tuples:
  match[i][r] in {0, 1}   1 iff rule r matches item i (i < m, r < k);
  cost[i][r] >= 0         paid if r is the first rule of the order that matches item i; where match[i][r] = 0 the
                          entry is a random integer that every algorithm must ignore;
  default[i] >= 0         paid if no rule matches item i.
Output: (minimum total cost, an order of the k rules attaining it). Several orders can be optimal, so `equal`
compares the costs only, and `check` verifies the returned order.

generate(n, rng) with n = k rules mixes six kinds (m varies independently of k):
  0  random items: each rule matches with probability p in {0.2, 0.4, 0.7}, m in 0..2k+2;
  1  the feedback-arc-set reduction of a random weighted digraph on the k rules: arc u -> v of weight w becomes an
     item matched by u and v with cost 0 for u and w for v (the order pays w iff v comes before u);
  2  the cyclic family used for V2: item i matched by rules i and i+1 (mod k), random costs;
  3  all pairs of rules (a linear ordering instance) with random costs on both sides, some single-rule items;
  4  many items matched by no rule or by every rule, zero costs (ties), duplicated items;
  5  random items over few rules with large costs.
For k = 0 every item matches no rule and the answer is (sum of defaults, ()).

check(instance, output) is independent of both implementations:
  - the output must be a pair (int, tuple) and the tuple a permutation of range(k);
  - the order's cost is recomputed from rule positions (for each item the matching rule of smallest position) and
    must equal the claimed cost;
  - lower bound: every item pays at least min over r in M_i of cost[i][r] (or its default); a claimed cost below it
    is rejected, a cost equal to it is certified optimal;
  - otherwise a depth-first branch and bound over order prefixes (bound: cost so far plus that lower bound for the
    items not yet captured) computes the optimum exactly; it always finishes for k <= 7 and gives up after
    BB_BUDGET nodes for larger k;
  - if branch and bound gave up: an improving move of one rule to another position proves non-optimality (False);
    otherwise the verdict is None (undecided).

V2 (measure "reported"): generate_scaling(n, rng) is the cyclic family with m = k items, item i matched by rules
i and i+1 (mod k), costs drawn from rng in 1..9, all entries CountingInt; it resets the counter. CountingInt counts
every truth test, comparison, +, -, <<, &, | on an entry or a value computed from one. Exact counts (k >= 3; derived
in entry.json, checked in experiments/2026-10-07_first_match_checks.py):
  enumeration   k! (k+1)(k+3)/3 - 1      = k! k(k+1)/3 truth tests + k! k additions + (k! - 1) comparisons
  subset DP     3k^2 + (7k - 2) 2^(k-1) + 2
No counted operation happens inside a CPython built-in such as sorted, min or max (sum() adds CountingInt values;
each addition goes through CountingInt.__add__/__radd__ and is counted).
"""
BB_EXACT_UP_TO = 7
BB_BUDGET = 300_000


# --------------------------------------------------------------------------
# Instances for V1
# --------------------------------------------------------------------------

def _freeze(k, match, cost, default):
    return (k, tuple(tuple(row) for row in match), tuple(tuple(row) for row in cost), tuple(default))


def _junk_costs(k, match, cost, rng):
    """Put random integers where a rule does not match (every algorithm must ignore them)."""
    for i, row in enumerate(match):
        for r in range(k):
            if not row[r]:
                cost[i][r] = rng.randint(0, 50)


def cyclic_items(k):
    """Match matrix of the V2 family: item i is matched by rules i and (i + 1) mod k."""
    return [[1 if r in (i, (i + 1) % k) else 0 for r in range(k)] for i in range(k)]


def generate(n, rng):
    k = n
    if k == 0:
        m = rng.randint(0, 4)
        return _freeze(0, [[] for _ in range(m)], [[] for _ in range(m)], [rng.randint(0, 9) for _ in range(m)])
    kind = rng.randrange(6)
    match, cost = [], []
    if kind == 0:
        p = rng.choice((0.2, 0.4, 0.7))
        for _ in range(rng.randint(0, 2 * k + 2)):
            match.append([1 if rng.random() < p else 0 for _ in range(k)])
            cost.append([rng.randint(0, 9) for _ in range(k)])
    elif kind == 1:
        p = rng.choice((0.3, 0.5, 0.8))
        for u in range(k):
            for v in range(k):
                if u != v and rng.random() < p:
                    row = [0] * k
                    row[u] = row[v] = 1
                    c = [0] * k
                    c[v] = rng.randint(1, 5)
                    match.append(row)
                    cost.append(c)
    elif kind == 2:
        match = cyclic_items(k)
        cost = [[rng.randint(1, 9) for _ in range(k)] for _ in range(k)]
    elif kind == 3:
        for u in range(k):
            for v in range(u + 1, k):
                row = [0] * k
                row[u] = row[v] = 1
                match.append(row)
                cost.append([rng.randint(0, 9) for _ in range(k)])
        for _ in range(rng.randint(0, k)):
            row = [0] * k
            row[rng.randrange(k)] = 1
            match.append(row)
            cost.append([rng.randint(0, 9) for _ in range(k)])
    elif kind == 4:
        for _ in range(rng.randint(1, k + 2)):
            style = rng.randrange(3)
            row = [0] * k if style == 0 else [1] * k if style == 1 else [1 if rng.random() < 0.5 else 0 for _ in range(k)]
            match.append(row)
            cost.append([rng.choice((0, 0, 1)) for _ in range(k)])
        if match and rng.random() < 0.7:
            j = rng.randrange(len(match))
            match.append(list(match[j]))
            cost.append(list(cost[j]))
    else:
        few = rng.sample(range(k), min(k, rng.randint(1, 3)))
        for _ in range(rng.randint(1, 2 * k + 2)):
            match.append([1 if r in few and rng.random() < 0.6 else 0 for r in range(k)])
            cost.append([rng.randint(0, 10 ** 6) for _ in range(k)])
    _junk_costs(k, match, cost, rng)
    default = [rng.randint(0, 9) for _ in match]
    perm = list(range(len(match)))
    rng.shuffle(perm)
    return _freeze(k, [match[i] for i in perm], [cost[i] for i in perm], [default[i] for i in perm])


# --------------------------------------------------------------------------
# Independent oracle
# --------------------------------------------------------------------------

def _rule_lists(instance):
    k, match, cost, default = instance
    return [[r for r in range(k) if match[i][r]] for i in range(len(match))]


def order_cost(instance, order):
    """Cost of `order` from rule positions: each item is captured by its matching rule of smallest position."""
    k, match, cost, default = instance
    pos = [0] * k
    for p, r in enumerate(order):
        pos[r] = p
    total = 0
    for i, rs in enumerate(_rule_lists(instance)):
        if rs:
            first = min(rs, key=pos.__getitem__)
            total += cost[i][first]
        else:
            total += default[i]
    return total


def lower_bound(instance):
    """Every item pays at least its cheapest matching rule (or its default)."""
    k, match, cost, default = instance
    lb = 0
    for i, rs in enumerate(_rule_lists(instance)):
        lb += min(cost[i][r] for r in rs) if rs else default[i]
    return lb


def branch_and_bound(instance, budget=None):
    """Exact optimum by depth-first search over order prefixes with the lower bound above; None if over budget."""
    k, match, cost, default = instance
    rls = _rule_lists(instance)
    items_of = [[i for i, rs in enumerate(rls) if r in rs] for r in range(k)]
    cheapest = [min(cost[i][r] for r in rs) if rs else 0 for i, rs in enumerate(rls)]
    fixed = sum(default[i] for i, rs in enumerate(rls) if not rs)
    best = [None]
    nodes = [0]
    captured = [False] * len(rls)

    def dfs(placed_mask, depth, so_far, remaining_lb):
        nodes[0] += 1
        if budget is not None and nodes[0] > budget:
            raise TimeoutError
        if best[0] is not None and so_far + remaining_lb >= best[0]:
            return
        if depth == k:
            best[0] = so_far
            return
        for r in range(k):
            if placed_mask >> r & 1:
                continue
            newly = [i for i in items_of[r] if not captured[i]]
            add = sum(cost[i][r] for i in newly)
            lb_drop = sum(cheapest[i] for i in newly)
            for i in newly:
                captured[i] = True
            dfs(placed_mask | (1 << r), depth + 1, so_far + add, remaining_lb - lb_drop)
            for i in newly:
                captured[i] = False

    try:
        dfs(0, 0, 0, sum(cheapest))
    except TimeoutError:
        return None
    return best[0] + fixed


def improving_move(instance, order):
    """True if moving one rule to another position lowers the cost (a proof that `order` is not optimal)."""
    base = order_cost(instance, order)
    k = len(order)
    for a in range(k):
        rest = order[:a] + order[a + 1:]
        for b in range(k):
            if b != a and order_cost(instance, rest[:b] + (order[a],) + rest[b:]) < base:
                return True
    return False


def check(instance, output):
    k = instance[0]
    if not (isinstance(output, tuple) and len(output) == 2):
        return False
    claimed, order = output
    if isinstance(claimed, bool) or not isinstance(claimed, int):
        return False
    if not isinstance(order, tuple) or sorted(order) != list(range(k)) or not all(type(r) is int for r in order):
        return False
    if order_cost(instance, order) != claimed:
        return False
    lb = lower_bound(instance)
    if claimed < lb:
        return False
    if claimed == lb:
        return True
    opt = branch_and_bound(instance, None if k <= BB_EXACT_UP_TO else BB_BUDGET)
    if opt is not None:
        return claimed == opt
    if improving_move(instance, order):
        return False
    return None


def equal(a, b):
    return a[0] == b[0]


# --------------------------------------------------------------------------
# Exact operation counting for V2 (measure: "reported")
# --------------------------------------------------------------------------

_ops = {"truth": 0, "compare": 0, "add": 0, "bit": 0}


class CountingInt:
    """An integer that counts every truth test, comparison, +, -, <<, &, | it takes part in."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def _op(self, kind, value):
        _ops[kind] += 1
        return CountingInt(value)

    def __add__(self, o):
        return self._op("add", self.v + self._val(o))

    def __radd__(self, o):
        return self._op("add", self._val(o) + self.v)

    def __sub__(self, o):
        return self._op("add", self.v - self._val(o))

    def __rsub__(self, o):
        return self._op("add", self._val(o) - self.v)

    def __lshift__(self, o):
        return self._op("bit", self.v << self._val(o))

    def __and__(self, o):
        return self._op("bit", self.v & self._val(o))

    def __rand__(self, o):
        return self._op("bit", self._val(o) & self.v)

    def __or__(self, o):
        return self._op("bit", self.v | self._val(o))

    def __ror__(self, o):
        return self._op("bit", self._val(o) | self.v)

    def _cmp(self, result):
        _ops["compare"] += 1
        return result

    def __eq__(self, o):
        return self._cmp(self.v == self._val(o))

    def __ne__(self, o):
        return self._cmp(self.v != self._val(o))

    def __lt__(self, o):
        return self._cmp(self.v < self._val(o))

    def __le__(self, o):
        return self._cmp(self.v <= self._val(o))

    def __gt__(self, o):
        return self._cmp(self.v > self._val(o))

    def __ge__(self, o):
        return self._cmp(self.v >= self._val(o))

    __hash__ = None

    def __bool__(self):
        _ops["truth"] += 1
        return self.v != 0

    def __int__(self):
        return self.v

    def __repr__(self):
        return f"CountingInt({self.v})"


def reset_counter():
    for key in _ops:
        _ops[key] = 0


def generate_scaling(n, rng):
    """Cyclic family with m = k items (item i matched by rules i, i+1 mod k), CountingInt entries; resets the counter."""
    k = n
    match = cyclic_items(k)
    cost = [[rng.randint(1, 9) for _ in range(k)] for _ in range(k)]
    default = [rng.randint(1, 9) for _ in range(k)]
    inst = (k,
            tuple(tuple(CountingInt(x) for x in row) for row in match),
            tuple(tuple(CountingInt(x) for x in row) for row in cost),
            tuple(CountingInt(x) for x in default))
    reset_counter()
    return inst


def reported_cost(output):
    """Counted operations on entry-derived values since the scaling instance was generated."""
    return sum(_ops.values())


def counts_by_kind():
    return dict(_ops)


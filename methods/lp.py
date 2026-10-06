"""An exact rational linear-programming solver: two-phase dense-tableau simplex with Bland's rule.

maximize c.x  subject to  A_ub x <= b_ub,  A_eq x = b_eq,  x_j >= 0 for j not in `free` (free variables are split
into a difference of two non-negative variables). All arithmetic is in `fractions.Fraction`, so the optimum is
exact. Bland's smallest-index rule prevents cycling (Bland 1977, New finite pivoting rules for the simplex
method, Math. Oper. Res. 2, doi:10.1287/moor.2.2.103). Dense and
slow: intended for a few hundred rows and columns at most.
"""
from __future__ import annotations

from fractions import Fraction


def solve_lp(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None, free=()) -> dict:
    """Return {"status": "optimal" | "infeasible" | "unbounded", "x": [...], "value": Fraction}."""
    A_ub, b_ub = [list(r) for r in (A_ub or [])], list(b_ub or [])
    A_eq, b_eq = [list(r) for r in (A_eq or [])], list(b_eq or [])
    nv = len(c)
    free = set(free)
    # split free variables: x_j = p_j - q_j
    cols = []  # (original index, sign)
    for j in range(nv):
        cols.append((j, 1))
        if j in free:
            cols.append((j, -1))

    def expand(row):
        return [Fraction(row[j]) * s for j, s in cols]

    rows, rhs, kinds = [], [], []
    for r, b in zip(A_ub, b_ub):
        rows.append(expand(r)); rhs.append(Fraction(b)); kinds.append("ub")
    for r, b in zip(A_eq, b_eq):
        rows.append(expand(r)); rhs.append(Fraction(b)); kinds.append("eq")
    m, n = len(rows), len(cols)
    n_slack = sum(1 for k in kinds if k == "ub")
    # columns: structural (n) | slacks (n_slack) | artificials (added as needed)
    T, basis, art = [], [], []
    si = 0
    for i in range(m):
        row = rows[i] + [Fraction(0)] * n_slack
        b = rhs[i]
        slack_col = None
        if kinds[i] == "ub":
            slack_col = n + si
            row[slack_col] = Fraction(1)
            si += 1
        if b < 0:
            row = [-x for x in row]
            b = -b
        T.append(row + [b])
        if kinds[i] == "ub" and row[slack_col] == 1:
            basis.append(slack_col)
        else:
            basis.append(None)
    width = n + n_slack
    for i in range(m):
        if basis[i] is None:
            for r in T:
                r.insert(width, Fraction(0))
            T[i][width] = Fraction(1)
            art.append(width)
            basis[i] = width
            width += 1
    # Phase 1: minimise the sum of artificials  <=> maximise -sum
    if art:
        obj = [Fraction(0)] * (width + 1)
        for a in art:
            obj[a] = Fraction(-1)
        status = _simplex(T, basis, obj, width)
        val = sum(T[i][-1] for i in range(m) if basis[i] in art)
        if val != 0:
            return {"status": "infeasible", "x": None, "value": None}
        # drive remaining (zero-level) artificials out of the basis
        for i in range(m):
            if basis[i] in art:
                piv = next((j for j in range(width) if j not in art and T[i][j] != 0), None)
                if piv is not None:
                    _pivot(T, basis, i, piv)
        keep = [j for j in range(width) if j not in art]
        drop_rows = [i for i in range(m) if basis[i] in art]
        T = [[T[i][j] for j in keep] + [T[i][-1]] for i in range(m) if i not in drop_rows]
        remap = {j: k for k, j in enumerate(keep)}
        basis = [remap[basis[i]] for i in range(m) if i not in drop_rows]
        width = len(keep)
        m = len(T)
    obj = [Fraction(0)] * (width + 1)
    for k, (j, s) in enumerate(cols):
        obj[k] = Fraction(c[j]) * s
    status = _simplex(T, basis, obj, width)
    if status == "unbounded":
        return {"status": "unbounded", "x": None, "value": None}
    xs = [Fraction(0)] * width
    for i in range(m):
        xs[basis[i]] = T[i][-1]
    x = [Fraction(0)] * nv
    for k, (j, s) in enumerate(cols):
        x[j] += s * xs[k]
    return {"status": "optimal", "x": x, "value": sum(Fraction(c[j]) * x[j] for j in range(nv))}


def _pivot(T, basis, r, col):
    pr = T[r]
    inv = 1 / pr[col]
    T[r] = pr = [v * inv for v in pr]
    for i in range(len(T)):
        if i != r and T[i][col] != 0:
            f = T[i][col]
            T[i] = [a - f * b for a, b in zip(T[i], pr)]
    basis[r] = col


def _simplex(T, basis, obj, width) -> str:
    """Maximise obj over the tableau (Bland's rule). obj: cost per column (last entry ignored)."""
    m = len(T)
    while True:
        # reduced costs: obj_j - sum_i obj_basis(i) T[i][j]
        cb = [obj[basis[i]] for i in range(m)]
        enter = None
        for j in range(width):
            if j in basis:
                continue
            rc = obj[j] - sum(cb[i] * T[i][j] for i in range(m) if T[i][j] != 0)
            if rc > 0:
                enter = j
                break
        if enter is None:
            return "optimal"
        best, leave = None, None
        for i in range(m):
            if T[i][enter] > 0:
                ratio = T[i][-1] / T[i][enter]
                if best is None or ratio < best or (ratio == best and basis[i] < basis[leave]):
                    best, leave = ratio, i
        if leave is None:
            return "unbounded"
        _pivot(T, basis, leave, enter)

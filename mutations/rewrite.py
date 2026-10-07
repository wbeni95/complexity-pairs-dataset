"""Load in-memory COPIES of repository implementations, optionally rewritten at the AST level.

Nothing on disk is modified: the source text is read, parsed, transformed and executed into a fresh module object
whose `__file__` names the original and whose `__mutation__` records the transforms and the SHA-256 of the source.

Transforms are targeted: each names the exact source segments (as returned by `ast.get_source_segment`) it applies
to, so a rewrite never touches index arithmetic or loop bounds by accident. A transform whose pattern matches
nothing raises `RewriteError`, so a mistyped pattern cannot silently yield an unchanged copy. A matched pattern can
still leave the code unchanged (for example a compare flip applied to `==`, or a constant swap to the same value).
"""
from __future__ import annotations

import ast
import copy
import hashlib
import types
from pathlib import Path

from . import algebra

REPO = Path(__file__).resolve().parent.parent


class RewriteError(ValueError):
    pass


def _seg(src, node):
    return ast.get_source_segment(src, node)


class _Targeted(ast.NodeTransformer):
    def __init__(self, src, patterns):
        self.src = src
        self.patterns = set(patterns)
        self.hits: set[str] = set()

    def match(self, node):
        s = _seg(self.src, node)
        if s in self.patterns:
            self.hits.add(s)
            return True
        return False

    def finish(self):
        missing = self.patterns - self.hits
        if missing:
            raise RewriteError(f"{type(self).__name__}: no match for {sorted(missing)}")


class CompareFlip(_Targeted):
    """Lt <-> Gt and LtE <-> GtE in the named comparisons."""
    SWAP = {ast.Lt: ast.Gt, ast.Gt: ast.Lt, ast.LtE: ast.GtE, ast.GtE: ast.LtE}

    def visit_Compare(self, node):
        self.generic_visit(node)
        if self.match(node):
            node.ops = [self.SWAP.get(type(o), type(o))() for o in node.ops]
        return node


class CallSwap(_Targeted):
    """Replace the function name of the named calls, e.g. min(...) -> max(...) or min(a, b) -> __oplus__(a, b)."""

    def __init__(self, src, patterns, new_name):
        super().__init__(src, patterns)
        self.new_name = new_name

    def visit_Call(self, node):
        self.generic_visit(node)
        if self.match(node):
            node.func = ast.Name(id=self.new_name, ctx=ast.Load())
        return node


class SortedReverse(_Targeted):
    """Add reverse=True to the named sorted(...) calls."""

    def visit_Call(self, node):
        self.generic_visit(node)
        if self.match(node):
            node.keywords = [k for k in node.keywords if k.arg != "reverse"] + [
                ast.keyword(arg="reverse", value=ast.Constant(True))]
        return node


class IfExpToOplus(_Targeted):
    """`A if <comparison> else B` (a selection of the better candidate) -> `__oplus__(A, B)`."""

    def visit_IfExp(self, node):
        self.generic_visit(node)
        if self.match(node):
            return ast.Call(func=ast.Name("__oplus__", ast.Load()), args=[node.body, node.orelse], keywords=[])
        return node


class RelaxToAccumulate(_Targeted):
    """Relaxation -> accumulation. Matches the named `if` statements of the forms

        if X < T: T = X                      ->  T = __oplus__(T, X)
        if T is None or X < T: T = X         ->  T = X if T is None else __oplus__(T, X)

    (any of <, >, <=, >=). Valid as a semantic rewrite exactly when the comparison selects the ⊕-better value.
    """

    def visit_If(self, node):
        self.generic_visit(node)
        test_src = _seg(self.src, node.test)
        if test_src not in self.patterns:
            return node
        if len(node.body) != 1 or node.orelse or not isinstance(node.body[0], ast.Assign):
            raise RewriteError(f"RelaxToAccumulate: unsupported body at {test_src!r}")
        assign = node.body[0]
        tgt, val = assign.targets[0], assign.value
        self.hits.add(test_src)
        acc_load = copy.deepcopy(tgt)
        acc_load.ctx = ast.Load()
        call = ast.Call(func=ast.Name("__oplus__", ast.Load()), args=[acc_load, val], keywords=[])
        test = node.test
        if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.Or) and len(test.values) == 2:
            none_check = test.values[0]
            new_val = ast.IfExp(test=none_check, body=copy.deepcopy(val), orelse=call)
        else:
            new_val = call
        new = ast.Assign(targets=[tgt], value=new_val)
        return ast.copy_location(new, node)


class ExprReplace(_Targeted):
    """Replace every expression whose source segment equals a key by the parsed replacement expression,
    e.g. {"math.inf": "-math.inf"} (sentinel flip)."""

    def __init__(self, src, mapping):
        super().__init__(src, mapping.keys())
        self.mapping = mapping

    def visit(self, node):
        if isinstance(node, ast.expr):
            s = _seg(self.src, node)
            if s in self.mapping:
                self.hits.add(s)
                return ast.copy_location(ast.parse(self.mapping[s], mode="eval").body, node)
        return super().visit(node)


class ConstSwap(ast.NodeTransformer):
    """Module-level `NAME = <constant>` -> `NAME = value`."""

    def __init__(self, values: dict):
        self.values = values
        self.hits: set[str] = set()

    def visit_Module(self, node):
        for stmt in node.body:
            if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name)
                    and stmt.targets[0].id in self.values):
                stmt.value = ast.Constant(self.values[stmt.targets[0].id])
                self.hits.add(stmt.targets[0].id)
        return node

    def finish(self):
        missing = set(self.values) - self.hits
        if missing:
            raise RewriteError(f"ConstSwap: no module-level assignment for {sorted(missing)}")


def load_copy(rel_path: str, transforms: list[tuple] | None = None, extra_globals: dict | None = None,
              tag: str = "copy") -> types.ModuleType:
    """Execute a (possibly rewritten) copy of REPO/rel_path into a fresh module.

    transforms: list of (kind, args...) with kind in
        ("flip", [segments]), ("call", [segments], new_name), ("sorted_reverse", [segments]),
        ("ifexp_oplus", [segments]), ("relax_accumulate", [test segments]), ("const", {NAME: value}).
    """
    path = REPO / rel_path
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    applied = []
    for t in transforms or []:
        kind = t[0]
        if kind == "flip":
            tr = CompareFlip(src, t[1])
        elif kind == "call":
            tr = CallSwap(src, t[1], t[2])
        elif kind == "sorted_reverse":
            tr = SortedReverse(src, t[1])
        elif kind == "ifexp_oplus":
            tr = IfExpToOplus(src, t[1])
        elif kind == "relax_accumulate":
            tr = RelaxToAccumulate(src, t[1])
        elif kind == "const":
            tr = ConstSwap(t[1])
        elif kind == "replace":
            tr = ExprReplace(src, t[1])
        else:
            raise RewriteError(f"unknown transform {kind}")
        tree = tr.visit(tree)
        tr.finish()
        applied.append([kind] + [list(x) if isinstance(x, (set, tuple)) else x for x in t[1:]])
    ast.fix_missing_locations(tree)
    code = compile(tree, f"<{tag} of {rel_path}>", "exec")
    mod = types.ModuleType(f"mutcopy_{abs(hash((rel_path, repr(applied))))}")
    mod.__file__ = str(path)
    mod.__dict__["__oplus__"] = algebra.oplus
    if extra_globals:
        mod.__dict__.update(extra_globals)
    exec(code, mod.__dict__)
    mod.__mutation__ = {"source": rel_path, "sha256": hashlib.sha256(src.encode("utf-8")).hexdigest(),
                        "transforms": applied}
    return mod

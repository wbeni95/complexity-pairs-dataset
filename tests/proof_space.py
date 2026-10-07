"""Instrumented peak size of the containers an implementation holds, for the space checks in tests/test_proofs_*.py.

`peak_words(func, args, impl_file)` runs `func(*args)` unchanged under sys.settrace. At every line event and every
return event of a frame whose code lives in `impl_file`, it collects the local variables of all such frames on the
current call stack (plus the returned object at a return event), follows every list, tuple, dict and set reachable
from them, and adds up their lengths (a dict counts 2 per item). Each container is counted once (by identity), and
every container reachable from the arguments is excluded: the input is not extra space. The result is the largest
total seen, in "words" (container slots).

What it does not see: containers that exist only as temporaries on the interpreter's value stack and are never bound
to a local variable, and the internal state of C-level library objects (iterators, generators, sort buffers). The
proofs in the PROOFS.md files account for those; a check covers the visible part on its stated range.
"""
import os
import sys

_CONTAINERS = (list, tuple, dict, set, frozenset)


def _reachable_ids(objs):
    seen = set()
    stack = list(objs)
    while stack:
        x = stack.pop()
        if isinstance(x, _CONTAINERS) and id(x) not in seen:
            seen.add(id(x))
            if isinstance(x, dict):
                stack.extend(x.keys())
                stack.extend(x.values())
            else:
                stack.extend(x)
    return seen


def peak_words(func, args, impl_file):
    """Return (result, peak) for func(*args); peak = largest number of container slots held (see module doc)."""
    target = os.path.normcase(os.path.abspath(impl_file))
    is_target = {}

    def in_impl(code):
        name = code.co_filename
        hit = is_target.get(name)
        if hit is None:
            hit = is_target[name] = os.path.normcase(os.path.abspath(name)) == target
        return hit

    excluded = _reachable_ids(args)
    keep = list(args)  # keep the arguments alive so that their ids stay reserved
    peak = 0

    def measure(frame, extra):
        nonlocal peak
        roots = []
        f = frame
        while f is not None:
            if in_impl(f.f_code):
                roots.extend(f.f_locals.values())
            f = f.f_back
        if extra is not None:
            roots.append(extra)
        seen = set()
        total = 0
        stack = roots
        while stack:
            x = stack.pop()
            if isinstance(x, _CONTAINERS):
                i = id(x)
                if i in seen or i in excluded:
                    continue
                seen.add(i)
                if isinstance(x, dict):
                    total += 2 * len(x)
                    stack.extend(x.keys())
                    stack.extend(x.values())
                else:
                    total += len(x)
                    stack.extend(x)
        if total > peak:
            peak = total

    def local_trace(frame, event, arg):
        if event == "line":
            measure(frame, None)
        elif event == "return":
            measure(frame, arg)
        return local_trace

    def global_trace(frame, event, arg):
        if in_impl(frame.f_code):
            return local_trace
        return None

    old = sys.gettrace()
    sys.settrace(global_trace)
    try:
        result = func(*args)
    finally:
        sys.settrace(old)
    del keep
    return result, peak

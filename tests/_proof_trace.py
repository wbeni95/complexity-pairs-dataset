"""Line tracer for the tests/test_proofs_*.py checks (not a test module itself).

LineTrace(func, markers) runs `func` under sys.settrace and counts how often each marked source line of `func` (or of a
function nested in it) is executed; a marker is a substring that must occur on exactly one line of the source. It can
also record, at every traced line, the peak of user-chosen sizes computed from the frame's local variables, the total
number of executed lines, the maximal recursion depth of a nested function, and a copy of the local variables when a
marked `snapshot` line is first reached (lists are copied one level deep). Nothing in the traced code is modified.
"""
import inspect
import sys


class LineTrace:
    def __init__(self, func, markers=None, sizes=None, nested=None, snapshot=None):
        self.func = func
        src, start = inspect.getsourcelines(func)
        self.codes = {func.__code__}
        self.nested_code = None
        if nested is not None:
            for c in func.__code__.co_consts:
                if inspect.iscode(c) and c.co_name == nested:
                    self.nested_code = c
                    self.codes.add(c)
            if self.nested_code is None:
                raise ValueError(f"no nested function {nested!r}")
        self.lines = {}
        for key, marker in (markers or {}).items():
            hits = [start + i for i, s in enumerate(src) if marker in s]
            if len(hits) != 1:
                raise ValueError(f"marker {marker!r} found on lines {hits}")
            self.lines[hits[0]] = key
        self.counts = dict.fromkeys((markers or {}), 0)
        self.snapshot_line = None
        self.snapshot = None
        if snapshot is not None:
            hits = [start + i for i, s in enumerate(src) if snapshot in s]
            if len(hits) != 1:
                raise ValueError(f"snapshot marker {snapshot!r} found on lines {hits}")
            self.snapshot_line = hits[0]
        self.sizes = sizes
        self.peak = {}
        self.depth = 0
        self.max_depth = 0
        self.total_lines = 0

    def _local(self, frame, event, arg):
        if event == "line":
            self.total_lines += 1
            key = self.lines.get(frame.f_lineno)
            if key is not None:
                self.counts[key] += 1
            if frame.f_lineno == self.snapshot_line and self.snapshot is None:
                self.snapshot = {k: (list(v) if isinstance(v, list) else v) for k, v in frame.f_locals.items()}
            if self.sizes is not None:
                for name, value in self.sizes(frame.f_locals).items():
                    if value > self.peak.get(name, -1):
                        self.peak[name] = value
        elif event == "return" and frame.f_code is self.nested_code:
            self.depth -= 1
        return self._local

    def _global(self, frame, event, arg):
        if frame.f_code in self.codes:
            if frame.f_code is self.nested_code:
                self.depth += 1
                self.max_depth = max(self.max_depth, self.depth)
            return self._local
        return None

    def run(self, *args):
        old = sys.gettrace()
        sys.settrace(self._global)
        try:
            return self.func(*args)
        finally:
            sys.settrace(old)

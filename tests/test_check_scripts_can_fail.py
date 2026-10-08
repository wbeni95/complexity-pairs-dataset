"""Lint: every check script behind the check mark has an exit that can report a failure.

tools/replay_proofs.py runs every file named in a `proof.checks` field and judges it by its exit code (and by lines
that start with [FAIL]). A script that only prints its results and always returns 0 would pass whatever it found.
This lint reads the source of every listed check that is not a unittest module and requires an exit that can be
non-zero on its main path:

  - a `sys.exit(...)` call or a `raise SystemExit` whose argument is not missing, 0 or None (for example the shared
    pattern `sys.exit(main(...))`, `sys.exit(1)`, or `sys.exit(1 if failed else 0)`), and
  - placed at module level (including the `if __name__ == "__main__":` block) or inside a top-level function that
    module-level code calls, directly or through other top-level functions.

What the lint cannot show: that the exit depends on every check the script makes, that a failed check really
reaches it, or that the checks are right. It is a static test of the source and runs nothing. The evidence that a
script can fail is a tamper test: run a copy in which one checked fact is made wrong and confirm a non-zero exit and
a [FAIL] line naming that check. Unittest modules are not linted here; a failing test makes `python -m unittest` exit
non-zero by construction.
"""
import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import replay_proofs  # noqa: E402


def check_scripts():
    """{script path relative to the repository root: [item slugs]} for every listed check that is not a unittest."""
    scripts = {}
    for item in replay_proofs.marked_items():
        for rel in item["proof"].get("checks", []):
            cmd = replay_proofs.command_for(item["path"] / rel)
            if cmd[0] == "-m":
                continue
            scripts.setdefault(cmd[0], []).append(item["slug"])
    return scripts


def _is_exit_call(node):
    """sys.exit(...) or SystemExit(...)."""
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    return (isinstance(f, ast.Attribute) and f.attr == "exit" and isinstance(f.value, ast.Name) and f.value.id == "sys"
            or isinstance(f, ast.Name) and f.id == "SystemExit")


def _can_be_nonzero(args):
    """False only for a missing argument or the constants 0, False and None (all exit with code 0)."""
    if not args:
        return False
    a = args[0]
    return not (isinstance(a, ast.Constant) and a.value in (0, None))


def _failure_exits(tree):
    """Nodes that can end the run with a non-zero exit code: sys.exit(x) calls and raise SystemExit(x)."""
    found = []
    for node in ast.walk(tree):
        if _is_exit_call(node) and _can_be_nonzero(node.args):
            found.append(node)
        elif isinstance(node, ast.Raise) and node.exc is not None:
            exc = node.exc
            if isinstance(exc, ast.Call) and _is_exit_call(exc) and _can_be_nonzero(exc.args):
                found.append(node)
    return found


def _called_names(nodes):
    names = set()
    for top in nodes:
        for node in ast.walk(top):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                names.add(node.func.id)
    return names


def exit_on_main_path(source):
    """True if a failure-capable exit sits at module level or in a top-level function reachable from module level."""
    tree = ast.parse(source)
    functions = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    module_level = [n for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    reachable, todo = set(), list(_called_names(module_level) & set(functions))
    while todo:
        name = todo.pop()
        if name in reachable:
            continue
        reachable.add(name)
        todo.extend((_called_names([functions[name]]) & set(functions)) - reachable)
    if any(_failure_exits(n) for n in module_level):
        return True
    return any(_failure_exits(functions[name]) for name in reachable)


class LintSelfTests(unittest.TestCase):
    def test_shared_main_pattern(self):
        self.assertTrue(exit_on_main_path("import sys\ndef main():\n    return 1\nif __name__ == '__main__':\n"
                                          "    sys.exit(main())\n"))

    def test_exit_in_a_helper_called_from_main(self):
        self.assertTrue(exit_on_main_path("import sys\nF = []\ndef finish():\n    if F:\n        sys.exit(1)\n"
                                          "def main():\n    finish()\nmain()\n"))

    def test_raise_system_exit(self):
        self.assertTrue(exit_on_main_path("bad = 1\nif bad:\n    raise SystemExit(1)\n"))

    def test_print_only_script_is_rejected(self):
        self.assertFalse(exit_on_main_path("def main():\n    print('ok:', 1 == 2)\nif __name__ == '__main__':\n"
                                           "    main()\n"))

    def test_exit_zero_only_is_rejected(self):
        self.assertFalse(exit_on_main_path("import sys\nprint('x')\nsys.exit(0)\n"))
        self.assertFalse(exit_on_main_path("import sys\nsys.exit()\n"))
        self.assertFalse(exit_on_main_path("import sys\nsys.exit(None)\n"))

    def test_exit_false_is_rejected(self):
        """sys.exit(False) and SystemExit(False) exit with code 0; sys.exit(True) exits with 1."""
        self.assertFalse(exit_on_main_path("import sys\nsys.exit(False)\n"))
        self.assertFalse(exit_on_main_path("raise SystemExit(False)\n"))
        self.assertTrue(exit_on_main_path("import sys\nsys.exit(True)\n"))

    def test_exit_in_an_uncalled_function_is_rejected(self):
        self.assertFalse(exit_on_main_path("import sys\ndef unused():\n    sys.exit(1)\nprint('done')\n"))


class CheckScriptsCanFailTests(unittest.TestCase):
    def test_there_are_check_scripts(self):
        self.assertGreater(len(check_scripts()), 0)

    def test_every_listed_check_script_has_a_failure_exit(self):
        for rel, slugs in sorted(check_scripts().items()):
            with self.subTest(script=rel, items=slugs[:3]):
                path = ROOT / rel
                self.assertTrue(path.is_file())
                self.assertTrue(exit_on_main_path(path.read_text(encoding="utf-8")),
                                f"{rel} has no exit that can be non-zero on its main path")


if __name__ == "__main__":
    unittest.main()

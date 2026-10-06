"""Experiment (research/2026-10-06f_new_entries.md): are the exact V2 counts of the round-2026-10-06f entries identical
across Python versions? CI runs CPython 3.12, local runs use 3.14 (RESEARCH_LOG RL-069: counts that pass through
CPython built-ins may differ between versions).

For every entry folder given on the command line (default: the seven entries of this round that exist), every
algorithm with measure "reported" is run on generate_scaling(n, rng) for its declared n_values, seeded exactly as
tools/validate.py does it (rng = random.Random(f"{id}|v2|{n}"), random.seed(f"{id}|v2|{n}|0|{name}") before the
call). Prints each count series and one SHA-256 over all series. Needs only the standard library, so it runs under
any interpreter:

    .venv/Scripts/python.exe experiments/2026-10-06f_entries_cross_version.py > a.txt
    py -3.12 experiments/2026-10-06f_entries_cross_version.py > b.txt

RESULT: see the report (both interpreters print the same hash, or the differing series are listed there).
"""
import hashlib
import importlib.util
import json
import platform
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DEFAULT = [
    "pairs/horn-sat-brute-force-vs-unit-propagation",
    "pairs/xor-sat-brute-force-vs-gaussian-elimination",
    "pairs/boolean-matrix-multiplication-naive-vs-strassen",
    "pairs/or-convolution-naive-vs-zeta-mobius",
    "pairs/planar-perfect-matchings-enumeration-vs-kasteleyn",
    "pairs/hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion",
    "pairs/max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp",
]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main(paths):
    digest = hashlib.sha256()
    print("python", platform.python_version())
    for rel in paths:
        d = ROOT / rel
        if not (d / "entry.json").is_file():
            print(f"{rel}: missing, skipped")
            continue
        e = json.loads((d / "entry.json").read_text(encoding="utf-8"))
        tag = "xv_" + e["id"].replace("-", "_")
        harness = load(d / e["test_harness"]["module"], tag + "_harness")
        gen = getattr(harness, "generate_scaling", harness.generate)
        for k, alg in enumerate(e["algorithms"]):
            sc = (alg.get("harness") or {}).get("scaling")
            if not alg.get("implementation") or not sc or sc.get("measure") != "reported":
                continue
            file_part, func = alg["implementation"].rsplit(":", 1)
            fn = getattr(load(d / file_part, f"{tag}_impl{k}"), func)
            vals = []
            for n in sc["n_values"]:
                rng = random.Random(f"{e['id']}|v2|{n}")
                inst = gen(n, rng)
                random.seed(f"{e['id']}|v2|{n}|0|{alg['name']}")
                vals.append(int(harness.reported_cost(fn(inst))))
            line = f"{e['id']} | {alg['name']} | {sc['n_values']} | {vals}"
            digest.update(line.encode("utf-8"))
            print(line)
    print("sha256", digest.hexdigest())


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT)

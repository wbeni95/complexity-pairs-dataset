# experiments/

Ad-hoc verification scripts behind entries in [RESEARCH_LOG.md](../RESEARCH_LOG.md). Each file is named
`YYYY-MM-DD_<topic>.py`, states in its docstring which question it answers and which log entry cites it,
and is deterministic, with fixed seeds, so its output can be reproduced. Run scripts from the repository
root with the project's Python.

Routine verification (V1/V2 for every entry) is not here. It is done by `tools/validate.py`, and
`--record` stores its results in `ledger/runs/`.

# synthetic/ (T7 entries)

This folder holds **deliberately bloated** pairs: a cheap algorithm rewritten in a wasteful, exponential
form. Producing these costs nothing. A model trained only on them learns to "un-bloat the obvious",
and that skill does not transfer to genuinely hard problems (START_HERE section 5).

Rules, enforced by `tools/validate.py`:

- every entry here must be tagged T7, and T7 entries may live nowhere else;
- T7 entries never count toward the "validated pairs" headline.

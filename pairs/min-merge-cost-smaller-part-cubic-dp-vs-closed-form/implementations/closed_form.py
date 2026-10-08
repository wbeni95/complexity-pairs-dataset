"""Merging adjacent piles at the cost of the smaller part (min sum of min(L, R)): the closed form, Theta(n).

Instance as in cubic_dp.py: a tuple of n + 1 non-negative pile sizes s_0..s_n. REQUIRED: every size is >= 0.

    answer = (s_0 + ... + s_n) - max(s_0, ..., s_n).

Correctness (entry README, Proposition): every merge tree costs at least S - max s, by induction over the last merge
(for parts of sizes L, R with largest piles m_L >= m_R, the smaller largest pile satisfies m_R <= min(L, R)); and the
caterpillar that starts at a largest pile and adds the neighbouring piles one at a time costs exactly S - max s,
because each added pile is no larger than the block it joins. Without the precondition the formula can be wrong
(entry README, Limits).

Work: one pass over the sizes with n comparisons for the running maximum, n additions and one subtraction.
"""


def merge_min_smaller_closed_form(sizes):
    total = sizes[0]
    largest = sizes[0]
    for s in sizes[1:]:
        total = total + s
        if s > largest:
            largest = s
    return total - largest

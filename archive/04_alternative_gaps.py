#!/usr/bin/env python3
"""
Script 4: Explore Alternative Gap Positions

The paper uses free positions {57,58,59,60,61} for sr=59.
The sigma_1 cascade enforces W[62] from W[60] and W[63] from W[61].

But what about other gap configurations? The key insight is that
W[t] = sigma_1(W[t-2]) + W[t-7] + sigma0(W[t-15]) + W[t-16].

If W[t-2] is free, the solver can satisfy the equation for W[t]
by choosing W[t-2] appropriately. This means:
- Free W[57] -> can enforce W[59]
- Free W[58] -> can enforce W[60]
- Free W[59] -> can enforce W[61]
- Free W[60] -> can enforce W[62]
- Free W[61] -> can enforce W[63]

Are there other dependency structures we can exploit?

For W[t] = sigma_1(W[t-2]) + W[t-7] + sigma0(W[t-15]) + W[t-16]:
- t-2 dependency (sigma_1): strongest, nonlinear
- t-7 dependency: linear (addition)
- t-15 dependency (sigma_0): nonlinear but weaker
- t-16 dependency: linear (addition)

What if we use the t-7 or t-16 dependency instead?
"""

def analyze_gap_config(free_positions, max_round=63):
    """
    Given a set of free schedule positions, determine which other positions
    are enforceable via the schedule recurrence.

    Returns the set of enforced positions and the total schedule compliance.
    """
    # Positions 0-15 are always from the message (always compliant)
    # Positions 16-63 need schedule equations

    enforced = set()
    free = set(free_positions)

    # Standard schedule: positions 16 through max_round
    # W[i] = sigma_1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]

    # A position i is "naturally compliant" if it's computed from the schedule
    # It's "free" if the solver assigns it independently
    # It's "enforceable" if one of its dependencies is free (the solver can
    # choose the free dep to satisfy the equation)

    for i in range(16, max_round + 1):
        if i in free:
            continue  # Free positions are not compliant

        deps = [i-2, i-7, i-15, i-16]

        # Check if this position can be enforced via a free dependency
        # The t-2 dependency through sigma_1 is the strongest
        if i - 2 in free:
            enforced.add(i)
            continue

        # Could also be enforced via t-7 (linear addition)
        # But this only works if all other deps are deterministic
        # and the free word at t-7 hasn't been "used up" already

    # Compute total compliance
    # Compliant = positions 16..max_round that are either:
    # 1. Naturally computed (not free and not needing enforcement)
    # 2. Enforced via a free dependency

    natural = set(range(16, max_round + 1)) - free - enforced

    # Natural positions: their equation holds because all deps are deterministic
    # (computed from earlier positions that are either natural or message words)

    sr = 16  # Base: 16 message words
    for i in range(16, max_round + 1):
        if i not in free:
            # Check if all dependencies are deterministic
            all_det = True
            for d in [i-2, i-7, i-15, i-16]:
                if d in free and i not in enforced:
                    all_det = False
            if all_det or i in enforced:
                sr += 1

    return sr, free, enforced


# Explore various gap configurations
print("=" * 70)
print("Alternative Gap Position Analysis")
print("=" * 70)

configs = [
    # Paper's sr=59: free = {57,58,59,60,61}
    ([57, 58, 59, 60, 61], "Paper's sr=59"),

    # What if we shift the gap earlier?
    ([56, 57, 58, 59, 60], "Shift left by 1"),
    ([55, 56, 57, 58, 59], "Shift left by 2"),

    # What about non-contiguous gaps?
    ([57, 58, 59, 60, 62], "Non-contiguous: skip 61"),
    ([57, 58, 59, 61, 62], "Non-contiguous: skip 60"),
    ([56, 58, 59, 60, 61], "Non-contiguous: skip 57"),

    # 4 free words (sr=60 territory)
    ([57, 58, 59, 60], "4 free (paper's sr=60 attempt)"),
    ([58, 59, 60, 61], "4 free shifted"),
    ([57, 59, 60, 61], "4 free non-contiguous"),
    ([56, 58, 60, 62], "4 free spread out"),

    # 3 free words (sr=61 territory)
    ([57, 58, 59], "3 free"),
    ([59, 60, 61], "3 free late"),
    ([57, 60, 63], "3 free spread"),

    # Exotic: use the t-7 dependency
    ([50, 57, 58, 59, 60], "5 free with early anchor at 50"),
    ([48, 55, 57, 58, 59], "5 free with two early anchors"),
]

for positions, label in configs:
    sr, free, enforced = analyze_gap_config(positions)
    enforced_list = sorted(enforced)
    print(f"\n{label}")
    print(f"  Free: {sorted(positions)}")
    print(f"  Enforced via cascade: {enforced_list}")
    print(f"  sr = {sr}, free words = {len(positions)}")
    print(f"  Freedom = {len(positions) * 2 * 32} bits, Slack = {len(positions) * 2 * 32 - 256} bits")

print("\n" + "=" * 70)
print("Key insight: the sigma_1(W[t-2]) cascade means free positions")
print("enforce positions 2 steps ahead. Contiguous blocks get the most")
print("cascade benefit. Non-contiguous gaps waste enforcement potential.")
print("=" * 70)

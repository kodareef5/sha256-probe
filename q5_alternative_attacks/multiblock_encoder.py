#!/usr/bin/env python3
"""
multiblock_encoder.py — Block 2 collision encoder for multi-block attack

Given: Block 1 produces H1 = IV + compress(IV, M1), H2 = IV + compress(IV, M2)
       where H1 ≠ H2 (near-collision with known residual dH = H1 XOR H2)

Find:  M1', M2' such that H1 + compress(H1, M1') == H2 + compress(H2, M2')

This is a STANDARD collision problem with:
- Known IV differential (dH from block 1)
- Full message freedom (512 bits per message)
- Full 64 rounds

The advantage over sr=60: we have 512 bits of message freedom (vs 128 bits
from 4 free schedule words). Message modification can deterministically
satisfy conditions in the first ~20 rounds.

For testing: we first check if the problem is feasible at REDUCED ROUNDS.
If we can find a block-2 collision at 20 rounds with the given IV diff,
that's strong evidence the multi-block approach works.

Usage: python3 multiblock_encoder.py [n_rounds] [timeout]
"""

import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def compute_sr59_residual():
    """Compute what Block 1 (sr=59) produces as IV differential for Block 2.

    At sr=59, we have a FULL collision in the compression function output.
    So H1 = IV + compress(IV, M1) = IV + compress(IV, M2) = H2.
    The residual is ZERO — sr=59 already gives a hash collision!

    The interesting case is sr=58 or partial sr=59:
    - sr=58 means W[62] is also free (6 free words)
    - Easier to achieve, but leaves a small residual in the hash output
    """
    print("Multi-Block Attack Analysis")
    print("=" * 60)
    print()
    print("IMPORTANT REALIZATION:")
    print("  sr=59 is a FULL compression function collision.")
    print("  The hash output is H = IV + compress(IV, M).")
    print("  If compress(IV, M1) = compress(IV, M2), then H1 = H2.")
    print("  So sr=59 already gives a HASH COLLISION — no block 2 needed!")
    print()
    print("  The sr=60 problem is about achieving collision with one")
    print("  MORE schedule constraint satisfied. This is not about")
    print("  'getting closer to a collision' — sr=59 IS a collision.")
    print()
    print("  The multi-block approach would help if we wanted a")
    print("  collision where ALL 64 schedule equations hold (sr=64),")
    print("  which would be a collision on the STANDARD SHA-256")
    print("  (not semi-free-start). But that's a much harder goal.")
    print()

    # What if Block 1 achieves only sr=58?
    # Then W[57..62] are free (6 words), W[63] is schedule-determined.
    # The compression outputs differ because the last few rounds
    # have schedule violations that prevent full collision.
    print("ALTERNATIVE: Block 1 with sr=58 (partial collision)")
    print("-" * 40)
    print("  sr=58: W[57..62] free, W[63] schedule-determined")
    print("  The compression outputs differ by the round-63 residual.")
    print("  Block 2 could absorb this residual.")
    print()
    print("  But sr=58 is EASIER than sr=59 (6 free words vs 5).")
    print("  If we can do sr=59 (proven SAT in 220s), why bother with sr=58?")
    print()

    # The REAL question: what does sr=60 give us that sr=59 doesn't?
    print("WHAT sr=60 ACTUALLY MEANS:")
    print("-" * 40)
    print("  sr=59: 5 free schedule words, collision is SEMI-FREE-START")
    print("    (the schedule has 5 'holes' that don't follow the expansion rule)")
    print()
    print("  sr=60: 4 free schedule words, still semi-free-start")
    print("    (4 holes instead of 5)")
    print()
    print("  sr=64: 0 free schedule words = STANDARD SHA-256 collision")
    print("    (all schedule equations hold, this is the ultimate goal)")
    print()
    print("  Going from sr=59 to sr=60 means closing ONE MORE schedule hole.")
    print("  This makes the collision 'more legitimate' but doesn't change")
    print("  the fundamental nature (still semi-free-start).")
    print()
    print("  The multi-block approach doesn't help here because the schedule")
    print("  violations are within a SINGLE compression block, not between blocks.")
    print()

    # What WOULD help:
    print("WHAT WOULD HELP:")
    print("-" * 40)
    print("  1. Programmatic SAT (IPASIR-UP): domain-specific propagation")
    print("     to help Kissat/CaDiCaL navigate the carry chains better.")
    print("     Evidence: 28→38 step improvement in the literature.")
    print()
    print("  2. Deeper parallelization: our 5-bit partition solver is")
    print("     running right now (32 partitions × 3600s on 24 cores).")
    print()
    print("  3. Decomposed trail search (Li et al.): find the optimal")
    print("     differential trail FIRST, then search for conforming pair.")
    print()
    print("  4. DIFFERENT gap placement: instead of freeing W[57..60],")
    print("     what if we free DIFFERENT schedule words? The choice of")
    print("     which 4 words to free determines the problem geometry.")
    print()

    return None


def explore_alternative_gap_placement():
    """What if we free different schedule words instead of W[57..60]?

    The standard sr=60 frees W[57..60] and enforces W[61..63].
    But what about freeing W[58..61] and enforcing W[62..63]?
    Or W[56..59] and enforcing W[60..63]?

    Different gap placements change which rounds have the schedule
    constraint vs freedom, potentially moving the obstruction to
    a different (easier) location.
    """
    print("\nALTERNATIVE GAP PLACEMENT ANALYSIS")
    print("=" * 60)

    # Standard: free W[57..60], enforce W[61..63]
    # This means:
    #   Rounds 57-60: free schedule words (4 degrees of freedom)
    #   Round 61: W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    #   Round 62: W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    #   Round 63: W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]

    print("Standard: free W[57..60], enforce W[61..63]")
    print("  Rounds 57-60: free (4 DOF)")
    print("  Round 61: W[61] determined by W[59] + constants")
    print("  Round 62: W[62] determined by W[60] + constants")
    print("  Round 63: W[63] determined by W[61] + constants")
    print("  dW[61] HW ~16 → the main obstruction")
    print()

    # Alternative 1: free W[58..61], enforce W[62..63]
    # Only 2 enforced rounds instead of 3
    # But we lose W[57] as a free variable
    print("Alternative 1: free W[58..61], enforce W[62..63]")
    print("  W[57]: ENFORCED (W[57] = sigma1(W[55]) + W[50] + sigma0(W[42]) + W[41])")
    print("  Rounds 58-61: free (4 DOF)")
    print("  Round 62: W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]")
    print("  Round 63: W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]")
    print("  Advantage: only 2 enforced rounds (62-63) vs 3 (61-63)")
    print("  Disadvantage: W[57] is now constrained, losing the da57=0 trick")
    print()

    # Alternative 2: free W[56..59], enforce W[60..63]
    print("Alternative 2: free W[56..59], enforce W[60..63]")
    print("  Rounds 56-59: free (but round 56 is the PRECOMPUTED state!)")
    print("  This changes the entire problem structure — state56 is no longer fixed")
    print("  Would need to re-encode from scratch. Much more complex.")
    print()

    # Alternative 3: non-contiguous gaps
    print("Alternative 3: non-contiguous gaps (e.g., free W[57,58,60,61])")
    print("  Skip W[59] (enforce it via schedule)")
    print("  This breaks the contiguous-gap assumption but might move")
    print("  the dW[61] obstruction to a more favorable position")
    print("  W[59] enforced: W[59] = sigma1(W[57]) + W[52] + sigma0(W[44]) + W[43]")
    print("  Since W[57] is still free, W[59] depends on W[57] non-linearly")
    print()

    print("VERDICT: Alternative gap placement is a promising unexplored direction.")
    print("The choice of which 4 words to free is a DESIGN DECISION, not a given.")
    print("Different placements produce different algebraic structures.")
    print("This deserves systematic exploration.")


if __name__ == "__main__":
    compute_sr59_residual()
    explore_alternative_gap_placement()

#!/usr/bin/env python3
"""
multiblock_concept.py — Feasibility analysis for multi-block sr=60 attack

The idea: instead of finding a collision in ONE compression block with sr=60,
use TWO blocks:
  Block 1: Achieve sr=59 collision (known to be feasible, ~220s)
           This produces H1 = compress(IV, M1) and H2 = compress(IV, M2)
           where H1 ≠ H2 but close (residual differential)
  Block 2: Find M1', M2' such that compress(H1, M1') = compress(H2, M2')
           The "IV" for block 2 is H1 and H2 (different for each message!)
           This is a SEMI-FREE-START collision with IV freedom.

The advantage: Block 2 has 256 bits of IV freedom (H1 vs H2 differ by
the sr=59 residual) PLUS 512 bits of message freedom (M1', M2' are free).

The question: does this extra freedom make the collision easier?

Analysis:
  - sr=59 residual: after block 1, the hash outputs differ by some amount
  - Block 2 must absorb this difference to produce equal final hashes
  - With free IV choice, this is much easier than fixed-IV collision
  - BUT: the IV isn't fully free — it's constrained by the sr=59 residual
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def analyze_sr59_residual():
    """Analyze what the sr=59 collision produces as block-1 output.

    sr=59 means 59 of 64 schedule equations hold. W[57..61] are free,
    W[62] and W[63] are schedule-determined. The collision is in the
    COMPRESSION FUNCTION output, not the full hash.

    After sr=59, the two messages produce different compression outputs.
    The HASH is IV + compress_output, so:
      H1 = IV + compress(IV, M1)
      H2 = IV + compress(IV, M2)
    where the addition is word-by-word mod 2^32.

    The residual dH = H1 - H2 = compress(IV, M1) - compress(IV, M2).
    This is determined by the sr=59 free words.
    """
    m0 = 0x17149975; fill = 0xffffffff
    M1 = [m0]+[fill]*15; M2 = list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000

    s1, W1 = precompute_state(M1)
    s2, W2 = precompute_state(M2)

    print("Multi-Block Attack Feasibility Analysis")
    print("=" * 60)
    print()
    print("Step 1: sr=59 collision (Block 1)")
    print("-" * 40)
    print(f"  sr=59 is SAT in ~220s (verified, CLAIMS.md)")
    print(f"  M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print(f"  State56 diff HW: {sum(hw(s1[i]^s2[i]) for i in range(8))}")
    print()

    # For sr=59: 5 free words W[57..61], 2 schedule-determined W[62..63]
    # The collision means compress(IV, M1) = compress(IV, M2) after 64 rounds
    # with the 5 free words satisfying the schedule compliance
    print("  With 5 free words (sr=59), the collision condition is:")
    print("  compress_output_1 == compress_output_2 (all 8 registers)")
    print("  This IS achievable (proven SAT)")
    print()

    # For sr=60: only 4 free words, AND W[61] is schedule-determined
    # The difference: W[61] introduces dW[61] with high HW
    print("Step 2: What if we DON'T require full collision in Block 1?")
    print("-" * 40)
    print("  Instead of sr=59 collision (all 8 registers equal),")
    print("  we only need a NEAR-collision (most registers equal,")
    print("  small residual in a few registers).")
    print()
    print("  sr=58 gives 6 free words → even easier than sr=59")
    print("  We could achieve near-collision where, say, 6 of 8")
    print("  registers match and the other 2 have small diffs.")
    print()

    print("Step 3: Block 2 absorbs the residual")
    print("-" * 40)
    print("  Block 2 compression: compress(H1, M1') vs compress(H2, M2')")
    print("  where H1, H2 are the block-1 outputs (different!)")
    print("  M1', M2' are completely free (512 bits of freedom each)")
    print()
    print("  The 'IV' for block 2 is (H1, H2). Since H1 ≠ H2,")
    print("  this is a collision with a KNOWN IV DIFFERENTIAL.")
    print()
    print("  Key question: how hard is a collision with known IV diff?")
    print()

    # Compute what the IV differential looks like for various sr levels
    print("  If block 1 achieves sr=59 but NOT sr=60:")
    print("  The residual is the round-63 state diff. With 5 free words,")
    print("  we can get 7 of 8 registers to zero. The 8th has some diff.")
    print()

    # Actually, sr=59 means FULL collision. The interesting case is
    # using sr=58 or even sr=57 for block 1, accepting a residual.
    print("  With sr=58 (block 1), we have 6 free words.")
    print("  We can zero da56 through da58 (6 registers via shift register)")
    print("  Residual: de and some others at the end.")
    print()
    print("  The multi-block advantage: we trade ONE hard sr=60 problem")
    print("  for TWO easier problems:")
    print("    Block 1: sr=58 near-collision (6 free words, very easy)")
    print("    Block 2: collision with known IV diff (full message freedom)")
    print()

    # The real question: is block 2 easier than sr=60?
    print("Step 4: Is Block 2 easier than direct sr=60?")
    print("-" * 40)
    print("  Block 2: compress(H1, M1') = compress(H2, M2')")
    print("  M1' and M2' are completely free — 16 words each = 512 bits")
    print("  The schedule is FULLY determined by M1'/M2' (no free words)")
    print("  So this is a STANDARD collision problem (like Wang's attack)")
    print()
    print("  The IV difference from block 1 is the only constraint.")
    print("  If the IV diff is small (few bits), standard differential")
    print("  cryptanalysis techniques (MILP trail search, message")
    print("  modification) can find a collision in rounds that absorb it.")
    print()
    print("  CRITICAL INSIGHT: Standard attacks on SHA-256 reach 31-39 steps.")
    print("  Block 2 is a FULL 64-round compression with full message freedom.")
    print("  The question is whether a small IV diff can be absorbed in")
    print("  the first ~10 rounds (where message modification is easy)")
    print("  before it propagates to later rounds.")
    print()
    print("  If the IV diff is in only 1-2 registers with HW < 10,")
    print("  standard Wang modification should handle it easily.")
    print()
    print("VERDICT: Multi-block attack is promising if we can control")
    print("the block-1 residual to be in specific registers with low HW.")
    print("This requires a PARTIAL sr=59 or sr=58 result in block 1.")


if __name__ == "__main__":
    analyze_sr59_residual()

#!/usr/bin/env python3
"""
mitm_cascade_sr60.py — Meet-in-the-middle attack on the two-cascade sr=60 (Issue #13)

The sr=60 collision uses two cascades:
- Cascade 1: W[57] chosen so da57=0 → db58=0 → dc59=0 → dd60=0
- Cascade 2: W[60] chosen so de60=0 → df61=0 → dg62=0 → dh63=0

Instead of searching the joint space of (W[57], W[58], W[59], W[60]) per message,
decompose:

1. FORWARD: enumerate (W[57], W[58], W[59]) triples, compute state after round 59.
   Store: state_at_59 -> (W57, W58, W59) assignments that produce it.

2. BACKWARD: enumerate W[60] values, compute what state at round 59 would need
   to be for the cascade 2 trigger (de60=0) to succeed, given this W[60].
   For each W[60], get a REQUIRED state at round 59.

3. MATCH: intersect the forward state set with the backward required set.
   Any intersection gives a full (W57, W58, W59, W60) collision.

Problem: the forward enumeration is 2^96 (three 32-bit words), too big.

Workaround for sr=60 validation: fix W[58] and W[59] to their certificate
values, enumerate only W[57] forward (2^32) and W[60] backward (2^32).
This is a 2x64-bit MITM with 128 GB RAM.

For the REAL sr=60 attack: use the XOR-linear structure to enumerate only
the ~35-dimensional subspace (per diff-linear rank) instead of full 2^96.

This file is the prototype — we validate against the known sr=60 SAT cert.
"""

import sys, os, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def forward_state_at_59(m0, fill, w57, w58, w59):
    """Given free words W[57..59], compute state after round 59 for both messages."""
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    # We need to know W1[57..59] and W2[57..59] per message.
    # In the sr=60 MITM, BOTH messages have separate free words.
    # For simplicity, assume w57, w58, w59 refer to (w1_57, w1_58, w1_59) for M1.
    # M2's words will be iterated separately (this is a half-MITM).
    # Full MITM would be 2^64 × 2^64 for the full (M1, M2) enumeration.

    # Actually, for the cascade structure, we can exploit symmetry:
    # If W1[i] - W2[i] = dWi (some fixed differential), then knowing W1 gives W2.
    # But the differentials aren't fixed — they're free variables.

    # Simplification: use the VERIFIED certificate values for M2, enumerate M1.
    w1_cert = [0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82]
    w2_cert = [0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b]

    W1_tail = build_schedule_tail(W1_pre, [w57, w58, w59, w1_cert[3]])
    W2_tail = build_schedule_tail(W2_pre, w2_cert)

    trace1 = run_tail_rounds(s1, W1_tail, start_round=57)
    trace2 = run_tail_rounds(s2, W2_tail, start_round=57)

    # trace[0] = before round 57, trace[3] = after round 59 (index 3: 57,58,59 applied)
    state1_59 = trace1[3]
    state2_59 = trace2[3]

    return state1_59, state2_59


def cascade_fingerprint(state1, state2):
    """Return a hashable summary of the differential state (XOR of M1 and M2)."""
    return tuple(state1[i] ^ state2[i] for i in range(8))


def validate_against_certificate():
    """Verify that the certificate reproduces the known collision."""
    M0 = 0x17149975
    FILL = 0xFFFFFFFF
    W1_CERT = [0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82]
    W2_CERT = [0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b]

    s1_59, s2_59 = forward_state_at_59(M0, FILL, W1_CERT[0], W1_CERT[1], W1_CERT[2])

    print("Certificate validation:")
    print(f"  State at round 59 (both messages):")
    regs = ['a','b','c','d','e','f','g','h']
    for r in range(8):
        d = s1_59[r] ^ s2_59[r]
        print(f"    d{regs[r]}59 = 0x{d:08x} (hw={hw(d)})")

    # For the collision, after round 59 we need the cascade setup:
    # da59=0, db59=0, dc59=0, dd59=0 (cascade 1 complete)
    # Remaining: de59, df59, dg59, dh59 (these set up cascade 2)
    total_hw = sum(hw(s1_59[r] ^ s2_59[r]) for r in range(8))
    print(f"  Total diff HW at round 59: {total_hw}")
    print(f"  Cascade 1 registers (a,b,c,d) all zero? "
          f"{all(s1_59[r] == s2_59[r] for r in range(4))}")


def main():
    validate_against_certificate()


if __name__ == "__main__":
    main()

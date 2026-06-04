#!/usr/bin/env python3
"""
verify_lever_collision.py — independent oracle for gap-placement witnesses.

Generalizes q6_verification/verify_sr60_collision.py to ARBITRARY free-position
sets (not just the top block {57..60}) and either message's free words.

Given a candidate (m0, fill, kernel_bit) and the free-word values for both
messages, this recomputes — using ONLY lib.sha256 primitives, sharing no code
with lever_gap_encoder.py — the full schedules and the 64-round compressions of
both messages, then reports:
  1. whether the state collides at round 63 (semi-free-start collision);
  2. the measured schedule compliance sr (count of expansion equations that
     actually hold), which must equal the claimed sr.

This is the ground truth. A correct encoder's solved witness must verify here; an
off-by-one in the encoder's schedule wiring produces free words that satisfy the
encoder's (wrong) instance but fail this independent recomputation.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lib.sha256 import (K, IV, MASK, add, sigma0, sigma1, Sigma0, Sigma1,
                        Ch, Maj, hw)

REG = ["a", "b", "c", "d", "e", "f", "g", "h"]


def build_schedule(M, free_overrides):
    """Full 64-word schedule for message M (16 words).

    free_overrides: {position: value} — at these expansion positions the word is
    a free/relaxed variable (use the given value); every other position 16..63 is
    computed from the recurrence W[t]=σ1(W[t-2])+W[t-7]+σ0(W[t-15])+W[t-16].
    """
    W = [w & MASK for w in M] + [0] * 48
    for t in range(16, 64):
        if t in free_overrides:
            W[t] = free_overrides[t] & MASK
        else:
            W[t] = add(sigma1(W[t - 2]), W[t - 7], sigma0(W[t - 15]), W[t - 16])
    return W


def run64(W):
    """Run all 64 SHA-256 rounds from the standard IV. Returns final state."""
    a, b, c, d, e, f, g, h = IV
    for i in range(64):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
    return (a, b, c, d, e, f, g, h)


def measure_sr(W):
    """sr = 16 + (# expansion equations 16..63 that hold for this schedule)."""
    held = [t for t in range(16, 64)
            if W[t] == add(sigma1(W[t - 2]), W[t - 7], sigma0(W[t - 15]), W[t - 16])]
    return 16 + len(held), set(held)


def verify(m0, fill, kernel_bit, free1, free2, claimed_sr=None, verbose=True):
    """Verify a gap-placement witness.

    free1/free2: {position: value} free-word assignments for M1 / M2.
    Returns dict with collision (bool), sr (int), and details.
    """
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= (1 << kernel_bit)
    M2[9] ^= (1 << kernel_bit)

    W1 = build_schedule(M1, free1)
    W2 = build_schedule(M2, free2)
    f1 = run64(W1)
    f2 = run64(W2)

    diffs = [f1[i] ^ f2[i] for i in range(8)]
    collision = all(d == 0 for d in diffs)
    sr1, held1 = measure_sr(W1)
    sr2, held2 = measure_sr(W2)

    H1 = tuple(add(IV[i], f1[i]) for i in range(8))
    H2 = tuple(add(IV[i], f2[i]) for i in range(8))

    if verbose:
        print(f"=== gap-placement witness verification ===")
        print(f"m0=0x{m0:08x} fill=0x{fill:08x} kernel_bit={kernel_bit}")
        print(f"free positions: {sorted(set(free1) | set(free2))}")
        print(f"da[56] xor = 0x{(_state_at(W1,56)[0]^_state_at(W2,56)[0]):08x}")
        print(f"measured sr: M1={sr1}, M2={sr2}  (held sets match: {held1==held2})")
        if claimed_sr is not None:
            ok = (sr1 == claimed_sr == sr2)
            print(f"claimed sr={claimed_sr}: {'OK' if ok else 'MISMATCH'}")
        for i in range(8):
            mark = "OK" if diffs[i] == 0 else f"DIFF hw={hw(diffs[i])}"
            print(f"  d{REG[i]}[63] = 0x{diffs[i]:08x}  {mark}")
        if collision:
            print("*** STATE COLLISION at r63 VERIFIED ***")
            print(f"H1 = {''.join(f'{h:08x}' for h in H1)}")
            print(f"H2 = {''.join(f'{h:08x}' for h in H2)}")
            print("HASH COLLISION CONFIRMED" if H1 == H2 else "WARN: hashes differ?!")
        else:
            print(f"NOT a collision: total diff HW = {sum(hw(d) for d in diffs)}")

    return {
        "collision": collision,
        "sr_m1": sr1, "sr_m2": sr2,
        "held_match": held1 == held2,
        "diffs": diffs,
        "total_diff_hw": sum(hw(d) for d in diffs),
        "H1": H1, "H2": H2,
        "W1": W1, "W2": W2,
    }


def _state_at(W, r):
    """State after round r (0-indexed), for diagnostics (e.g. da[56])."""
    a, b, c, d, e, f, g, h = IV
    for i in range(r + 1):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
    return (a, b, c, d, e, f, g, h)


# --- Self-test against the known sr=60 certificate (validates THIS verifier) ---
CERT = {
    "m0": 0x17149975, "fill": 0xFFFFFFFF, "kernel_bit": 31,
    "W1": {57: 0x9ccfa55e, 58: 0xd9d64416, 59: 0x9e3ffb08, 60: 0xb6befe82},
    "W2": {57: 0x72e6c8cd, 58: 0x4b96ca51, 59: 0x587ffaa6, 60: 0xea3ce26b},
    "claimed_sr": 60,
}


def selftest():
    print("### SELF-TEST: known sr=60 certificate (sr60_n32_m17149975) ###")
    r = verify(CERT["m0"], CERT["fill"], CERT["kernel_bit"],
               CERT["W1"], CERT["W2"], claimed_sr=CERT["claimed_sr"])
    ok = r["collision"] and r["sr_m1"] == 60 and r["sr_m2"] == 60 and r["held_match"]
    print(f"\nSELF-TEST {'PASSED' if ok else 'FAILED'}: "
          f"verifier reproduces the cert as a genuine sr=60 collision.")
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(0 if selftest() else 1)
    selftest()

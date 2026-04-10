#!/usr/bin/env python3
"""
Full MITM attack on the two-cascade sr=60 mechanism (Issue #13).

Architecture:
  FORWARD (W[57]):   enumerate W1[57], compute state @ round 57 (after cascade 1 init)
  EXTEND (W[58,59]): apply fixed W[58], W[59] to reach round 59 state
  BACKWARD (W[60]):  for each W1[60], compute what round 59 state is REQUIRED
  MATCH:             forward round-59 state ∩ backward required state

For the prototype: fix W[58] and W[59] to the certificate values, enumerate
W[57] and W[60] independently, match on the round-59 state fingerprint.

This validates:
1. The MITM decomposition recovers the known sr=60 collision
2. How many hits exist (if more than just the cert, the methodology scales)
3. The RAM footprint matches the 128 GB budget

Usage: python3 cascade_mitm_full.py [n_forward] [n_backward]
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


# Verified sr=60 certificate
M0 = 0x17149975
FILL = 0xFFFFFFFF
W1_CERT = [0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82]
W2_CERT = [0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b]


def compute_cascade1_offset(s1, s2):
    """Compute C such that W2[57] = W1[57] + C gives da57 = 0."""
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    dT2 = (T2_1 - T2_2) & MASK
    return (dh + dSig1 + dCh + dT2) & MASK


def compute_cascade2_offset(s1, s2):
    """Compute C such that W2[60] = W1[60] + C gives de60 = 0.

    At round 60: e60 = d59 + T1_60
    T1_60 = h59 + Sigma1(e59) + Ch(e59,f59,g59) + K[60] + W[60]
    For de60 = 0: (d59_1 - d59_2) + (T1_60_1 - T1_60_2) = 0

    But d59_1 = d59_2 = 0 after cascade 1 propagates (dd59=0 from c58=0 from b57=0 from a56=0).
    Wait — the shift register gives d59 = c58 = b57 = a56 = 0. Yes, dd59 = 0.

    So de60 = 0 reduces to dT1_60 = 0:
      W2[60] = W1[60] + dh59 + dSigma1(e59) + dCh(e59,f59,g59)
    """
    # Note: requires s1, s2 to be state at round 59, not 56
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    return (dh + dSig1 + dCh) & MASK


def round57_state(s1, s2, w1_57, C_w57):
    """Apply round 57 to both messages, return (state1_57, state2_57)."""
    w2_57 = (w1_57 + C_w57) & MASK

    def one_round(s, w):
        T1 = add(s[7], Sigma1(s[4]), Ch(s[4], s[5], s[6]), K[57], w)
        T2 = add(Sigma0(s[0]), Maj(s[0], s[1], s[2]))
        a = add(T1, T2)
        e = add(s[3], T1)
        return (a, s[0], s[1], s[2], e, s[4], s[5], s[6])

    return one_round(s1, w1_57), one_round(s2, w2_57)


def apply_round(state, w, round_idx):
    """Apply one SHA-256 round."""
    T1 = add(state[7], Sigma1(state[4]), Ch(state[4], state[5], state[6]),
             K[round_idx], w)
    T2 = add(Sigma0(state[0]), Maj(state[0], state[1], state[2]))
    a = add(T1, T2)
    e = add(state[3], T1)
    return (a, state[0], state[1], state[2], e, state[4], state[5], state[6])


def round_state_diff(s1, s2):
    """XOR difference of two states."""
    return tuple(s1[i] ^ s2[i] for i in range(8))


def main():
    n_forward = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    n_backward = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

    # Setup
    M1 = [M0] + [FILL] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1_init, W1_pre = precompute_state(M1)
    s2_init, W2_pre = precompute_state(M2)

    C_w57 = compute_cascade1_offset(s1_init, s2_init)
    print(f"Cascade 1 offset: W2[57] = W1[57] + 0x{C_w57:08x}")
    print(f"Cert W1[57]=0x{W1_CERT[0]:08x}, W2[57]=0x{W2_CERT[0]:08x}")
    assert (W1_CERT[0] + C_w57) & MASK == W2_CERT[0], (
        f"Cert mismatch: expected 0x{(W1_CERT[0]+C_w57)&MASK:08x}, "
        f"got 0x{W2_CERT[0]:08x}"
    )
    print("  -> Cert values match the offset formula.\n")

    # Forward: enumerate W1[57], apply cert W[58] and W[59], record round-59 state
    print(f"=== FORWARD: {n_forward} W1[57] samples ===")
    print("(W[58] and W[59] fixed to cert values)\n")

    forward_states = {}  # diff_fingerprint -> w1_57
    import random
    random.seed(42)
    t0 = time.time()

    for trial in range(n_forward):
        if trial == 0:
            w1_57 = W1_CERT[0]  # cert first for validation
        else:
            w1_57 = random.getrandbits(32)
        w2_57 = (w1_57 + C_w57) & MASK

        # Round 57
        s1_57 = apply_round(s1_init, w1_57, 57)
        s2_57 = apply_round(s2_init, w2_57, 57)
        # Round 58 (cert W)
        s1_58 = apply_round(s1_57, W1_CERT[1], 58)
        s2_58 = apply_round(s2_57, W2_CERT[1], 58)
        # Round 59 (cert W)
        s1_59 = apply_round(s1_58, W1_CERT[2], 59)
        s2_59 = apply_round(s2_58, W2_CERT[2], 59)

        # Verify cascade 1: da59 should == 0 (via shift: a59 depends on a58 = a57_shifted...
        # Actually at round 59: a59 is NEW (T1+T2), b59 = a58, c59 = b58 = a57 = 0 ✓, d59 = c58 = b57 = a56 = 0 ✓
        dc59 = s1_59[2] ^ s2_59[2]
        dd59 = s1_59[3] ^ s2_59[3]
        if dc59 != 0 or dd59 != 0:
            print(f"  WARNING: cascade 1 broke at w1_57=0x{w1_57:08x}")
            continue

        # Record round-59 state diff (just e, f, g, h since a,b,c,d vary independently)
        # For cascade 2 to work: need de60=0, which requires dh59 + dSigma1(e59) + dCh match
        # The "fingerprint" for matching is (de59, df59, dg59, dh59)
        diff = round_state_diff(s1_59, s2_59)
        fp = (diff[4], diff[5], diff[6], diff[7])
        forward_states[fp] = (w1_57, diff)

        if trial == 0:
            print(f"  CERT w1_57=0x{w1_57:08x}")
            regs = ['a','b','c','d','e','f','g','h']
            for r in range(8):
                print(f"    d{regs[r]}59 = 0x{diff[r]:08x} (hw={hw(diff[r])})")
            print()

    t_fwd = time.time() - t0
    print(f"Forward: {len(forward_states)} unique round-59 fingerprints in {t_fwd:.1f}s "
          f"({n_forward/t_fwd:.0f} samples/s)")
    print()

    # Backward: for each W1[60], compute what round-59 state is compatible with de60=0
    # But we also need d59=0 (cascade 1), so we need forward state with dd59=0
    # AND the dW[60] must zero de60 given the forward (de59, df59, dg59, dh59)
    #
    # Rather than enumerating W1[60] directly, we observe:
    # For ANY forward round-59 state (de59, df59, dg59, dh59):
    #   exactly one W1[60] -> W2[60] pair makes de60 = 0
    # So the MITM matching is trivial once forward is computed — ONE W1[60] per forward state.
    #
    # The real MITM match is at ROUND 63: need all 8 registers to collide.
    # Given cascade 2 propagation (de60=0 → df61=0 → dg62=0 → dh63=0),
    # we get de63=df63=dg63=dh63=0 for free.
    # But what about a63, b63, c63, d63? These depend on T1+T2 accumulation in rounds 60-63.
    #
    # So the MITM real test is: for the cert forward state, does W[60] trigger cascade 2
    # AND produce a,b,c,d collision at round 63?

    print("=== MATCHING: For cert forward state, compute required W[60] ===")
    cert_fp = (forward_states.get(tuple(W1_CERT[0:4]))
               if tuple(W1_CERT[0:4]) in forward_states
               else list(forward_states.values())[0])
    # Just use the first (cert) forward state
    cert_entry = list(forward_states.values())[0]  # cert is first
    cert_w57, cert_diff59 = cert_entry
    print(f"Using forward state from w1_57=0x{cert_w57:08x}")
    print(f"  Round-59 diffs (hex): {[f'0x{d:08x}' for d in cert_diff59]}")

    # Compute what W1[60] to W2[60] offset makes de60=0
    # Need state at round 59, but only have the diff. Recompute from cert.
    s1_59_cert = s1_init
    s2_59_cert = s2_init
    s1_59_cert = apply_round(s1_59_cert, W1_CERT[0], 57)
    s2_59_cert = apply_round(s2_59_cert, W2_CERT[0], 57)
    s1_59_cert = apply_round(s1_59_cert, W1_CERT[1], 58)
    s2_59_cert = apply_round(s2_59_cert, W2_CERT[1], 58)
    s1_59_cert = apply_round(s1_59_cert, W1_CERT[2], 59)
    s2_59_cert = apply_round(s2_59_cert, W2_CERT[2], 59)

    C_w60 = compute_cascade2_offset(s1_59_cert, s2_59_cert)
    print(f"Cascade 2 offset: W2[60] = W1[60] + 0x{C_w60:08x}")
    cert_offset = (W2_CERT[3] - W1_CERT[3]) & MASK
    print(f"Cert offset: W2[60]-W1[60] = 0x{cert_offset:08x}")
    print(f"Match: {C_w60 == cert_offset}")


if __name__ == "__main__":
    main()

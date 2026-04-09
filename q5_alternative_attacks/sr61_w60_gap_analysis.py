#!/usr/bin/env python3
"""
sr61_w60_gap_analysis.py — Quantify the algebraic gap between
the cascade-triggering W[60] (verified sr=60 cert) and the
schedule-mandated W[60] for the same message prefix.

In sr=61, W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44].
Of those, W[44], W[45], W[53] are precomputed (fixed by M[0]+fill).
Only W[58] is "tunable" per-message (it's also one of the 3 free words).

So W[60]_rule = sigma1(W[58]) + const_per_message.

This script measures, for the verified sr=60 collision:
1. The actual W[60] in the certificate (which produces de60=0)
2. The schedule-mandated W[60] using the cert's W[58]
3. The XOR distance and additive distance between them
4. Whether ANY W[58] choice could close the gap (sigma1 is non-bijective
   so we sweep — but we can also reason about its image)
5. The image dimension of sigma1 — if it covers <2^32 values, the gap
   may be unreachable for some constants
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *

# The verified sr=60 collision certificate
M0 = 0x17149975
FILL = 0xFFFFFFFF
W1_CERT = [0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82]  # W[57..60]
W2_CERT = [0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b]


def schedule_w60(W_pre, w58):
    """W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]"""
    return add(sigma1(w58), W_pre[53], sigma0(W_pre[45]), W_pre[44])


def main():
    M1 = [M0] + [FILL] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    print("=== sr=61 W[60] Gap Analysis ===")
    print(f"Candidate: M[0]=0x{M0:08x}, fill=0x{FILL:08x}\n")

    for tag, W_pre, W_cert in [("M1", W1_pre, W1_CERT),
                                ("M2", W2_pre, W2_CERT)]:
        w57, w58, w59, w60_actual = W_cert
        w60_rule = schedule_w60(W_pre, w58)
        xor_diff = w60_actual ^ w60_rule
        add_diff = (w60_actual - w60_rule) & MASK

        # Decompose: const = W[53] + sigma0(W[45]) + W[44]
        const = add(W_pre[53], sigma0(W_pre[45]), W_pre[44])
        # Required sigma1(W[58]_alt) to make rule match actual:
        required_sig = (w60_actual - const) & MASK

        print(f"--- {tag} ---")
        print(f"  W[44]    = 0x{W_pre[44]:08x}")
        print(f"  W[45]    = 0x{W_pre[45]:08x}")
        print(f"  W[53]    = 0x{W_pre[53]:08x}")
        print(f"  const    = 0x{const:08x}  (W[53]+sigma0(W[45])+W[44])")
        print(f"  W[58]    = 0x{w58:08x}  (cert)")
        print(f"  sigma1(W[58]) = 0x{sigma1(w58):08x}")
        print(f"  W[60] cert     = 0x{w60_actual:08x}  (cascade-triggering)")
        print(f"  W[60] rule     = 0x{w60_rule:08x}  (schedule-mandated, using cert W[58])")
        print(f"  XOR diff       = 0x{xor_diff:08x} (hw={hw(xor_diff)})")
        print(f"  ADD diff       = 0x{add_diff:08x} (hw={hw(add_diff)})")
        print(f"  required sigma1(W[58]_alt) = 0x{required_sig:08x}")
        print()


def sigma1_image_test(n_samples=1<<22):
    """How surjective is sigma1? Sample and count distinct images."""
    print("=== sigma1 image density test ===")
    seen = set()
    for i in range(n_samples):
        seen.add(sigma1(i))
        if i & 0xFFFFF == 0xFFFFF:
            print(f"  {(i+1)>>20}M inputs -> {len(seen)} distinct outputs "
                  f"({100*len(seen)/(i+1):.2f}%)")
    print(f"  Final: {n_samples} inputs -> {len(seen)} outputs")
    print(f"  Surjectivity proxy: {len(seen)/n_samples:.4f}")


def search_compatible_w58(W_pre, w60_target, max_steps=1<<24):
    """Brute-search for ANY w58 such that schedule_w60(w58) == target."""
    const = add(W_pre[53], sigma0(W_pre[45]), W_pre[44])
    needed_sig = (w60_target - const) & MASK
    print(f"  Searching for sigma1(x) == 0x{needed_sig:08x}...")
    found = []
    for x in range(max_steps):
        if sigma1(x) == needed_sig:
            found.append(x)
            if len(found) >= 5:
                break
    if found:
        print(f"  FOUND: {[hex(f) for f in found]}")
    else:
        print(f"  Searched {max_steps} inputs, no preimage in low range")
    return found


def joint_search(W1_pre, W2_pre, w60_1_target, w60_2_target, max_steps=1<<20):
    """
    Even harder: find w58_1, w58_2 such that BOTH messages get correct
    cascade-triggering W[60]. (They can be different per message.)
    Since they're independent, just search each separately.
    """
    print("\n=== Independent W[58] preimage search per message ===")
    print(f"M1 target W[60] = 0x{w60_1_target:08x}")
    f1 = search_compatible_w58(W1_pre, w60_1_target, max_steps)
    print(f"M2 target W[60] = 0x{w60_2_target:08x}")
    f2 = search_compatible_w58(W2_pre, w60_2_target, max_steps)

    if f1 and f2:
        print(f"\n  Both have preimages -> sr=61 W[60] WOULD be reachable")
        print(f"  IF such (w58_1, w58_2) also satisfy the rest of the constraints")
    else:
        print(f"\n  At least one target has no low-range preimage")
        print(f"  But sigma1 is essentially surjective, so longer search may find one")


if __name__ == "__main__":
    main()
    print()
    M1 = [M0] + [FILL] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)
    joint_search(W1_pre, W2_pre, W1_CERT[3], W2_CERT[3], max_steps=1<<22)

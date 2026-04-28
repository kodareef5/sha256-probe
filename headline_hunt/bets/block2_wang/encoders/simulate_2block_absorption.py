#!/usr/bin/env python3
"""
simulate_2block_absorption.py — pre-SAT forward simulator for 2-block
cascade-1 + Wang absorption trail bundles.

Takes a trail bundle JSON (per 2BLOCK_CERTPIN_SPEC.md / F82) and
forward-simulates BOTH block-1 (cascade-1 differential trail) and
block-2 (yale's absorption design) deterministically. Reports whether
the chained 2-block output is a collision, a near-residual, or
forward-broken (where yale's block-2 design fails to absorb the
expected residual).

Usage:
    python3 simulate_2block_absorption.py <trail_bundle.json>

Why this exists:
- F84's build_2block_certpin.py handles the trivial case + dispatches
  to single-block cert-pin. Non-trivial bundles need encoder extension.
- Before yale invests in the SAT-side encoder extension, this simulator
  gives yale fast feedback on whether their block-2 trail is
  *structurally consistent* with their claimed block-1 residual.
- If the simulator says "the chained output diff is non-zero," yale's
  trail is forward-broken — no point submitting it to SAT.
- If the simulator says "all zero," the trail is at least
  forward-consistent — worth running through the SAT verifier.

This is FORWARD-ONLY simulation. It uses the W-witness from the
bundle directly; for trail bundles with `exact_diff` or
`bit_condition` constraints (where W2 is partly free), the simulator
samples W2 random within the constraint set and reports the FRACTION
of samples that are forward-consistent. Yale gets a probability
estimate.
"""
import argparse
import json
import os
import random
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from lib.sha256 import (K, IV, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, add)


def compress(M, IV_in):
    """Run all 64 rounds of SHA-256 compression on message M with input IV.
    Returns the round-63 working-state and final chaining-output state."""
    W = list(M) + [0] * 48
    for i in range(16, 64):
        W[i] = add(sigma1(W[i-2]), W[i-7], sigma0(W[i-15]), W[i-16])

    a, b, c, d, e, f, g, h = IV_in
    for i in range(64):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)

    final_state = (a, b, c, d, e, f, g, h)
    chain_out = tuple(add(a, b) for a, b in zip(IV_in, final_state))
    return final_state, chain_out


def compress_with_trace(M, IV_in):
    """Same as compress() but returns the per-round state trace. Returns
    (final_state, chain_out, trace) where trace[r] is the (a,b,c,d,e,f,g,h)
    tuple after round r (1-indexed; trace[0] = IV)."""
    W = list(M) + [0] * 48
    for i in range(16, 64):
        W[i] = add(sigma1(W[i-2]), W[i-7], sigma0(W[i-15]), W[i-16])

    a, b, c, d, e, f, g, h = IV_in
    trace = [(a, b, c, d, e, f, g, h)]
    for i in range(64):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
        trace.append((a, b, c, d, e, f, g, h))

    final_state = (a, b, c, d, e, f, g, h)
    chain_out = tuple(add(a, b) for a, b in zip(IV_in, final_state))
    return final_state, chain_out, trace


REG_INDEX = {ch: i for i, ch in enumerate("abcdefgh")}


def check_bit_conditions(trace1, trace2, conditions):
    """Check that all bit_condition entries hold against per-round state diff.
    Each condition: {round: R, register: 'a-h', bit: 0-31,
                     predicate: 'diff_zero' | 'diff_one' | 'diff_set' | 'diff_clear'}
    Returns (n_satisfied, n_total)."""
    n_total = len(conditions)
    n_satisfied = 0
    for c in conditions:
        if c.get("type") != "bit_condition":
            continue
        rnd = c["round"]
        reg = c.get("register", "a")
        bit = c.get("bit", 0)
        pred = c.get("predicate", "diff_zero")
        if rnd < 0 or rnd > 64:
            continue  # invalid
        # trace[rnd+1] is the state AFTER round rnd (matching round-63=trace[64])
        # but for "at round R" we usually mean the state after round R completes
        idx = min(rnd + 1, len(trace1) - 1)
        ri = REG_INDEX.get(reg, 0)
        v1 = (trace1[idx][ri] >> bit) & 1
        v2 = (trace2[idx][ri] >> bit) & 1
        d = v1 ^ v2
        if pred == "diff_zero" and d == 0:
            n_satisfied += 1
        elif pred == "diff_one" and d == 1:
            n_satisfied += 1
        elif pred == "diff_set" and d == 1:
            n_satisfied += 1  # synonym
        elif pred == "diff_clear" and d == 0:
            n_satisfied += 1  # synonym
    return n_satisfied, n_total


def hw32(x):
    return bin(x & MASK).count("1")


def reconstruct_block1(b1_spec):
    """From bundle's block1 spec, reconstruct the M1 / M1' messages and run.
    block1.W1_57_60 is the witness. For 4-W-free cascade-1, W[0..15] = padded
    cand message; the W[57..60] are pinned, and W[16..56,61..63] follow
    the schedule from W[0..15]."""
    m0 = int(b1_spec["m0"], 16)
    fill = int(b1_spec["fill"], 16)
    kernel_bit = b1_spec["kernel_bit"]
    diff = 1 << kernel_bit

    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= diff
    M2[9] ^= diff

    # The bundle pins W[57..60]; verify our schedule produces them
    # (else the bundle's W1_witness is inconsistent with the cand)
    W1_57_60_claimed = [int(x, 16) for x in b1_spec["W1_57_60"]]

    # Compute schedule from M1 to round 60
    W1 = list(M1) + [0] * 48
    for i in range(16, 64):
        W1[i] = add(sigma1(W1[i-2]), W1[i-7], sigma0(W1[i-15]), W1[i-16])

    # Note: in cascade-1, the "free" W1[57..60] don't follow the schedule —
    # they're the additional degrees of freedom beyond the cand's m0+fill.
    # So we should OVERRIDE schedule W1[57..60] with the bundle's witness.
    for i, val in enumerate(W1_57_60_claimed):
        W1[57 + i] = val
    # And recompute the dependent tail W[61..63] from the new W1[57..60]
    for i in range(61, 64):
        W1[i] = add(sigma1(W1[i-2]), W1[i-7], sigma0(W1[i-15]), W1[i-16])

    # Run M1's compression with the modified schedule
    a, b, c, d, e, f, g, h = IV
    for i in range(64):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W1[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
    state1_63 = (a, b, c, d, e, f, g, h)
    chain1_out = tuple(add(iv, s) for iv, s in zip(IV, state1_63))

    # For M2: cascade-1 chooses W2[57..60] specifically (NOT M2's natural
    # schedule) so that the cascade-zero structure holds at rounds 60-63.
    # If the bundle provides W2_57_60 explicitly (cascade-cert format), use it.
    # Otherwise, fall back to M2's natural schedule (which may produce a
    # different residual than yale claims).
    W2 = list(M2) + [0] * 48
    for i in range(16, 64):
        W2[i] = add(sigma1(W2[i-2]), W2[i-7], sigma0(W2[i-15]), W2[i-16])
    W2_57_60_explicit = b1_spec.get("W2_57_60")
    if W2_57_60_explicit:
        for i, val in enumerate(W2_57_60_explicit):
            W2[57 + i] = int(val, 16)
        # Recompute tail W2[61..63] from new W2[57..60]
        for i in range(61, 64):
            W2[i] = add(sigma1(W2[i-2]), W2[i-7], sigma0(W2[i-15]), W2[i-16])

    a, b, c, d, e, f, g, h = IV
    for i in range(64):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W2[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
    state2_63 = (a, b, c, d, e, f, g, h)
    chain2_out = tuple(add(iv, s) for iv, s in zip(IV, state2_63))

    return state1_63, state2_63, chain1_out, chain2_out


def synthesize_block2_W2(constraints, seed=42):
    """From a list of W2 constraints (per F82 SPEC), synthesize a concrete
    W2 message (16 words). For 'exact', use the value. For 'exact_diff',
    leave that round's value unconstrained (caller supplies pair). For
    'modular_relation' / 'bit_condition', random-sample within constraint.
    Returns W2_M_pair = (W2_M1, W2_M2) where each is a 16-word M."""
    rng = random.Random(seed)
    W2_M1 = [rng.getrandbits(32) for _ in range(16)]
    W2_M2 = list(W2_M1)

    for c in constraints:
        rnd = c["round"]
        if rnd >= 16:
            continue  # message-schedule-derived rounds; can't directly pin in M
        ctype = c["type"]
        if ctype == "exact":
            v = int(c["value"], 16)
            W2_M1[rnd] = v
            W2_M2[rnd] = v
        elif ctype == "exact_diff":
            d = int(c["diff"], 16)
            W2_M2[rnd] = W2_M1[rnd] ^ d
        # modular_relation, bit_condition: skip for now (random)

    return W2_M1, W2_M2


def simulate_bundle(bundle, n_samples=100, verbose=False):
    """Forward-simulate the trail bundle and report results.
    Returns dict with verdict, hw stats, etc."""
    b1 = bundle["block1"]
    b2 = bundle["block2"]

    state1_63, state2_63, chain1_out, chain2_out = reconstruct_block1(b1)
    actual_chain_diff = tuple(c1 ^ c2 for c1, c2 in zip(chain1_out, chain2_out))
    actual_chain_hw = sum(hw32(x) for x in actual_chain_diff)

    # Compare actual vs claimed residual_state_diff
    claimed = b1.get("residual_state_diff", {})
    claimed_diff_state = tuple(int(claimed.get(f"d{r}63", "0x0"), 16)
                               for r in "abcdefgh")
    actual_state_diff = tuple(s1 ^ s2 for s1, s2 in zip(state1_63, state2_63))

    if actual_state_diff != claimed_diff_state:
        return {
            "verdict": "BUNDLE_INCONSISTENT_BLOCK1",
            "claimed_state_diff": [hex(x) for x in claimed_diff_state],
            "actual_state_diff":  [hex(x) for x in actual_state_diff],
            "actual_state_hw":    sum(hw32(x) for x in actual_state_diff),
            "explanation": ("Bundle's claimed block-1 residual_state_diff "
                             "doesn't match forward simulation. Yale's trail "
                             "needs to use the ACTUAL block-1 residual, not "
                             "a different W-witness's residual."),
        }

    # Block-2 forward sim: sample W2 message-pairs satisfying constraints
    constraints = b2.get("W2_constraints", [])
    target = b2.get("target_diff_at_round_N", {})
    target_diff = tuple(int(target.get(f"diff_{r}", "0x0"), 16)
                        for r in "abcdefgh")
    target_hw = sum(hw32(x) for x in target_diff)

    bit_conditions = [c for c in constraints if c.get("type") == "bit_condition"]
    n_bit_conditions = len(bit_conditions)
    use_trace = n_bit_conditions > 0

    n_collision = 0
    n_near = 0
    n_bc_full = 0  # samples satisfying ALL bit-conditions
    n_bc_full_collisions = 0  # samples that BOTH satisfy bc + reach HW=0
    final_hws = []
    bc_satisfaction_dist = []  # how many bcs satisfied per sample
    for s in range(n_samples):
        W2_M1, W2_M2 = synthesize_block2_W2(constraints, seed=42 + s)
        # block-2 starts from chain1_out / chain2_out
        if use_trace:
            _, chain1_after2, trace1 = compress_with_trace(W2_M1, chain1_out)
            _, chain2_after2, trace2 = compress_with_trace(W2_M2, chain2_out)
            n_sat, _ = check_bit_conditions(trace1, trace2, bit_conditions)
            bc_satisfaction_dist.append(n_sat)
            if n_sat == n_bit_conditions:
                n_bc_full += 1
        else:
            _, chain1_after2 = compress(W2_M1, chain1_out)
            _, chain2_after2 = compress(W2_M2, chain2_out)
        diff = tuple(c1 ^ c2 for c1, c2 in zip(chain1_after2, chain2_after2))
        hw = sum(hw32(x) for x in diff)
        final_hws.append(hw)
        if hw == 0:
            n_collision += 1
            if use_trace and bc_satisfaction_dist[-1] == n_bit_conditions:
                n_bc_full_collisions += 1
        if hw <= target_hw + 4:  # within 4 bits of target
            n_near += 1

    final_hws.sort()
    verdict = ("COLLISIONS_FOUND" if n_collision > 0
               else "NEAR_RESIDUALS_FOUND" if n_near > 0
               else "FORWARD_BROKEN")

    return {
        "verdict": verdict,
        "n_samples": n_samples,
        "n_collisions_at_block2_round63": n_collision,
        "n_near_residuals": n_near,
        "n_bit_conditions": n_bit_conditions,
        "n_samples_satisfying_all_bit_conditions": n_bc_full,
        "n_bc_full_collisions": n_bc_full_collisions,
        "max_bc_satisfied": max(bc_satisfaction_dist) if bc_satisfaction_dist else None,
        "median_bc_satisfied": (sorted(bc_satisfaction_dist)[len(bc_satisfaction_dist)//2]
                                 if bc_satisfaction_dist else None),
        "min_final_hw": final_hws[0] if final_hws else None,
        "median_final_hw": final_hws[len(final_hws)//2] if final_hws else None,
        "max_final_hw": final_hws[-1] if final_hws else None,
        "target_hw": target_hw,
        "block1_residual_hw_consistent": True,
        "block1_actual_residual_hw": sum(hw32(x) for x in actual_state_diff),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="Path to 2blockcertpin/v1 trail bundle JSON")
    ap.add_argument("--n-samples", type=int, default=100,
                    help="W2 random samples (when constraints are partial). "
                         "Default 100.")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    with open(args.bundle) as f:
        bundle = json.load(f)

    result = simulate_bundle(bundle, n_samples=args.n_samples,
                              verbose=args.verbose)

    print(f"\n=== 2-block absorption forward simulation ===")
    print(f"Bundle:    {args.bundle}")
    print(f"Cand:      {bundle.get('cand_id', '?')}")
    print(f"Witness:   {bundle.get('witness_id', '?')}")
    print(f"Verdict:   {result['verdict']}")

    if result["verdict"] == "BUNDLE_INCONSISTENT_BLOCK1":
        print(f"\nBundle's claimed residual: {result['claimed_state_diff']}")
        print(f"Forward-sim actual:        {result['actual_state_diff']}")
        print(f"Actual HW: {result['actual_state_hw']}")
        print(f"\n{result['explanation']}")
        sys.exit(2)

    print(f"\nBlock-1 residual HW: {result['block1_actual_residual_hw']} (matches bundle)")
    print(f"Block-2 forward simulation:")
    print(f"  Samples:                        {result['n_samples']}")
    print(f"  Block-2 round-63 final HW range: "
          f"{result['min_final_hw']} - {result['max_final_hw']} "
          f"(median {result['median_final_hw']})")
    print(f"  Target HW:                      {result['target_hw']}")
    print(f"  Collisions (HW=0):              {result['n_collisions_at_block2_round63']}")
    print(f"  Near-residuals (HW≤target+4):   {result['n_near_residuals']}")
    if result.get("n_bit_conditions", 0) > 0:
        print(f"\nBit-conditions:                   {result['n_bit_conditions']}")
        print(f"  Samples satisfying ALL:           {result['n_samples_satisfying_all_bit_conditions']}/{result['n_samples']}")
        print(f"  Median bc satisfied per sample:   {result['median_bc_satisfied']}/{result['n_bit_conditions']}")
        print(f"  Max bc satisfied per sample:      {result['max_bc_satisfied']}/{result['n_bit_conditions']}")
        print(f"  Collisions ALSO satisfying ALL bc: {result['n_bc_full_collisions']}")

    if result["verdict"] == "COLLISIONS_FOUND":
        print(f"\n🎉 Forward simulation found a collision! "
              f"Submit to SAT verifier next.")
    elif result["verdict"] == "NEAR_RESIDUALS_FOUND":
        print(f"\nForward sim found near-residuals. Trail is structurally "
              f"close to a collision; SAT search may find it.")
    else:
        print(f"\nForward sim found NO collisions or near-residuals. "
              f"Trail may be forward-broken. Review block-2 constraints.")


if __name__ == "__main__":
    main()

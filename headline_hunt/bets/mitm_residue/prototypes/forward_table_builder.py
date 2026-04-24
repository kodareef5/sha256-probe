#!/usr/bin/env python3
"""
forward_table_builder.py — Extend q4_mitm_geometry/cascade_mitm_full.py all the
way to round 63 and dump the round-63 residue distribution as JSONL.

Why this is the next move: cascade_mitm_full.py only goes to round 59. The
real MITM target is round 63 (the collision boundary). With cascade-1 (W[57])
and cascade-2 (W[60]) determined by the chosen W[57] and the round-59 state,
the residue at round 63 is a function of (W[57], W[58], W[59]) only — 3×32 =
96 bits of freedom. This script enumerates that space and dumps the round-63
register-difference HW for downstream analysis.

Use cases:
  - Empirical check: does the round-63 residue concentrate on the predicted
    24-bit hard residue (g60, h60 propagated forward)?
  - Cross-candidate: run for 5 candidates, compare residue distributions —
    test the "candidate-independence" assumption from the bet.
  - Memory budget: if the distribution is broad and uniform, the 24-bit
    table assumption fails and the bet hits its kill criterion.

Usage:
    python3 forward_table_builder.py --m0 0x17149975 --fill 0xffffffff \
        --kernel-bit 31 --samples 1000 --w58 0xd9d64416 --w59 0x9e3ffb08 \
        --out forward_dist.jsonl

By default fixes W[58] and W[59] to the sr=60 cert values (so a 1000-sample
run includes the cert and serves as a sanity check). To explore the full 96-bit
W[58]×W[59]×W[57] space, pass --w58 random or --w58 sweep (TODO).

Output format (JSONL):
    {"w1_57":..., "w1_60":..., "diff63": {"a":hex, "b":hex, ..., "h":hex},
     "hw63": {"a":int, ..., "h":int}, "hw_abcd_total":int, "is_collision": bool}
"""
import argparse
import json
import os
import random
import sys
import time

# Find lib/ regardless of cwd
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from lib.sha256 import (K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, hw,
                        add, precompute_state)


REG_NAMES = "abcdefgh"


def cascade1_offset(s1, s2):
    """W2[57] = W1[57] + offset such that da57 = 0."""
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    return (dh + dSig1 + dCh + T2_1 - T2_2) & MASK


def cascade2_offset(s1_r59, s2_r59):
    """W2[60] = W1[60] + offset such that de60 = 0, given state at round 59."""
    dh = (s1_r59[7] - s2_r59[7]) & MASK
    dSig1 = (Sigma1(s1_r59[4]) - Sigma1(s2_r59[4])) & MASK
    dCh = (Ch(s1_r59[4], s1_r59[5], s1_r59[6]) - Ch(s2_r59[4], s2_r59[5], s2_r59[6])) & MASK
    return (dh + dSig1 + dCh) & MASK


def cascade_step_offset(s1_r, s2_r, round_idx):
    """W2[r] = W1[r] + offset such that the diagonal-zero cascade continues at round r+1.
    The required offset zeros da_{r+1} given that da_r=db_r=...=0 already (cascade has held).
    Same algebraic form as cascade1_offset/cascade2_offset, just at the current round's state.
    """
    dh = (s1_r[7] - s2_r[7]) & MASK
    dSig1 = (Sigma1(s1_r[4]) - Sigma1(s2_r[4])) & MASK
    dCh = (Ch(s1_r[4], s1_r[5], s1_r[6]) - Ch(s2_r[4], s2_r[5], s2_r[6])) & MASK
    T2_1 = (Sigma0(s1_r[0]) + Maj(s1_r[0], s1_r[1], s1_r[2])) & MASK
    T2_2 = (Sigma0(s2_r[0]) + Maj(s2_r[0], s2_r[1], s2_r[2])) & MASK
    return (dh + dSig1 + dCh + T2_1 - T2_2) & MASK


def apply_round(state, w, round_idx):
    T1 = add(state[7], Sigma1(state[4]), Ch(state[4], state[5], state[6]),
             K[round_idx], w)
    T2 = add(Sigma0(state[0]), Maj(state[0], state[1], state[2]))
    a = add(T1, T2)
    e = add(state[3], T1)
    return (a, state[0], state[1], state[2], e, state[4], state[5], state[6])


def build_schedule_word(W_pre, W_free, r):
    """Return W[r] using existing W (W_pre for r<57, W_free for r in [57, current))."""
    def W_at(idx):
        if idx < 57:
            return W_pre[idx]
        return W_free[idx - 57]
    return add(sigma1(W_at(r - 2)), W_at(r - 7),
               sigma0(W_at(r - 15)), W_at(r - 16))


def run_one(s1_init, s2_init, W1_pre, W2_pre, w1_57, w1_58, w1_59, w1_60,
            return_intermediate=False):
    """
    One forward sample. cw57, cw58, cw59, cw60 are computed *dynamically* per
    round from the current state — that's what makes the cascade chain hold.
    Fixing cw to cert values from a previous run is wrong because the round-r
    state depends on W[57..r-1], so the required offset shifts.

    Returns the 8-register diff at round 63, or None on cascade break.
    If return_intermediate=True, returns dict with diff at rounds 60 and 63.
    """
    # Round 57 — cw57 from initial state
    cw57 = cascade_step_offset(s1_init, s2_init, 57)
    w2_57 = (w1_57 + cw57) & MASK
    s1_57 = apply_round(s1_init, w1_57, 57)
    s2_57 = apply_round(s2_init, w2_57, 57)

    # Round 58 — cw58 from state-after-57
    cw58 = cascade_step_offset(s1_57, s2_57, 58)
    w2_58 = (w1_58 + cw58) & MASK
    s1_58 = apply_round(s1_57, w1_58, 58)
    s2_58 = apply_round(s2_57, w2_58, 58)

    # Round 59 — cw59 from state-after-58
    cw59 = cascade_step_offset(s1_58, s2_58, 59)
    w2_59 = (w1_59 + cw59) & MASK
    s1_59 = apply_round(s1_58, w1_59, 59)
    s2_59 = apply_round(s2_58, w2_59, 59)

    # Cascade chain sanity: db59, dc59, dd59 should be 0 by construction.
    if (s1_59[1] ^ s2_59[1]) or (s1_59[2] ^ s2_59[2]) or (s1_59[3] ^ s2_59[3]):
        return None

    # Round 60 — cw60 specifically zeros de60 (cascade 2 init).
    cw60 = cascade2_offset(s1_59, s2_59)
    w2_60 = (w1_60 + cw60) & MASK

    # Round 60
    s1_60 = apply_round(s1_59, w1_60, 60)
    s2_60 = apply_round(s2_59, w2_60, 60)

    # de60 sanity (cascade 2 should have zeroed it)
    if (s1_60[4] ^ s2_60[4]):
        return None

    # Build schedule for W[61..63]
    W1 = list(W1_pre[:57]) + [w1_57, w1_58, w1_59, w1_60]
    W2 = list(W2_pre[:57]) + [w2_57, w2_58, w2_59, w2_60]
    # Extend W to 64
    for r in range(61, 64):
        W1.append(add(sigma1(W1[r - 2]), W1[r - 7],
                      sigma0(W1[r - 15]), W1[r - 16]))
        W2.append(add(sigma1(W2[r - 2]), W2[r - 7],
                      sigma0(W2[r - 15]), W2[r - 16]))

    # Rounds 61, 62, 63
    s1, s2 = s1_60, s2_60
    for r in range(61, 64):
        s1 = apply_round(s1, W1[r], r)
        s2 = apply_round(s2, W2[r], r)

    diff63 = tuple(s1[i] ^ s2[i] for i in range(8))
    if return_intermediate:
        diff60 = tuple(s1_60[i] ^ s2_60[i] for i in range(8))
        return {"diff60": diff60, "diff63": diff63}
    return diff63


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m0", default="0x17149975")
    ap.add_argument("--fill", default="0xffffffff")
    ap.add_argument("--kernel-bit", type=int, default=31)
    ap.add_argument("--samples", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="/dev/stdout",
                    help="Output JSONL path (default stdout)")
    ap.add_argument("--w1-60", default="0xb6befe82",
                    help="W1[60] anchor. Default: cert value (0xb6befe82). The cascade-2 "
                         "offset is computed dynamically; W1[60] itself is the user's "
                         "free choice in this round.")
    args = ap.parse_args()

    m0 = int(args.m0, 16)
    fill = int(args.fill, 16)
    diff = 1 << args.kernel_bit

    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= diff
    M2[9] ^= diff

    s1_init, W1_pre = precompute_state(M1)
    s2_init, W2_pre = precompute_state(M2)
    if s1_init[0] != s2_init[0]:
        print(f"ERROR: candidate has da[56] != 0 — not cascade-eligible "
              f"({s1_init[0]:#x} vs {s2_init[0]:#x})", file=sys.stderr)
        sys.exit(2)

    w1_60_anchor = int(args.w1_60, 16)

    rng = random.Random(args.seed)
    fout = sys.stdout if args.out == "/dev/stdout" else open(args.out, "w")

    t0 = time.time()
    n_attempted = 0
    n_cascade_held = 0
    n_collisions = 0
    hw_dist = []  # list of (hw_abcd_total) for all good runs

    # Cert anchors for sanity. Trial 0 uses all four cert values; remaining trials
    # randomize W[57], W[58], W[59] (W[60] stays anchored — cascade-2 already
    # constrains it; varying both is a future extension).
    cert = {"w57": 0x9ccfa55e, "w58": 0xd9d64416, "w59": 0x9e3ffb08, "w60": 0xb6befe82}

    for trial in range(args.samples):
        if trial == 0:
            w1_57, w1_58, w1_59, w1_60 = cert["w57"], cert["w58"], cert["w59"], cert["w60"]
        else:
            w1_57 = rng.getrandbits(32)
            w1_58 = rng.getrandbits(32)
            w1_59 = rng.getrandbits(32)
            w1_60 = w1_60_anchor
        n_attempted += 1
        diff63 = run_one(s1_init, s2_init, W1_pre, W2_pre,
                         w1_57, w1_58, w1_59, w1_60)
        if diff63 is None:
            continue
        n_cascade_held += 1
        hw_per_reg = [hw(d) for d in diff63]
        hw_abcd = sum(hw_per_reg[:4])
        hw_dist.append(hw_abcd)
        is_coll = all(d == 0 for d in diff63)
        if is_coll:
            n_collisions += 1

        rec = {
            "w1_57": f"0x{w1_57:08x}",
            "diff63": {REG_NAMES[i]: f"0x{diff63[i]:08x}" for i in range(8)},
            "hw63": {REG_NAMES[i]: hw_per_reg[i] for i in range(8)},
            "hw_abcd_total": hw_abcd,
            "is_collision": is_coll,
        }
        fout.write(json.dumps(rec) + "\n")

    if fout is not sys.stdout:
        fout.close()

    elapsed = time.time() - t0
    rate = n_attempted / elapsed if elapsed > 0 else 0
    print(f"Done. {n_attempted} attempts in {elapsed:.2f}s ({rate:.0f}/s).",
          file=sys.stderr)
    print(f"  cascade-1 held:  {n_cascade_held}/{n_attempted}",
          file=sys.stderr)
    print(f"  collisions:      {n_collisions}", file=sys.stderr)
    if hw_dist:
        hw_dist.sort()
        print(f"  hw_abcd_total: min={hw_dist[0]} median={hw_dist[len(hw_dist)//2]} "
              f"max={hw_dist[-1]} mean={sum(hw_dist)/len(hw_dist):.1f}", file=sys.stderr)


if __name__ == "__main__":
    main()

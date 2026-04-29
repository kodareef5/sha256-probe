#!/usr/bin/env python3
"""
carry_chart_atlas.py — record carry-coordinate anatomy of singular_chamber
HW4/HW5 points and block2_wang score-86/87 absorber points.

Per the Tool 1 plan: decompose each "good" point into:
  D60, D61_hw, a57_xor guard
  parts at round 61: dh, dSig1, dCh, dT2
  carry masks at round 61
  round-56 trace (t1_carry_xor[4], t2_carry_xor)
  per-round tail (rounds 57..63)

Then enumerate small move operators and classify each as:
  PRESERVES_CHART + CLOSES_GUARD  (the holy grail per BET.yaml lines 83-87)
  PRESERVES_CHART (low D61, parts ratio similar) but a57_xor != 0
  DESTROYS_CHART  (parts ratio shifts, D61 jumps)

Reuses primitives from lib.sha256 (Sigma0/1, Ch, Maj, sigma0/1, precompute_state).
The C primitives in singular_defect_rank.c (cascade1_offset, cascade1_offset_parts,
carry_mask_add) are reimplemented in Python here for the small atlas dataset.

Usage:
    python3 carry_chart_atlas.py \\
        --chamber 0:0x370fef5f:0x6ced4182:0x9af03606 \\
        --chamber 8:0xaf07f044:0xdd73a9d7:0x57046fad \\
        --absorber-json path/to/F115_score86.json \\
        --absorber-json path/to/F135_score87.json \\
        --moves \\
        --out carry_chart_atlas.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Dict, Any, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from lib.sha256 import (
    K, IV, MASK, Ch, Maj, Sigma0, Sigma1, sigma0, sigma1,
    hw, add, precompute_state,
)


# ---------------------------------------------------------------------------
# Candidate registry — mirrors CANDIDATES[] in singular_defect_rank.c lines 125-147
# Index → (id, m0, fill, kernel_bit)
# ---------------------------------------------------------------------------
CANDIDATES = [
    ("msb_cert_m17149975_ff_bit31", 0x17149975, 0xffffffff, 31),  # idx=0
    ("bit19_m51ca0b34_55",          0x51ca0b34, 0x55555555, 19),  # idx=1
    ("msb_m9cfea9ce_00",            0x9cfea9ce, 0x00000000, 31),  # idx=2
    ("bit20_m294e1ea8_ff",          0x294e1ea8, 0xffffffff, 20),  # idx=3
    ("bit28_md1acca79_ff",          0xd1acca79, 0xffffffff, 28),  # idx=4
    ("bit28_m3e57289c_ff",          0x3e57289c, 0xffffffff, 28),  # idx=5
    ("bit18_m99bf552b_ff",          0x99bf552b, 0xffffffff, 18),  # idx=6
    ("bit18_mcbe11dc1_ff",          0xcbe11dc1, 0xffffffff, 18),  # idx=7
    ("bit3_m33ec77ca_ff",           0x33ec77ca, 0xffffffff, 3),   # idx=8
    ("bit3_m5fa301aa_ff",           0x5fa301aa, 0xffffffff, 3),   # idx=9
    ("bit1_m6fbc8d8e_ff",           0x6fbc8d8e, 0xffffffff, 1),   # idx=10
    ("bit14_m67043cdd_ff",          0x67043cdd, 0xffffffff, 14),  # idx=11
    ("bit14_mb5541a6e_ff",          0xb5541a6e, 0xffffffff, 14),  # idx=12
    ("bit14_m40fde4d2_ff",          0x40fde4d2, 0xffffffff, 14),  # idx=13
    ("bit25_ma2f498b1_ff",          0xa2f498b1, 0xffffffff, 25),  # idx=14
    ("bit4_m39a03c2d_ff",           0x39a03c2d, 0xffffffff, 4),   # idx=15
    ("bit29_m17454e4b_ff",          0x17454e4b, 0xffffffff, 16),  # idx=16
    ("bit15_m28c09a5a_ff",          0x28c09a5a, 0xffffffff, 15),  # idx=17
    ("msb_m189b13c7_80",            0x189b13c7, 0x80000000, 31),  # idx=18
    ("bit13_m4e560940_aa",          0x4e560940, 0xaaaaaaaa, 13),  # idx=19
    ("bit17_m427c281d_80",          0x427c281d, 0x80000000, 17),  # idx=20
]


# ---------------------------------------------------------------------------
# C-primitive ports (singular_defect_rank.c lines 163-199)
# ---------------------------------------------------------------------------

def carry_mask_add(a: int, b: int) -> int:
    """Bit-by-bit carry mask of (a + b) mod 2^32. Mirrors carry_mask_add() in C."""
    a &= MASK
    b &= MASK
    carry = 0
    mask = 0
    for i in range(32):
        ai = (a >> i) & 1
        bi = (b >> i) & 1
        co = (ai & bi) | (ai & carry) | (bi & carry)
        if co:
            mask |= 1 << i
        carry = co
    return mask


def cascade1_offset_parts(s1: Tuple[int, ...], s2: Tuple[int, ...]) -> Dict[str, Any]:
    """
    Decompose cascade1_offset = dh + dSig1 + dCh + dT2 into parts + sums + carries.
    Mirrors cascade1_offset_parts() in singular_defect_rank.c lines 185-199.
    """
    dh    = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh   = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    dT2   = ((Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2]))
             - (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2]))) & MASK
    parts = [dh, dSig1, dCh, dT2]
    sums = [0, 0, 0]
    sums[0] = (parts[0] + parts[1]) & MASK
    sums[1] = (sums[0] + parts[2]) & MASK
    sums[2] = (sums[1] + parts[3]) & MASK
    carries = [
        carry_mask_add(parts[0], parts[1]),
        carry_mask_add(sums[0],  parts[2]),
        carry_mask_add(sums[1],  parts[3]),
    ]
    offset = sums[2]
    return {"parts": parts, "sums": sums, "carries": carries, "offset": offset}


def apply_round(s: Tuple[int, ...], w: int, r: int) -> Tuple[int, ...]:
    """One SHA-256 round."""
    a, b, c, d, e, f, g, h = s
    T1 = add(h, Sigma1(e), Ch(e, f, g), K[r], w)
    T2 = add(Sigma0(a), Maj(a, b, c))
    return (
        add(T1, T2),  # new a
        a,            # new b = old a
        b,            # new c = old b
        c,            # new d = old c
        add(d, T1),   # new e = old d + T1
        e,            # new f = old e
        f,            # new g = old f
        g,            # new h = old g
    )


# ---------------------------------------------------------------------------
# Chamber / absorber → atlas record
# ---------------------------------------------------------------------------

def candidate_iv_pair(idx: int) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """
    For candidate idx, build M1 = [m0] + [fill]*15 and M2 = M1 with kernel diff
    at words 0 and 9 (cascade-1 standard), run rounds 0..56, return (s1, s2).
    """
    cand_id, m0, fill, kbit = CANDIDATES[idx]
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    diff = 1 << kbit
    M2[0] = M1[0] ^ diff
    M2[9] = M1[9] ^ diff
    s1, _ = precompute_state(M1)
    s2, _ = precompute_state(M2)
    return s1, s2


def expand_schedule(M: List[int]) -> List[int]:
    """W[0..63] from M[0..15]."""
    W = list(M) + [0] * 48
    for i in range(16, 64):
        W[i] = add(sigma1(W[i-2]), W[i-7], sigma0(W[i-15]), W[i-16])
    return W


def state_pair_at_rounds(s1_57: Tuple[int, ...], s2_57: Tuple[int, ...],
                         W1: List[int], W2: List[int]) -> Dict[int, Tuple[Tuple, Tuple]]:
    """
    Apply rounds 57..63 starting from state-AFTER-round-56 (== state-BEFORE-round-57).
    Returns {round_index: (s1, s2)} where state at key R is the state BEFORE applying
    round R (== AFTER applying round R-1).

    Convention: s1_57 / s2_57 is the state AFTER round 56 (which is what
    lib.sha256.precompute_state returns). We apply rounds 57..63.
    """
    states = {57: (s1_57, s2_57)}
    s1, s2 = s1_57, s2_57
    for r in range(57, 64):
        s1 = apply_round(s1, W1[r], r)
        s2 = apply_round(s2, W2[r], r)
        states[r + 1] = (s1, s2)
    return states


def decompose_point(s1_57: Tuple[int, ...], s2_57: Tuple[int, ...],
                    W1: List[int], W2: List[int]) -> Dict[str, Any]:
    """
    Compute the carry-chart atlas record for a (s_after_55, schedule) pair.

    "Defect" at round r (per singular_defect_rank.c tail_defects_for_x):
        offset[r] = cascade1_offset(s1, s2) BEFORE applying round r
        defect[r] = (W2[r] - W1[r]) - offset[r] mod 2^32

    For cascade-eligible (M1, M2) where W2 = W1 + offset at rounds 57..59 by
    construction, defect[57] = defect[58] = defect[59] = 0 exactly. Defects
    at rounds 60..63 emerge because schedule recurrence does NOT preserve
    the cascade offset.

    "D60" = defect[60]; "D61" = defect[61]; "D61_hw" = popcount(D61).
    "Exact D60 = 0" means the chamber sits on the cascade surface at round 60
    (the holy grail for slot-60 cascade hits).

    a57_xor = (state1[0] ^ state2[0]) AFTER round 56 (== before round 57).
    """
    states = state_pair_at_rounds(s1_57, s2_57, W1, W2)

    # a57_xor: state[0] difference AFTER round 56 (== before round 57).
    a57_xor = s1_57[0] ^ s2_57[0]

    # Round 56 trace: cannot be reconstructed without state-before-56;
    # left as zero placeholders for now (decompose_point is given state AFTER round 56).
    t1_xor = 0
    t2_xor = 0

    # Per-round defect computation for rounds 57..63.
    tail = []
    defects = {}
    for r in range(57, 64):
        s1_r, s2_r = states[r]
        decomp = cascade1_offset_parts(s1_r, s2_r)
        offset_r = decomp["offset"]
        defect_r = ((W2[r] - W1[r]) - offset_r) & MASK
        defects[r] = defect_r
        diff_full = tuple((s1_r[i] ^ s2_r[i]) & MASK for i in range(8))
        tail.append({
            "round": r,
            "W1": f"0x{W1[r]:08x}",
            "W2": f"0x{W2[r]:08x}",
            "cascade_offset": f"0x{offset_r:08x}",
            "defect": f"0x{defect_r:08x}",
            "defect_hw": hw(defect_r),
            "parts": [f"0x{p:08x}" for p in decomp["parts"]],
            "sums":  [f"0x{s:08x}" for s in decomp["sums"]],
            "carries": [f"0x{c:08x}" for c in decomp["carries"]],
            "state_diff_hw_per_reg": [hw(d) for d in diff_full],
            "state_diff_total_hw": sum(hw(d) for d in diff_full),
        })

    # D60 = defect at round 60. D61 = defect at round 61.
    D60 = defects[60]
    D61 = defects[61]
    D60_hw = hw(D60)
    D61_hw = hw(D61)

    # Parts decomposition AT round 61 (the most informative for chart
    # classification per the chamber memos).
    s1_61, s2_61 = states[61]
    parts61 = cascade1_offset_parts(s1_61, s2_61)

    return {
        "a57_guard_xor": f"0x{a57_xor:08x}",
        "a57_guard_xor_hw": hw(a57_xor),
        "D60": f"0x{D60:08x}",
        "D60_hw": D60_hw,
        "D61": f"0x{D61:08x}",
        "D61_hw": D61_hw,
        "round56_trace": {
            "t1_xor": f"0x{t1_xor:08x}",
            "t2_xor": f"0x{t2_xor:08x}",
            "t1_xor_hw": hw(t1_xor),
            "t2_xor_hw": hw(t2_xor),
        },
        "parts_at_61": {
            "dh":    f"0x{parts61['parts'][0]:08x}",
            "dSig1": f"0x{parts61['parts'][1]:08x}",
            "dCh":   f"0x{parts61['parts'][2]:08x}",
            "dT2":   f"0x{parts61['parts'][3]:08x}",
        },
        "parts_at_61_hw": {
            "dh":    hw(parts61["parts"][0]),
            "dSig1": hw(parts61["parts"][1]),
            "dCh":   hw(parts61["parts"][2]),
            "dT2":   hw(parts61["parts"][3]),
        },
        "carries_at_61": [f"0x{c:08x}" for c in parts61["carries"]],
        "tail": tail,
    }


# ---------------------------------------------------------------------------
# Move-operator generator + classifier
# ---------------------------------------------------------------------------

def chart_signature(record: Dict[str, Any]) -> Tuple:
    """
    Derive a coarse 'chart signature' from the parts-at-round-61 ratios.
    Two records are 'on the same chart' if their parts ratios + which parts
    dominate the cascade1_offset are similar. We use a simple categorical
    hash: which of {dh, dSig1, dCh, dT2} is largest by HW.
    """
    parts = record["parts_at_61"]
    hws = {k: hw(int(v, 16)) for k, v in parts.items()}
    # Sort parts by HW descending and take top-2 names.
    top = sorted(hws.items(), key=lambda kv: -kv[1])
    return (top[0][0], top[1][0], top[0][1] + top[1][1])  # dominant pair + their combined HW


def classify_move(base: Dict[str, Any], perturbed: Dict[str, Any]) -> str:
    """
    Return one of:
      PRESERVES_CHART_AND_CLOSES_GUARD   (the holy grail)
      PRESERVES_CHART                    (chart same, guard non-zero)
      CLOSES_GUARD_BUT_DESTROYS_CHART    (guard 0 but D61 jumped + chart shifted)
      DESTROYS_CHART                     (D61 ≥ base D61 + 4, chart shifted)
      NEUTRAL                            (no strong change)
    """
    base_a57 = int(base["a57_guard_xor"], 16)
    pert_a57 = int(perturbed["a57_guard_xor"], 16)
    base_d61 = base["D61_hw"]
    pert_d61 = perturbed["D61_hw"]
    base_sig = chart_signature(base)
    pert_sig = chart_signature(perturbed)

    chart_same = (base_sig[0] == pert_sig[0] and base_sig[1] == pert_sig[1])
    d61_jump = pert_d61 - base_d61

    if chart_same and pert_a57 == 0 and base_a57 != 0:
        return "PRESERVES_CHART_AND_CLOSES_GUARD"
    if chart_same and pert_d61 <= base_d61 + 1:
        return "PRESERVES_CHART"
    if pert_a57 == 0 and base_a57 != 0 and not chart_same:
        return "CLOSES_GUARD_BUT_DESTROYS_CHART"
    if d61_jump >= 4 and not chart_same:
        return "DESTROYS_CHART"
    return "NEUTRAL"


def generate_w_moves(W57: int, W58: int, W59: int, max_per_word: int = 32) -> List[Dict[str, Any]]:
    """
    Enumerate small W57/W58/W59 moves: single-bit flips on each word, plus
    a few small-delta operators (±1, ±2 mod 2^32).
    """
    moves = []
    for j in range(max_per_word):
        moves.append({
            "label": f"flip_W57_b{j}",
            "delta": (1 << j, 0, 0),
        })
        moves.append({
            "label": f"flip_W58_b{j}",
            "delta": (0, 1 << j, 0),
        })
        moves.append({
            "label": f"flip_W59_b{j}",
            "delta": (0, 0, 1 << j),
        })
    # Common-mode XOR at LSB family (move all three by the same bit).
    for j in range(max_per_word):
        moves.append({
            "label": f"xor_all_b{j}",
            "delta": (1 << j, 1 << j, 1 << j),
        })
    # Small modular increments.
    for k in (1, 2, 0xffffffff, 0xfffffffe):
        moves.append({"label": f"add_W57_{k:#x}", "delta": (k, 0, 0)})
        moves.append({"label": f"add_W58_{k:#x}", "delta": (0, k, 0)})
        moves.append({"label": f"add_W59_{k:#x}", "delta": (0, 0, k)})
    return moves


# ---------------------------------------------------------------------------
# Entry points: chamber + absorber
# ---------------------------------------------------------------------------

def evaluate_chamber(idx: int, W57: int, W58: int, W59: int,
                     W60: int = None) -> Dict[str, Any]:
    """
    Evaluate a singular_chamber witness on candidate idx.
    The C tool's cascade convention determines W2 from W1 + cascade-step offset
    for cands where the M1/M2 difference flows to schedule.
    For atlas purposes we mirror what the chamber search does: W1 = (W57..W60),
    W2[r] derived via cascade-step offset at each free round.

    For simplicity here we use a dedicated computation:
      M1 = [m0, fill, ..., fill]; M2 = M1 ^ kernel diff at words 0/9.
      Free schedule words W57..W60 are user-provided (chamber witness).
      We synthesize W2[57..60] from W1[57..60] + (W2 - W1) cascade offset
      computed via the SHA round-equation.

    For the atlas, we record both branches (chamber-style cascade derivation
    of W2, and the M-derived schedule). For the canonical chamber witnesses,
    the (W57..W60) ARE the M1 schedule values, and W2 is derived differently —
    so we use the cascade convention from singular_defect_rank.c.

    Approach (matching the C tool):
      1. Take s1, s2 = state after round 55 from M1/M2 (precompute_state).
      2. We need to apply round 56 first to get to "before round 57" state.
         But the chamber search treats W56 as the M-derived W56 (from M1 schedule).
      3. Then round 57 uses the chamber-given W57; W2 derived from cascade1_offset
         at round 57 to maintain the cascade-1 hardlock.
      4. Same for rounds 58, 59. Round 60 uses provided W60 if given, else
         reconstructed.
    """
    M1 = [CANDIDATES[idx][1]] + [CANDIDATES[idx][2]] * 15
    M2 = list(M1)
    diff = 1 << CANDIDATES[idx][3]
    M2[0] ^= diff
    M2[9] ^= diff
    # precompute_state returns state AFTER round 56 (== BEFORE round 57).
    s1_after56, _ = precompute_state(M1)
    s2_after56, _ = precompute_state(M2)

    W1_full = expand_schedule(M1)
    W2_full = expand_schedule(M2)

    # Plug in the chamber-given W57..W59 for the M1 side. W2 schedule for rounds
    # 57..59 follows the cascade-1 convention: W2[r] = W1[r] + offset_r, where
    # offset_r = cascade1_offset at that round so that the slot-r difference is
    # absorbed. W1[60..63] are computed via schedule recurrence using the
    # chamber-overridden W57..W59. This matches the C tail_defects_for_x
    # convention.
    s1, s2 = s1_after56, s2_after56
    W1_chamber = [W57, W58, W59]
    W2_chamber = []
    for i, w1_val in enumerate(W1_chamber):
        r = 57 + i
        offset_r = cascade1_offset_parts(s1, s2)["offset"]
        w2_val = (w1_val + offset_r) & MASK
        W2_chamber.append(w2_val)
        s1 = apply_round(s1, w1_val, r)
        s2 = apply_round(s2, w2_val, r)

    # Build full W1/W2: rounds 0..56 from M, rounds 57..59 from chamber,
    # rounds 60..63 from recurrence using chamber W57..W59.
    W1 = list(W1_full)
    W2 = list(W2_full)
    W1[57] = W1_chamber[0]; W1[58] = W1_chamber[1]; W1[59] = W1_chamber[2]
    W2[57] = W2_chamber[0]; W2[58] = W2_chamber[1]; W2[59] = W2_chamber[2]
    for r in range(60, 64):
        W1[r] = add(sigma1(W1[r-2]), W1[r-7], sigma0(W1[r-15]), W1[r-16])
        W2[r] = add(sigma1(W2[r-2]), W2[r-7], sigma0(W2[r-15]), W2[r-16])

    record = decompose_point(s1_after56, s2_after56, W1, W2)
    record["source"] = f"chamber:idx={idx}:{CANDIDATES[idx][0]}"
    record["candidate_idx"] = idx
    record["W57"] = f"0x{W57:08x}"
    record["W58"] = f"0x{W58:08x}"
    record["W59"] = f"0x{W59:08x}"
    record["W60_from_chamber"] = f"0x{W1[60]:08x}"
    record["W2_57"] = f"0x{W2_chamber[0]:08x}"
    record["W2_58"] = f"0x{W2_chamber[1]:08x}"
    record["W2_59"] = f"0x{W2_chamber[2]:08x}"
    return record


def evaluate_absorber(M1_hex: List[str], M2_hex: List[str],
                      label: str = "absorber") -> Dict[str, Any]:
    """
    Decompose a block2_wang absorber point given M1, M2 (16 hex strings each).
    For the absorber, schedule is M-derived. We compute s_after_55 from each
    side and run forward through round 63.
    """
    M1 = [int(x, 16) for x in M1_hex]
    M2 = [int(x, 16) for x in M2_hex]
    # precompute_state returns state AFTER round 56.
    s1_after56, _ = precompute_state(M1)
    s2_after56, _ = precompute_state(M2)
    W1 = expand_schedule(M1)
    W2 = expand_schedule(M2)

    record = decompose_point(s1_after56, s2_after56, W1, W2)
    record["source"] = f"absorber:{label}"
    record["W57"] = f"0x{W1[57]:08x}"
    record["W58"] = f"0x{W1[58]:08x}"
    record["W59"] = f"0x{W1[59]:08x}"
    record["W60_from_M"] = f"0x{W1[60]:08x}"
    record["W2_57"] = f"0x{W2[57]:08x}"
    record["W2_58"] = f"0x{W2[58]:08x}"
    record["W2_59"] = f"0x{W2[59]:08x}"
    record["M1_first_word"] = M1_hex[0]
    record["M2_first_word"] = M2_hex[0]
    return record


# ---------------------------------------------------------------------------
# Move enumeration on chamber points
# ---------------------------------------------------------------------------

def enumerate_chamber_moves(idx: int, W57: int, W58: int, W59: int,
                            base_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    For a chamber point, enumerate move operators and classify each.
    """
    moves = generate_w_moves(W57, W58, W59)
    out = []
    for mv in moves:
        d57, d58, d59 = mv["delta"]
        nw57 = (W57 + d57) & MASK
        nw58 = (W58 + d58) & MASK
        nw59 = (W59 + d59) & MASK
        try:
            pert = evaluate_chamber(idx, nw57, nw58, nw59)
        except Exception as e:
            pert = {"error": str(e)}
            continue
        cls = classify_move(base_record, pert)
        out.append({
            "move_label": mv["label"],
            "delta": [f"0x{d57:08x}", f"0x{d58:08x}", f"0x{d59:08x}"],
            "result_D61_hw": pert["D61_hw"],
            "result_a57_xor_hw": pert["a57_guard_xor_hw"],
            "result_chart_top": chart_signature(pert)[:2],
            "delta_D61": pert["D61_hw"] - base_record["D61_hw"],
            "classification": cls,
        })
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_chamber_arg(s: str) -> Tuple[int, int, int, int]:
    """Parse 'idx:W57:W58:W59' format."""
    parts = s.split(":")
    if len(parts) != 4:
        raise ValueError(f"--chamber needs format idx:W57:W58:W59 (got {s})")
    return int(parts[0]), int(parts[1], 16), int(parts[2], 16), int(parts[3], 16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chamber", action="append", default=[],
                    help="Chamber witness in 'idx:W57:W58:W59' hex form. Repeatable.")
    ap.add_argument("--absorber-json", action="append", default=[],
                    help="Path to score-86/87 absorber result JSON. Repeatable.")
    ap.add_argument("--moves", action="store_true",
                    help="Also enumerate move operators around each chamber point.")
    ap.add_argument("--out", default="carry_chart_atlas.jsonl",
                    help="Output JSONL.")
    args = ap.parse_args()

    records = []

    # Chamber points
    for ch in args.chamber:
        idx, w57, w58, w59 = parse_chamber_arg(ch)
        rec = evaluate_chamber(idx, w57, w58, w59)
        records.append(rec)
        print(f"  CHAMBER idx={idx} W57=0x{w57:08x}: D61_hw={rec['D61_hw']}, "
              f"a57_xor_hw={rec['a57_guard_xor_hw']}, "
              f"chart_top={chart_signature(rec)[:2]}")
        if args.moves:
            move_results = enumerate_chamber_moves(idx, w57, w58, w59, rec)
            cls_count = {}
            for m in move_results:
                cls_count[m["classification"]] = cls_count.get(m["classification"], 0) + 1
            print(f"    moves: {cls_count}")
            holy_grail = [m for m in move_results
                          if m["classification"] == "PRESERVES_CHART_AND_CLOSES_GUARD"]
            if holy_grail:
                print(f"    HOLY-GRAIL hits: {len(holy_grail)}")
                for hg in holy_grail[:5]:
                    print(f"      {hg['move_label']} D61={hg['result_D61_hw']}")
            rec["move_summary"] = cls_count
            rec["holy_grail_moves"] = [
                m for m in move_results
                if m["classification"] in
                   ("PRESERVES_CHART_AND_CLOSES_GUARD",
                    "CLOSES_GUARD_BUT_DESTROYS_CHART")
            ]
            rec["all_moves"] = move_results

    # Absorber points
    for path in args.absorber_json:
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception as e:
            print(f"  ABSORBER {path}: load error {e}", file=sys.stderr)
            continue
        # The result format has either "results" (list of restart records) or
        # "subsets" (list of mask records). Handle both.
        absorber_pairs = []
        if "results" in data:
            for r in data["results"]:
                if "M1" in r and "M2" in r:
                    absorber_pairs.append((r["M1"], r["M2"], f"score{r.get('score','?')}_r{r.get('restart','?')}"))
        if "subsets" in data:
            for s in data["subsets"]:
                best = s.get("best", {})
                if "M1" in best and "M2" in best:
                    aw = ",".join(str(x) for x in s.get("active_words", []))
                    absorber_pairs.append((best["M1"], best["M2"],
                                            f"active{aw}_score{best.get('score','?')}"))
        # Take only the top score from each file (smallest score) to avoid
        # bloating the atlas with thousands of records.
        absorber_pairs.sort(key=lambda x: int(x[2].split("score")[-1].split("_")[0])
                            if "score" in x[2] else 999)
        for M1_hex, M2_hex, label in absorber_pairs[:5]:
            rec = evaluate_absorber(M1_hex, M2_hex,
                                    label=f"{os.path.basename(path)}:{label}")
            records.append(rec)
            print(f"  ABSORBER {label}: D61_hw={rec['D61_hw']}, "
                  f"a57_xor_hw={rec['a57_guard_xor_hw']}, "
                  f"chart_top={chart_signature(rec)[:2]}, "
                  f"tail63_hw={rec['tail'][-1]['state_diff_total_hw']}")

    with open(args.out, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"\nWrote {len(records)} records to {args.out}")


if __name__ == "__main__":
    main()

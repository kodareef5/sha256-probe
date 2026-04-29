#!/usr/bin/env python3
"""
preimage_lift.py — lift target dW[16..23] back to dM[0..15] (Tool 2 part 1).

Truncated scope per plan: targets dW[16..23] only (8 words × 32 bits = 256
schedule-bit search dim), couples directly to dM[0..15].

Approach
--------
SHA-256 schedule recurrence:
  W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]   (mod 2^32)

In XOR-space (working with dM_XOR = M2 XOR M1, dW_XOR = W2 XOR W1):
- sigma0, sigma1 are GF(2)-linear in their input → predictable.
- The modular addition introduces CARRIES, which depend on M1's actual bits
  (not just dM_XOR). Without carry corrections, dW_XOR is a perfectly linear
  function of dM_XOR.

Two-step lift:
  1. LINEAR LIFT (no-carry approximation): solve A·dM_XOR = T over GF(2),
     where A is the 256x512 matrix of the no-carry schedule recurrence.
  2. VERIFY by running build_schedule on (M1, M2 = M1 XOR dM_XOR) and
     checking actual dW XOR matches T.

For most short trails, the linear lift is exact. Where carries differ,
the residual is small (HW few bits) and can be corrected by local search
or accepted with a penalty.

Usage:
    # Round-trip test on dM_XOR = 0:
    python3 preimage_lift.py --self-test

    # Lift a target taken from an absorber's actual schedule:
    python3 preimage_lift.py --absorber-json <path> --restart 0
"""
import argparse
import json
import os
import sys
from typing import List, Tuple, Optional

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from lib.sha256 import MASK, sigma0 as sigma0_w, sigma1 as sigma1_w


# ---------------------------------------------------------------------------
# GF(2) linear algebra utilities
# ---------------------------------------------------------------------------

def gf2_eliminate(A_rows: List[int], B_vals: List[int], n_cols: int
                  ) -> Tuple[List[int], List[int], List[int]]:
    """
    Reduce [A | b] over GF(2) to RREF. Each row of A is encoded as a Python
    int (bit i = column i). B_vals[i] is the RHS bit for row i.
    Returns (reduced_rows, reduced_b, pivot_cols).
    Inconsistent system raises ValueError.
    """
    A = list(A_rows); B = list(B_vals)
    pivot_cols = []
    r = 0
    for col in range(n_cols):
        bit = 1 << col
        pivot = None
        for i in range(r, len(A)):
            if A[i] & bit:
                pivot = i
                break
        if pivot is None:
            continue
        A[r], A[pivot] = A[pivot], A[r]
        B[r], B[pivot] = B[pivot], B[r]
        for i in range(len(A)):
            if i != r and (A[i] & bit):
                A[i] ^= A[r]
                B[i] ^= B[r]
        pivot_cols.append(col)
        r += 1
    # Check consistency: rows r.. must have A=0 and B=0
    for i in range(r, len(A)):
        if A[i] != 0:
            raise RuntimeError("internal: row not reduced")
        if B[i] != 0:
            raise ValueError("system inconsistent — target dW not in image of A")
    return A[:r], B[:r], pivot_cols


def gf2_solve(A_rows: List[int], B_vals: List[int], n_cols: int) -> int:
    """
    Find any solution x (encoded as int, bit i = x_i) to A·x = B.
    Free vars set to 0. Raises ValueError if inconsistent.
    """
    A_red, B_red, pivots = gf2_eliminate(A_rows, B_vals, n_cols)
    x = 0
    for i, col in enumerate(pivots):
        if B_red[i] & 1:
            x |= 1 << col
    return x


# ---------------------------------------------------------------------------
# Schedule recurrence as GF(2) operator (no-carry approximation)
# ---------------------------------------------------------------------------

def sigma_matrix(rot1: int, rot2: int, shr: int = None) -> List[int]:
    """
    32-row, 32-col GF(2) matrix M such that M·x = ROR(x, rot1) ^ ROR(x, rot2)
    [^ SHR(x, shr) if given]. Each row encoded as int (bit j = M[i][j]).
    Output bit i depends linearly on input bits.
      - ROR(x, r) bit i comes from input bit (i + r) mod 32.
      - SHR(x, s) bit i comes from input bit (i + s) if i + s < 32 else 0.
    """
    M = [0] * 32
    for i in range(32):
        # ROR(x, rot1) contribution: out bit i = in bit (i + rot1) mod 32
        M[i] ^= 1 << ((i + rot1) % 32)
        M[i] ^= 1 << ((i + rot2) % 32)
        if shr is not None:
            j = i + shr
            if j < 32:
                M[i] ^= 1 << j
    return M


SIGMA0_MAT = sigma_matrix(7, 18, 3)    # sigma0 for schedule
SIGMA1_MAT = sigma_matrix(17, 19, 10)  # sigma1 for schedule


def apply_gf2_mat(mat: List[int], x: int) -> int:
    """y_i = popcount(mat[i] & x) mod 2."""
    y = 0
    for i in range(32):
        if bin(mat[i] & x).count('1') & 1:
            y |= 1 << i
    return y


def schedule_dW_xor_linear(dM_xor: List[int], n_target: int = 8) -> List[int]:
    """
    Predict dW_xor[16..16+n_target-1] from dM_xor[0..15] using the
    no-carry XOR-recurrence:
      dW_xor[i] = sigma1(dW_xor[i-2]) ^ dW_xor[i-7] ^ sigma0(dW_xor[i-15]) ^ dW_xor[i-16]
    with dW_xor[0..15] = dM_xor[0..15].
    """
    dW = list(dM_xor) + [0] * n_target
    for i in range(16, 16 + n_target):
        dW[i] = (apply_gf2_mat(SIGMA1_MAT, dW[i-2])
                 ^ dW[i-7]
                 ^ apply_gf2_mat(SIGMA0_MAT, dW[i-15])
                 ^ dW[i-16])
    return dW[16:16 + n_target]


# ---------------------------------------------------------------------------
# Build linear map dM_xor (512 bits) → dW_xor[16..23] (256 bits)
# ---------------------------------------------------------------------------

def build_lift_matrix(n_target: int = 8) -> List[int]:
    """
    For each output bit b ∈ [0, 32*n_target), find which input bits in
    dM_xor[0..15] (512 bits total) it XOR-depends on.
    Return a list of 32*n_target row-ints; bit j of row i = does input j
    contribute to output i.
    """
    A = []
    for out_bit in range(32 * n_target):
        # Probe: set output bit by setting an input bit, see what propagates.
        # Actually, easier: set each input bit one at a time and run forward.
        # To build A row-by-row efficiently we instead build COLUMN-wise:
        # for each input bit j, run forward; the resulting dW bits are the
        # nonzero entries in column j.
        A.append(0)
    for inp_bit in range(512):
        word = inp_bit // 32
        bit  = inp_bit % 32
        dM = [0] * 16
        dM[word] = 1 << bit
        dW_target = schedule_dW_xor_linear(dM, n_target)
        for ti, w in enumerate(dW_target):
            for tb in range(32):
                if (w >> tb) & 1:
                    out_bit = ti * 32 + tb
                    A[out_bit] |= 1 << inp_bit
    return A


# Cache the lift matrix at module import (small computation: 512 forward sweeps)
_LIFT_MAT_CACHE = {}

def get_lift_matrix(n_target: int = 8) -> List[int]:
    if n_target not in _LIFT_MAT_CACHE:
        _LIFT_MAT_CACHE[n_target] = build_lift_matrix(n_target)
    return _LIFT_MAT_CACHE[n_target]


# ---------------------------------------------------------------------------
# Lift API
# ---------------------------------------------------------------------------

def lift_target_to_dM_xor(target_dW: List[int], n_target: int = 8) -> int:
    """
    Solve linear system: A · dM_xor = target_dW.
    target_dW: list of n_target uint32 (target XOR-difference at W[16..16+n_target-1]).
    Returns dM_xor as 512-bit int (bit i = bit i%32 of dM_xor[i//32]).
    Raises ValueError if linear system has no solution.
    """
    if len(target_dW) != n_target:
        raise ValueError(f"need {n_target} target words, got {len(target_dW)}")
    A = get_lift_matrix(n_target)
    # Build B vector: B[out_bit] = bit of target_dW
    B = []
    for ti in range(n_target):
        for tb in range(32):
            B.append((target_dW[ti] >> tb) & 1)
    return gf2_solve(A, B, 512)


def dM_xor_to_words(dM_xor_int: int) -> List[int]:
    return [(dM_xor_int >> (32 * w)) & MASK for w in range(16)]


def words_to_dM_xor(words: List[int]) -> int:
    out = 0
    for w, v in enumerate(words):
        out |= (v & MASK) << (32 * w)
    return out


# ---------------------------------------------------------------------------
# Verify: run real schedule and check actual dW XOR vs predicted
# ---------------------------------------------------------------------------

def actual_dW_xor(M1: List[int], M2: List[int], n_target: int = 8) -> List[int]:
    """Compute (W2[16..16+n_target-1] XOR W1[...]) from the actual schedule."""
    def expand(M):
        W = list(M) + [0] * (16 + n_target)
        for i in range(16, 16 + n_target):
            W[i] = (sigma1_w(W[i-2]) + W[i-7] + sigma0_w(W[i-15]) + W[i-16]) & MASK
        return W
    W1 = expand(M1)
    W2 = expand(M2)
    return [(W2[i] ^ W1[i]) for i in range(16, 16 + n_target)]


def carry_residual(M1: List[int], dM_xor_words: List[int], target_dW: List[int],
                    n_target: int = 8) -> Tuple[List[int], int]:
    """
    Apply the lifted dM to M1, run schedule forward, compare to target.
    Returns (per-word residual XOR, total HW of residual).
    """
    M2 = [(m1 ^ dm) & MASK for m1, dm in zip(M1, dM_xor_words)]
    dW_actual = actual_dW_xor(M1, M2, n_target)
    residual = [a ^ t for a, t in zip(dW_actual, target_dW)]
    total_hw = sum(bin(r).count('1') for r in residual)
    return residual, total_hw


# ---------------------------------------------------------------------------
# CLI / self-test
# ---------------------------------------------------------------------------

def self_test():
    """
    1. Trivial: dM_xor = 0 → dW_xor = 0 → lifting target=0 must give x=0.
    2. Inverse: take dM_xor = single bit, predict dW, lift back, verify
       it satisfies the linear equation.
    3. Round-trip on a real (M1, M2) pair from F115 absorber: compute
       actual dW[16..23] XOR, lift it back to dM_xor, verify the lifted
       dM_xor produces the target dW under linear prediction.
    """
    print("[self-test] 1. trivial dW = 0 → dM = 0")
    target = [0] * 8
    dM_xor = lift_target_to_dM_xor(target, n_target=8)
    assert dM_xor == 0, f"expected 0, got {dM_xor:#x}"
    print(f"  PASS (dM_xor = 0)")

    print("[self-test] 2. inverse round-trip on dM_xor = 1 << 0 (M[0] LSB)")
    dM = [0] * 16
    dM[0] = 1
    dW_pred = schedule_dW_xor_linear(dM, 8)
    print(f"  dW_pred = {[hex(w) for w in dW_pred]}")
    dM_xor_int = lift_target_to_dM_xor(dW_pred, n_target=8)
    dM_back = dM_xor_to_words(dM_xor_int)
    print(f"  dM_back = {[hex(w) for w in dM_back]}")
    dW_back = schedule_dW_xor_linear(dM_back, 8)
    assert dW_back == dW_pred, "lifted dM does not regenerate target dW"
    print(f"  PASS (linear round-trip consistent)")

    print("[self-test] 3. real (M1, M2) round-trip via F115 absorber")
    f115 = os.path.join(REPO, "headline_hunt/bets/block2_wang/results/"
                              "search_artifacts/"
                              "20260428_F115_bit3_active_01289_continue_8x50k.json")
    with open(f115) as f:
        data = json.load(f)
    r0 = data["results"][0]
    M1 = [int(x, 16) for x in r0["M1"]]
    M2 = [int(x, 16) for x in r0["M2"]]
    target = actual_dW_xor(M1, M2, 8)
    dM_xor_words = [(m1 ^ m2) for m1, m2 in zip(M1, M2)]
    print(f"  actual dW[16..23] XOR = {[hex(w) for w in target]}")
    print(f"  actual dM_xor[0..15]  = {[hex(w) for w in dM_xor_words]}")
    print(f"  target HW total = {sum(bin(w).count('1') for w in target)}")
    print(f"  dM_xor HW total = {sum(bin(w).count('1') for w in dM_xor_words)}")

    # Predict dW from actual dM under linear approx
    dW_linear = schedule_dW_xor_linear(dM_xor_words, 8)
    residual = [a ^ b for a, b in zip(dW_linear, target)]
    res_hw = sum(bin(r).count('1') for r in residual)
    print(f"  linear-vs-actual residual HW = {res_hw}")

    # Lift the actual target and check what dM the linear lift produces.
    try:
        dM_xor_lifted = lift_target_to_dM_xor(target, n_target=8)
        dM_lifted_words = dM_xor_to_words(dM_xor_lifted)
        print(f"  lifted dM_xor[0..15]  = {[hex(w) for w in dM_lifted_words]}")
        # Check if the lifted dM produces the target under linear approx.
        dW_check = schedule_dW_xor_linear(dM_lifted_words, 8)
        check_match = (dW_check == target)
        print(f"  lifted dM → linear dW matches target: {check_match}")
        # And what the lifted dM gives under ACTUAL recurrence (carries)
        M1_check = M1
        M2_check = [(m1 ^ dm) & MASK for m1, dm in zip(M1_check, dM_lifted_words)]
        dW_actual_check = actual_dW_xor(M1_check, M2_check, 8)
        actual_residual = [a ^ t for a, t in zip(dW_actual_check, target)]
        actual_residual_hw = sum(bin(r).count('1') for r in actual_residual)
        print(f"  lifted dM under actual-recurrence (with carries) → residual HW = "
              f"{actual_residual_hw}")
    except ValueError as e:
        print(f"  LIFT FAILED: {e}")

    print("[self-test] DONE")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true", help="run smoke tests")
    ap.add_argument("--absorber-json", default=None,
                    help="path to absorber result JSON; lift target taken from "
                         "results[--restart].M1, M2.")
    ap.add_argument("--restart", type=int, default=0)
    ap.add_argument("--n-target", type=int, default=8,
                    help="number of dW words to lift (default 8 = dW[16..23])")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    if args.absorber_json:
        with open(args.absorber_json) as f:
            data = json.load(f)
        r = data["results"][args.restart]
        M1 = [int(x, 16) for x in r["M1"]]
        M2 = [int(x, 16) for x in r["M2"]]
        target = actual_dW_xor(M1, M2, args.n_target)
        print(f"Target dW[16..{15 + args.n_target}] XOR:")
        for i, w in enumerate(target):
            print(f"  W[{16 + i}]: 0x{w:08x}  (HW {bin(w).count('1')})")
        try:
            dM_xor_int = lift_target_to_dM_xor(target, args.n_target)
            dM_words = dM_xor_to_words(dM_xor_int)
            print(f"\nLifted dM_xor[0..15]:")
            for i, w in enumerate(dM_words):
                print(f"  dM[{i}]: 0x{w:08x}")
            residual, hw = carry_residual(M1, dM_words, target, args.n_target)
            print(f"\nCarry residual after applying lifted dM to original M1:")
            for i, w in enumerate(residual):
                print(f"  W[{16+i}] residual: 0x{w:08x}  (HW {bin(w).count('1')})")
            print(f"  TOTAL residual HW: {hw}")
        except ValueError as e:
            print(f"  LIFT FAILED: {e}")
        return

    print("(no action; pass --self-test or --absorber-json ...)")


if __name__ == "__main__":
    main()

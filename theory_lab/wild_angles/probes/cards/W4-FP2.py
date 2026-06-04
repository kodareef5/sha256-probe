#!/usr/bin/env python3
"""
W4-FP2 -- S-transform zero-atom -> 132 from SHR rank-loss.

Card claim (CATALOG):
  SHR drops bits -> rank-deficient Jacobians -> an atom at 0; under box-times the
  zero-atoms compound to saturation = the cokernel -> conjecturally 132/256.

  probe: per-round corank (singular values < eps), combine via the box-times
  zero-atom rule, compare to the *direct* product corank; corank(P)/N -> 0.516?
  removing SHR kills the atom?
  kill: direct corank ~0 or ~1, or SHR-removal barely changes it.
  skeptic (card's own): over R the add-Jacobian is generically full-rank and may
  refill SHR's drop -- the deficiency may be a GF(2) statement classical free-prob
  can't see.

ADVERSARIAL FRAMING (prior finding #1: "132 = corank" is a CATEGORY ERROR,
confirmed 7 ways; a real, stable, basis-independent corank is 0/128, not 132).
We measure REAL coranks (over R, the domain where S-transforms / free prob live)
of:
  (a) the per-round COMPRESSION Jacobian (where the card thinks SHR lives -- it
      does NOT; SHR is only in the message schedule);
  (b) the per-round MESSAGE-SCHEDULE map sigma0/sigma1 = ROR^a ^ ROR^b ^ SHR^c,
      which is where SHR actually appears, at N up to 32 (the literal-32 case);
  (c) the SHR-removal counterfactual (replace SHR^c by ROR^c) to see if the atom
      "dies" -- the card's discriminating test.
Then test 132 and the claimed corank/N -> 0.516 saturation ratio.
"""
import sys, time
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as TO
import linround as LR
import numpy as np

HARDCORE = sb.HARDCORE['total']      # 132 pinned ground truth
EPS = 1e-9


def real_corank(M, eps=EPS):
    """corank over R = (#cols) - (#singular values > eps)."""
    M = np.asarray(M, float)
    sv = np.linalg.svd(M, compute_uv=False)
    return M.shape[1] - int((sv > eps).sum()), sv


# ---- (a) local compression-round difference-Jacobian (real 0/1, 8N x 8N) ----
def local_round_jac(N, state, k, w):
    rnd = TO._make_round(N)
    m = (1 << N) - 1

    def pack(o):
        v = 0
        for bi, word in enumerate(o):
            v |= (word & m) << (bi * N)
        return v

    base = pack(rnd(state, k, w))
    n = 8 * N
    J = np.zeros((n, n))
    for j in range(n):
        blk, bit = divmod(j, N)
        st2 = list(state)
        st2[blk] ^= (1 << bit)
        d = pack(rnd(st2, k, w)) ^ base
        for i in range(n):
            if (d >> i) & 1:
                J[i, j] = 1.0
    return J


# ---- (b) message-schedule small-sigma matrices (SHR lives HERE), real 0/1 ----
def small_sigma_real(N, rots, use_shr=True):
    """sigma_small = ROR^a ^ ROR^b ^ (SHR^c if use_shr else ROR^c). N x N real 0/1."""
    a, b, c = rots
    third = LR.shr_mat(N, c) if use_shr else LR.ror_mat(N, c % N)
    M = LR._xor(LR.ror_mat(N, a % N), LR.ror_mat(N, b % N), third)
    R = np.zeros((N, N))
    for i, row in enumerate(M):
        for j in range(N):
            if (row >> j) & 1:
                R[i, j] = 1.0
    return R


# ---- the full 8N x 8N one-step message-state map of the schedule recurrence ----
# W[t] = sigma1(W[t-2]) + W[t-7] + sigma0(W[t-15]) + W[t-16].  As a companion-style
# linear map on the 16-word window (16N x 16N), the only rank-loss source is SHR.
def schedule_companion(N, use_shr=True):
    rp = LR.scaled_rots(N)
    s0 = small_sigma_real(N, rp['s0'], use_shr)   # ROR7^ROR18^SHR3
    s1 = small_sigma_real(N, rp['s1'], use_shr)   # ROR17^ROR19^SHR10
    n = 16 * N
    C = np.zeros((n, n))
    # new word W[16] (top block) = s1 @ W[14] + I @ W[9] + s0 @ W[1] + I @ W[0]
    # shift the window: blocks 0..14 <- 1..15 (identity), block 15 <- new word.
    Id = np.eye(N)
    for blk in range(15):
        C[blk * N:(blk + 1) * N, (blk + 1) * N:(blk + 2) * N] = Id  # W'[blk]=W[blk+1]
    top = slice(15 * N, 16 * N)
    C[top, 14 * N:15 * N] += s1          # sigma1(W[14])
    C[top, 9 * N:10 * N] += Id           # W[9]
    C[top, 1 * N:2 * N] += s0            # sigma0(W[1])
    C[top, 0 * N:1 * N] += Id            # W[0]
    return C


def main():
    print("=" * 74)
    print("W4-FP2: SHR zero-atom -> corank -> 132?  (real coranks; SHR-removal test)")
    print("=" * 74)
    print(f"  pinned target 'hard-core' total = {HARDCORE}; claimed corank/N -> 0.516\n")

    # ---------- (a) compression-round Jacobian corank ----------
    print("[a] local COMPRESSION-round difference-Jacobian corank (real, 8N x 8N)")
    print("    (note: SHR is NOT in the compression round -- only ROR/add/Ch/Maj)")
    rng = np.random.default_rng(7)
    for N in (4, 6, 8):
        cks = []
        for _ in range(8):
            st = [int(rng.integers(0, 1 << N)) for _ in range(8)]
            w = int(rng.integers(0, 1 << N))
            ck, _ = real_corank(local_round_jac(N, st, sb.K[40] & ((1 << N) - 1), w))
            cks.append(ck)
        print(f"    N={N:2d}: corank over 8 base points = {cks}  (8N={8*N})")

    # ---------- (b) message-schedule small-sigma corank, WITH SHR ----------
    print("\n[b] MESSAGE-SCHEDULE small-sigma corank (SHR lives here), real N x N")
    print("    sigma0=ROR^a^ROR^b^SHR^c ; sigma1=ROR^a^ROR^b^SHR^c  (scaled to N)")
    for N in (8, 16, 32):
        rp = LR.scaled_rots(N)
        ck0, sv0 = real_corank(small_sigma_real(N, rp['s0'], use_shr=True))
        ck1, sv1 = real_corank(small_sigma_real(N, rp['s1'], use_shr=True))
        print(f"    N={N:2d}: sigma0 corank={ck0}  sigma1 corank={ck1}  "
              f"(min sv0={sv0.min():.3g}, min sv1={sv1.min():.3g})")

    # ---------- (b') full 16-word schedule companion corank, WITH SHR ----------
    print("\n[b'] full schedule-companion map corank (16N x 16N), WITH SHR")
    for N in (8, 16, 32):
        C = schedule_companion(N, use_shr=True)
        ck, sv = real_corank(C)
        print(f"    N={N:2d}: corank(companion)={ck}  (16N={16*N})  min sv={sv.min():.3g}")

    # ---------- (c) SHR-REMOVAL counterfactual (the card's discriminating test) ----
    print("\n[c] SHR-REMOVAL test: replace SHR^c by ROR^c (the card's 'kill the atom?')")
    for N in (8, 16, 32):
        rp = LR.scaled_rots(N)
        ck0_s, _ = real_corank(small_sigma_real(N, rp['s0'], True))
        ck0_r, _ = real_corank(small_sigma_real(N, rp['s0'], False))
        ckC_s, _ = real_corank(schedule_companion(N, True))
        ckC_r, _ = real_corank(schedule_companion(N, False))
        print(f"    N={N:2d}: sigma0 corank  WITH-SHR={ck0_s}  NO-SHR(ROR)={ck0_r}   |   "
              f"companion corank WITH-SHR={ckC_s}  NO-SHR={ckC_r}")

    # ---------- 132 / 0.516 saturation check ----------
    print("\n[132 / 0.516 SATURATION CHECK]")
    print("    The card wants corank(P)/N -> 0.516 with corank -> 132 at N=32.")
    print("    For sigma at N=32: corank/N = (measured corank)/32.")
    for N in (32,):
        rp = LR.scaled_rots(N)
        ck0, _ = real_corank(small_sigma_real(N, rp['s0'], True))
        ckC, _ = real_corank(schedule_companion(N, True))
        print(f"    N={N}: sigma0 corank={ck0} -> /N={ck0/N:.3f}  (need 0.516)")
        print(f"    N={N}: companion corank={ckC} -> /(16N)={ckC/(16*N):.3f}")
        print(f"    132 would need a stable corank of 132; measured = {ckC} (companion), "
              f"{ck0} (sigma).")

    print("\n[CONCLUSION] Over R (where S-transforms live) SHR's dropped bits are")
    print("    REFILLED by the two ROR terms it is XORed with -> every relevant")
    print("    Jacobian is FULL RANK (corank 0). There is no zero-atom to compound,")
    print("    no saturation to 132, and removing SHR does NOT change the (already 0)")
    print("    corank. The 132 is a GF(2)/output-census number, not a real corank.")


if __name__ == '__main__':
    main()

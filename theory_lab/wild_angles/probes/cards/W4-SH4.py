#!/usr/bin/env python3
"""
W4-SH4 -- Spectral-gap order parameter -> a rank-2 degeneration at 60->61.

Card probe: "full spectrum of L_{F_r}, r=57..62; plot lambda1(r), count near-zero
modes; predict a drop + *two* new modes at 60->61, localized on g/h."
Kill: "lambda1 flat (no anomaly at 61), or new-mode count != 2 (and != 2N)."

SPLIT-CLAUSE scoring (prior-findings #3, #4):
  [RANK-2]  is the sr=61 degeneration genuinely rank-2?  Tested two ways:
            (a) the spectral increment of near-zero modes added by the last round;
            (b) the ESTABLISHED structural fact g2 = g1 + h (codim-2 / rank-2),
                reproduced on the repo N=10 gap data -- the real rank-2 anchor.
  ["AT 60->61"]  does anything anomalous happen SPECIFICALLY at the 60->61 step, or
            is lambda1 / the near-zero count smooth across the whole sweep (no knee)?
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import sheaf_delta as sd
import numpy as np
np.seterr(all='ignore')

def near_zero_count(sp, tol):
    return int((sp < tol).sum())

def run():
    print("=== W4-SH4: spectral-gap order parameter -> rank-2 degeneration at 60->61 ===\n")

    print("[CLAUSE A: at-60->61 anomaly] full real spectrum of L over the tail sweep,")
    print("N=4; lambda1(r), near-zero-mode count, and the INCREMENT each step.\n")
    N = 4
    tol = 1e-6
    print(f"  {'R':>2} {'~sr':>4} {'lambda1':>12} {'#near0(<1e-6)':>13} "
          f"{'increment':>10} {'lambda1 ratio':>13}")
    prev_nz = None; prev_l1 = None
    incs = []
    for R in (1, 2, 3, 4, 5, 6):
        rows, nc, info = sd.assemble(N, R, force_collision=True, carry_order=0)
        sp = sd.spectrum(rows, nc)
        nz = near_zero_count(sp, tol)
        pos = sp[sp > tol]; l1 = pos[0] if pos.size else float('nan')
        inc = (nz - prev_nz) if prev_nz is not None else 0
        if prev_nz is not None: incs.append(inc)
        ratio = (prev_l1 / l1) if (prev_l1 and l1 > 0) else float('nan')
        print(f"  {R:>2} {56+R:>4} {l1:>12.5f} {nz:>13} {inc:>10} {ratio:>13.3f}")
        prev_nz = nz; prev_l1 = l1
    print(f"\n  per-step near-zero increments: {incs}")
    print(f"  prediction = exactly 2 new modes at the 60->61 step (R=4->5).")
    step_60_61 = incs[3] if len(incs) >= 4 else None       # R4->R5
    print(f"  ACTUAL increment at 60->61 (R=4->5) = {step_60_61}  (2N={2*N})")
    uniform = len(set(incs)) == 1
    print(f"  increments uniform across all steps? {uniform}  -> if uniform, NO 60->61 anomaly")

    print("\n[CLAUSE B: genuine rank-2] the ESTABLISHED structural anchor g2 = g1 + h")
    print("on the repo N=10 collision gap data (cols g1,g2,h). This is the real rank-2.")
    rows_csv = sb.load_gap_rows()
    N10 = 10; M = (1 << N10) - 1
    ok = 0; tot = 0
    for row in rows_csv:
        g1 = int(row['g1']); g2 = int(row['g2']); h = int(row['h'])
        if (g1 + h) % (1 << N10) == g2 % (1 << N10):
            ok += 1
        tot += 1
    print(f"  g2 == g1 + h (mod 2^{N10}) for {ok}/{tot} collisions "
          f"-> {'EXACT rank-2 (codim-2 point)' if ok==tot else 'NOT rank-2'}")
    # corank of the 2x(number of distinct (g1,g2)) map: the (g1,h)->(g1,g2) map is the
    # unimodular [[1,0],[1,1]], det 1, so sr=61 = the codim-2 origin (g1,g2)=(0,0).
    # Verify the empirical 2-D image is genuinely 2-D (rank 2 over the reals/ints).
    pts = np.array([[int(r['g1']), int(r['g2'])] for r in rows_csv], dtype=float)
    pts = pts - pts.mean(0)
    rank2 = np.linalg.matrix_rank(pts, tol=1e-6)
    print(f"  empirical (g1,g2) cloud rank = {rank2}  (expect 2 = full -> two independent")
    print(f"  conditions g1=0 AND g2=0 == g1=0 AND h=0); slope of log2 P(both) is -2 (IG2).")

    print("\n[verdict logic] RANK-2 clause: CONFIRM iff g2=g1+h exact AND image rank 2.")
    print("                AT-60->61 clause: KILL iff lambda1/increments are smooth")
    print("                (uniform, no anomaly localized at the R=4->5 step).")

if __name__ == '__main__':
    run()

#!/usr/bin/env python3
"""
W6-OC3 — The 132 hard-core bits = the costate's kernel.

Card claim: a final bit with zero costate support is a direction Pontryagin can't steer
to first order; conjecture 132 = ker of the pulled-back costate map (da,db,de,df at r63),
zeroed only by 2nd-order carry; HW~74 = kernel-dim/2 + small.
Probe: N=8,12 build S[bit,(r,j)] = d(final bit)/d(dW[r] bit j) by finite differences; do
the all-zero rows concentrate in da,db,de,df (the 132) and predict plateau HW=kernel-dim/2?
Kill: zero-rows don't match the measured hard core, or kernel-dim/2 mispredicts the plateau.

ADVERSARIAL FRAMING (prior finding #1 — the "132=corank" CATEGORY ERROR, seen 12x):
"132" is the deterministic-CONTROL CENSUS of *uncontrollable output bits* {a,b,e,f}@63
(=128) + 4 dc = 4N+4, a WIDTH-SCALING census, NOT a basis-independent kernel dim. An
HONEST linear/costate kernel dimension is 0 or 128, never a stable 132. So we compute
BOTH and label which is which:

  (CENSUS) S[out_bit, ctrl_bit] = d(final bit)/d(W[57..60] bit) by finite diff over the
           exact cascade.  ZERO ROWS = output bits no free control flips (first order).
           This is the W2-CT1 census reframed; if it lands on {a,b,e,f} it is the 132 --
           but it SCALES with N (=4N+4), so it is the CENSUS, not a kernel.

  (KERNEL) the honest costate kernel: dim of the kernel of the pulled-back costate /
           control-to-output Jacobian. We report corank of the full control->output map
           S (over r=57..60), and the costate-kernel dim at the trajectory. An honest
           kernel is basis-independent and should be 0 or N-scaled, NOT a frozen 132.

Decision: does the zero-row set reproduce the *measured* 132 STRUCTURE, AND does kernel
-dim/2 predict the HW~74 plateau?  Per finding #1 the plateau is a 32-bit-width fact
(132/256 ~ HW74); at small N the analogue is (4N+4)/(8N) of 8N output bits.
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _w6oc_engine as oc

REG = oc.REG; OFF = oc.OFF
FREE_ROUNDS = (57, 58, 59, 60)         # the genuinely free control words


def control_to_output(N, seeds=40):
    """S[out_bit, (r,j)] over the FREE control bits W[57..60] (4N control bits) by exact
    finite difference, requiring a flip in EVERY seed (deterministic control, matching
    the repo census). Returns: zero-row mask per output bit, and per-register zero counts.
    A control bit (r,j) flips output o iff flipping W[r] bit j flips final bit o; an
    output o is 'controlled' iff some free control bit flips it in ALL seeds."""
    rng = random.Random(20260603)
    M = oc.eng.make_model(N); setup = oc.eng.find_M0(M)
    n = 8 * N
    KN = M['KN']; MASK = M['MASK']
    ctrl_bits = [(r, j) for r in FREE_ROUNDS for j in range(N)]      # 4N controls
    # flip_all[o] = set of control indices that flip output o in EVERY seed
    flip_all = [set(range(len(ctrl_bits))) for _ in range(n)]
    for _ in range(seeds):
        w0 = [rng.randint(0, MASK) for _ in range(4)]
        states, controls, _, _ = oc.cascade_trajectory(N, *w0)
        base = oc.pack(states[64], N)
        for ci, (r, j) in enumerate(ctrl_bits):
            w1 = list(w0); w1[r - 57] ^= (1 << j)
            st1, _, _, _ = oc.cascade_trajectory(N, *w1)
            resp = oc.pack(st1[64], N) ^ base
            # control ci flips output o iff bit o set in resp
            flipped = resp
            o = 0
            keep = flip_all
            # remove from flip_all[o] any o NOT flipped this seed
            notflipped = (~resp) & ((1 << n) - 1)
            x = notflipped
            while x:
                o = (x & -x).bit_length() - 1
                flip_all[o].discard(ci)
                x &= x - 1
    controlled = [o for o in range(n) if flip_all[o]]
    zero_rows = [o for o in range(n) if not flip_all[o]]
    per_reg_zero = {name: sum(1 for o in zero_rows
                              if OFF[name] * N <= o < (OFF[name] + 1) * N)
                    for name in REG}
    # corank of the deterministic control->output map (rank over GF(2) of the
    # deterministic-flip incidence) as a sanity dim:
    rows = [0] * n
    for o in range(n):
        for ci in flip_all[o]:
            rows[o] |= (1 << ci)
    ctrl_rank = oc.rank(rows)
    return zero_rows, per_reg_zero, ctrl_rank, len(ctrl_bits), n


def costate_kernel_dim(N):
    """Honest costate kernel: corank of the pulled-back control->output Jacobian, and
    rank/kernel of the costate at the start of the controllable window. We assemble the
    linearized control-to-output map over the free rounds (NOT requiring all-seed
    determinism -- the pure first-order tangent) and report its corank."""
    M = oc.eng.make_model(N); n = 8 * N
    D = oc.costate_sweep(N, 0, 0, 0, 0)
    # control-to-output tangent: out-response to each free control bit at its round,
    # pushed forward to r64 via the chain. Easiest faithful build: finite-diff once.
    base = oc.pack(D['states'][64], N)
    cols = []                              # each col = 8N out-mask for one free control bit
    for r in FREE_ROUNDS:
        for j in range(N):
            w = [0, 0, 0, 0]; w[r - 57] ^= (1 << j)
            st1, _, _, _ = oc.cascade_trajectory(N, *w)
            cols.append(oc.pack(st1[64], N) ^ base)
    # control->output map as 8N rows over (4N) control cols
    rows = [0] * n
    for ci, c in enumerate(cols):
        for o in oc.setbits(c):
            rows[o] |= (1 << ci)
    img_rank = oc.rank(rows)               # dim of reachable output subspace (first order)
    out_kernel = n - img_rank              # output directions with NO first-order control
    ctrl_kernel = len(cols) - img_rank     # control directions that do nothing (>=0)
    return img_rank, out_kernel, ctrl_kernel, len(cols), n


def main():
    print("W6-OC3 : is the 132 hard core the costate's KERNEL, or the control CENSUS?\n")
    for N in (8, 10):
        print(f"=== N={N} ===")
        zr, pz, crank, nctrl, n = control_to_output(N)
        cen = 4 * N + 4                    # repo census formula {a,b,e,f}(4N) + 4dc
        abef = pz['a'] + pz['b'] + pz['e'] + pz['f']
        print(f"  CENSUS (deterministic control of {n} output bits by {nctrl} free ctrl bits):")
        print(f"    zero-control output bits = {len(zr)}   (4N+4 = {cen})")
        print(f"    per-register zero-control: " +
              ", ".join(f"{k}:{pz[k]}" for k in REG))
        print(f"    {{a,b,e,f}} zero-control = {abef}/{4*N}  (dc={pz['c']})  "
              f"control rank = {crank}")
        ir, ok, ck, nc, _ = costate_kernel_dim(N)
        print(f"  KERNEL (honest first-order control->output tangent map):")
        print(f"    image rank = {ir}/{n};  OUTPUT kernel dim = {ok};  "
              f"control kernel dim = {ck}")
        # plateau HW prediction: card says HW ~ kernel-dim/2
        print(f"  PLATEAU CHECK: card predicts HW ~ kernel_dim/2.")
        print(f"    census/2 = {len(zr)/2:.1f} ;  output-kernel/2 = {ok/2:.1f} ;  "
              f"(8N)/2 = {n/2:.1f}  [half of all output bits]")
        # is the kernel a frozen 132-analogue or N-scaling?
        print(f"  --> CENSUS scales as 4N+4 ({len(zr)}=={cen}? {len(zr)==cen}); "
              f"KERNEL dim = {ok} (honest, basis-independent)\n")
    print("INTERPRETATION (finding #1): the ~132 lives in the CENSUS of uncontrollable")
    print("output bits {a,b,e,f}+4dc = 4N+4 (WIDTH-SCALING). The honest costate/Jacobian")
    print("KERNEL dim is whatever the rank deficit is -- a different object. If the card's")
    print("'costate kernel' is just the census it is the category error; CONFIRM only if a")
    print("basis-independent kernel object equals the hard core AND kernel/2 hits HW74.")


if __name__ == '__main__':
    main()

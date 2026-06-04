"""
W6-FR4 — Two-phase multifractal -> the 132/124 split as two local dimensions.

CARD CLAIM: The output-bit invariance measure is multifractal: 124 controlled
bits = the regular phase (alpha~0), 132 hard-core = the singular/dominant phase
(alpha~1) carrying the HW mass => HW~74 = the f(alpha)-weighted mean. The VALUE
is whether a genuine INTERMEDIATE band exists (partially-controllable bits = new
attack surface).

PROBE (card's own): N=8,10,12 per-bit invariance frequency p_i; generalized
dimensions D_q from Sum p_i^q (q=0,1,2), Legendre -> f(alpha); two concentrations
with mass-mean=74, AND a non-trivial spread?
KILL: the p_i histogram is a clean two-point mass (every bit p=1 or p=0.5, nothing
between) -> "multifractal" adds nothing over the 124/132 count.
SKEPTIC (orchestrator #1): MOST rebrand-prone -- the entire value is the middle
band; if empty, KILL. "132" is the 4N+4 deterministic-control census vs 256
(width-scaling, fraction->0.5), NOT two intrinsic fractal dimensions. Never
CONFIRM a near-132/0.516 without a stable basis-independent object.

WHAT WE COMPUTE (the genuine per-bit invariance measure):
For the tail (rounds 57..63) at width N, build the EXACT boolean control map
J: input bits (the 4 free words W57..60 = 4N bits) -> the 8N output bits at r63,
J[o, j] = 1 iff flipping input bit j flips output bit o (finite difference at a
real cascade trajectory point, exact carries -- the same object the repo's
hard_core_132 measured from the diff-linear matrix). Then:
  c_o = (1/4N) Sum_j J[o,j]  = the DETERMINISTIC-CONTROL FREQUENCY of output bit o
        (how often a random input-bit flip flips it). This is the per-bit
        "invariance/controllability" p_o the card calls multifractal.
  - histogram c_o over the 8N output bits;
  - is it a clean TWO-POINT mass {0 (hard core), ~0.5 (controlled)} or is there a
    NON-TRIVIAL middle band (bits with c_o strictly between)?
  - generalized dimensions D_q from the box-measure mu_o = c_o / Sum c_o:
        D_q = (1/(q-1)) log(Sum mu_o^q) / log(1/eps), eps = 1/(8N) (box scale).
We compute these averaged over several real trajectory points (the control map is
set-valued at the carry kinks, so we average to get the family frequency).
"""
import sys, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import shabridge as sb
import _w6oc_engine as OC          # exact tail Jacobians / control columns
import _w5co_engine as E
import numpy as np

REG = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')


def output_control_map(N, samples=24, seed=0):
    """DETERMINISTIC-control census (the hard_core_132 object, NOT avalanche).

    For each (input bit j, output bit o), j is a DETERMINISTIC controller of o iff
    flipping j flips o with probability 1 across ALL sampled trajectory points
    (a stable GF(2)-linear dependence). Carry-mediated (nonlinear) dependences
    flip o only ~half the time and are NOT deterministic controllers -- those are
    exactly the 'hard-core' bits the writeup found (a,b,e,f@63 have ZERO
    deterministic controllers; d,g,h have full shift-register control).

    Returns:
      ctrl_count[o] = # input bits that deterministically control output bit o,
      c_o = ctrl_count[o]/(4N) = the per-bit DETERMINISTIC-control FREQUENCY.
    plus the avalanche freq aval[o] (fraction of flips, ~0.5) for contrast.
    """
    M, setup = OC.get_model(N)
    rng = np.random.default_rng(seed)
    n_out = 8 * N
    n_in = 4 * N
    # flip_prob[o, j] aggregated: count flips and trials per (o,j)
    flips = np.zeros((n_out, n_in), dtype=float)
    trials = np.zeros(n_in, dtype=float)
    for _ in range(samples):
        w = [int(rng.integers(0, 1 << N)) for _ in range(4)]
        states, _, _, _ = OC.cascade_trajectory(N, *w)
        base = OC.pack(states[64], N)
        for fi in range(4):
            for jb in range(N):
                jglob = fi * N + jb
                w2 = list(w); w2[fi] ^= (1 << jb)
                st2, _, _, _ = OC.cascade_trajectory(N, *w2)
                flipped = base ^ OC.pack(st2[64], N)
                trials[jglob] += 1
                for o in range(n_out):
                    if (flipped >> o) & 1:
                        flips[o, jglob] += 1.0
    # deterministic controller: flips every time (prob 1) OR never (prob 0 = no dep).
    # control = prob-1 dependence. avalanche = prob in (0,1).
    prob = flips / np.maximum(trials, 1)[None, :]
    deterministic = (prob > 0.999)                  # prob-1 flippers = linear controllers
    ctrl_count = deterministic.sum(axis=1)          # per output bit
    c = ctrl_count / n_in
    aval = prob.mean(axis=1)                          # avalanche freq per output bit
    return c, ctrl_count, aval, M


def generalized_dimensions(c, n_boxes):
    """D_q for q=0,1,2 from the box measure mu_o = c_o / sum(c_o). Box scale
    eps = 1/n_boxes. (A clean two-point mass has D_0 = log(#nonzero)/log(N) and
    D_1=D_2 collapsing -- no spectrum. A real multifractal has D_0>D_1>D_2 with a
    nontrivial f(alpha).)"""
    tot = c.sum()
    if tot <= 0:
        return None
    mu = c / tot
    nz = mu[mu > 0]
    logeps = math.log(n_boxes)
    D0 = math.log(len(nz)) / logeps
    D1 = -(nz * np.log(nz)).sum() / logeps           # information dimension
    D2 = -math.log((nz ** 2).sum()) / logeps * -1     # correlation: (1/(q-1)) log Sum mu^2
    D2 = (1.0 / (2 - 1)) * math.log((nz ** 2).sum()) / logeps
    return dict(D0=D0, D1=D1, D2=D2)


def histogram_bands(c, tol=0.03):
    """Classify output bits into c~0 (hard core), c~0.5 (controlled), and the
    MIDDLE band (strictly between). Returns counts + the middle-band values."""
    hard = int(np.sum(c < tol))
    ctrl = int(np.sum(np.abs(c - 0.5) < tol))
    full = int(np.sum(c > 1 - tol))
    mid = [float(x) for x in c if tol <= x <= 1 - tol and abs(x - 0.5) >= tol]
    return dict(hard=hard, ctrl_half=ctrl, full=full, n_mid=len(mid),
                mid_vals=sorted(mid))


if __name__ == '__main__':
    import time
    print("=" * 74)
    print("W6-FR4 : two-phase multifractal -> 132/124 as two local dimensions")
    print("=" * 74)
    print("Ground truth: 132 = 4N+4 deterministic-control census (a,b,e,f full +4dc)")
    print("              vs 256 = 8N; fraction 132/256 -> 0.5 as N grows (width-scaling).")

    for N in (8, 10, 12):
        t0 = time.time()
        c, ctrl_count, aval, M = output_control_map(N, samples=16, seed=1)
        n_out = 8 * N
        # per-register: # deterministic controllers per bit (the writeup's table)
        reg_ctrl = {REG[r]: ctrl_count[r * N:(r + 1) * N] for r in range(8)}
        # bands on the DETERMINISTIC-controller count: 0 = hard core; full(=4N or the
        # shift-register max) = controlled; strictly between = MIDDLE band.
        hard = int(np.sum(ctrl_count == 0))
        maxc = int(ctrl_count.max())
        full = int(np.sum(ctrl_count == maxc))
        mid_mask = (ctrl_count > 0) & (ctrl_count < maxc)
        n_mid = int(np.sum(mid_mask))
        mid_vals = sorted(int(x) for x in ctrl_count[mid_mask])
        print("\n--- N=%d  (8N=%d output bits, 4N=%d free input bits) [%.1fs] ---"
              % (N, n_out, 4 * N, time.time() - t0))
        print("  per-register DETERMINISTIC-controller count (min..max over the N bits):")
        for R in REG:
            cc = reg_ctrl[R]
            print("      d%s: %d/%d bits have 0 ctrl; count range %d..%d"
                  % (R, int(np.sum(cc == 0)), N, int(cc.min()), int(cc.max())))
        print("  avalanche freq per register (should be ~0.5 = NOT the control object):")
        print("    " + "  ".join("d%s=%.2f" % (R, float(np.mean(aval[REG.index(R)*N:(REG.index(R)+1)*N]))) for R in REG))
        print("  hard-core bits (0 det-controllers) = %d  (predicted 4N = %d for a,b,e,f)"
              % (hard, 4 * N))
        print("  fully-controlled bits (=max %d ctrl) = %d ;  MIDDLE band (0<ctrl<max) = %d"
              % (maxc, full, n_mid))
        if n_mid:
            from collections import Counter
            cnt = Counter(mid_vals)
            print("  MIDDLE-band controller-counts: %s" % dict(sorted(cnt.items())))
        else:
            print("  MIDDLE band EMPTY -> clean two-point mass {0 ctrl, %d ctrl}." % maxc)
        # multifractal: D_q on the controller-count measure (does a spectrum exist?)
        Dq = generalized_dimensions(ctrl_count.astype(float), n_out)
        if Dq:
            print("  generalized dims on controller-measure: D0=%.4f D1=%.4f D2=%.4f (spread D0-D2=%.4f)"
                  % (Dq['D0'], Dq['D1'], Dq['D2'], Dq['D0'] - Dq['D2']))
        print("  => hard-core fraction = %d/%d = %.3f (census 4N/8N -> 0.5, width-scaling)"
              % (hard, n_out, hard / n_out))

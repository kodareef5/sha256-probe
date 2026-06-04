"""
W7-QW3 — Discriminant kernel -> 132 = corank(D)   [P3 cheap]

CARD CLAIM: A hard-core bit can't be flipped independently -> forward or backward
independent-transition prob is 0 -> its mode has a zero singular value; conjecture
corank(D)=132 (rank 124), corank/total -> 0.516, projection-robust, kernel vectors
aligned with the known hard bits.

PROBE (per CATALOG): N=8 build a bit-projected P, D=sqrt(P .* P^T), SVD, count
near-zero singular values (threshold-sweep); corank/total ~0.516, robust across N,
kernel aligned with hard bits.

KILL: corank not a stable ~0.5 fraction across N, OR kernel = numerical noise /
projection artifact.

ADVERSARIAL PRIOR #1 ("132=corank" CATEGORY ERROR, 16x): every honest corank/kernel
computed so far = 0/128, never 132. The 132 is a CENSUS (# output-difference bits
with zero deterministic control = registers a,b,e,f@63 fully + 4 dc), NOT a matrix
corank. We compute the discriminant corank HONESTLY and report whether it is the
census 132/256 (=0.516) or the generic connected-chain answer.

WHAT WE BUILD: a *bit-level* differential transfer matrix. Two natural choices, both
reported:
  (A) Per-bit AVALANCHE / dependency matrix B over the 2N head bits (da||de):
      B[i,j] = P(output head bit i flips | input head bit j flipped), the diff-Jacobian
      already in transfer_operator.py. D=sqrt(B .* B^T). corank(D)=?  (2N-wide)
  (B) The full (da,de)-HEAD diff-config chain P (transfer_operator), D=sqrt(P .* P^T),
      corank(D)=?  (the chain the through-line actually names).
For the 132 to be a CORANK it must (a) be basis-independent/stable and (b) be ~0.516
of the dimension. We sweep thresholds and N and check the FRACTION.
"""
import sys, time
import numpy as np
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to
import _qw_kit as qw

s = sb.s
np.set_printoptions(precision=4, suppress=True)


def bit_jacobian_disc_corank(N, samples=20000, seed=3):
    """(A) 2N x 2N per-bit avalanche matrix B -> D=sqrt(B .* B^T) -> corank fractions."""
    rng = np.random.default_rng(seed)
    k = s.K[40] & ((1 << N) - 1)
    B = to.diff_jacobian(N, k, rng, samples=samples, msgdiff=0)   # 2N x 2N, entries in [0,1]
    D = qw.discriminant(B)
    sv = qw.svals(D)
    smax = sv[0] if len(sv) else 0.0
    fracs = {}
    for thr in (1e-9, 1e-6, 1e-3, 1e-2, 1e-1):
        cr = int(np.sum(sv < thr * smax)) if smax > 0 else len(sv)
        fracs[thr] = (cr, len(sv), cr / len(sv))
    return B, D, sv, fracs


def chain_disc_corank(N, samples=8000, seed=1, max_heads=260):
    """(B) (da,de)-head diff-config chain P -> D=sqrt(P .* P^T) -> corank fractions."""
    states, P = to.build_diff_operator_fast(N, msgdiff=0, samples=samples,
                                             seed=seed, max_heads=max_heads)
    D = qw.discriminant(P)
    sv = qw.svals(D)
    smax = sv[0] if len(sv) else 0.0
    fracs = {}
    for thr in (1e-9, 1e-6, 1e-3, 1e-2, 1e-1):
        cr = int(np.sum(sv < thr * smax)) if smax > 0 else len(sv)
        fracs[thr] = (cr, len(sv), cr / len(sv))
    return states, P, D, sv, fracs


if __name__ == '__main__':
    print("=" * 74)
    print("W7-QW3 : is corank(D) = 132 (a stable ~0.516 fraction), or a census?")
    print("=" * 74)

    print("\n--- (A) per-bit avalanche-Jacobian discriminant, corank fraction ---")
    print(f"{'N':>3} {'dim=2N':>6} {'corank@1e-6':>12} {'frac':>7} {'corank@1e-2':>12} {'frac':>7}")
    for N in (6, 8, 10):
        t0 = time.time()
        B, D, sv, fr = bit_jacobian_disc_corank(N, samples=24000, seed=3)
        cr6, dim, f6 = fr[1e-6]
        cr2, _, f2 = fr[1e-2]
        print(f"{N:>3} {2*N:>6} {cr6:>12} {f6:>7.3f} {cr2:>12} {f2:>7.3f}"
              f"   (top svals {sv[:4]} ... t={time.time()-t0:.1f}s)")
    # show the full threshold sweep at N=8 to expose whether there's a gap at 0.516
    print("\n  threshold sweep, N=8 (does a stable corank emerge at frac~0.516?):")
    _, _, sv8, fr8 = bit_jacobian_disc_corank(8, samples=40000, seed=3)
    for thr, (cr, dim, f) in fr8.items():
        print(f"    thr={thr:>7}: corank={cr:>3}/{dim}  frac={f:.3f}")
    print(f"    smallest 6 singular values @N=8: {sv8[-6:]}")

    print("\n--- (B) (da,de)-head diff-config chain discriminant, corank fraction ---")
    print(f"{'N':>3} {'dim':>5} {'corank@1e-6':>12} {'frac':>7} {'corank@1e-2':>12} {'frac':>7}")
    for N in (6, 8):
        t0 = time.time()
        states, P, D, sv, fr = chain_disc_corank(N, samples=8000, seed=1, max_heads=260)
        cr6, dim, f6 = fr[1e-6]
        cr2, _, f2 = fr[1e-2]
        print(f"{N:>3} {dim:>5} {cr6:>12} {f6:>7.3f} {cr2:>12} {f2:>7.3f}   t={time.time()-t0:.1f}s")

    print("\n--- reference: is the chain P reversible? (does D just relabel P?) ---")
    states, P, D, sv, fr = chain_disc_corank(8, samples=8000, seed=1, max_heads=120)
    gap = qw.is_reversible(P)
    print(f"  N=8 chain: max|s(D)-|eig(P)|| = {gap:.4f}  "
          f"({'REVERSIBLE/relabel' if gap < 1e-2 else 'NON-reversible (D != relabel P)'})")

    print("\n--- ground truth: 132 = census of output-difference hard-core bits ---")
    print(f"  HARDCORE['total'] = {sb.HARDCORE['total']}  "
          f"= {sb.HARDCORE['full_count']} (a,b,e,f@63 full) + {sb.HARDCORE['dc_scattered']} (scattered dc)")
    print("  -> 132 lives in the 256-wide OUTPUT-bit census, not in any D's singular spectrum.")

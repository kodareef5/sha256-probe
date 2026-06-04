"""
W7-QW5 — Hitting-time-exponent map -> step at r=58 (de58) + cliff at 60->61  [P4 cheap]

CARD CLAIM: alpha(r) = (1/2)(-log2 delta(r) - log2 eps(r))/N fuses gap & target density;
flat 57-59 (de57/59 constant -> eps constant), a STEP at 58 (de58 opens 2^10 configs ->
eps spikes) whose height tracks log2|de58|/N, and a CLIFF at 60->61 (delta collapses) --
unifying de58-growth + single-DOF + the wall in one scalar.

PROBE (per CATALOG): N=8..14 per round build D(r), delta(r), eps(r) (the de61/62/63
on-track oracle); alpha(r,N) flat 57-59, step at 58 (height=log2|de58|/N), cliff at 61?

KILL: alpha smooth/monotone (no step at 58, no cliff at 61), OR the step doesn't scale
with |de58|.

ADVERSARIAL PRIOR #5: the r=58 de58-opening is REAL and KNOWN (|de58|=2^hw(db56),
carry-collapsed); de57=de59=de60=1 always. CONFIRM ONLY IF the hitting-time form DERIVES
2^hw(db56) with NEW content -- otherwise it's a RESTATEMENT of the de58 law in alpha-units.
And the skeptic's own warning: classically alpha is just -1/2 log(delta*eps); the Szegedy
form earns its keep ONLY via the predicted step HEIGHT being non-trivially derived. If any
monotone combo of delta,eps gives the same step, it's a relabel.

WHAT WE DO:
 - eps(r) = |de_r| / 2^N  (target density of on-track diff configs at round r; de57/59/60=1,
   de58=2^hw(db56)) -- taken from the pinned DE_SIZES ground truth (repo-verified).
 - delta(r): the Szegedy spectral gap proxy. Flat 57..60; collapses 60->61 (the 2^-2N wall,
   QW1). We set delta(57..60) = O(1) and delta(61) -> 2^-2N to test the cliff.
 - alpha(r,N) = (1/2)(-log2 delta - log2 eps)/N. Check: (a) flat at 57,59,60; (b) STEP at
   58 of height exactly log2|de58|/N; (c) cliff at 61.
 - RELABEL test: is the 'step' anything more than log2|de_r| plugged in? (it is not -- the
   Szegedy sqrt/product contribute NO new derivation of 2^hw(db56)).
"""
import sys, math
import numpy as np
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

s = sb.s


def de_sizes(N):
    return sb.DE_SIZES.get(N)  # (|de57|,|de58|,|de59|,|de60|)


def alpha_map(N, delta_flat=0.5):
    """alpha(r) for r in 57..61. eps(r)=|de_r|/2^N; delta flat then cliff at 61."""
    d57, d58, d59, d60 = de_sizes(N)
    de = {57: d57, 58: d58, 59: d59, 60: d60}
    eps = {r: de[r] / (1 << N) for r in de}
    # the sr=61 wall: delta collapses to ~2^-2N (the two-condition rank-2 rate; QW1)
    delta = {57: delta_flat, 58: delta_flat, 59: delta_flat, 60: delta_flat,
             61: 2.0 ** (-2 * N)}
    eps[61] = eps[60]  # de61=1 (on-track) -- the collapse is in delta, not eps
    out = {}
    for r in (57, 58, 59, 60, 61):
        a = 0.5 * (-math.log2(delta[r]) - math.log2(eps[r])) / N
        out[r] = a
    return out, eps, delta, de


if __name__ == '__main__':
    print("=" * 74)
    print("W7-QW5 : alpha(r) -- step at r=58 (log2|de58|/N) + cliff at 60->61?")
    print("=" * 74)

    print("\n--- alpha(r,N) map (eps from pinned de-set sizes; delta flat then 2^-2N@61) ---")
    print(f"{'N':>3} | {'a57':>7} {'a58':>7} {'a59':>7} {'a60':>7} {'a61':>8} | "
          f"{'step58':>7} {'log2|de58|/N':>13}")
    step_ok = True
    for N in (8, 10, 12, 14):
        a, eps, delta, de = alpha_map(N)
        step = a[58] - a[57]                      # measured step height at r=58
        predicted = 0.5 * math.log2(de[58]) / N   # = (1/2) log2|de58| / N  (eps doubles the 1/2)
        # NB: alpha has a 1/2; eps enters as -log2(eps)/2N = +log2|de_r|/2N relative shift.
        print(f"{N:>3} | {a[57]:>7.4f} {a[58]:>7.4f} {a[59]:>7.4f} {a[60]:>7.4f} "
              f"{a[61]:>8.3f} | {step:>7.4f} {predicted:>13.4f}")
        if abs(step - predicted) > 1e-9:
            step_ok = False

    print("\n--- (1) is r=58 a STEP? (a58 != a57=a59=a60) ---")
    a, eps, delta, de = alpha_map(10)
    flat = abs(a[57]-a[59]) < 1e-9 and abs(a[59]-a[60]) < 1e-9
    print(f"    N=10: a57={a[57]:.4f} a58={a[58]:.4f} a59={a[59]:.4f} a60={a[60]:.4f}")
    print(f"    57/59/60 flat? {flat}   58 differs? {abs(a[58]-a[57])>1e-9} "
          f"(step up = de58 opening)")

    print("\n--- (2) cliff at 60->61? (a61 >> a60 via delta collapse) ---")
    print(f"    N=10: a60={a[60]:.4f}  a61={a[61]:.3f}  (jump = {a[61]-a[60]:.3f}, "
          f"from delta:0.5 -> 2^-2N)")

    print("\n--- (3) does the step SCALE with |de58|? (height == log2|de58|/(2N)) ---")
    print(f"    step height == (1/2)log2|de58|/N for all N?  {step_ok}")
    print("    de58 by N:", {N: de_sizes(N)[1] for N in (8, 10, 12, 14)})

    print("\n--- (4) RELABEL test: is the step DERIVED, or just |de58| plugged in? ---")
    print("    The step height is, BY CONSTRUCTION, (1/2)log2|de58|/N -- i.e. the KNOWN")
    print("    de58 census 2^hw(db56) inserted into eps. The Szegedy sqrt/product add NO")
    print("    independent derivation of 2^hw(db56); ANY monotone f(delta,eps) with eps∝|de_r|")
    print("    yields the same step. So the alpha-form RESTATES the de58 law, not derives it.")
    print(f"\n  pinned: {sb.DE_LAW}")

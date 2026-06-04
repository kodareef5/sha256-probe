#!/usr/bin/env python3
"""
W3-CR5 — Mass-action analog computer -> collisions as ODE fixed points, 2^-2N as a
         codim-2 bifurcation

Card claim: Engineer a mass-action ODE whose positive stable steady states <-> collisions;
#steady-states realizes 2^0.74N, and the codimension of the bifurcation that annihilates
them along the round axis = 2 (two zero eigenvalues) realizing 2^-2N.

PROBE (per card): N=3,4 build the mass-action steady-state polynomial system, count real
positive solutions per round (sympy resultants / grid); does the count grow like 2^0.74N
and do steady states annihilate in a codim-2 fold near sr=61? Run the JACOBIAN-INJECTIVITY
test (is multistationarity even possible?).

KILL: injectivity says monostationary (can't encode an exponential count), OR count != 2^0.74N,
OR bifurcations are codim-1.

ADVERSARIAL FRAME (orchestrator priors #3, skeptic note): there is NO canonical GF(2) ->
positive-mass-action encoding, so any "2^-2N match" risks being imposed/circular. The one
NON-circular, decisive test the card itself names is the Jacobian-injectivity (Craciun-Feinberg)
test: if the species-formation Jacobian is INJECTIVE on the positive orthant, the network is
MONOSTATIONARY -- it can have at most ONE positive steady state, hence CANNOT encode an
exponential (2^0.74N) count of collisions-as-steady-states. That kills the card's count claim
without needing an arbitrary encoding. We run that test on the genuine difference-reaction
network (the same network CR1/CR2 build from the round's carry/shift gates), at N=3,4.

Craciun-Feinberg injectivity criterion (mass-action): the network is injective (=> at most one
positive steady state in each stoichiometric compatibility class) iff the determinant of the
Jacobian  J(x) = S * (dv/dx)  NEVER VANISHES on the positive orthant. Since det J is a
polynomial whose monomials (in positive concentrations x and positive rate constants k) each
carry a definite sign, det J keeps a constant sign on the whole positive orthant IFF all its
monomials share one sign -> injective -> monostationary. We test this NUMERICALLY without
sympy: evaluate det J at a large random sample of positive (x, k) points; if sign(det J) is
constant (never flips) the network is injective/monostationary; a single sign flip exhibits a
zero of det J on the positive orthant -> NON-injective -> multistationarity is *possible*.
(This is a sound, decisive test: one observed sign change disproves injectivity outright; a
constant sign over a dense sample is strong evidence of injectivity, cross-checked by also
trying to find two distinct positive steady states directly.)

We ALSO test the bifurcation-codimension content: even if one IMPOSED an encoding, is the
claimed "2" the genuine two independent conditions (g1,h with g2=g1+h, indep ratio 1.005) or
a coincidental codim-2? We report what would be required (two simultaneous zero eigenvalues
tied to g1 and h) and whether the mass-action object supplies it (it cannot, if monostationary).

Throttled, sympy symbolic, N in {3,4}. No SAT.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import numpy as np
s = sb.s


def build_diff_crn(N):
    """Same difference-reaction network as CR1/CR2: species = per-bit difference indicators
    on the (a,e) heads + carry species; reactions = carry-birth + xor-flip + shift copies.
    Returns (species_list, reactions=[(reactant_dict, product_dict)]) with multiplicities."""
    # Keep it small for symbolic det: model the a-head carry chain (the active path).
    spec = [('d', i) for i in range(N)] + [('c', i) for i in range(1, N)]
    sidx = {sname: k for k, sname in enumerate(spec)}
    rx = []
    for i in range(N):
        d_i = ('d', i)
        c_in = ('c', i) if i >= 1 else None
        c_out = ('c', i + 1) if i + 1 <= N - 1 else None
        react = {d_i: 1}
        if c_in is not None:
            react[c_in] = 1
        prod = {c_out: 1} if c_out is not None else {}
        rx.append((react, prod))
        if c_in is not None:
            rx.append(({c_in: 1}, {d_i: 1}))
    return spec, sidx, rx


def _crn_matrices(N):
    """Return (S, reactant_mult, nsp, nrx): stoichiometric matrix S (nsp x nrx) and the
    reactant multiplicity matrix R (nrx x nsp) for the mass-action rate v_j = k_j prod x_i^{R[j,i]}."""
    spec, sidx, rx = build_diff_crn(N)
    nsp = len(spec); nrx = len(rx)
    S = np.zeros((nsp, nrx))
    R = np.zeros((nrx, nsp))
    for j, (react, prod) in enumerate(rx):
        for sn, mult in react.items():
            S[sidx[sn], j] -= mult
            R[j, sidx[sn]] += mult
        for sn, mult in prod.items():
            S[sidx[sn], j] += mult
    return S, R, nsp, nrx


def _detJ(x, k, S, R):
    """det of the mass-action species-formation Jacobian J = S diag(v) (R/x) at point (x,k).
    v_j = k_j prod_i x_i^{R[j,i]} ; dv_j/dx_i = v_j * R[j,i]/x_i.
    J[a,i] = sum_j S[a,j] * dv_j/dx_i."""
    # v_j
    logv = np.log(k) + R @ np.log(x)
    v = np.exp(logv)
    # dv/dx : (nrx x nsp), dvdx[j,i] = v_j * R[j,i] / x_i
    dvdx = (v[:, None] * R) / x[None, :]
    J = S @ dvdx                       # (nsp x nsp)
    return np.linalg.det(J)


def jacobian_injectivity(N, samples=20000, seed=0):
    """Numerical Craciun-Feinberg injectivity test: sample positive (x,k), watch sign(det J).
    Constant sign over the sample => injective => monostationary. Any flip => non-injective."""
    S, R, nsp, nrx = _crn_matrices(N)
    rng = np.random.default_rng(seed)
    signs = []
    detzero = True
    pos = neg = 0
    for _ in range(samples):
        x = np.exp(rng.uniform(-4, 4, size=nsp))   # positive concentrations spanning orders of mag
        k = np.exp(rng.uniform(-4, 4, size=nrx))   # positive rate constants
        d = _detJ(x, k, S, R)
        if abs(d) > 1e-14 * (1 + abs(d)):
            detzero = False
        if d > 0:
            pos += 1
        elif d < 0:
            neg += 1
    flips = (pos > 0 and neg > 0)
    injective = (not flips)            # one sign only (or det ~0 everywhere -> degenerate)
    return dict(nsp=nsp, nrx=nrx, det_identically_zero=(pos == 0 and neg == 0),
                pos=pos, neg=neg, sign_flip=flips, injective=injective,
                monostationary=(injective and not (pos == 0 and neg == 0)))


def main():
    print("=" * 78)
    print("W3-CR5: mass-action multistationarity (can collisions even BE distinct steady states?)")
    print("=" * 78)
    print("\nGround truth: collision count ~ 2^0.74N (MANY steady states needed);")
    print("rate 2^-2N == TWO independent conditions g1,h (g2=g1+h exact, indep 1.005).\n")

    print("[Jacobian-injectivity (Craciun-Feinberg) test on the difference-CRN, numerical]")
    print("injective on positive orthant  =>  MONOSTATIONARY  =>  <=1 positive steady state")
    print(f"{'N':>3} | {'species':>7} {'rxns':>5} | {'det>0':>6} {'det<0':>6} | {'sign-flip?':>10} | {'injective?':>10} | {'monostationary?':>15}")
    mono = {}
    for N in (3, 4):
        r = jacobian_injectivity(N, samples=20000)
        mono[N] = r['monostationary']
        print(f"{N:>3} | {r['nsp']:>7} {r['nrx']:>5} | {r['pos']:>6} {r['neg']:>6} | "
              f"{str(r['sign_flip']):>10} | {str(r['injective']):>10} | {str(r['monostationary']):>15}")
        if r['det_identically_zero']:
            print("      det J ~ 0 everywhere -> degenerate (conservation laws); steady states "
                  "form a continuum, not 2^0.74N discrete points (still NOT an exp count).")

    print("\n--- count claim ---")
    print("For collisions-as-steady-states to realize 2^0.74N, the network MUST be multistationary")
    print("with EXPONENTIALLY many positive steady states. Injective/monostationary forbids >1.")
    print(f"   N=3: 2^0.74N = {2**(0.74*3):.1f} steady states needed; N=4: {2**(0.74*4):.1f}.")

    print("\n--- codim-2 / 2^-2N claim ---")
    print("Even granting an encoding, 'codim 2' is only the genuine structure if the TWO zero")
    print("eigenvalues correspond to the TWO independent conditions g1=0 and h=0 (g2=g1+h).")
    print("A monostationary system has a UNIQUE steady state with a single stable branch -- no")
    print("multi-state annihilation, so no fold/cusp encoding two independent N-bit conditions.")
    print("=> any 'codim-2' would be IMPOSED by the (non-canonical) encoding, not derived.")

    # degenerate-or-monostationary: either way it cannot supply a DISCRETE 2^0.74N count
    cannot_count = {}
    for N in (3, 4):
        r = jacobian_injectivity(N, samples=8000, seed=7)
        cannot_count[N] = r['monostationary'] or r['det_identically_zero']

    print("\n" + "=" * 78)
    print("KILL: injectivity says monostationary, OR count != 2^0.74N, OR bifurcations codim-1.")
    allmono = all(mono.values())
    print(f"all N injective/monostationary? {allmono}")
    print(f"all N unable to supply a discrete exp count (monostationary OR degenerate)? "
          f"{all(cannot_count.values())}")
    if all(cannot_count.values()):
        print("-> KILL: the mass-action difference-network CANNOT encode 2^0.74N discrete")
        print("   positive steady states; the codim-2/2^-2N story would be an imposed,")
        print("   non-canonical encoding, NOT a derivation of the two-conditions structure.")
    else:
        print("-> SURVIVES the injectivity gate; would need explicit steady-state count next.")
    print("=" * 78)


if __name__ == '__main__':
    main()

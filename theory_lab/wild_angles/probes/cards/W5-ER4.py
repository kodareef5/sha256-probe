#!/usr/bin/env python3
"""
W5-ER4 -- Foster's theorem audit: round-60 boundary as a resistance-budget depletion.

Card claim (CATALOG): Foster pins Sum_edges w_e * R_eff(e) = n-1 (a conserved budget). Conjecture
early/mid rounds absorb almost all of it (good diffusion), the tail is starved -- and that
starvation is the slack the cascade exploits; the boundary = where the cumulative Foster share
crosses a threshold (a knee near r~59).

probe: N=8,12 full rounds; R_eff(e) from L+; verify Foster (a free correctness oracle); plot
cumulative Foster share vs round -- a knee near 57-59? tail depleted vs mid?
kill: featureless curve (no knee within +-3 of 59) across N and all conductance choices, OR tail
not depleted.
skeptic (card's own, weakest of the four): Foster pins the TOTAL, not the per-round allocation --
"where the budget concentrates" is an artifact of the (tunable) conductance choice unless physics-
forced.

==========================================================================================
PRIOR FINDING #4 (adversarial bar): NO round-60 knee. Structural quantities saturate EARLY/
SMOOTHLY; every "boundary at 60/61" so far is bookkeeping or a fit. To survive, ER4 must show a
REAL depletion concentrated AT round ~59 (a knee within +-3), robust across N AND conductance
choices. We show the per-round Foster-share curve explicitly and look for a knee vs a smooth/
monotone ramp. We test 2 physics-motivated conductances (avalanche sensitivity; and uniform) to
check the skeptic's "artifact of the conductance choice" worry.
==========================================================================================

GRAPH (full 64 rounds): node = (round r in 0..64) x (register k) x (bit j in 0..N-1) over N active
lanes. We use the REAL full compression (lib.full_compression-style per-round recompute) to measure
the avalanche conductance of each inter-round edge: cond[(r,k,j)->(r+1,k',j')] = P(out-bit flips |
in-bit flips) at round r+1, over random messages. Foster: Sum_e w_e R_eff(e) must equal rank(L) =
(#nodes - #components). The per-round share = Sum over edges leaving round r of w_e R_eff(e); its
cumulative fraction vs r is the budget-depletion curve.
"""
import sys, random, time
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import numpy as np
s = sb.s
np.seterr(all='ignore')

REG = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')


def full_round_states(M):
    """Return [state_0(=IV after schedule? no: pre-round-0), state_1, ..., state_64] using the
    repo's full_compression to get W[0..63], then replay all 64 rounds capturing every state.
    full_compression(M, free_57_61) returns (final_state, W[0..63]); we set free to the natural
    schedule by passing the schedule-derived words. Simpler: rebuild W[0..63] from M directly via
    precompute + build_schedule_tail with the *natural* free words (the real message schedule)."""
    # Build the genuine full schedule W[0..63] for message M (standard SHA-256 schedule).
    W = list(M)
    for t in range(16, 64):
        W.append(s.add(s.sigma1(W[t - 2]), W[t - 7], s.sigma0(W[t - 15]), W[t - 16]))
    # replay 64 rounds from IV
    a, b, c, d, e, f, g, h = s.IV
    states = [(a, b, c, d, e, f, g, h)]
    for t in range(64):
        T1 = s.add(h, s.Sigma1(e), s.Ch(e, f, g), s.K[t], W[t])
        T2 = s.add(s.Sigma0(a), s.Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, s.add(d, T1), c, b, a, s.add(T1, T2)
        states.append((a, b, c, d, e, f, g, h))
    return states, W


def one_round(state, W, t):
    """Recompute exactly round t from `state` (state is after round t-1, i.e. states[t])."""
    a, b, c, d, e, f, g, h = state
    T1 = s.add(h, s.Sigma1(e), s.Ch(e, f, g), s.K[t], W[t])
    T2 = s.add(s.Sigma0(a), s.Maj(a, b, c))
    h, g, f, e, d, c, b, a = g, f, e, s.add(d, T1), c, b, a, s.add(T1, T2)
    return (a, b, c, d, e, f, g, h)


def build_full_graph(N, samples=12, seed=20260603, uniform=False):
    """Full 64-round resistor network over N active lanes. Returns (Lap, node_of, ROUNDS, NN)."""
    rng = random.Random(seed)
    R = 64
    nstates = R + 1                       # states[0..64]
    NLAYER = 8 * N
    def nid(layer, k, j):
        return layer * NLAYER + k * N + j
    NTOT = nstates * NLAYER

    Nmask = (1 << N) - 1
    # per-transition conductance matrix
    cond = [np.zeros((NLAYER, NLAYER)) for _ in range(R)]    # transition t: states[t]->states[t+1]
    if not uniform:
        for _ in range(samples):
            M = [rng.getrandbits(32) for _ in range(16)]
            states, W = full_round_states(M)
            for t in range(R):
                st = states[t]
                nxt0 = states[t + 1]
                for k in range(8):
                    for j in range(N):
                        st2 = list(st); st2[k] ^= (1 << j)
                        nxt2 = one_round(tuple(st2), W, t)
                        for kk in range(8):
                            d = (nxt2[kk] ^ nxt0[kk]) & Nmask
                            jj = d
                            while jj:
                                jb = (jj & -jj).bit_length() - 1
                                cond[t][kk * N + jb, k * N + j] += 1.0
                                jj &= jj - 1
        for t in range(R):
            cond[t] /= samples
    else:
        # uniform conductance: every realized edge weight 1 (structure-only). Use one sample to
        # find which edges exist (nonzero avalanche), set them to 1.
        M = [rng.getrandbits(32) for _ in range(16)]
        states, W = full_round_states(M)
        for t in range(R):
            st = states[t]; nxt0 = states[t + 1]
            for k in range(8):
                for j in range(N):
                    st2 = list(st); st2[k] ^= (1 << j)
                    nxt2 = one_round(tuple(st2), W, t)
                    for kk in range(8):
                        d = (nxt2[kk] ^ nxt0[kk]) & Nmask
                        jj = d
                        while jj:
                            jb = (jj & -jj).bit_length() - 1
                            cond[t][kk * N + jb, k * N + j] = 1.0
                            jj &= jj - 1

    # assemble Laplacian and remember edge list grouped by round-of-origin t
    Lap = np.zeros((NTOT, NTOT))
    edges_by_round = [[] for _ in range(R)]
    for t in range(R):
        Cmat = cond[t]
        for kk in range(8):
            for jj in range(N):
                u = nid(t + 1, kk, jj)
                for k in range(8):
                    for j in range(N):
                        w = Cmat[kk * N + jj, k * N + j]
                        if w > 0:
                            v = nid(t, k, j)
                            Lap[u, u] += w; Lap[v, v] += w
                            Lap[u, v] -= w; Lap[v, u] -= w
                            edges_by_round[t].append((u, v, w))
    return Lap, edges_by_round, NTOT


def foster_audit(Lap, edges_by_round, ntot):
    """Compute R_eff(e) via L+ for every edge, verify Foster Sum w_e R_eff = rank, return per-round
    Foster share."""
    Lp = np.linalg.pinv(Lap)
    R = len(edges_by_round)
    share = np.zeros(R)
    total = 0.0
    for t in range(R):
        s_t = 0.0
        for (u, v, w) in edges_by_round[t]:
            reff = Lp[u, u] + Lp[v, v] - 2 * Lp[u, v]
            s_t += w * reff
        share[t] = s_t
        total += s_t
    # Foster target = rank of Laplacian = ntot - (#connected components)
    # estimate rank numerically
    ev = np.linalg.eigvalsh(Lap)
    rank = int(np.sum(ev > 1e-7))
    return share, total, rank


def find_knee(cum):
    """Return the round index where the cumulative curve has its sharpest second-difference
    (the 'knee'), and a flatness/smoothness measure."""
    cum = np.asarray(cum)
    if len(cum) < 5:
        return None, None
    d2 = np.abs(np.diff(cum, 2))
    knee = int(np.argmax(d2)) + 1     # +1 to map back to round index
    # smoothness: max |d2| relative to mean |d2| -- a real knee has a sharp spike
    sharp = d2.max() / (d2.mean() + 1e-12)
    return knee, sharp


def main():
    print("=" * 80)
    print("W5-ER4: Foster resistance-budget depletion -> a knee near round 57-59?")
    print("=" * 80)

    for N in (8, 12):
        for uniform in (False, True):
            tag = "uniform-cond" if uniform else "avalanche-cond"
            t0 = time.time()
            samples = (10 if N == 8 else 6)
            Lap, ebr, ntot = build_full_graph(N, samples=samples, uniform=uniform)
            share, total, rank = foster_audit(Lap, ebr, ntot)
            # Foster correctness oracle: total should equal rank
            err = abs(total - rank) / max(rank, 1)
            cum = np.cumsum(share) / (total + 1e-12)
            knee, sharp = find_knee(cum)
            # where does cumulative cross 0.5, 0.9?  (depletion = most budget spent early)
            cross50 = int(np.searchsorted(cum, 0.5))
            cross90 = int(np.searchsorted(cum, 0.9))
            # tail share: rounds 57..63 fraction of total
            tail_share = share[57:64].sum() / (total + 1e-12)
            mid_share = share[20:40].sum() / (total + 1e-12)
            print(f"\n--- N={N}  [{tag}]  ({time.time()-t0:.1f}s) ---")
            print(f"  Foster oracle: Sum w_e R_eff = {total:.3f}  vs rank(L) = {rank}  "
                  f"(rel err {err:.2e}; <1e-6 confirms the identity & the code)")
            print(f"  cumulative budget crosses 0.5 at round {cross50}, 0.9 at round {cross90}")
            print(f"  detected KNEE (max 2nd-diff) at round {knee}  (sharpness {sharp:.1f}x mean; "
                  f">~5x = real knee, ~1-2x = smooth)")
            print(f"  tail (r57-63) Foster share = {tail_share:.4f} ; mid (r20-39) = {mid_share:.4f} "
                  f"-> tail/mid ratio = {tail_share/(mid_share+1e-12):.3f}")
            # print a coarse per-8-round share profile to SHOW the curve
            prof = [share[b:b+8].sum() / (total + 1e-12) for b in range(0, 64, 8)]
            print("  per-8-round Foster share: " +
                  " ".join(f"r{b}-{b+7}:{prof[i]:.3f}" for i, b in enumerate(range(0, 64, 8))))

    print("\n" + "=" * 80)
    print("DECISION (kill: no knee within +-3 of round 59 across N & conductance, OR tail not depleted):")
    print("  - If the KNEE is NOT near 57-61 (e.g. it sits early, or sharpness ~1-2x = smooth), AND")
    print("    the tail share is comparable to mid (not specially depleted) -> KILLED (finding #4:")
    print("    structural quantities saturate smoothly; no round-60 boundary).")
    print("  - A knee robustly at 57-61 across BOTH N and BOTH conductances would be needed to survive.")
    print("=" * 80)


if __name__ == '__main__':
    main()

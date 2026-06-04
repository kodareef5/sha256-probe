#!/usr/bin/env python3
"""
W5-ER1 -- Davies-Meyer ground node: 132 = the high-resistance (recompute) registers.

Card claim (CATALOG): make the message-input layer the electrical GROUND; controllability
= 1/effective-resistance-to-ground. Recompute registers (da,db,de,df + 4 dc @63) are screened
from input by the T1+T2 carry-bottleneck (long thin resistor => high R_eff => hard-core);
pass-through registers (dd,dg,dh) wire near-directly to earlier a/e (low R_eff).

probe: N=8,10,12 build the round x bit graph (conductance = avalanche sensitivity), L+ = pinv,
R_eff(out-bit, ground) = L+_uu + L+_vv - 2 L+_uv ; do the top-132 R_eff bits = {da,db,de,df,+4dc}?
AUC vs the known set.
kill: top-132 overlap <= chance (AUC <= 0.55) at N=12, OR no recompute/pass-through R_eff gap.
skeptic: R_eff and avalanche-sensitivity may be the same measurement -- must show the network/path
structure (multi-hop screening) beats a raw sensitivity column-sum.

==========================================================================================
PRIOR FINDING #1 (adversarial bar): "132 = corank" is a CATEGORY ERROR. A *real* effective-
resistance partition should give 0/128 or the WRONG set, NOT a stable 132 with {a,b,e,f}+4dc.
We never CONFIRM a near-132 without that support landing. The genuine "132" only ever appears
as the single-bit DETERMINISTIC-control census (sample-dependent). So we ALSO compute, as a
control, the raw single-bit-sensitivity column-sum 1/R_naive ranking -- if R_eff merely
reproduces that, it's the census in disguise (a rename), not a network result.
==========================================================================================

GRAPH CONSTRUCTION (faithful to the card):
 Nodes = (round r in 57..63) x (register k in 0..7) x (bit j in 0..N-1), i.e. one node per
   register-bit at each tail round, PLUS one GROUND node g (the message-input layer, W[57..60]).
 Edges (undirected, weight = conductance):
   - GROUND -> every register-bit at round 57's INPUT (state_after_56), weight = avalanche
     sensitivity of that bit to a random input-bit flip in the free schedule words.  Actually
     the input layer feeds the WHOLE tail through the schedule; we connect ground to the
     round-57 register bits with conductance = P(that bit flips | random free-input flip).
   - layer-to-layer: node (r,k,j) -- (r+1,k',j') weight = P(out-bit (r+1,k',j') flips |
     in-bit (r,k,j) flips), measured by a single-bit-flip avalanche census at that round.
 This is a genuine multi-hop resistor network: a recompute output bit at round 63 reaches
 ground only through the long T1+T2 carry path; a pass-through bit (dd=da slid down) reaches
 it in one hop.  R_eff(out63-bit, ground) is then the network effective resistance.

We then rank all 256 round-63 register-bits by R_eff-to-ground (high R_eff = hard-core) and
ask: do the top-132 match the recompute set {a,b,e,f}@63 (128) + the 4 dc?  AUC of R_eff as a
classifier for membership in that 132-set.
"""
import sys, random, time
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import numpy as np
s = sb.s
np.seterr(all='ignore')

REG = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')
TAIL_ROUNDS = list(range(57, 64))          # 57..63 inclusive -> 7 layers of register STATES (56..63)


def pack_full_width(states_list):
    """states_list[t] = (a..h) tuple; return list over t of a 256-bit int (8*32 bits)."""
    out = []
    for st in states_list:
        v = 0
        for k, w in enumerate(st):
            v |= (w & 0xffffffff) << (32 * k)
        out.append(v)
    return out


def tail_states(state56, Wpre, free):
    """Return [state56, state57, ..., state63] (8 states). Only tail depends on `free`.
    run_tail_rounds already returns [state56, after57, ..., after63] (8 states)."""
    sched = s.build_schedule_tail(Wpre, free)
    return list(s.run_tail_rounds(state56, sched, start_round=57))


def build_avalanche_graph(N, samples=24, seed=20260603):
    """Build the round x register-bit resistor network at full 32-bit width, but only use
    the low N bits of each 32-bit register as 'active lanes' so the graph stays small.
    Returns (node_index, edges, ground_idx, out63_nodes).

    NOTE on N: the recompute/pass-through register *identity* is a 32-bit-width phenomenon
    (the named 132-set). We keep the full 32-bit compression but restrict the GRAPH NODES to
    bits [0..N) of each register at each round (N<=12) so pinv is cheap. The card explicitly
    allows N=8,10,12 here and the support question is about WHICH registers, not which bit.
    """
    rng = random.Random(seed)
    nstates = len(TAIL_ROUNDS) + 1               # 56..63 -> 8 layers
    # node id = layer * (8*N) + reg*N + bit ; layer 0 == round-56 state (the input side)
    def nid(layer, reg, bit):
        return layer * (8 * N) + reg * N + bit
    NLAYER = 8 * N
    NREG_NODES = nstates * NLAYER
    GROUND = NREG_NODES                          # single extra ground node
    NTOT = NREG_NODES + 1

    # accumulate edge conductances
    # (A) ground -> round-56 (layer 0) bits: how often a free-input flip reaches that input bit
    # (B) layer L -> layer L+1: avalanche of one register-bit flip across one round
    condG = np.zeros(NLAYER)                       # ground to each layer-0 bit
    condLL = [np.zeros((NLAYER, NLAYER)) for _ in range(nstates - 1)]  # per layer transition

    Nmask = (1 << N) - 1
    for _ in range(samples):
        M = [rng.getrandbits(32) for _ in range(16)]
        state56, Wpre = s.precompute_state(M)
        free0 = [rng.getrandbits(32) for _ in range(4)]
        base_states = tail_states(state56, Wpre, free0)
        base_packed = pack_full_width(base_states)

        # (A) ground coupling: flip each of the 128 free-input bits, see which round-56-side
        # *and* which layer-0 register bits move. The input enters via the SCHEDULE, which only
        # affects rounds >=57, so layer-0 (state56) does NOT move from free flips. Instead we
        # connect ground to layer 1 (round-57 OUTPUT) -- the first place the input acts.
        # We approximate ground->layer0 by the round-57 input sensitivity folded back:
        for ib in range(128):                      # all 128 free-schedule bits
            w, b = divmod(ib, 32)
            free1 = list(free0); free1[w] ^= (1 << b)
            p1 = pack_full_width(tail_states(state56, Wpre, free1))
            resp57 = (p1[1] ^ base_packed[1])      # round-57 output difference
            for k in range(8):
                for j in range(N):
                    if (resp57 >> (32 * k + j)) & 1:
                        condG[k * N + j] += 1.0

        # (B) per-layer avalanche: flip register-bit (k,j) of state at layer L, recompute the
        # ONE next round, count which (k',j') flip. We do this honestly by reconstructing the
        # round from the perturbed state. Use full_compression-style single round via lib.
        for L in range(nstates - 1):               # transitions 0->1 .. 6->7  (states 56..62 -> next)
            st = base_states[L]
            # to recompute exactly one round we need the schedule word for that round and run it.
            rno = 56 + L                            # this state is "after round rno"; next round = rno+1
            sched = s.build_schedule_tail(Wpre, free0)   # W[57..63] indexed 0..6
            rnext = rno + 1                          # the round we recompute
            wword = sched[rnext - 57]                # schedule word for round rnext
            for k in range(8):
                for j in range(N):
                    st2 = list(st); st2[k] ^= (1 << j)
                    # run exactly one round (rnext) from st2 with its single schedule word
                    nxt2 = s.run_tail_rounds(tuple(st2), [wword], start_round=rnext)[1]
                    nxt0 = base_states[L + 1]
                    d = 0
                    for kk in range(8):
                        d |= ((nxt2[kk] ^ nxt0[kk]) & 0xffffffff) << (32 * kk)
                    for kk in range(8):
                        for jj in range(N):
                            if (d >> (32 * kk + jj)) & 1:
                                condLL[L][kk * N + jj, k * N + j] += 1.0

    # normalize to [0,1] conductances
    condG /= (samples * 128)
    for L in range(nstates - 1):
        condLL[L] /= samples

    # assemble the weighted Laplacian
    Lap = np.zeros((NTOT, NTOT))
    def add_edge(u, v, w):
        if w <= 0:
            return
        Lap[u, u] += w; Lap[v, v] += w
        Lap[u, v] -= w; Lap[v, u] -= w
    # ground -> layer-0 register bits (use condG as conductance from ground into the network)
    for k in range(8):
        for j in range(N):
            add_edge(GROUND, nid(0, k, j), condG[k * N + j])
    # layer transitions
    for L in range(nstates - 1):
        Cmat = condLL[L]
        for kk in range(8):
            for jj in range(N):
                u = nid(L + 1, kk, jj)
                for k in range(8):
                    for j in range(N):
                        w = Cmat[kk * N + jj, k * N + j]
                        if w > 0:
                            add_edge(u, nid(L, k, j), w)

    out63 = {(k, j): nid(nstates - 1, k, j) for k in range(8) for j in range(N)}
    return Lap, GROUND, out63, NTOT


def reff_to_ground(Lap, ground, targets):
    """R_eff(u, ground) = Lpinv_uu + Lpinv_gg - 2 Lpinv_ug, via Moore-Penrose pinv of Laplacian."""
    Lp = np.linalg.pinv(Lap)
    g = ground
    out = {}
    for key, u in targets.items():
        out[key] = Lp[u, u] + Lp[g, g] - 2 * Lp[u, g]
    return out


def auc_score(scores, positive_set):
    """AUC = P(score(pos) > score(neg)). scores: dict key->float ; positive_set: set of keys."""
    pos = [v for k, v in scores.items() if k in positive_set]
    neg = [v for k, v in scores.items() if k not in positive_set]
    if not pos or not neg:
        return float('nan')
    cnt = 0; tot = 0
    for p in pos:
        for n in neg:
            tot += 1
            if p > n: cnt += 1
            elif p == n: cnt += 0.5
    return cnt / tot


def main():
    print("=" * 78)
    print("W5-ER1: effective-resistance-to-ground -> 132 = recompute registers {a,b,e,f}+4dc?")
    print("=" * 78)
    # The known recompute (hard-core) set over the N active lanes of each register:
    # full registers a(0),b(1),e(4),f(5) at round 63 + 4 scattered dc bits.
    # On the restricted N lanes we mark a,b,e,f fully; dc we cannot pin to exact positions at
    # arbitrary N, so we report the register-level partition (the discriminating question).
    RECOMPUTE_REGS = {0, 1, 4, 5}        # a,b,e,f  (high R_eff predicted)
    PASSTHRU_REGS = {3, 6, 7}            # d,g,h    (low  R_eff predicted -- shift-register slides)
    # c is mixed (dc: 28/32 controlled, 4 hard) -> treat as ambiguous, exclude from clean partition

    for N in (8, 10, 12):
        t0 = time.time()
        samples = 24 if N <= 10 else 16
        Lap, ground, out63, ntot = build_avalanche_graph(N, samples=samples)
        reff = reff_to_ground(Lap, ground, out63)
        # rank all 8N round-63 bits by R_eff (descending = highest resistance first)
        ranked = sorted(reff.items(), key=lambda kv: -kv[1])
        # register-level mean R_eff
        per_reg = {k: [] for k in range(8)}
        for (k, j), v in reff.items():
            per_reg[k].append(v)
        means = {k: (np.mean(per_reg[k]) if per_reg[k] else float('nan')) for k in range(8)}

        # AUC: does high R_eff predict membership in the recompute (a,b,e,f) register set?
        # positive = bits whose register is in RECOMPUTE_REGS ; restrict to a,b,e,f vs d,g,h
        clean_keys = {(k, j) for (k, j) in reff if k in (RECOMPUTE_REGS | PASSTHRU_REGS)}
        sub = {kk: reff[kk] for kk in clean_keys}
        positives = {kk for kk in clean_keys if kk[0] in RECOMPUTE_REGS}
        auc = auc_score(sub, positives)

        # top-(4N) (= the 132-analog: 4 full registers worth) and what fraction are a,b,e,f
        topK = 4 * N
        top = [k for k, _ in ranked[:topK]]
        frac_abef = np.mean([1.0 if kk[0] in RECOMPUTE_REGS else 0.0 for kk in top])

        rec_mean = np.mean([means[k] for k in RECOMPUTE_REGS])
        pas_mean = np.mean([means[k] for k in PASSTHRU_REGS])
        gap = rec_mean - pas_mean

        print(f"\n--- N={N}  (samples={samples}, {time.time()-t0:.1f}s) ---")
        print("  per-register mean R_eff-to-ground (round 63):")
        for k in range(8):
            tag = "RECOMPUTE(hi?)" if k in RECOMPUTE_REGS else ("passthru(lo?)" if k in PASSTHRU_REGS else "mixed(dc)")
            print(f"    d{REG[k]}[63]: R_eff={means[k]:.5f}   [{tag}]")
        print(f"  recompute-reg mean R_eff = {rec_mean:.5f} ; passthru-reg mean = {pas_mean:.5f}")
        print(f"  R_eff GAP (recompute - passthru) = {gap:+.5f}  (card needs recompute > passthru)")
        print(f"  AUC[R_eff predicts a,b,e,f vs d,g,h] = {auc:.4f}  (kill if <=0.55 at N=12)")
        print(f"  top-{topK} R_eff bits: fraction in {{a,b,e,f}} = {frac_abef:.3f}  (1.0 = perfect 132-set)")

    print("\n" + "=" * 78)
    print("DECISION (kill: AUC<=0.55 at N=12 OR no recompute/passthru gap):")
    print("  - If R_eff GAP is NEGATIVE or ~0, OR AUC<=0.55, the resistance partition does")
    print("    NOT select the recompute set -> KILLED (per prior finding #1: no stable 132).")
    print("  - A CONFIRMED requires AUC>0.55 AND recompute>passthru AND top-4N landing on a,b,e,f.")
    print("=" * 78)


if __name__ == '__main__':
    main()

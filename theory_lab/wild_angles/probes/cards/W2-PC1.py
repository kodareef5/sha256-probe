#!/usr/bin/env python3
"""
W2-PC1 — Boundary-expansion width jump -> resolution lower bound firing at 61, not 59.

Card (CATALOG): build the sr=k collision-constraint bipartite graph G_k for k=58..61;
(a) Hopcroft-Karp: does G_61 FAIL the constraint->private-variable matching while G_60 PASSES?
(b) plot min boundary delta(s)/s; a CONSTANT lower bound only at 61 is the headline (Ben-Sasson-
Wigderson: boundary-expanding formulas force resolution width >= Omega(c*s)).
KILL: dead if G_60 ALREADY fails the matching (also over-determined yet easy), OR a bounded-size
UNSAT sub-core exists at sr=61 (short refutation by inspection).

ADVERSARIAL FOCUS (lead finding #4): NO round-60 knee exists in the repo — control/rigidity/
reachability dimension decays SMOOTHLY (PH2, CT2 KILLED); the obstruction is the CARRY
nonlinearity, not linear structure. So I must show the ACTUAL per-round quantity and decide:
is the matching/expansion genuinely DISCONTINUOUS at 61, or is the "jump" just the boundary-proof
free-word bookkeeping (slack = -64) relabeled as proof theory?

------------------------------------------------------------------------------------------------
MODEL (solver-free, the card's own probe), grounded in MEASURED schedule structure:
The SHA-256 message schedule W[r] = sigma1(W[r-2]) + W[r-7] + sigma0(W[r-15]) + W[r-16].
Empirically (this probe), the free words W[57..60] feed the tail rounds like this:
  round 57 <- W57   round 58 <- W58   round 59 <- W59   round 60 <- W60   (one FRESH free word each)
  round 61 <- W59 (via the recurrence; W54,W46,W45 are FIXED block-1 words)
  round 62 <- W60        round 63 <- W61 (= recurrence of W59)
So rounds 57-60 each get a private free word (perfect matching exists); rounds >=61 RE-USE
W59 / W60 (no fresh lever) -> Hall deficit by construction.

Bipartite graph G_k:  LEFT = the de(r)=0 collision constraints for enforced rounds r in {57..k}
(per repo ground truth EACH held round = TWO independent N-bit scalar conditions g1=0 AND h=0, so
2 constraint-equations per round, exposed at bit granularity = 2N bit-constraints/round); RIGHT =
the free message bits {(w,j): w in 57..60, j in 0..N-1}, 4N total. Edge iff free bit (w,j) lies in
the carry-monotone GF(2) support of the governing schedule word W[r] at the constraint's output bit
(support computed via the exact linearized recurrence; carries only ADD edges, so a real edge set
is a superset -> this UNDER-counts edges = the HARDEST case for the attacker's matching = most
generous to the card's "matching survives below, fails at 61" hope).

Two readouts per round k:
 (a) Hopcroft-Karp max matching of constraints into free bits; feasible <=> matching == #constraints.
 (b) boundary (unique-neighbour) expansion: full-set ratio |{free bits touched exactly once}|/#C,
     and the per-round min boundary over the round-blocks (the BW sub-core). A CONSTANT > 0 floor
     appearing ONLY at 61 is the headline; a flat-across-k ratio means the "jump" is fake.

N small (4,6,8). Throttled.
"""
import sys
from collections import Counter
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

MASKN = lambda N: (1 << N) - 1

def sched_rots(N):
    base = dict(s0=(7, 18, 3), s1=(17, 19, 10))
    f = lambda x: max(0, min(N - 1, round(x * N / 32)))
    return {k: tuple(f(v) for v in t) for k, t in base.items()}

def ror_bit(j, r, N):
    return (j - r) % N

def shr_bit(j, r, N):
    src = j - r
    return src if src >= 0 else None

def _small_sigma(word_bits, N, rots):
    a, b, c = rots
    out = []
    for j in range(N):
        s = set()
        s ^= word_bits[ror_bit(j, a, N)]
        s ^= word_bits[ror_bit(j, b, N)]
        sj = shr_bit(j, c, N)
        if sj is not None:
            s ^= word_bits[sj]
        out.append(s)
    return out

def build_schedule_support(N, last_round=63):
    r = sched_rots(N)
    s0r, s1r = r['s0'], r['s1']
    W = [[set() for _ in range(N)] for _ in range(last_round + 1)]
    for w in (57, 58, 59, 60):
        W[w] = [{(w, j)} for j in range(N)]
    for rr in range(61, last_round + 1):
        s1 = _small_sigma(W[rr - 2], N, s1r)
        wm7 = W[rr - 7]
        s0 = _small_sigma(W[rr - 15], N, s0r)
        wm16 = W[rr - 16]
        W[rr] = [s1[j] ^ wm7[j] ^ s0[j] ^ wm16[j] for j in range(N)]
    return W

def constraints_for_sr(N, k, W):
    """Round r in {57..k} -> de(r)=0 gate = 2 indep N-bit conditions (g1,h). Bit granularity:
    one constraint per output bit j and per condition-family. Carry-monotone support of de(r) bit j
    = union of W[r] supports at bits 0..j (carry feeds low->high)."""
    cons = []
    for r in range(57, k + 1):
        cum = set()
        for j in range(N):
            cum |= W[r][j]
            cons.append(('g1', r, j, frozenset(cum)))
            cons.append(('h', r, j, frozenset(cum)))
    return cons

def max_matching(constraints):
    adj = [list(c[3]) for c in constraints]
    matchR = {}
    def kuhn(u, seen):
        for v in adj[u]:
            if v in seen:
                continue
            seen.add(v)
            if v not in matchR or kuhn(matchR[v], seen):
                matchR[v] = u
                return True
        return False
    res = 0
    for u in range(len(adj)):
        if adj[u] and kuhn(u, set()):
            res += 1
    return res

def boundary_ratio_full(constraints):
    if not constraints:
        return None, 0
    cnt = Counter()
    for c in constraints:
        for b in c[3]:
            cnt[b] += 1
    uniq = sum(1 for b, v in cnt.items() if v == 1)
    return uniq / len(constraints), len(cnt)

def per_round_min_boundary(N, k, W):
    """min over single enforced-round blocks of (unique free bits in that round)/(#constr in round).
    This is the densest-sub-core boundary BW cares about: if ANY round-block has boundary 0 the
    expander argument dies there."""
    best = None
    for r in range(57, k + 1):
        block = [c for c in constraints_for_sr(N, r, W) if c[1] == r]
        br, _ = boundary_ratio_full(block)
        if br is None:
            continue
        best = br if best is None else min(best, br)
    return best

def run(Ns=(4, 6, 8)):
    print("=" * 80)
    print("W2-PC1: sr=k constraint-graph matching feasibility + boundary expansion, per round.")
    print("KILL: dead if G_60 already fails matching, OR bounded UNSAT sub-core at sr=61.")
    print("=" * 80)
    for N in Ns:
        W = build_schedule_support(N, 63)
        print(f"\n### N={N}  (free words 57..60, {N} bits each -> {4*N} free bits) ###")
        print(f"  {'sr=k':>5} {'#constr':>8} {'#freeBits':>10} {'matching':>9} {'feasible':>9} "
              f"{'bdyRatioFull':>13} {'minRoundBdy':>12}")
        feas, bdy = {}, {}
        for k in range(57, 64):
            cons = constraints_for_sr(N, k, W)
            mm = max_matching(cons)
            br, nf = boundary_ratio_full(cons)
            mrb = per_round_min_boundary(N, k, W)
            feas[k] = (mm == len(cons))
            bdy[k] = br
            print(f"  {k:>5} {len(cons):>8} {nf:>10} {mm:>9} {str(feas[k]):>9} "
                  f"{br:>13.4f} {mrb:>12.4f}")
        print(f"  --> matching feasible: sr=60={feas.get(60)}  sr=61={feas.get(61)}")
        print(f"  --> boundary-ratio: sr=59={bdy.get(59):.4f} sr=60={bdy.get(60):.4f} "
              f"sr=61={bdy.get(61):.4f}")
        # is the boundary ratio DISCONTINUOUS at 61, or smooth?
        seq = [bdy[k] for k in range(57, 64)]
        steps = [seq[i+1] - seq[i] for i in range(len(seq) - 1)]
        jump_6061 = steps[3]  # 60->61
        maxstep = max(abs(s) for s in steps)
        print(f"  --> boundary-ratio per-step deltas (57->58..62->63): "
              f"{[round(s,4) for s in steps]}")
        print(f"  --> 60->61 step = {jump_6061:+.4f}; max |step| anywhere = {maxstep:.4f}  "
              f"(jump at 61 'special' only if |60->61| >> other steps)")
        if feas.get(60) is False:
            print("  ==> KILL CLAUSE 1: matching already fails at sr=60.")
        elif feas.get(60) is True and feas.get(61) is False:
            print("  ==> matching collapses 60->61 (by word re-use). Headline iff boundary ALSO jumps.")
    print("\nNOTE: matching flips at 61 because rounds 61-63 RE-USE free words 59/60 (no fresh lever)")
    print("      = the boundary proof's slack=-64 free-word bookkeeping. The PROOF-THEORETIC")
    print("      headline requires the BOUNDARY EXPANSION (not just matchability) to be")
    print("      discontinuous at 61. Read the boundary-ratio column to judge that.")

if __name__ == '__main__':
    run()

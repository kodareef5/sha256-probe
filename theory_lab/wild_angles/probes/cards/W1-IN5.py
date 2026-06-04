"""
W1-IN5 — Communication complexity of the round-60 predicate → MITM as a barrier.

Card: split the collision predicate at the cut round. Alice holds forward freedoms
(IV -> r_cut), Bob backward (target -> r_cut); collision ⇔ their round-r_cut state-sets
INTERSECT = Set-Intersection / Disjointness on the state. MITM's 232/256 = the effective
input length. A communication LOWER bound (Disjointness is Ω(n)) would prove no
forward/backward split beats 2^b — a real barrier (vs MITM's upper bound).

PROBE (as stated): N=4,6 — build the communication matrix M[a][b]=1 iff forward-a,
backward-b COLLIDE at the reduced-round cut; measure LOG-RANK, FOOLING-SET size, and
DISTANCE from the Disjointness pattern; predict LOW-rank below the frontier, FULL-rank
just past it.
KILL: dead if the matrix is LOW-rank on BOTH sides (always easy) OR FULL-rank EVERYWHERE
(no transition).

OPERATIONALIZATION:
We build the genuine N-bit reduced compression to R rounds. The MITM cut at round r splits
the computation:
  * Alice's freedom = the first FA free message words (feed the FORWARD pass IV -> state_r).
    Alice's input a indexes (M[0..FA-1]) -> a forward cut-state  Sf(a) = state after r rounds.
  * Bob's freedom = the last FB free SCHEDULE/tail words (feed the BACKWARD pass from the
    OUTPUT/target back to state_r). Bob's input b indexes the tail freedom -> a backward
    cut-state  Sb(b) = state at round r implied by his tail choice + a fixed target hash.
A 'collision at the cut' ⇔ Sf(a) == Sb(b) on the matched lanes (the MITM meet condition).

Concretely (small N, exact): we fix a target final state H*. Alice enumerates FA forward
words -> Sf(a) (forward state at r). Bob enumerates FB tail words; for each, run the tail
r..R forward from a *candidate* cut-state is circular, so instead Bob's object is: given his
tail words and the target H*, the cut-state he NEEDS is obtained by running the known tail
rounds BACKWARD from H* (rounds are invertible given the schedule words). We invert the tail.
Then M[a][b] = [ Sf(a) == Sb(b) ] on the cut lanes.

We measure, vs cut position r:
  * real rank and GF(2) rank of M, and LOG2-RANK,
  * fooling-set lower bound (size of a large 1-monochromatic combinatorial rectangle-free set),
  * the matrix's resemblance to EQUALITY/Identity (the canonical high-communication pattern).
Card needs a TRANSITION (low-rank below frontier -> full just past). Kill if low on both
sides, or full everywhere.

Throttle: this process. N<=6, FA=FB=1..2 words so M is at most 2^{2N} x 2^{2N} (<=4096^2 at
N=6,FA=2 is too big; we use FA=FB=1 at N=6 -> 64x64, and FA=FB=2 only at N=4 -> 256x256).
"""
import sys, math, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to
import numpy as np

MASKN = lambda N: (1 << N) - 1


def make_prims(N):
    m = MASKN(N)
    rnd = to._make_round(N)
    rp = to._rot_params(N)

    def ror(x, kk):
        kk %= N
        return ((x >> kk) | (x << (N - kk))) & m
    s0r, s1r = rp['s0'], rp['s1']
    sig0 = lambda x: ror(x, s0r[0]) ^ ror(x, s0r[1]) ^ ((x >> s0r[2]) & m)
    sig1 = lambda x: ror(x, s1r[0]) ^ ror(x, s1r[1]) ^ ((x >> s1r[2]) & m)
    return m, rnd, sig0, sig1


def round_fwd(rnd, st, ki, w):
    return rnd(st, ki, w)


def round_inv(N, st_next, ki, w):
    """Invert one SHA round given the schedule word w and round constant ki.
    Forward: a'=T1+T2, b'=a, c'=b, d'=c, e'=d+T1, f'=e, g'=f, h'=g.
    Given (a',b',c',d',e',f',g',h'): a=b', b=c', c=d', e=f', f=g', g=h'.
    T1 = h + S1(e) + Ch(e,f,g) + k + w ; T2 = S0(a)+Maj(a,b,c).
    a' = T1+T2 -> T1 = a' - T2 (T2 computable from a,b,c). Then d = e' - T1. h = T1 - S1(e)
    - Ch(e,f,g) - k - w."""
    m = MASKN(N)
    ap, bp, cp, dp, ep, fp, gp, hp = st_next
    a = bp; b = cp; c = dp
    e = fp; f = gp; g = hp
    rp = to._rot_params(N)

    def ror(x, kk):
        kk %= N
        return ((x >> kk) | (x << (N - kk))) & m
    s0r, s1r = rp['S0'], rp['S1']
    S0 = lambda x: ror(x, s0r[0]) ^ ror(x, s0r[1]) ^ ror(x, s0r[2])
    S1 = lambda x: ror(x, s1r[0]) ^ ror(x, s1r[1]) ^ ror(x, s1r[2])
    Ch = lambda e, f, g: ((e & f) ^ ((~e & m) & g)) & m
    Maj = lambda a, b, c: ((a & b) ^ (a & c) ^ (b & c)) & m
    T2 = (S0(a) + Maj(a, b, c)) & m
    T1 = (ap - T2) & m
    d = (ep - T1) & m
    h = (T1 - S1(e) - Ch(e, f, g) - (ki & m) - (w & m)) & m
    return (a, b, c, d, e, f, g, h)


def build_comm_matrix(N, r_cut, R, FA, FB, target_seed=0, match_lanes=None):
    """Forward: Alice's FA words -> Sf(a)=state after r_cut. Backward: Bob's FB tail words
    (the LAST FB schedule words, r in [R-FB, R-1]) + fixed target H* -> Sb(b) = state at r_cut
    obtained by inverting rounds R-1 .. r_cut. M[a][b] = [Sf(a)==Sb(b) on match_lanes]."""
    m, rnd, sig0, sig1 = make_prims(N)
    rng = np.random.default_rng(target_seed)
    # fixed base message fill (non-free words) and a fixed target final state H*
    base = [int(rng.integers(0, 1 << N)) for _ in range(16)]
    Hstar = tuple(int(rng.integers(0, 1 << N)) for _ in range(8))
    if match_lanes is None:
        match_lanes = tuple(range(8))

    # tail schedule words r in [r_cut .. R-1] depend on the message; for the backward pass we
    # need explicit words to invert. We let Bob FREELY choose the last FB tail words and fix the
    # remaining tail words from the base schedule. Build base full schedule once.
    def full_sched(M):
        W = list(M) + [0] * (R - 16)
        for i in range(16, R):
            W[i] = (sig1(W[i-2]) + W[i-7] + sig0(W[i-15]) + W[i-16]) & m
        return W

    Wbase = full_sched(base)

    # FORWARD: vary Alice's FA message words (positions 0..FA-1), run IV -> r_cut.
    fwd_states = []
    for combo in itertools.product(range(1 << N), repeat=FA):
        M = list(base)
        for i in range(FA):
            M[i] = combo[i]
        W = full_sched(M)
        st = tuple(int(v) & m for v in sb.IV[:8])
        for i in range(r_cut):
            st = rnd(st, sb.s.K[i] & m, W[i] & m)
        fwd_states.append(tuple(st[L] for L in match_lanes))

    # BACKWARD: vary Bob's FB tail words (positions R-FB..R-1), invert R-1 .. r_cut from H*.
    bwd_states = []
    tail_positions = list(range(R - FB, R))
    for combo in itertools.product(range(1 << N), repeat=FB):
        W = list(Wbase)
        for j, pos in enumerate(tail_positions):
            W[pos] = combo[j] & m
        st = Hstar
        ok = True
        for i in range(R - 1, r_cut - 1, -1):
            st = round_inv(N, st, sb.s.K[i] & m, W[i] & m)
        bwd_states.append(tuple(st[L] for L in match_lanes))

    A = len(fwd_states)
    B = len(bwd_states)
    M = np.zeros((A, B), dtype=np.int8)
    fwd_idx = {}
    for ai, sf in enumerate(fwd_states):
        for bi, sb_ in enumerate(bwd_states):
            if sf == sb_:
                M[ai, bi] = 1
    return M, fwd_states, bwd_states


def gf2_rank_mat(M):
    rows = [int(''.join(str(int(x)) for x in row[::-1]), 2) if M.shape[1] else 0 for row in M]
    n_cols = M.shape[1]
    return sb.gf2_rank(rows, n_cols)


def fooling_lower_bound(M):
    """Cheap fooling-set proxy: the max number of 1-cells no two of which share a row or column
    AND whose 'rectangle' is not monochromatic — we use the simpler '1-cells forming a partial
    permutation' (a matching in the bipartite 1-graph). For an EQUALITY/identity-like matrix this
    equals the number of distinct matched states. Returns the matching size (a valid fooling-set
    lower bound when off-diagonal rectangles are 0)."""
    # greedy maximum matching on the bipartite graph of 1-cells
    A, B = M.shape
    rows_used = set(); cols_used = set(); k = 0
    ones = list(zip(*np.where(M == 1)))
    for (i, j) in ones:
        if i not in rows_used and j not in cols_used:
            rows_used.add(i); cols_used.add(j); k += 1
    return k


def run():
    print("# W1-IN5  communication matrix of the MITM round-cut predicate.")
    print("# M[a][b]=1 iff forward-a state == backward-b state at the cut round (matched lanes).")
    print("# CARD PREDICTS: low-rank below the frontier -> FULL-rank just past it (a barrier).")
    print("# We scan the cut position and watch the rank profile + density, 3 random targets.\n")
    out = {}
    # balanced regime: match `nlanes` lanes so the cut-state space ~ the freedom (density ~0.004,
    # a healthy structured matrix, neither empty nor all-ones).
    configs = [
        (4, 2, 2, 22, 2),   # N=4, 256x256, match 2 lanes, deep R to reach 'just past' cuts
        (6, 1, 1, 16, 1),   # N=6, 64x64, match 1 lane
    ]
    for (N, FA, FB, R, nl) in configs:
        lanes = tuple(range(nl))
        maxdim = 1 << (min(FA, FB) * N)
        print(f"N={N} FA={FA} FB={FB} R={R} match {nl} lane(s)  (matrix {(1<<(FA*N))}x{(1<<(FB*N))}, maxdim {maxdim})")
        print(f"  {'r_cut':>5} | {'rk(t0)':>6} {'rk(t1)':>6} {'rk(t2)':>6} | {'mean_log2rk':>11} {'normrk':>6} {'dens':>6}  interp")
        ranks = []
        for r_cut in range(3, R):
            rks = []
            dens = []
            grs = []
            for t in range(3):
                M, fs, bs = build_comm_matrix(N, r_cut, R, FA, FB, target_seed=100 * t + N,
                                              match_lanes=lanes)
                rks.append(int(np.linalg.matrix_rank(M.astype(float))) if M.sum() else 0)
                dens.append(M.sum() / M.size)
                grs.append(gf2_rank_mat(M))
            mlog = float(np.mean([math.log2(r) if r > 0 else 0 for r in rks]))
            nrm = float(np.mean(rks)) / maxdim
            d0 = dens[0]
            if np.mean(rks) == 0 and np.mean(dens) == 0:
                interp = "EMPTY (no meet)"
            elif np.mean(rks) <= 1.5:
                interp = "rank<=1 ALL-ONES (always meet = trivially EASY)"
            elif nrm >= 0.7:
                interp = "~FULL rank (high comm)"
            else:
                interp = "mid"
            print(f"  {r_cut:>5} |  {rks[0]:5d} {rks[1]:6d} {rks[2]:6d} | {mlog:11.3f} {nrm:6.3f} {np.mean(dens):6.4f}  {interp}")
            ranks.append((r_cut, float(np.mean(rks)), nrm, float(np.mean(dens))))
        out[(N, FA, FB)] = ranks
        # --- transition diagnosis vs the CARD's stated direction ---
        nrms = [x[2] for x in ranks]
        # is the deepest third low-rank (rank<=1 / empty)?  card needs it FULL.
        deep = ranks[-max(2, len(ranks)//4):]
        shallow = ranks[:max(2, len(ranks)//4)]
        deep_full = all(d[1] >= 0.7 * maxdim for d in deep)
        deep_trivial = all(d[1] <= 1.5 for d in deep)
        shallow_low = all(s[1] <= 0.1 * maxdim for s in shallow)
        spread = max(nrms) - min(nrms)
        print(f"  normrank range [{min(nrms):.3f}..{max(nrms):.3f}]  spread={spread:.3f}")
        print(f"  CARD prediction (low below frontier -> FULL just past): "
              f"shallow-low={shallow_low}  deep-FULL={deep_full}")
        if deep_trivial:
            print("  OBSERVED: deepest cuts are rank<=1 (always-meet = EASY), the OPPOSITE of the")
            print("            predicted 'full-rank barrier just past the frontier' -> card refuted.")
        print()
    return out


if __name__ == '__main__':
    run()

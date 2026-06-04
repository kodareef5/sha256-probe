"""
W1-IN4 — 2D PEPS over the round×bit lattice → an entanglement anisotropy.

Card: the killed MPS cut 1D along BITS (carry chain => bond dim ~2^N => death). A 2D
tensor network with a tensor at each (round,bit) — horizontal bonds = carry propagation
(bit->bit), vertical = round recurrence — might be AREA-LAW across the ROUND-cut (= the
MITM cut, only ~24/256 bits cross) even where the BIT-cut is volume-law. Anisotropy.

PROBE (as stated): N=4,6 reduced-round. DON'T contract — measure boundary rank
(Renyi-0 = log2 of # distinct boundary states) for the ROUND-cut vs BIT-cut across cut
positions. Predict bit-cut ≈ 2^N (MPS death) but round-cut grows SLOWLY (area law) with a
knee near the frontier.
KILL: dead if round-cut boundary rank grows AS FAST AS the bit-cut (slope >= 0.8/round) —
brute force in every direction.

OPERATIONALIZATION (boundary rank = log2 # distinct boundary configurations):
We build the genuine N-bit reduced compression. The "freedom" that generates boundary
states is a set of FREE message words (we use the first F words; the rest frozen). The
tensor network's value on the open boundary is determined by the boundary cut.

ROUND-CUT at position r:  the boundary carries the full 8-lane state AFTER round r. The
   Renyi-0 boundary rank = log2( # DISTINCT states-after-r ) over all inputs. This is exactly
   the bond dimension a vertical MPS (rounds as sites) would need across that cut. We track it
   vs r and take the per-round slope.

BIT-CUT at position beta (a vertical line splitting bits < beta from bits >= beta, ALL rounds):
   the boundary carries, for EACH round, the carry bit crossing position beta PLUS the bit-slice
   state that must pass left<->right. The Renyi-0 bit-cut rank = log2( # distinct boundary
   "carry+slice" vectors ) over inputs. The killed-MPS claim is this ~ N (i.e. ~2^N states),
   roughly flat in beta (carry chain saturates immediately).

We compare the two SLOPES:
   slope_round = d(log2 #distinct state)/dr      [bits of boundary per added round]
   slope_bit   = d(log2 #distinct boundary)/dbeta
Card SURVIVES iff slope_round is SUBSTANTIALLY below slope_bit AND below the 0.8/round kill
line, with a knee. Card KILLED iff slope_round >= 0.8 * (a full-state growth) ~ as fast as bit.

Caveat (baked in, per the Wave-1 spine): if the round map is uniformly full-rank/expanding,
the round-cut #distinct states will saturate at the FULL input-freedom 2^{F·N} immediately
(slope = N bits/round until saturation) — i.e. NO area law -> KILLED. We measure, not assume.
"""
import sys, math, itertools, collections
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


def all_states_by_round(N, F, R, base_seed=0):
    """Enumerate all 2^(F*N) messages (first F words free, rest a fixed random fill); return,
    for each round r in 0..R, the SET of distinct full 8-lane states reached after round r."""
    m, rnd, sig0, sig1 = make_prims(N)
    rng = np.random.default_rng(base_seed)
    fill = [int(rng.integers(0, 1 << N)) for _ in range(16)]
    # precompute schedule per message lazily; we need states after each round, so run all.
    distinct = [set() for _ in range(R + 1)]
    # also track bit-cut boundary objects: for each round, the carry crossing & slice
    # We'll collect, per beta, the set of (per-round low-bits-of-a, low-bits-of-e) vectors.
    state_traces = []          # list over messages of the per-round state tuple (subsampled)
    msgs = list(itertools.product(range(1 << N), repeat=F))
    for combo in msgs:
        M = list(fill)
        for i in range(F):
            M[i] = combo[i]
        W = list(M) + [0] * (R - 16 if R > 16 else 0)
        for i in range(16, R):
            W.append(0)
        for i in range(16, R):
            W[i] = (sig1(W[i-2]) + W[i-7] + sig0(W[i-15]) + W[i-16]) & m
        st = tuple(int(v) & m for v in sb.IV[:8])
        trace = [st]
        distinct[0].add(st)
        for i in range(R):
            st = rnd(st, sb.s.K[i] & m, W[i] & m)
            distinct[i + 1].add(st)
            trace.append(st)
        state_traces.append(trace)
    return distinct, state_traces, len(msgs)


def round_cut_ranks(distinct):
    """log2 # distinct states after each round = Renyi-0 boundary rank of the round-cut at r."""
    return [math.log2(len(s)) if len(s) > 0 else 0.0 for s in distinct]


def bit_cut_ranks(N, state_traces, R, F):
    """Renyi-0 boundary rank of the BIT-cut at vertical position beta (split bits<beta from
    bits>=beta across ALL rounds). The boundary that must cross is, per round, the bit-slice of
    the two adder-lanes (a,e) at the cut and the carry into it. We approximate the crossing
    object by the per-round pair of bit-slices of (a,e) around beta: the value of bits
    {beta-1, beta} of a and e at every round (the carry chain crosses exactly there).
    Boundary rank(beta) = log2 # distinct such cross-vectors over all messages."""
    m = MASKN(N)
    ranks = []
    for beta in range(1, N):          # cut between bit beta-1 and bit beta
        boundary_set = set()
        for trace in state_traces:
            vec = []
            for st in trace:
                a, e = st[0], st[4]
                # the two bits straddling the cut for the two adder lanes (carry crosses here)
                va = ((a >> (beta - 1)) & 1) | (((a >> beta) & 1) << 1)
                ve = ((e >> (beta - 1)) & 1) | (((e >> beta) & 1) << 1)
                vec.append((va, ve))
            boundary_set.add(tuple(vec))
        ranks.append(math.log2(len(boundary_set)) if boundary_set else 0.0)
    return ranks


def run(Ns=(4, 6), F=2):
    print("# W1-IN4  PEPS anisotropy: round-cut vs bit-cut boundary rank (Renyi-0).")
    print(f"# F={F} free message words; boundary rank = log2(# distinct boundary configs).\n")
    out = {}
    for N in Ns:
        R = max(16, 12) if N <= 6 else 16
        R = 20                                  # enough rounds to see the trend
        distinct, traces, nmsg = all_states_by_round(N, F, R, base_seed=N)
        rc = round_cut_ranks(distinct)
        bc = bit_cut_ranks(N, traces, R, F)
        cap = F * N                              # max possible boundary rank (input freedom)
        print(f"N={N}  (input freedom = F*N = {cap} bits; {nmsg} messages)")
        print(f"  ROUND-CUT boundary rank log2#states after r:")
        sl_round = []
        for r in range(1, min(R, 12) + 1):
            slope = rc[r] - rc[r - 1]
            sl_round.append(slope)
            knee = " <- saturates" if abs(rc[r] - cap) < 1e-9 else ""
            print(f"     r={r:2d}: {rc[r]:6.3f}   (Δ/round = {slope:+.3f}){knee}")
        # early slope (rounds 1..4) where growth is visible
        early = [rc[r] - rc[r-1] for r in range(1, 6)]
        print(f"  BIT-CUT boundary rank log2#configs vs beta:")
        for i, beta in enumerate(range(1, N)):
            slope = bc[i] - (bc[i-1] if i > 0 else 0.0)
            print(f"     beta={beta}: {bc[i]:6.3f}   (Δ/bit = {slope:+.3f})")
        mean_round_slope = float(np.mean([s for s in early if s > 1e-9])) if any(s>1e-9 for s in early) else 0.0
        bit_max = max(bc) if bc else 0.0
        bit_slope = float(np.mean([bc[i]-(bc[i-1] if i>0 else 0) for i in range(len(bc))])) if bc else 0.0
        print(f"  --> round-cut early Δ/round (rounds 1-5)   = {mean_round_slope:.3f} bits/round")
        print(f"  --> round-cut saturates at {max(rc):.3f} (cap {cap}); reaches cap by round "
              f"{next((r for r in range(R+1) if abs(rc[r]-cap)<1e-9), None)}")
        print(f"  --> bit-cut max rank = {bit_max:.3f}, mean Δ/bit = {bit_slope:.3f}")
        # KILL test: is round-cut growth >= 0.8 of a 'full' growth? Full growth = N bits/round
        # until saturation. Normalize: slope per round relative to N.
        norm_round = mean_round_slope / N
        print(f"  KILL CHECK: round-cut slope/N = {norm_round:.3f}  "
              f"(kill if >=0.8 => grows as fast as input freedom allows = no area law)")
        out[N] = dict(rc=rc, bc=bc, cap=cap, round_slope=mean_round_slope,
                      norm=norm_round, bit_max=bit_max)
        print()
    return out


if __name__ == '__main__':
    run()

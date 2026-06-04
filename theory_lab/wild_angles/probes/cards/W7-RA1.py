"""
W7-RA1 — The 132 as a forced monochromatic core (Gallai / Hales-Jewett).  [P3]

Card claim: 2-color the bit x slot carry grid; ~132 grid cells are color-FROZEN
across (almost) all messages = the unavoidable monochromatic core, with the
hard-core output bits downstream of it; HW~74 = its density.

Probe (CATALOG): N=4..12 extract the carry matrix per message (recompute each add,
XOR sum vs XOR of addends -> carry-ins); per-cell color entropy over the sample;
count entropy ~= 0 (frozen) cells -> 132 projected? are they *contiguous*
(a sub-grid/line, the Ramsey signature) vs scattered?
Kill: frozen count grows like the FULL grid area, OR frozen cells are SCATTERED
(no line geometry) across >=3 N.
Skeptic (finding #1): HJ numbers dwarf a 32x448 grid; a frozen core at small N is
finite-size/propagation determinism, NOT asymptotic forcing; only contiguity+scaling
rescue it. And the '132' is the deterministic-control census {a,b,e,f}+4dc = 4N+4
(width-scaling) -- a frozen count that scales like ~c*N is NOT a stable basis-
independent invariant. Never CONFIRM a near-132 without a stable invariant object.

Carry matrix: for each modular add z = sum(addends) at a round, the carry-in vector
is  c[j] = z[j] XOR (XOR of addends' bit j).  We collect, per round r and per add
'slot' (h+S1+Ch+K+W -> a running 5-term add gives 4 carry vectors; T2 1; d+T1 1;
a=T1+T2 1), an N-bit carry word. Grid cell = (slot, bit). Color = the carry bit.
Frozen cell = constant across the message sample (entropy 0).

READ-ONLY toward the repo. Uses the FULL 32-bit lib primitives via shabridge for
the literal-132 question, AND the width-N engine for the scaling/contiguity test.
Throttle externally:  OMP_NUM_THREADS=2 taskpolicy -b python3 W7-RA1.py
"""
import sys, random, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s


def carry_vec(addends, N, MASK):
    """Carry-in vector of a modular add of `addends` (list of N-bit ints):
       c[j] = (sum mod 2^N)[j] XOR (XOR_k addends_k[j]).  Returns N-bit int."""
    z = 0
    for a in addends:
        z = (z + a) & MASK
    x = 0
    for a in addends:
        x ^= (a & MASK)
    return (z ^ x) & MASK


def round_carries(state, k, w, N, MASK, S0, S1, Ch, Mj):
    """All carry words produced in ONE round, as a dict slot_name -> N-bit carry.
       Mirrors the modular adds of the real round (associative left-fold)."""
    a, b, c, d, e, f, g, h = state
    s1 = S1(e); ch = Ch(e, f, g)
    s0a = S0(a); mj = Mj(a, b, c)
    carries = {}
    # T1 = h + S1 + Ch + k + w  (4 carry steps in a left fold)
    carries['T1_1'] = carry_vec([h, s1], N, MASK)               # h+S1
    p = (h + s1) & MASK
    carries['T1_2'] = carry_vec([p, ch], N, MASK)               # +Ch
    p = (p + ch) & MASK
    carries['T1_3'] = carry_vec([p, k], N, MASK)                # +K
    p = (p + k) & MASK
    carries['T1_4'] = carry_vec([p, w], N, MASK)                # +W
    T1 = (p + w) & MASK
    # T2 = S0 + Maj
    carries['T2'] = carry_vec([s0a, mj], N, MASK)
    T2 = (s0a + mj) & MASK
    # e_new = d + T1 ; a_new = T1 + T2
    carries['e_add'] = carry_vec([d, T1], N, MASK)
    carries['a_add'] = carry_vec([T1, T2], N, MASK)
    new = ((T1 + T2) & MASK, a, b, c, (d + T1) & MASK, e, f, g)
    return new, carries


SLOTS = ['T1_1', 'T1_2', 'T1_3', 'T1_4', 'T2', 'e_add', 'a_add']  # 7 carry slots/round


def make_model(N):
    MASK = (1 << N) - 1
    def sr(k32): return max(1, round(k32 * N / 32.0))
    rS0 = [sr(2), sr(13), sr(22)]; rS1 = [sr(6), sr(11), sr(25)]
    KN = [k & MASK for k in s.K]; IVN = [v & MASK for v in s.IV]
    rs0 = [sr(7), sr(18)]; ss0 = sr(3); rs1 = [sr(17), sr(19)]; ss1 = sr(10)
    def ror(x, k): k %= N; return ((x >> k) | (x << (N - k))) & MASK
    def S0(a): return ror(a, rS0[0]) ^ ror(a, rS0[1]) ^ ror(a, rS0[2])
    def S1(e): return ror(e, rS1[0]) ^ ror(e, rS1[1]) ^ ror(e, rS1[2])
    def sg0(x): return ror(x, rs0[0]) ^ ror(x, rs0[1]) ^ ((x >> ss0) & MASK)
    def sg1(x): return ror(x, rs1[0]) ^ ror(x, rs1[1]) ^ ((x >> ss1) & MASK)
    def Ch(e, f, g): return ((e & f) ^ ((~e) & g)) & MASK
    def Mj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & MASK
    return dict(N=N, MASK=MASK, KN=KN, IVN=IVN, S0=S0, S1=S1, sg0=sg0, sg1=sg1, Ch=Ch, Mj=Mj)


def carry_grid_for_message(M, Mmsg, n_rounds=64):
    """Return dict (round, slot) -> N-bit carry word, over n_rounds rounds from IV."""
    N, MASK = M['N'], M['MASK']
    W = [Mmsg[i] & MASK for i in range(16)] + [0] * (n_rounds - 16 if n_rounds > 16 else 0)
    for i in range(16, n_rounds):
        W[i] = (M['sg1'](W[i-2]) + W[i-7] + M['sg0'](W[i-15]) + W[i-16]) & MASK
    st = tuple(M['IVN'])
    grid = {}
    for r in range(n_rounds):
        st, carries = round_carries(st, M['KN'][r], W[r], N, MASK,
                                    M['S0'], M['S1'], M['Ch'], M['Mj'])
        for slot in SLOTS:
            grid[(r, slot)] = carries[slot]
    return grid


def frozen_analysis(N, n_msgs=400, n_rounds=64, seed=0):
    """Sample messages, collect carry grids, find FROZEN cells (constant carry bit
    across all sampled messages). Cell = (round, slot, bit). Return frozen set +
    geometry stats."""
    M = make_model(N)
    rng = random.Random(seed + N)
    MASK = M['MASK']
    # accumulate per-cell value sets
    cells = {}  # (r,slot,bit) -> set of observed bits
    for _ in range(n_msgs):
        Mmsg = [rng.randint(0, MASK) for _ in range(16)]
        grid = carry_grid_for_message(M, Mmsg, n_rounds)
        for (r, slot), cw in grid.items():
            for j in range(N):
                bit = (cw >> j) & 1
                key = (r, slot, j)
                cset = cells.get(key)
                if cset is None:
                    cells[key] = {bit}
                elif bit not in cset:
                    cset.add(bit)
    total_cells = n_rounds * len(SLOTS) * N
    frozen = [k for k, v in cells.items() if len(v) == 1]
    return M, frozen, total_cells, cells


def contiguity(frozen, n_rounds, N):
    """Quantify whether frozen cells form a LINE / sub-grid (Ramsey signature) vs
    scattered. Heuristic measures:
      * fraction of frozen cells whose grid-neighbor (same slot, adjacent round, or
        same round, adjacent bit) is also frozen -> high => contiguous block.
      * how concentrated by round (are frozen cells localized to a few rounds?).
    """
    F = set(frozen)
    if not F:
        return dict(neighbor_frac=0.0, rounds_used=0, by_round={})
    nbr = 0; deg = 0
    for (r, slot, j) in F:
        for dr, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            deg += 1
            if (r + dr, slot, j + dj) in F:
                nbr += 1
    by_round = {}
    for (r, slot, j) in F:
        by_round[r] = by_round.get(r, 0) + 1
    return dict(neighbor_frac=nbr / deg if deg else 0.0,
                rounds_used=len(by_round), by_round=by_round)


if __name__ == '__main__':
    print("W7-RA1 — frozen carry-grid cells vs the 132 hard-core; scaling + contiguity\n")
    print(f"Ground truth: 132 = {{a,b,e,f}}@63 (4N at width N) + 4 dc = 4N+4. "
          f"Total carry-grid cells = 64 rounds x {len(SLOTS)} slots x N.\n")
    rows = []
    for N in (4, 6, 8, 10, 12):
        M, frozen, total, cells = frozen_analysis(N, n_msgs=500, n_rounds=64, seed=3)
        geo = contiguity(frozen, 64, N)
        nf = len(frozen)
        rows.append((N, nf, total, geo))
        # predicted census-style values for comparison
        print(f"N={N:>2}: frozen carry cells = {nf:>4} / {total} total "
              f"(grid is 64x{len(SLOTS)}x{N})")
        print(f"      4N+4 (census) = {4*N+4}   |   132? {'~' if abs(nf-132)<=8 else 'no'}")
        print(f"      contiguity: neighbor_frac={geo['neighbor_frac']:.3f} "
              f"(1.0=solid block, ~0=scattered); rounds spanned={geo['rounds_used']}/64")
        # show which rounds hold frozen cells (localization)
        br = sorted(geo['by_round'].items())
        print(f"      frozen-by-round (nonzero): {br[:12]}{' ...' if len(br)>12 else ''}\n")

    print("=== SCALING TEST: does frozen count scale like grid AREA, like c*N, or flat? ===")
    Ns = [r[0] for r in rows]; nfs = [r[1] for r in rows]; totals = [r[2] for r in rows]
    for (N, nf, total, geo) in rows:
        print(f"  N={N:>2}: frozen={nf:<5} grid_area={total:<6} frac_of_area={nf/total:.3f} "
              f"4N+4={4*N+4}")
    # linear fit frozen ~ alpha*N + beta
    n = len(Ns); sx = sum(Ns); sy = sum(nfs); sxx = sum(x*x for x in Ns); sxy = sum(x*y for x,y in zip(Ns,nfs))
    denom = (n*sxx - sx*sx)
    if denom:
        alpha = (n*sxy - sx*sy)/denom; beta = (sy - alpha*sx)/n
        print(f"\n  linear fit: frozen ~ {alpha:.2f}*N + {beta:.2f}")
        print(f"  ratio frozen/area across N: "
              f"{['%.3f'%(nf/tot) for (_,nf,tot,_) in rows]}  "
              f"(rising => scales with area => KILL prong 1)")
    avg_nbr = sum(g['neighbor_frac'] for (_,_,_,g) in rows)/len(rows)
    print(f"\n  mean neighbor_frac (contiguity) across N = {avg_nbr:.3f}")
    print("  KILL prong A fires if frozen ~ grid AREA (frac_of_area rising / not flat-small).")
    print("  KILL prong B fires if frozen cells SCATTERED (neighbor_frac low) across >=3 N.")
    print("  finding #1: a frozen count tracking ~c*N (width-scaling census), not a")
    print("  STABLE basis-independent 132, is a CATEGORY-ERROR match -> not CONFIRM.")

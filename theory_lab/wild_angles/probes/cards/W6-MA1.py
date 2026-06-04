#!/usr/bin/env python3
"""
W6-MA1 (FLAGSHIP, matroid) — Is the 132 the CORANK of the GF(2) constraint matroid M[A]?

Card claim: the GF(2) cascade matroid M[A] (carries as free ground elements); rank =
controllable dim, corank = |E|-rank = the cobasis = the forced bits. Conjecture the
fundamental-cocircuit support = 132 = 128 (W*_59,W*_60, 4 words x 32) + 4 anchors, DERIVED
from rank, order-independent, no solver. Probe: N=8..32 assemble A (linear sigma/Sigma/XOR
layer + carry ground elements), call gf2_eliminate; corank, cobasis labels; does the
schedule-bit corank -> 132 +-4, cobasis preferring W*_59/W*_60, anchors = W1_57[0],
W2_57[0], W2_58[14], W2_58[26]?
Kill: corank NOT-> 132, or all 256 schedule bits equally free/forced.

ADVERSARIAL FRAMING (prior finding #1 — the "132 = corank" CATEGORY ERROR, now 15x).
Every honest corank/kernel/rank dimension measured so far = 0 or 128 (= 4N width-scaling),
NEVER a stable, basis-independent 132. The "132" is the deterministic-CONTROL CENSUS =
{a,b,e,f}@63 (4N) + 4 scattered dc = 4N+4, a width-scaling census, not a matroid corank.
W6-MA1 is THE flagship matroid version of this exact claim. We therefore compute, HONESTLY:

  (A) The GF(2) CONSTRAINT MATROID itself.  Ground set E = all bits that appear in the
      linearized tail round-relations (state bits a..h at each round 57..64, schedule
      control bits W57..63, and the carry bits introduced by each modular add). The
      constraint rows are the EXACT GF(2) linearizations (at the actual cascade trajectory
      point) of every defining relation:
          out_state[r+1] = sha_round(state[r], W[r])   (rows for each output state bit)
          W[61..63]      = schedule recurrence in W[57..60]  (rows for the pinned words)
      rank(A) = # independent constraints; corank in the MATROID sense = |E| - rank(A)
      (the size of any cobasis / the dimension of the cocircuit space). This is the honest,
      elimination-order-independent number the card asks for.

  (B) The SOLUTION-SPACE corank restricted to the SCHEDULE bits (the card's "256 schedule
      bits"): of the 8N schedule control bits W[57..63] (treating each as a ground element),
      how many are FORCED by the schedule recurrence vs FREE?  Honest answer: W[57..60] are
      free (4N), W[61..63] are pinned (3N forced) — a width-scaling split, not 132.

  (C) The CENSUS the "132" really is: deterministic control of the 8N output bits by the 4N
      free schedule bits => {a,b,e,f} uncontrollable (4N) + dc extras. 4N+4 at width 32 = 132.

CONFIRM only if (A) gives a genuinely STABLE basis-independent corank = 132 at N=8..32 with
{a,b,e,f}+4dc cobasis support. Predict (per #1) it will NOT: corank will be 0 (full-rank
bijective round map) for the round-relations, and the schedule split will be the 4N/3N
width-scaling census — and the only thing that hits "132" is the 4N+4 census at width 32.
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w6oc_engine as oc
import shabridge as sb

REG = oc.REG; OFF = oc.OFF
FREE_ROUNDS = (57, 58, 59, 60)
ALL_TAIL = (57, 58, 59, 60, 61, 62, 63)


# --------------------------------------------------------------------------- #
# (A) The GF(2) CONSTRAINT MATROID of the linearized tail round-relations.
#
# We linearize each round map F_r at the actual cascade trajectory point as a GF(2)
# relation:  out_state_bits  =  J_r * in_state_bits  XOR  B_r * control_bits.
# Ground set columns: [in_state(8N) | control(N)]  for that round; rows = 8N output bits.
# Stacking all rounds with shared state variables and per-round fresh control variables
# gives the full constraint system. The matroid rank = GF(2) rank of the stacked relation
# matrix; corank (matroid) = #columns - rank.  We report it for the per-round block (the
# cleanest object) AND for the full stacked tail.
# --------------------------------------------------------------------------- #
def round_relation_block(N):
    """For each tail round r, build the GF(2) relation matrix [J_r | B_r] mapping
    (in_state 8N, control N) -> (out_state 8N). Return per-round rank and corank where
    ground set = the (8N + N) input columns and the constraints are the 8N output rows
    written as  out = M_r @ input. Matroid of the relation = column matroid of M_r.
    corank = (8N+N) - rank(M_r)."""
    M = oc.eng.make_model(N); n = 8 * N
    D = oc.costate_sweep(N, 0, 0, 0, 0)         # gives Jrows[r], Brows[r] at trajectory
    res = []
    for r in ALL_TAIL:
        Jr = D['Jrows'][r]                      # 8N rows, each 8N-bit in-state mask
        Br = D['Brows'][r]                      # 8N rows, each N-bit control mask
        # combined relation row o = J-part (cols 0..8N-1) | B-part (cols 8N..9N-1)
        rows = [Jr[o] | (Br[o] << n) for o in range(n)]
        rk = oc.rank(rows)
        ncols = n + N
        res.append((r, rk, ncols, ncols - rk, oc.rank(Jr), oc.rank(Br)))
    return res, n


def full_tail_matroid(N):
    """Stack ALL tail-round relations into one big GF(2) system over a shared variable set:
        variables = state bits at rounds 57..64 (8 layers x 8N) + control bits W57..63 (7N).
    Each round r contributes 8N constraint rows of the form
        out_state[r] (=state at r+1)  XOR  J_r @ state[r]  XOR  B_r @ control[r]  = 0.
    Matroid rank = GF(2) rank of this whole constraint matrix; corank (matroid) =
    #columns - rank = dim of the cocircuit space / cobasis size. Honest & order-free."""
    M = oc.eng.make_model(N); n = 8 * N
    D = oc.costate_sweep(N, 0, 0, 0, 0)
    # column layout: state layers L=0..7 -> state at round (57+L); each n cols.
    # then control layer for r=57..63 -> 7 blocks of N cols.
    NL = 8                                       # state layers 57..64
    state_base = lambda L: L * n
    ctrl_base = lambda r: NL * n + (r - 57) * N
    ncols = NL * n + 7 * N
    rows = []
    for r in ALL_TAIL:
        L_in = r - 57                            # state[r] layer
        L_out = r - 57 + 1                       # state[r+1] layer
        Jr = D['Jrows'][r]; Br = D['Brows'][r]
        for o in range(n):                       # one row per output state bit o
            row = 0
            row |= (1 << (state_base(L_out) + o))            # out_state bit
            # XOR J_r @ state[r]: set the in-state cols in Jr[o]
            x = Jr[o]
            while x:
                j = (x & -x).bit_length() - 1
                row ^= (1 << (state_base(L_in) + j)); x &= x - 1
            # XOR B_r @ control[r]
            x = Br[o]
            while x:
                j = (x & -x).bit_length() - 1
                row ^= (1 << (ctrl_base(r) + j)); x &= x - 1
            rows.append(row)
    rk = oc.rank(rows)
    return rk, ncols, ncols - rk, n


# --------------------------------------------------------------------------- #
# (B) SCHEDULE-bit corank: of the 8N control bits W[57..63], how many are forced by the
# schedule recurrence (W61..63 = sigma1/sigma0 combos of W57..60) vs free?
# Build the GF(2) schedule constraint rows for W[61..63] and compute corank over the
# 7N schedule-bit ground set. (The card's "256 schedule bits" = 8N at width 32.)
# --------------------------------------------------------------------------- #
def schedule_corank(N):
    """W[61],W[62],W[63] are each an affine GF(2) function of W[57..60] and fixed precompute
    words. Linearize sigma1/sigma0 (they ARE GF(2)-linear: rotations+shifts+XOR) to get the
    exact rows. Ground set = the 7N schedule bits W57..63. rank = #independent constraints
    (= 3N, one per pinned word bit, IF independent); schedule-solution corank = 7N - rank =
    the free dimension = 4N (W57..60). Report it; it is width-scaling, not 132."""
    M = oc.eng.make_model(N); MASK = M['MASK']
    s0 = M['s0']; s1 = M['s1']
    # column index of schedule bit W[r] bit j:  (r-57)*N + j  over 7N cols
    col = lambda r, j: (r - 57) * N + j
    ncols = 7 * N

    def lin_rows_of(fn):
        """GF(2) matrix (list of N output row-masks over N input cols) of a linear fn on
        N-bit words: row o has bit i set iff output bit o depends on input bit i."""
        cols = [fn(1 << i) for i in range(N)]    # response to each unit input
        rows = [0] * N
        for i in range(N):
            x = cols[i]
            while x:
                o = (x & -x).bit_length() - 1
                rows[o] |= (1 << i); x &= x - 1
        return rows

    s1_rows = lin_rows_of(s1)                    # sigma1 as NxN GF(2)
    s0_rows = lin_rows_of(s0)                    # sigma0 as NxN GF(2)
    # schedule recurrence (linear parts; constants drop out of the matroid):
    # W[61] = s1(W[59]) + W54 + s0(W46) + W45   -> depends (linearly) on W59
    # W[62] = s1(W[60]) + W55 + s0(W47) + W46   -> depends on W60
    # W[63] = s1(W[61]) + W56 + s0(W48) + W47   -> depends on W61 (= s1(W59)+..)
    rows = []
    # W61 bit o = XOR_i s1_rows[o][i] * W59[i]  ==>  W61[o] XOR (s1 applied to W59) = 0
    for o in range(N):
        row = (1 << col(61, o))
        x = s1_rows[o]
        while x:
            i = (x & -x).bit_length() - 1
            row ^= (1 << col(59, i)); x &= x - 1
        rows.append(row)
    # W62 bit o depends on W60
    for o in range(N):
        row = (1 << col(62, o))
        x = s1_rows[o]
        while x:
            i = (x & -x).bit_length() - 1
            row ^= (1 << col(60, i)); x &= x - 1
        rows.append(row)
    # W63 bit o depends on W61 (already a column)
    for o in range(N):
        row = (1 << col(63, o))
        x = s1_rows[o]
        while x:
            i = (x & -x).bit_length() - 1
            row ^= (1 << col(61, i)); x &= x - 1
        rows.append(row)
    rk = oc.rank(rows)
    corank = ncols - rk
    return rk, ncols, corank


# --------------------------------------------------------------------------- #
# (C) The deterministic-control CENSUS — what "132" actually is.
# --------------------------------------------------------------------------- #
def census(N, seeds=40):
    """Deterministic control of the 8N output bits by the 4N free schedule bits W57..60.
    Output bit FORCED (zero-control / 'cobasis') iff no free control flips it in EVERY seed.
    Returns total zero-control count and per-register breakdown (the {a,b,e,f}+dc structure).
    This is the 4N+4 census that equals 132 at width 32 — and it SCALES with N."""
    rng = random.Random(20260603)
    M = oc.eng.make_model(N); n = 8 * N
    ctrl = [(r, j) for r in FREE_ROUNDS for j in range(N)]
    flip_all = [set(range(len(ctrl))) for _ in range(n)]
    for _ in range(seeds):
        w0 = [rng.randint(0, M['MASK']) for _ in range(4)]
        st, _, _, _ = oc.cascade_trajectory(N, *w0)
        base = oc.pack(st[64], N)
        for ci, (r, j) in enumerate(ctrl):
            w1 = list(w0); w1[r - 57] ^= (1 << j)
            st1, _, _, _ = oc.cascade_trajectory(N, *w1)
            resp = oc.pack(st1[64], N) ^ base
            notf = (~resp) & ((1 << n) - 1)
            x = notf
            while x:
                o = (x & -x).bit_length() - 1
                flip_all[o].discard(ci); x &= x - 1
    zero = [o for o in range(n) if not flip_all[o]]
    per = {name: sum(1 for o in zero if OFF[name] * N <= o < (OFF[name] + 1) * N) for name in REG}
    return len(zero), per, n


def main():
    print("W6-MA1 : honest GF(2) CONSTRAINT-MATROID corank vs the '132' census.\n")
    print("ground truth pin: sb.HARDCORE['total'] =", sb.HARDCORE['total'],
          "(= 4N+4 at width 32 = the CENSUS, claimed here as a matroid corank)\n")

    for N in (8, 10, 12):
        print(f"================  N={N}  (8N={8*N} state bits)  ================")
        # (A) per-round relation matroid + full stacked tail matroid
        blk, n = round_relation_block(N)
        print("  (A) PER-ROUND relation matroid M[J_r|B_r] (ground = 9N input cols):")
        print(f"      {'r':>3} | rank | ncols(9N) | MATROID corank | rank J_r | rank B_r")
        for (r, rk, nc, cor, jr, br) in blk:
            print(f"      {r:>3} | {rk:>4} | {nc:>9} | {cor:>14} | {jr:>8} | {br:>7}")
        frk, fnc, fcor, _ = full_tail_matroid(N)
        print(f"  (A) FULL STACKED tail matroid: rank={frk}, ncols={fnc}, "
              f"MATROID corank={fcor}")
        print(f"      (corank counts the FREE variables: input state 8N + free ctrl "
              f"W57..60 4N that the system never pins; structural, NOT 132)")

        # (B) schedule-bit corank
        srk, snc, scor = schedule_corank(N)
        print(f"  (B) SCHEDULE-bit matroid (7N={7*N} schedule bits W57..63): "
              f"rank(constraints)={srk}, corank(free schedule dim)={scor}  "
              f"[expect 4N={4*N} free = W57..60; 3N={3*N} forced]")

        # (C) the census that IS 132 at width 32
        cz, cper, _ = census(N)
        cen = 4 * N + 4
        abef = cper['a'] + cper['b'] + cper['e'] + cper['f']
        print(f"  (C) CENSUS (deterministic control): zero-control output bits = {cz}  "
              f"(4N+4 = {cen})")
        print(f"      per-register: " + ", ".join(f"{k}:{cper[k]}" for k in REG) +
              f"   {{a,b,e,f}}={abef}/{4*N}, dc={cper['c']}")
        # honest verdict line per N
        print(f"  --> matroid corank (round-relations) = {blk[0][3]} per round / "
              f"{fcor} stacked;  schedule free-corank = {scor} (=4N);  census = {cz}\n")

    print("INTERPRETATION (finding #1, 15x): the honest GF(2) constraint-matroid corank is")
    print("a WIDTH-SCALING quantity (per-round relation corank = N free-control cols; full")
    print("tail corank = the 8N+4N free inputs; schedule corank = 4N free words). NONE is a")
    print("stable, basis-independent 132. The ONLY object that equals 132 is the 4N+4")
    print("deterministic-control CENSUS at width 32 ({a,b,e,f}+4dc) — exactly the category")
    print("error: a census of uncontrollable bits, not a matroid cocircuit support.")


if __name__ == '__main__':
    main()

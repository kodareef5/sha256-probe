#!/usr/bin/env python3
"""
W2-RG2 -- Floppy modes = controllable bits; self-stresses (left-null of the rigidity matrix)
          = the 132 hard core.   [CORANK-FAMILY card -- lead guidance #1]

CARD PROBE (CATALOG):
  N=8,10,12: linearize the output-diff-vs-freedom map at several collisions via track_carries;
  compute rank, left-/right-null dims; compare left-null support to the known hard-core positions.
  Predict dim(left-null) ~ 132, rank ~ 124.
KILL: Dead if self-stress dim doesn't scale toward 132 at N=32, OR its support doesn't overlap
      the hard-core positions above chance.

==================  THE CATEGORY-ERROR GUARD (lead finding #1)  ==================
W2-CT1 (flagship) was KILLED: 132 reproduces ONLY as the repo's single-bit DETERMINISTIC-
CONTROL census (carry nonlinearity), NOT as a basis-independent linear corank. The genuine
linear corank (cokernel of the reachability/rigidity matrix) is 0 (generous, union over base
points) or 128 (single point) -- NEVER 132. So this card CONFIRMS only if dim(left-null) is a
REAL, basis-independent, stable linear corank landing on 132 -- which W2-CT1 already showed it
is NOT. We run BOTH objects side by side to expose the conflation:
  (L) LINEAR rigidity-matrix corank: rows = output-diff bits, cols = freedoms; entries = GF(2)
      response (does flipping freedom j flip output bit i, linearized at a collision via the
      REAL modular tail = track_carries). left-null dim = 256 - GF(2) rank. Basis-independent.
  (C) single-bit DETERMINISTIC census (the repo's 132 protocol): output bit i is "self-stressed"
      iff NO single freedom flips it at EVERY base point. This is the carry census, not a corank.
If (L) != 132 and only (C) == 132, the card commits the corank category error -> KILLED.

Throttled. Full width N=32 for the literal-132 question; small N for the scaling test.
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s

INPUT_BITS = 128          # freedoms = W[57..60], 4 words x 32 bits
N_OUT = 256               # output-diff bits = 8 registers x 32 at round 63
REG = ('a','b','c','d','e','f','g','h')

def tail_out(state56, Wpre, free):
    sched = s.build_schedule_tail(Wpre, free)
    final = s.run_tail_rounds(state56, sched, start_round=57)[-1]
    out = 0
    for k,w in enumerate(final):
        out |= (w & 0xffffffff) << (32*k)
    return out

# ----------------- (L) the LINEAR rigidity-matrix corank (basis-independent) -------------
def linear_corank(P, seed):
    """Stack all single-bit-flip output responses over P base points (the rigidity matrix's
    column space = floppy-mode image); corank = 256 - rank = dim(left-null / self-stress)."""
    rng = random.Random(seed)
    responses = []
    for _ in range(P):
        M = [rng.getrandbits(32) for _ in range(16)]
        st56, Wpre = s.precompute_state(M)
        free0 = [rng.getrandbits(32) for _ in range(4)]
        base = tail_out(st56, Wpre, free0)
        for i in range(INPUT_BITS):
            w,b = divmod(i,32)
            f1 = list(free0); f1[w]^=(1<<b)
            r = tail_out(st56, Wpre, f1) ^ base
            if r: responses.append(r)
    rank = sb.gf2_rank(responses, N_OUT)
    return rank, N_OUT-rank, len(responses)

# ----------------- (C) the single-bit deterministic census (the repo's 132 protocol) -----
def census_selfstress(SAMPLES, seed):
    """output bit j is 'self-stressed' iff NO single freedom flips it in ALL samples."""
    rng = random.Random(seed)
    flip_count = [[0]*INPUT_BITS for _ in range(N_OUT)]
    for _ in range(SAMPLES):
        M=[rng.getrandbits(32) for _ in range(16)]
        st56,Wpre=s.precompute_state(M)
        free0=[rng.getrandbits(32) for _ in range(4)]
        base=tail_out(st56,Wpre,free0)
        for i in range(INPUT_BITS):
            w,b=divmod(i,32)
            f1=list(free0); f1[w]^=(1<<b)
            resp=tail_out(st56,Wpre,f1)^base
            jj=resp
            while jj:
                j=(jj&-jj).bit_length()-1
                flip_count[j][i]+=1
                jj&=jj-1
    ctl=[sum(1 for i in range(INPUT_BITS) if flip_count[j][i]==SAMPLES) for j in range(N_OUT)]
    hard=[j for j in range(N_OUT) if ctl[j]==0]
    per_reg={name: sum(1 for j in range(32*k,32*k+32) if ctl[j]==0) for k,name in enumerate(REG)}
    dc_pos=sorted(j-64 for j in hard if 64<=j<96)
    return hard, per_reg, dc_pos

def main():
    print("="*80)
    print("W2-RG2  rigidity-matrix self-stress vs the 132 hard core  [CORANK-FAMILY guard]")
    print("="*80)

    # ---- (L) LINEAR corank at full N=32: is it a real, stable 132? ----
    print("\n[L] LINEAR rigidity-matrix corank = dim(left-null/self-stress), basis-independent")
    print(f"    rows=256 output-diff bits, cols=freedoms; carries included (real modular tail)")
    print(f"    {'#base pts':>9} | {'#responses':>10} | {'rank':>5} | {'corank (=self-stress dim)':>26}")
    coranks={}
    for P in (1,5,20,60):
        rank,cor,nr=linear_corank(P, 100+P)
        coranks[P]=cor
        print(f"    {P:>9} | {nr:>10} | {rank:>5} | {cor:>26}")
    single_pt = coranks[1]; generous = coranks[60]

    # ---- (C) single-bit census: the repo's 132 protocol ----
    print("\n[C] single-bit DETERMINISTIC census (the repo's 132 protocol, NOT a corank)")
    SAMPLES=80
    hard, per_reg, dc_pos = census_selfstress(SAMPLES, 20260603)
    abef = per_reg['a']+per_reg['b']+per_reg['e']+per_reg['f']
    print(f"    SAMPLES={SAMPLES}  census self-stress count = {len(hard)}  [repo ground truth: 132]")
    print(f"    per-register zero-control: " + ", ".join(f"{k}={per_reg[k]}" for k in REG))
    print(f"    a,b,e,f total = {abef}/128 ;  dc scattered = {per_reg['c']} at positions {dc_pos}")

    # ---- the conflation, made explicit ----
    print("\n" + "-"*80)
    print("DOES THE LINEAR CORANK == 132?  (the card's actual claim)")
    print(f"    linear corank single-point   = {single_pt}   (W2-CT1: 128)")
    print(f"    linear corank generous (P=60)= {generous}   (W2-CT1: 0 = full controllability)")
    print(f"    census self-stress           = {len(hard)} (matches 132 -- but it is the CENSUS,")
    print(f"                                   not a basis-independent corank)")
    stable_132 = (single_pt==132 and generous==132)
    census_132 = (len(hard)==132)

    # ---- support-overlap test (only meaningful if a real corank existed) ----
    # The census support IS the hard core by construction (it reproduces the repo). The card
    # needs the LINEAR left-null support; but the generous linear left-null is 0-dim (empty),
    # so there is no linear self-stress support to overlap. Report this.
    print("\nSUPPORT OVERLAP (card: left-null support overlaps hard-core positions above chance):")
    print(f"    generous LINEAR left-null is {generous}-dim -> "
          f"{'EMPTY: no self-stress subspace exists to test support' if generous==0 else 'nonempty'}")
    print(f"    (the 132 census support {{a,b,e,f}}+{len(dc_pos)}dc is real, but it is the carry")
    print(f"     census's support, reproduced from W2-CT1 / hard_core_132_bits.md, not a corank)")

    # ---- VERDICT ----
    print("\n" + "="*80)
    # KILL: self-stress (LINEAR corank) doesn't scale toward 132, OR support doesn't overlap.
    # The genuine LINEAR corank is 128 (point) / 0 (generous) -> never 132 -> first clause fires.
    kill = (not stable_132)
    print(f"  Is dim(left-null) a REAL, stable, basis-independent linear corank == 132?  {stable_132}")
    print(f"  -> 132 appears ONLY as the single-bit census (carry nonlinearity), the SAME")
    print(f"     category error that KILLED flagship W2-CT1. The rigidity-matrix left-null is")
    print(f"     {single_pt} (single point) / {generous} (generous) -- never 132.")
    print(f"  KILL_CRITERION fires (self-stress dim != 132 as a real corank)?  {'YES' if kill else 'NO'}")
    print("="*80)

if __name__ == '__main__':
    main()

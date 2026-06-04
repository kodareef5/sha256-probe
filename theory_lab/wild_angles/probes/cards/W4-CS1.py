#!/usr/bin/env python3
"""
W4-CS1 -- "The 132 hard-core = do-orphans of the cascade mutilation".

CARD CLAIM: the cascade replaces M2's free edges with M2:=cascade(M1) -- exactly
Pearl's do()-surgery on the twin-world difference DAG. A *do-orphan* = an output-diff
bit whose EVERY path-in is severed (no admissible *exogenous* intervention can move it)
-> conjecturally the 132 (124 reachable -> HW~74). Kill: orphan count !-> 132 (~0/256) or
wildly intervention-set-dependent.

CRITICAL PRIOR (#1 + W2-CT1 KILLED verdict): "132 = corank" is a CATEGORY ERROR. The
canonical corank card W2-CT1 found the *genuine* basis-independent corank = 0/128 (full
controllability), never 132; the only way to GET 132 is the single-bit DETERMINISTIC-
CONTROL census, which is sample-dependent (132 in the writeup, 138 in a 48-base sample).
So CS1 is CONFIRM-able ONLY if a REAL causal-orphan/intervention count (a bit that NO
exogenous do() can move) lands on a stable 132 with {a,b,e,f}+4dc support. If it lands on
~0, CS1 is re-running the census (rename, not a do-orphan mechanism) -> KILL.

THE DECISIVE DISTINCTION this probe draws:
  (A) DO-ORPHAN (the card's actual object): output-diff bit b is an orphan iff for EVERY
      admissible exogenous do(W_j := v) (j in the free tail words, v any value), the
      output-DIFFERENCE bit b is UNCHANGED from baseline. I.e. NO intervention -- single
      OR joint, any value -- reaches b. This is the union-over-interventions reachability
      (a "severed every path-in" count). Pearl-faithful: we intervene on the twin-world
      difference DAG only on exogenous (free-schedule) words.
  (B) DETERMINISTIC-CONTROL CENSUS (the repo's 132): bit b is "hard" iff NO single input
      bit flip flips b at EVERY base-point. A WEAKER condition than (A): a bit can be a
      non-orphan (some joint/any-value intervention moves it) yet still census-hard
      (no single bit moves it deterministically). So (B)>=(A) always.

If the card's "do-orphan" (A) = 132, that's a genuine new invariant. If (A)~0 while only
(B)~132, CS1 has relabeled the census. We compute BOTH on the SAME real cascade tail.

We use full-width N=32 (the 132 is a 32-bit phenomenon; the card names "256" output bits)
and reuse lib.sha256 via shabridge (precompute_state / build_schedule_tail / run_tail_rounds),
exactly as W2-CT1 did, so the census arm reproduces the repo number as a control.

Run throttled:  OMP_NUM_THREADS=2 taskpolicy -b python3 W4-CS1.py    (~30-60s)
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s

REG = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')
N_OUT = 256                 # 8 registers x 32 bits at round 63
FREE_WORDS = 4              # W[57..60] are the exogenous (free) tail words
INPUT_BITS = FREE_WORDS * 32

def out63_packed(state56, Wpre, free):
    """Round-63 output register state (a..h) packed into a 256-bit int (single path)."""
    sched = s.build_schedule_tail(Wpre, free)
    f = s.run_tail_rounds(state56, sched, start_round=57)[-1]
    out = 0
    for k in range(8):
        out |= (f[k] & 0xffffffff) << (32 * k)
    return out

def out63_pair(state56_1, Wpre1, free1, state56_2, Wpre2, free2):
    """Round-63 output-DIFFERENCE (XOR) as a 256-bit int, for the twin world.
    Path 1 uses (state56_1, Wpre1, free1); path 2 uses (state56_2, Wpre2, free2)."""
    out = 0
    f1 = s.run_tail_rounds(state56_1, s.build_schedule_tail(Wpre1, free1), start_round=57)[-1]
    f2 = s.run_tail_rounds(state56_2, s.build_schedule_tail(Wpre2, free2), start_round=57)[-1]
    for k in range(8):
        out |= ((f1[k] ^ f2[k]) & 0xffffffff) << (32 * k)
    return out

def main():
    rng = random.Random(20260603)
    # ---- Build a TWIN WORLD: two messages M1,M2 sharing the same exogenous free tail
    # words, with a nonzero baseline message difference (so the difference DAG is live).
    # The cascade-mutilation analog at full width: path 2's *precompute* differs from
    # path 1's (different M), but BOTH paths receive the SAME exogenous do(W[57..60]) --
    # this is exactly do()-surgery that pins the free edges to a common value across twins,
    # leaving only the (severed-or-not) difference structure in the tail.
    BASES = 24                # base difference-configs (twin pairs) for (A)
    # (A) DO-ORPHAN tally: out-diff bit b is "reached" if SOME exogenous intervention moves it
    reached_anyintervention = [False] * N_OUT
    INTERV_PER_BASE = 96      # random exogenous joint interventions (any value) per base, for (A)

    for _ in range(BASES):
        M1 = [rng.getrandbits(32) for _ in range(16)]
        M2 = list(M1); M2[rng.randrange(16)] ^= (1 << rng.randrange(32))  # nonzero msg diff
        st1, Wp1 = s.precompute_state(M1)
        st2, Wp2 = s.precompute_state(M2)
        free0 = [rng.getrandbits(32) for _ in range(FREE_WORDS)]
        base = out63_pair(st1, Wp1, free0, st2, Wp2, free0)

        # (A) any-value exogenous interventions on the SHARED free tail; ALSO single-word set-to-v.
        # Pearl-faithful do(W_j := v): pin one or all free words to a fresh value across BOTH twins,
        # recompute the output-DIFFERENCE; if any out-diff bit changes vs baseline, that bit is reached.
        for _t in range(INTERV_PER_BASE):
            free1 = [rng.getrandbits(32) for _ in range(FREE_WORDS)]  # joint do(W57..60 := v)
            resp = out63_pair(st1, Wp1, free1, st2, Wp2, free1) ^ base  # change in the DIFFERENCE
            jj = resp
            while jj:
                b = (jj & -jj).bit_length() - 1
                reached_anyintervention[b] = True
                jj &= jj - 1
        for wj in range(FREE_WORDS):            # single-word do(W_{57+wj} := v), several values
            for _v in range(8):
                free1 = list(free0); free1[wj] = rng.getrandbits(32)
                resp = out63_pair(st1, Wp1, free1, st2, Wp2, free1) ^ base
                jj = resp
                while jj:
                    b = (jj & -jj).bit_length() - 1
                    reached_anyintervention[b] = True
                    jj &= jj - 1

    # ---- (B) CONTROL ARM: reproduce the repo's 132 EXACTLY via W2-CT1's single-path protocol
    # (single message, single path's round-63 register output; bit b "hard" iff no single free-bit
    # flip flips it at every base). This is the *known* 132; it is the foil, not the card's object.
    CENSUS_SAMPLES = 80
    flip_count = [[0] * INPUT_BITS for _ in range(N_OUT)]
    crng = random.Random(20260603)
    for _ in range(CENSUS_SAMPLES):
        M = [crng.getrandbits(32) for _ in range(16)]
        st, Wp = s.precompute_state(M)
        free0 = [crng.getrandbits(32) for _ in range(FREE_WORDS)]
        base = out63_packed(st, Wp, free0)
        for i in range(INPUT_BITS):
            w, bit = divmod(i, 32)
            free1 = list(free0); free1[w] ^= (1 << bit)
            resp = out63_packed(st, Wp, free1) ^ base
            jj = resp
            while jj:
                b = (jj & -jj).bit_length() - 1
                flip_count[b][i] += 1
                jj &= jj - 1

    # ---- (A) DO-ORPHAN count: bit b is an orphan iff NO exogenous intervention reached it
    orphans = [b for b in range(N_OUT) if not reached_anyintervention[b]]
    # ---- (B) census hard-core: bit b is "hard" iff no single input bit flips it at EVERY base
    census_ctl = [sum(1 for i in range(INPUT_BITS) if flip_count[b][i] == CENSUS_SAMPLES) for b in range(N_OUT)]
    census_hard = [b for b in range(N_OUT) if census_ctl[b] == 0]

    print(f"N=32  do-orphan BASES={BASES} (interv/base={INTERV_PER_BASE}+32)  census SAMPLES={CENSUS_SAMPLES}  free W[57..60]\n")

    def per_reg(setbits):
        d = {}
        for k, nm in enumerate(REG):
            d[nm] = sum(1 for b in setbits if 32*k <= b < 32*k+32)
        return d

    pa = per_reg(orphans); pc = per_reg(census_hard)
    print("           |  (A) DO-ORPHAN (no exogenous do() moves the out-diff bit) | (B) census-hard")
    print(f"{'reg':>4}       | per-reg orphan/32                                       | per-reg census/32")
    for nm in REG:
        print(f"{nm:>4}       | {pa[nm]:>3}/32                                                  | {pc[nm]:>3}/32")
    abef_A = pa['a']+pa['b']+pa['e']+pa['f']
    abef_B = pc['a']+pc['b']+pc['e']+pc['f']
    print(f"\n(A) DO-ORPHAN count          = {len(orphans):>3} / 256   (a,b,e,f = {abef_A}/128)")
    print(f"(B) deterministic census     = {len(census_hard):>3} / 256   (a,b,e,f = {abef_B}/128)  [repo ground truth 132]")

    # ---- stability check on (A): re-run orphan tally on an independent base-set, see if it wanders
    rng2 = random.Random(7)
    reached2 = [False]*N_OUT
    for _ in range(BASES):
        M1 = [rng2.getrandbits(32) for _ in range(16)]
        M2 = list(M1); M2[rng2.randrange(16)] ^= (1 << rng2.randrange(32))
        st1, Wp1 = s.precompute_state(M1); st2, Wp2 = s.precompute_state(M2)
        free0 = [rng2.getrandbits(32) for _ in range(FREE_WORDS)]
        base = out63_pair(st1, Wp1, free0, st2, Wp2, free0)
        for _t in range(INTERV_PER_BASE):
            free1 = [rng2.getrandbits(32) for _ in range(FREE_WORDS)]
            resp = out63_pair(st1, Wp1, free1, st2, Wp2, free1) ^ base
            jj = resp
            while jj:
                b=(jj & -jj).bit_length()-1; reached2[b]=True; jj &= jj-1
    orphans2 = sum(1 for b in range(N_OUT) if not reached2[b])
    print(f"\n[stability] (A) do-orphan count on independent base-set = {orphans2} (vs {len(orphans)})")

    # ---- VERDICT logic
    A = len(orphans)
    kill_orphan_not132 = (abs(A-132) > 12)        # "orphan count !-> 132 (~0/256)"
    print(f"\n--- DECISION ---")
    print(f"card needs the *do-orphan* count (A) ~ 132 with a,b,e,f support.")
    print(f"  (A) do-orphan = {A}; (B) census = {len(census_hard)} (reproduces repo 132 as control)")
    if A <= 12:
        print(f"  => (A) ~ 0/256: every output-diff bit is reached by SOME exogenous intervention.")
        print(f"     The 132 lives ONLY in the weaker single-bit census (B), which is sample-dependent.")
        print(f"     CS1 has relabeled the deterministic-control census as 'do-orphans' -> CATEGORY-ERROR rename.")
        print(f"  => KILL FIRES (orphan count !-> 132; it is ~0, exactly the W2-CT1 corank=0 finding).")
    elif kill_orphan_not132:
        print(f"  => (A) = {A} != 132 -> KILL FIRES (orphan count !-> 132).")
    else:
        print(f"  => (A) = {A} ~ 132 with a,b,e,f support: a GENUINE do-orphan invariant (rare CONFIRM).")

if __name__ == '__main__':
    main()

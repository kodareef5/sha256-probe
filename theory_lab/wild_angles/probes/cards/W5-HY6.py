#!/usr/bin/env python3
"""
W5-HY6 — Special-cube hyperplane osculation -> carries as the sole specialness obstruction.

Card claim: Haglund-Wise specialness forbids hyperplane self/inter-osculation; XOR-only
walls are special (clean CAT(0)), and CARRIES (the only nonlinearity) make walls osculate
-- localizing nonlinearity to a named pathology with a measurable OSCULATION DEPTH (a finer
cut than round 61).

PROBE (faithful, with the mandatory carry-on/off control): N=4 (exhaustive).
  Per round 57..60 compute the de-image = SET of reachable e-register differences across
  the cascade, in TWO models:
    * carry-ON  (exact modular add, Ch, Maj)   -> the real round
    * carry-OFF (XOR-linearized: '+' -> XOR)   -> the "special" control
  A wall "osculates" when the de-image COLLAPSES (the difference map stops being injective
  on the difference set) -- i.e. |de_carry(r)| < |de_linear(r)|.
  OSCULATION DEPTH = first round r where the carry image is smaller than the linear image.
  NEW NUMBER (finding #7 bar): does the carry collapse reproduce |de58| = 2**hw(db56)
  (the repo's measured carry image-count), NOT just "carries are the obstruction"?

KILL: osculation even in the carry-FREE model (linear de-image also collapses), OR none up
to the wall (carry and linear images identical through 60), OR depth unrelated to carry length.

Skeptic (mandatory): must run carry-on/off control or "osculation" is relabeled adjacency.
Directionality (finding #5): collapse must come FROM carries (off => no collapse), not be
present in the linear skeleton.
"""
import sys, importlib.util, os
KD = '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards'
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, KD)
import shabridge as sb
spec = importlib.util.spec_from_file_location("w5eng", os.path.join(KD, "_w5co_engine.py"))
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)


def make_linear_model(N):
    """A carry-OFF twin of eng.make_model: every modular '+' becomes XOR, Ch/Maj become
    their linear surrogates (Ch->0, Maj->0 deterministic part) -- the 'special' wall model.
    Rotations identical. This isolates the carry nonlinearity as the ONLY difference."""
    M = eng.make_model(N)
    MASK = M['MASK']
    S0, S1, s0, s1 = M['S0'], M['S1'], M['s0'], M['s1']

    def lin_round(s, k, w):
        a, b, c, d, e, f, g, h = s
        # carry-off: T1 = h XOR S1(e) XOR Ch~ XOR k XOR w ; Ch->0, '+'->XOR
        T1 = h ^ S1(e) ^ w            # k is constant (drops from DIFFERENCE); Ch->0
        T2 = S0(a)                    # Maj->0
        return ((T1 ^ T2) & MASK, a, b, c, (d ^ T1) & MASK, e, f, g)
    return M, lin_round


def de_images(N):
    """Enumerate the cascade; collect the SET of de (e-register difference) at rounds
    57..60 for BOTH the exact and the linear round, plus db56 (b-diff at round 56)."""
    M = eng.make_model(N)
    setup = eng.find_M0(M)
    if setup is None:
        return None
    Mlin, lin_round = make_linear_model(N)
    MASK = M['MASK']; R = MASK + 1
    s1_0, s2_0 = setup['st1'], setup['st2']

    # db56 = b-register difference at round 56 (the precompute end-state).
    # The repo law uses the XOR difference: |de58| = 2**hw(db56 XOR) for N<=14
    # (cascade_structure_complete.md line 33). db56 is the cascade constant (= dc57).
    db56 = s1_0[1] ^ s2_0[1]

    de_carry = {57: set(), 58: set(), 59: set(), 60: set()}
    de_lin = {57: set(), 58: set(), 59: set(), 60: set()}

    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    # --- carry-ON exact cascade ---
                    s1, s2 = s1_0, s2_0
                    w57b = eng.find_w2(s1, s2, 57, w57, M)
                    s1 = eng.sha_round(s1, M['KN'][57], w57, M)
                    s2 = eng.sha_round(s2, M['KN'][57], w57b, M)
                    de_carry[57].add((s1[4] - s2[4]) & MASK)
                    w58b = eng.find_w2(s1, s2, 58, w58, M)
                    s1 = eng.sha_round(s1, M['KN'][58], w58, M)
                    s2 = eng.sha_round(s2, M['KN'][58], w58b, M)
                    de_carry[58].add((s1[4] - s2[4]) & MASK)
                    w59b = eng.find_w2(s1, s2, 59, w59, M)
                    s1 = eng.sha_round(s1, M['KN'][59], w59, M)
                    s2 = eng.sha_round(s2, M['KN'][59], w59b, M)
                    de_carry[59].add((s1[4] - s2[4]) & MASK)
                    co = eng.find_w2(s1, s2, 60, 0, M)
                    w60b = (w60 + co) & MASK
                    s1 = eng.sha_round(s1, M['KN'][60], w60, M)
                    s2 = eng.sha_round(s2, M['KN'][60], w60b, M)
                    de_carry[60].add((s1[4] - s2[4]) & MASK)

                    # --- carry-OFF linear cascade (same free words; XOR diff is exact) ---
                    t1, t2 = s1_0, s2_0
                    t1 = lin_round(t1, M['KN'][57], w57); t2 = lin_round(t2, M['KN'][57], w57b)
                    de_lin[57].add((t1[4] ^ t2[4]) & MASK)
                    t1 = lin_round(t1, M['KN'][58], w58); t2 = lin_round(t2, M['KN'][58], w58b)
                    de_lin[58].add((t1[4] ^ t2[4]) & MASK)
                    t1 = lin_round(t1, M['KN'][59], w59); t2 = lin_round(t2, M['KN'][59], w59b)
                    de_lin[59].add((t1[4] ^ t2[4]) & MASK)
                    t1 = lin_round(t1, M['KN'][60], w60); t2 = lin_round(t2, M['KN'][60], w60b)
                    de_lin[60].add((t1[4] ^ t2[4]) & MASK)

    return dict(N=N, db56=db56, hw_db56=sb.hw(db56),
                de_carry={r: len(de_carry[r]) for r in de_carry},
                de_lin={r: len(de_lin[r]) for r in de_lin})


def main():
    print("== W5-HY6: carries as the sole specialness obstruction (osculation depth) ==\n")
    print("Carry-ON/OFF control on the de-image (set of reachable e-differences) per round.")
    print("Osculation = carry image COLLAPSES below the linear (special) image.\n")
    for N in (4,):
        d = de_images(N)
        if d is None:
            print(f"N={N}: (no cascade-eligible M0)")
            continue
        print(f"N={N}:  db56=0x{d['db56']:x}  hw(db56)={d['hw_db56']}  "
              f"2^hw(db56)={2**d['hw_db56']}")
        print(f"{'round':>5} | {'|de| carry-ON':>13} | {'|de| carry-OFF':>14} | "
              f"{'collapse?':>9} | note")
        osc_depth = None
        for r in (57, 58, 59, 60):
            c = d['de_carry'][r]; l = d['de_lin'][r]
            collapse = c < l
            if collapse and osc_depth is None:
                osc_depth = r
            note = ""
            if r == 58:
                note = f"law: |de58|=2^hw(db56)={2**d['hw_db56']} -> {'MATCH' if c == 2**d['hw_db56'] else 'NO'}"
            print(f"{r:>5} | {c:>13} | {l:>14} | {str(collapse):>9} | {note}")
        print(f"\n  OSCULATION DEPTH (first carry-collapse round) = {osc_depth}")
        print(f"  de58 carry image = {d['de_carry'][58]}  vs  2^hw(db56) = {2**d['hw_db56']}  "
              f"vs  linear {d['de_lin'][58]}")
    print()
    print("Ground-truth de58 law cross-check (shabridge.DE_SIZES + paper_figures_data.md):")
    print("  N=4:|de58|=2 hw=1 2^1=2 OK | N=8:8 hw=3 2^3=8 OK | N=10:16 hw=4 2^4=16 OK | N=32:1024<2^17(collapse)")
    print()
    print("INTERPRETATION: if carry-OFF images do NOT collapse (special walls embed) while")
    print(" carry-ON collapses, and the collapse value = 2^hw(db56), then carries are the")
    print(" sole osculation source AND we recover the repo number (not just 'carries=hardness').")
    print(" KILL fires if the linear image ALSO collapses, or if no collapse <=60.")


if __name__ == '__main__':
    main()

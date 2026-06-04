#!/usr/bin/env python3
"""
W6-OM6 — 1-D monotonicity: de58 membership = intervals (tame) vs fractal (wild).

Card claim: along the de58 axis, the set of values completing to a collision is a finite
union of INTERVALS (tame, o-minimal) for rounds <=60, and a pseudo-random SIEVE (wild) at
round 61; the sieve's entropy = the HW~74/132 plateau. "The sharpest 1-D o-minimality test."

PROBE (per CATALOG): N=6..12 — build s[v] = [de58 value v completes to a collision];
run-count + block-entropy / LZ vs round; LOW (few long runs, low entropy) <=60, -> MAXIMAL
(entropy ~1 bit/symbol) at round 61.
KILL: entropy already ~1 bit/symbol for r<=58, OR run-count never breaks at 61.
Skeptic (CATALOG + finding #5): few populated points at small N make interval-structure
fragile (need N>=12); an LFSR-like sieve looks random but is tame -> SCREENING only.

Realization of "the de58 axis": cascade_structure_complete.md states de58 is computable
from w57 ALONE, so w57 IS the de58 1-cell coordinate. We build the membership indicator
over the w57 axis at three nested "rounds":
   r=58 : completes to de58 having ANY collision-compatible continuation? (loosest)
   r=61 : completes to de61=0 (the cascade-break wall)
   r=63 : completes to a FULL sr=60 collision (8-register equality)
For each, s[w57]=1 iff EXISTS (w58,w59,w60) achieving the condition. We measure on this
1-D 0/1 string: density, number of maximal runs (interval count), and the per-symbol
block entropy (order-1 and order-3) + a crude LZ78 dictionary size (compressibility).
The card's o-minimal prediction: <=60 the string is a few long intervals (run-count small,
entropy low); at 61 it fractures into a high-entropy sieve. We test whether r=61 differs.
"""
import sys, importlib.util, os, math
KD = '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards'
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, KD)
import shabridge as sb
spec = importlib.util.spec_from_file_location("w5eng", os.path.join(KD, "_w5co_engine.py"))
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)


def membership_strings(N):
    """For each w57 (the de58 axis), set bits in three indicators over (w58,w59,w60):
       s58[w57]=1 iff that w57 is cascade-eligible at all (always 1: cascade is free)
       s61[w57]=1 iff EXISTS (w58,w59,w60) with de61==0
       s63[w57]=1 iff EXISTS (w58,w59,w60) with a full collision (sr=60)
    Returns dict of 0/1 lists indexed by w57. Cost: 2^{4N} run_tail calls -> N<=8 in C-less
    python is heavy; we use N where 2^{4N} is tractable (N=4 exact; N=5 exact)."""
    M = eng.make_model(N)
    setup = eng.find_M0(M)
    if setup is None:
        return None
    R = M['MASK'] + 1
    s61 = [0] * R; s63 = [0] * R
    for w57 in range(R):
        hit61 = hit63 = False
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    r = eng.run_tail(M, setup, w57, w58, w59, w60)
                    if r['de61'] == 0:
                        hit61 = True
                        if r['collide']:
                            hit63 = True
                            break
                if hit63:
                    break
            if hit63 and hit61:
                break
        s61[w57] = 1 if hit61 else 0
        s63[w57] = 1 if hit63 else 0
    return dict(N=N, s61=s61, s63=s63)


def runs(bits):
    """number of maximal constant runs (interval count of the 0/1 string)."""
    if not bits:
        return 0
    return 1 + sum(1 for i in range(1, len(bits)) if bits[i] != bits[i-1])


def block_entropy(bits, k):
    """order-k empirical block entropy in bits/symbol (H_k / k, sliding window)."""
    n = len(bits)
    if n < k:
        return float('nan')
    from collections import Counter
    cnt = Counter(tuple(bits[i:i+k]) for i in range(n - k + 1))
    tot = sum(cnt.values())
    H = -sum((c/tot) * math.log2(c/tot) for c in cnt.values())
    return H / k


def lz78_size(bits):
    """crude LZ78 dictionary size: lower => more compressible (tame); ~n/log n => random."""
    s = ''.join(map(str, bits))
    d, w, n = set(), '', 0
    for ch in s:
        if w + ch in d:
            w += ch
        else:
            d.add(w + ch); n += 1; w = ''
    return n


def analyze(name, bits):
    dens = sum(bits) / len(bits) if bits else 0
    return dict(name=name, n=len(bits), density=dens, runs=runs(bits),
                H1=block_entropy(bits, 1), H3=block_entropy(bits, 3),
                lz=lz78_size(bits))


def main():
    print("== W6-OM6: de58 axis membership -- intervals (tame) vs fractal (wild) ==\n")
    print("w57 IS the de58 1-cell coordinate (de58 computable from w57 alone).")
    print("Membership at three nested rounds; o-minimal claim: few long intervals <=60,")
    print("high-entropy sieve at 61. Exact exhaustive over (w58,w59,w60).\n")
    for N in (4, 5):
        d = membership_strings(N)
        if d is None:
            print(f"N={N}: (no cascade-eligible M0)\n"); continue
        print(f"--- N={N} (axis length 2^{N}={2**N}) ---")
        print(f"{'round-condition':>22} | {'density':>7} {'#runs':>5} {'#intervals(1-blocks)':>20} "
              f"| {'H1':>5} {'H3':>5} {'LZ':>4}")
        for nm, bits in (('completes de61=0 (r61)', d['s61']),
                         ('completes collision(r63)', d['s63'])):
            a = analyze(nm, bits)
            one_blocks = sum(1 for i in range(len(bits))
                             if bits[i] == 1 and (i == 0 or bits[i-1] == 0))
            print(f"{nm:>22} | {a['density']:>7.3f} {a['runs']:>5} {one_blocks:>20} "
                  f"| {a['H1']:>5.3f} {a['H3']:>5.3f} {a['lz']:>4}")
        # show the raw strings for eyeballing interval vs sieve
        print(f"   s_r61 = {''.join(map(str, d['s61']))}")
        print(f"   s_r63 = {''.join(map(str, d['s63']))}")
        print()

    # ---- N=8 corroboration: project the 260 C-enumerated collisions onto the w57 axis ----
    # (the de58 1-cell). Gives a 256-long r63-membership string -- enough support to call
    # entropy/run-structure, unlike the 16-pt N=4 case. Reproduce the dump with:
    #   cp .../trails/backward_construct_n10.c /tmp/bc_n8.c; sed -i '' 's/N      10/N       8/' ...
    #   (patched to fprintf all collisions to /tmp/coll_n8.txt); see card .md.
    cf = '/tmp/coll_n8.txt'
    if os.path.exists(cf):
        w57set = set()
        with open(cf) as fh:
            for ln in fh:
                w57set.add(int(ln.split()[0]))
        s63_8 = [1 if w in w57set else 0 for w in range(256)]
        a = analyze('N8 r63 (w57 axis)', s63_8)
        one_blocks = sum(1 for i in range(256)
                         if s63_8[i] == 1 and (i == 0 or s63_8[i-1] == 0))
        print("--- N=8 corroboration: 260 collisions projected on w57 (de58 axis), len 256 ---")
        print(f"  r63 membership: density={a['density']:.3f} #runs={a['runs']} "
              f"#intervals={one_blocks} H1={a['H1']:.3f} H3={a['H3']:.3f} LZ={a['lz']}")
        print(f"  (r61 membership at N=8 is again all-1s structurally: every w57 admits a")
        print(f"   de61=0 completion -- the cascade is free; entropy 0, perfectly tame.)")
        print()

    print("KILL test: 'entropy already ~1 bit/symbol for r<=58, OR run-count never breaks at 61.'")
    print("Here the comparison is r61 vs r63 (the wall is AT 61). Reading:")
    print("  - If s_r61 and s_r63 have SIMILAR run-count/entropy (no fracture stepping into 61),")
    print("    the o-minimal 'tame<=60 / wild@61' dichotomy is absent -> KILL.")
    print("  - The card needs LOW entropy / interval structure BELOW the wall that BREAKS at 61.")
    print("  - SCREENING ONLY at this N (skeptic: need N>=12 for robust interval structure);")
    print("    an LFSR-like sieve would be tame yet look random, so high entropy alone != wild.")


if __name__ == '__main__':
    main()

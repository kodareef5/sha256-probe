#!/usr/bin/env python3
"""
W8-KC3 — Solution-set freezing -> 132 = frozen variables, 0.74 = cluster entropy.

CARD CLAIM: the collision solution set is a d1RSB-frozen cluster; the repo's
"132 universal bits" ARE the frozen variables; the 88 free bits carry cluster
entropy 0.74N; sr=61 = the freezing threshold (last cluster's entropy -> 0).

PROBE (honored): enumerate the N=8 collision set (260, ground-truth-verified by
/tmp/bc_dump from the repo's backward_construct_n10.c), take the solution
coordinates = (w57,w58,w59,w60) free words = 4N = 32 bits. Measure:
  1. per-bit frequency over the 260 collisions -> frozen bits (==0 or ==1 in 100%)
  2. frozen-fraction of the 4N=32 solution bits; compare to 132/256 = 0.516
  3. cluster entropy estimate log2(#colls)/N ; compare to 0.74
  4. WHERE are the frozen bits (w57/w58 early vs w59/w60 late)?
  5. cluster count by single-bit flip-distance Hamming graph on the 32-bit coords
KILL: frozen-fraction not in [0.45,0.58], OR 0.74 off by >0.1, OR frozen bits
not the late-round (w59/w60) set.

ADVERSARIAL (prior findings #1,#2): the repo's 132 are OUTPUT-difference bits
(a,b,e,f @ round63), NOT input/solution-coordinate frozen bits. So the
"132 = frozen variables" identity is suspect (category error). 0.74 is DEAD as
a sharp constant. We measure both honestly.

READ-ONLY toward repo. Collision list produced lab-side by /tmp/bc_dump
(verbatim repo enumerator, N=8, 260 colls, cross-validated 260/260).
"""
import sys, csv, math, os
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb  # noqa: F401  (ground truth pins)

N = 8
CSV = '/tmp/colls_n8.csv'

def load():
    if not os.path.exists(CSV):
        sys.exit(f"missing {CSV}; build+run /tmp/bc_dump first (lab-side repo enumerator)")
    rows = []
    with open(CSV) as f:
        for r in csv.DictReader(f):
            rows.append((int(r['w57']), int(r['w58']), int(r['w59']), int(r['w60'])))
    return rows

def coord_bits(rec):
    """Flatten (w57,w58,w59,w60) into a 4N=32-bit vector, MSB-first per word.
    Returns list of 4N bits and a label per bit (word,bitpos)."""
    bits = []
    labels = []
    for wi, w in zip((57, 58, 59, 60), rec):
        for b in range(N - 1, -1, -1):
            bits.append((w >> b) & 1)
            labels.append((wi, b))
    return bits, labels

def main():
    colls = load()
    M = len(colls)
    nbits = 4 * N
    print(f"=== W8-KC3: solution-set freezing, N={N}, {M} collisions ===")
    print(f"solution coordinates = (w57,w58,w59,w60) = 4N = {nbits} bits\n")

    # --- 1+2: per-bit frequency -> frozen bits ---
    _, labels = coord_bits(colls[0])
    ones = [0] * nbits
    for rec in colls:
        bits, _ = coord_bits(rec)
        for i, bit in enumerate(bits):
            ones[i] += bit
    frozen = []   # (idx, value)
    for i in range(nbits):
        if ones[i] == 0:
            frozen.append((i, 0))
        elif ones[i] == M:
            frozen.append((i, 1))
    frozen_frac = len(frozen) / nbits
    print("--- per-bit frequency of the 32 solution-coordinate bits ---")
    print(f"{'bit':>3} {'word':>4} {'pos':>3} | P(=1) over {M} colls   frozen?")
    for i in range(nbits):
        wi, b = labels[i]
        p = ones[i] / M
        fz = ' FROZEN' if ones[i] in (0, M) else ''
        print(f"{i:>3} W{wi:>3} {b:>3} | {p:6.3f}{fz}")
    print(f"\nfrozen bits: {len(frozen)} / {nbits}  -> frozen-fraction = {frozen_frac:.3f}")
    print(f"compare to repo 132/256 = {132/256:.3f}")

    # --- 3: cluster entropy log2(#colls)/N vs 0.74 ---
    ent = math.log2(M) / N
    print(f"\n--- cluster entropy estimate ---")
    print(f"log2({M})/N = {ent:.4f}   compare 0.74  (|diff| = {abs(ent-0.74):.4f})")
    # alt definition the card hints: unfrozen entropy = log2(#colls)/(unfrozen bits)
    unfrozen = nbits - len(frozen)
    if unfrozen:
        print(f"alt: log2({M})/(unfrozen bits {unfrozen}) = {math.log2(M)/unfrozen:.4f}")

    # --- 4: WHERE are frozen bits (which word) ---
    by_word = {57: 0, 58: 0, 59: 0, 60: 0}
    for i, _v in frozen:
        by_word[labels[i][0]] += 1
    print(f"\n--- frozen-bit location by word ---")
    for w in (57, 58, 59, 60):
        print(f"  W{w}: {by_word[w]} frozen of {N} bits")
    late = by_word[59] + by_word[60]
    early = by_word[57] + by_word[58]
    print(f"  early(W57,58)={early}  late(W59,60)={late}  "
          f"-> frozen-set is {'LATE-ROUND' if late>early else 'NOT late-round'}")

    # --- 5: cluster count by single-bit flip Hamming-graph connectivity ---
    # Build the set of 32-bit coordinate words; union-find over edges that differ
    # in exactly one bit (Hamming distance 1). #components = #clusters at flip-dist-1.
    def packed(rec):
        v = 0
        for w in rec:
            v = (v << N) | (w & ((1 << N) - 1))
        return v
    pts = [packed(r) for r in colls]
    idx = {v: i for i, v in enumerate(pts)}
    parent = list(range(M))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    for i, v in enumerate(pts):
        for bit in range(nbits):
            nb = v ^ (1 << bit)
            j = idx.get(nb)
            if j is not None:
                union(i, j)
    comps = len(set(find(i) for i in range(M)))
    sizes = {}
    for i in range(M):
        r = find(i); sizes[r] = sizes.get(r, 0) + 1
    szlist = sorted(sizes.values(), reverse=True)
    print(f"\n--- Hamming flip-distance-1 clustering of the 260 solutions ---")
    print(f"  #clusters (connected components, dist-1) = {comps}")
    print(f"  cluster sizes (top 10): {szlist[:10]}")
    # also dist<=2 for context
    parent2 = list(range(M))
    def f2(x):
        while parent2[x]!=x: parent2[x]=parent2[parent2[x]]; x=parent2[x]
        return x
    def u2(a,b):
        ra,rb=f2(a),f2(b)
        if ra!=rb: parent2[ra]=rb
    ptset = set(pts)
    for i, v in enumerate(pts):
        # dist 1 and dist 2 neighbors present?
        for b1 in range(nbits):
            n1 = v ^ (1<<b1)
            if n1 in idx: u2(i, idx[n1])
            for b2 in range(b1+1, nbits):
                n2 = v ^ (1<<b1) ^ (1<<b2)
                if n2 in idx: u2(i, idx[n2])
    comps2 = len(set(f2(i) for i in range(M)))
    print(f"  #clusters (dist<=2) = {comps2}")

    # --- verdict inputs ---
    print(f"\n=== KILL CHECK ===")
    k1 = not (0.45 <= frozen_frac <= 0.58)
    k2 = abs(ent - 0.74) > 0.10
    k3 = not (late > early and (by_word[59] + by_word[60]) > 0)
    print(f"  frozen-frac {frozen_frac:.3f} in [0.45,0.58]? {'NO->KILL' if k1 else 'yes'}")
    print(f"  entropy {ent:.3f} within 0.1 of 0.74? {'NO->KILL' if k2 else 'yes'}")
    print(f"  frozen bits late-round (W59/60)? {'NO->KILL' if k3 else 'yes'}")
    print(f"  KILL FIRES: {k1 or k2 or k3}  (any one => KILLED)")

if __name__ == '__main__':
    main()

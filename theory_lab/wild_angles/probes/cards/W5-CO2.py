"""
W5-CO2 — Hennessy–Milner: 132 = the minimal distinguishing-formula set.

Card claim: bisimilar states satisfy the same modal formulas; the 132 hard-core
bits = the irreducible distinguishing formulas (cofree observations) no message-move
can equalize; HW~74 = where the distinguishing set saturates.
Probe: N=8 greedily select output-bit modalities separating collisions from
non-collisions; does the set = the empirical hard-core bits (Jaccard) and its
fraction track 132/256?
Kill: Jaccard < 0.3 OR fraction doesn't track across N.
Skeptic: risks being a bit-influence skin (near banned Walsh) — must show the
MODALITY structure beats a flat influence ranking.

Per prior finding #1 (the "132 = corank" category error, 11x): the 132 is the
single-bit DETERMINISTIC-CONTROL CENSUS = width 4N+4 (a,b,e,f fully + 4 dc), NOT a
basis-independent invariant. A real HM distinguishing-set is 0/128/width-scaling.
So: if the greedy distinguishing set lands on ~4N+4 (=36 at N=8) it is just the
census re-labelled; CONFIRM only a real, stable, basis-independent object.

----------------------------------------------------------------------------
Construction (faithful to the card's own probe):
We work in the OUTPUT-DIFFERENCE space (de63, the 8N-bit modular diff of the final
state between the two cascade paths). The "observations"/modalities are the 8N
output-difference bit positions. A collision is the point de63 = 0 (all bits 0).
A non-collision is a cascade pair whose de63 != 0.

HM distinguishing set = the minimal set S of output-diff bit positions such that
"de63 restricted to S = 0" already separates every collision from every sampled
non-collision (i.e. no non-collision has all-zero on S). We build S greedily
(set cover: each non-collision must be 'hit' by a chosen bit where it is 1).

We then compare S's SUPPORT against the 132-census support (the bits with zero
single-bit deterministic control), via Jaccard, and check size scaling vs:
   * the census width  4N+4   (the suspected category error)
   * 0 / full-width 8N        (a real basis-independent HM answer)
and whether the greedy MODAL set beats a flat per-bit influence (popcount) ranking.
"""
import sys, math, random
from collections import Counter
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _w5co_engine as E


def diff_vector(M, r):
    """8N-bit modular output-difference vector de63 as a list of bits, block order a..h."""
    N = M['N']; MASK = M['MASK']
    s1, s2 = r['s63']
    bits = []
    for blk in range(8):
        d = (s1[blk] - s2[blk]) & MASK
        bits.extend((d >> j) & 1 for j in range(N))
    return bits


def single_bit_control_census(N, n_base=40, seed=0):
    """Repo's hard-core method: output-diff bit j is 'controlled' if SOME single-bit
    flip of a free word changes it at SOME base point; 'hard core' = never controlled.
    Returns set of hard-core (uncontrolled) output-diff bit indices, and per-block counts."""
    M = E.make_model(N); setup = E.find_M0(M); R = M['MASK'] + 1
    rng = random.Random(seed)
    controlled = [False] * (8 * N)
    free_words = 4
    for _ in range(n_base):
        base = [rng.randrange(R) for _ in range(free_words)]
        r0 = E.run_tail(M, setup, *base)
        v0 = diff_vector(M, r0)
        # flip each bit of each free word
        for wi in range(free_words):
            for bit in range(N):
                pert = base[:]
                pert[wi] ^= (1 << bit)
                r1 = E.run_tail(M, setup, *pert)
                v1 = diff_vector(M, r1)
                for j in range(8 * N):
                    if v0[j] != v1[j]:
                        controlled[j] = True
    hard = {j for j in range(8 * N) if not controlled[j]}
    # per-block
    per = Counter()
    blk_names = 'a b c d e f g h'.split()
    for j in hard:
        per[blk_names[j // N]] += 1
    return hard, per, M


def greedy_distinguishing_set(N, n_noncoll=4000, seed=1):
    """Greedy set cover: minimal output-diff bit positions S s.t. every sampled
    non-collision has at least one '1' in S (so 'all-zero on S' => collision)."""
    M = E.make_model(N); setup = E.find_M0(M); R = M['MASK'] + 1
    rng = random.Random(seed)
    # sample non-collisions (cascade pairs that do NOT collide) -> their diff vectors
    nz_vecs = []
    tries = 0
    while len(nz_vecs) < n_noncoll and tries < n_noncoll * 6:
        tries += 1
        w = [rng.randrange(R) for _ in range(4)]
        r = E.run_tail(M, setup, *w)
        if not r['collide']:
            nz_vecs.append(diff_vector(M, r))
    # greedy cover: repeatedly pick the bit that is 1 in the most still-uncovered vecs
    uncovered = list(range(len(nz_vecs)))
    chosen = []
    ones_by_bit = None
    while uncovered:
        # count, per bit, how many uncovered vecs have a 1 there
        cnt = [0] * (8 * N)
        for idx in uncovered:
            v = nz_vecs[idx]
            for j in range(8 * N):
                if v[j]:
                    cnt[j] += 1
        best = max(range(8 * N), key=lambda j: cnt[j])
        if cnt[best] == 0:
            break  # remaining vecs are all-zero on every bit (shouldn't happen for non-colls)
        chosen.append(best)
        uncovered = [idx for idx in uncovered if not nz_vecs[idx][best]]
    # flat influence ranking baseline: bits by total popcount over the same sample
    flat = [0] * (8 * N)
    for v in nz_vecs:
        for j in range(8 * N):
            flat[j] += v[j]
    flat_rank = sorted(range(8 * N), key=lambda j: -flat[j])
    return set(chosen), chosen, nz_vecs, flat_rank, M


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a | b) else 1.0


def main():
    print("=== W5-CO2: Hennessy–Milner minimal distinguishing-formula set vs 132 census ===\n")
    for N in (4, 8):
        print(f"================ N = {N}  (8N = {8*N} output-diff bits) ================")
        hard, per, M = single_bit_control_census(N)
        width_census = 4 * N + 4
        print(f"[census] single-bit hard-core (uncontrolled) bits = {len(hard)} "
              f"(repo '132' object; expected width 4N+4 = {width_census})")
        print(f"[census] per-block: {dict(per)}")

        S, chosen, nz_vecs, flat_rank, M = greedy_distinguishing_set(N)
        print(f"[HM]     greedy minimal distinguishing set size = {len(S)}  "
              f"over {len(nz_vecs)} sampled non-collisions")
        print(f"[HM]     fraction of 8N = {len(S)/(8*N):.3f}  (card: track 132/256 = 0.516)")
        jac = jaccard(S, hard)
        print(f"[HM]     Jaccard(distinguishing-set support, census hard-core) = {jac:.3f}  "
              f"(kill if < 0.30)")
        # Does HM set beat flat influence ranking? Compare cover-size: how many of the
        # top-|S| flat-ranked bits are needed to cover the same non-collisions.
        def cover_size(order):
            unc = set(range(len(nz_vecs))); k = 0
            for j in order:
                if not unc:
                    break
                unc = {idx for idx in unc if not nz_vecs[idx][j]}
                k += 1
            return k, len(unc)
        k_hm, rem_hm = cover_size(chosen)
        k_flat, rem_flat = cover_size(flat_rank)
        print(f"[HM]     greedy(modal) cover size = {k_hm} (uncovered {rem_hm}); "
              f"flat-influence cover size = {k_flat} (uncovered {rem_flat})")
        print(f"[HM]     does modal structure beat flat ranking? "
              f"{'YES' if k_hm < k_flat else 'NO/TIE'} "
              f"(HM {k_hm} vs flat {k_flat})")
        # scaling check
        print(f"[scale]  |S| vs candidates: census-width(4N+4)={width_census}, "
              f"0, full(8N)={8*N}\n")


if __name__ == '__main__':
    main()

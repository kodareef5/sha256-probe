"""
_hc_family.py — shared collision-family loader for the W5-HC* (hypergraph/sunflower)
cards.  READ-ONLY toward the repo.

Provides the sr=60 collision family at small N as:
  * 4N-bit feature vectors (the free words w57,w58,w59,w60 concatenated), and
  * the full per-round modular difference trace da..dh for rounds 57..63
    (so "carry-difference supports" can be intersected for the sunflower-core card).

Data sources (all verified, all read-only or lab-side):
  N=4 : enumerated in-process via _w5co_engine        (49 collisions)
  N=8 : /tmp/coll_n8.csv (lab-side, 260 collisions, prior-card artifact; re-validated)
  N=10: repo headline_hunt/bets/coincidence_variety/gap_rows.csv (946, READ-ONLY)

Every loaded tuple is re-verified to be a true sr=60 collision before use.
"""
import sys, csv, os
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as E
import shabridge as sb

GAP_ROWS_N10 = sb.GAP_ROWS_CSV          # repo N=10, read-only
COLL_N8 = '/tmp/coll_n8.csv'            # lab-side N=8 artifact


def _tuples(N):
    """Return the list of (w57,w58,w59,w60) collision tuples at width N."""
    if N <= 5:
        colls, M, setup = E.enumerate_tail(N, want='collide')
        return colls, M, setup
    M = E.make_model(N); setup = E.find_M0(M)
    if N == 8:
        path = COLL_N8
    elif N == 10:
        path = GAP_ROWS_N10
    else:
        raise ValueError(f"no collision source wired for N={N}")
    rows = list(csv.DictReader(open(path)))
    tuples = [(int(r['w57']), int(r['w58']), int(r['w59']), int(r['w60'])) for r in rows]
    return tuples, M, setup


def tail_trace(M, setup, w57, w58, w59, w60):
    """Replay one collision; return per-round MODULAR difference dict for rounds 57..63.
    diff[r] = (da,db,dc,dd,de,df,dg,dh) = (s1[i]-s2[i]) mod 2^N after round r.
    Mirrors _w5co_engine.run_tail exactly (path-2 free words via the cascade)."""
    MASK = M['MASK']; KN = M['KN']
    W1p, W2p = setup['W1'], setup['W2']
    s1, s2 = setup['st1'], setup['st2']

    def diff(a, b):
        return tuple((a[i] - b[i]) & MASK for i in range(8))

    trace = {}
    # round 57
    w57b = E.find_w2(s1, s2, 57, w57, M)
    s1 = E.sha_round(s1, KN[57], w57, M); s2 = E.sha_round(s2, KN[57], w57b, M)
    trace[57] = diff(s1, s2)
    # round 58
    w58b = E.find_w2(s1, s2, 58, w58, M)
    s1 = E.sha_round(s1, KN[58], w58, M); s2 = E.sha_round(s2, KN[58], w58b, M)
    trace[58] = diff(s1, s2)
    # round 59
    w59b = E.find_w2(s1, s2, 59, w59, M)
    s1 = E.sha_round(s1, KN[59], w59, M); s2 = E.sha_round(s2, KN[59], w59b, M)
    trace[59] = diff(s1, s2)
    # round 60
    cas_off60 = E.find_w2(s1, s2, 60, 0, M)
    w60b = (w60 + cas_off60) & MASK
    s1 = E.sha_round(s1, KN[60], w60, M); s2 = E.sha_round(s2, KN[60], w60b, M)
    trace[60] = diff(s1, s2)
    # schedule-fixed words 61..63
    W1_61 = (M['s1'](w59) + W1p[54] + M['s0'](W1p[46]) + W1p[45]) & MASK
    W2_61 = (M['s1'](w59b) + W2p[54] + M['s0'](W2p[46]) + W2p[45]) & MASK
    W1_62 = (M['s1'](w60) + W1p[55] + M['s0'](W1p[47]) + W1p[46]) & MASK
    W2_62 = (M['s1'](w60b) + W2p[55] + M['s0'](W2p[47]) + W2p[46]) & MASK
    W1_63 = (M['s1'](W1_61) + W1p[56] + M['s0'](W1p[48]) + W1p[47]) & MASK
    W2_63 = (M['s1'](W2_61) + W2p[56] + M['s0'](W2p[48]) + W2p[47]) & MASK
    s1 = E.sha_round(s1, KN[61], W1_61, M); s2 = E.sha_round(s2, KN[61], W2_61, M)
    trace[61] = diff(s1, s2)
    s1 = E.sha_round(s1, KN[62], W1_62, M); s2 = E.sha_round(s2, KN[62], W2_62, M)
    trace[62] = diff(s1, s2)
    s1 = E.sha_round(s1, KN[63], W1_63, M); s2 = E.sha_round(s2, KN[63], W2_63, M)
    trace[63] = diff(s1, s2)
    collide = all(v == 0 for v in trace[63])
    return trace, collide


def load_family(N, with_trace=False, verify=True):
    """Return dict:
        N, MASK, count,
        bitvecs : list[int]  (4N-bit feature vector per collision; bit (k*N+j) = word_k bit j)
        tuples  : list[(w57,w58,w59,w60)]
        traces  : list[dict round->8-tuple of modular diffs]   (only if with_trace)
    """
    tuples, M, setup = _tuples(N)
    MASK = M['MASK']
    bitvecs, traces, kept = [], [], []
    for w in tuples:
        if with_trace or verify:
            tr, ok = tail_trace(M, setup, *w)
            if verify and not ok:
                continue
            if with_trace:
                traces.append(tr)
        bv = 0
        for k, x in enumerate(w):
            bv |= (x & MASK) << (k * M['N'])
        bitvecs.append(bv)
        kept.append(w)
    out = dict(N=M['N'], MASK=MASK, count=len(kept), bitvecs=bitvecs, tuples=kept,
               M=M, setup=setup)
    if with_trace:
        out['traces'] = traces
    return out


if __name__ == '__main__':
    for N in (4, 8, 10):
        fam = load_family(N, with_trace=(N <= 8))
        msg = f"N={N}: {fam['count']} collisions, 4N={4*N} feature bits"
        if 'traces' in fam:
            # sanity: every trace[63] must be all-zero (it's a collision)
            bad = sum(1 for t in fam['traces'] if any(t[63]))
            msg += f"; trace[63]!=0 count = {bad} (expect 0)"
        print(msg)

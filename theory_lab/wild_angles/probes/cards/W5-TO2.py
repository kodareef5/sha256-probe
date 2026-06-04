"""
W5-TO2 — Heyting-meet measure: 2^-2N as mu(U_A)*mu(U_B), anchored to the 1.005 ratio.

Card claim: the two sr=61 conditions are two opens U_A={g1=0}, U_B={h=0} in Omega; the
collision truth value is the meet U_A ^ U_B, whose measure FACTORS as 2^-N*2^-N *iff* the
opens are independent -- exactly the measured ratio 1.005. The deviation of rho_r from 1
ACROSS ROUNDS = a *map of which conditions share a carry chain* (a lever).

Probe (card): Monte-Carlo rho_r = mu(A^B)/(mu(A)mu(B)) per round; ~1.000 at the 61-analog
(-> 2^-2N), DEPARTS from 1 where conditions share carries?
Kill: rho_r ~ 1 for *every* round (independence generic, no fingerprint), OR rho noisy/
unstable.
Skeptic (card): the round-dependence of rho-1 must predict known carry-sharing or the
topos dressing is inert.

------------------------------------------------------------------------------
PRIOR FINDING #3 (the adversarial bar for THIS card): 2^-2N is ALREADY established as
genuinely rank-2 (g1 _|_ h, independence ratio 1.005 over 1.07B samples). The topos
language (meet U_A ^ U_B = product-of-measures) will RE-DERIVE that 1.005 product because
the substrate is real. Per the RENAME rule, this card earns CONFIRMED only if it ADDS a
NEW number/prediction beyond restating g1 _|_ h -- specifically, the card's own extra
claim: a *round-dependent* fingerprint rho_r != 1 mapping which rounds share a carry chain.
If rho_r ~ 1 at EVERY round (no round structure), it is a pure rename -> SURVIVES-as-rename.

WHAT WE COMPUTE
For each candidate boundary round r in {58,59,60,61} (the analog of "the round where the
word becomes schedule-determined"): rounds 57..r-1 run as cascade-free, then at round r:
   sched1_r = sigma1(w_{r-2}) + W1p[r-7] + sigma0(W1p[r-15]) + W1p[r-16]   (path-1)
   sched2_r = same with path-2 words
   g1_r = w_r       - sched1_r            (mod 2^N)   -- per-message value gap (open A)
   h_r  = casoff_r  - (sched2_r - sched1_r) (mod 2^N) -- inter-message compat gap (open B)
Monte-Carlo over random free words (w57..w_r). Then
   mu(A)=P(g1_r=0), mu(B)=P(h_r=0), mu(A^B)=P(both),  rho_r = mu(A^B)/(mu(A)mu(B)).
rho_r ~ 1 means the meet factors (the 2^-2N product is exact at round r).

This (a) reproduces the 1.005 product at the r=60->61 analog and (b) asks the card's ADD
question: is rho_r structured across rounds (a carry-sharing fingerprint) or flat ~1?
"""
import sys, random, csv
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as E
import shabridge as sb


def boundary_gaps_at(M, setup, r, free_words):
    """Run the cascade with given path-1 free words w57..w_r, evaluate g1_r and h_r at the
    'boundary round' r (where W[r] would become schedule-fixed). free_words = list indexed
    by round 57..r. Returns (g1_r, h_r). Cascade keeps da=0 up to round r-1; at round r we
    compare the chosen free word to its schedule value."""
    MASK = M['MASK']; KN = M['KN']
    W1p, W2p = setup['W1'], setup['W2']
    s1, s2 = setup['st1'], setup['st2']
    # path-1 word history (need w_{r-2} and the schedule taps) -- we keep both paths' words
    w1hist = {}; w2hist = {}
    for rr in range(57, r):
        w1 = free_words[rr]
        w2 = E.find_w2(s1, s2, rr, w1, M)
        w1hist[rr] = w1; w2hist[rr] = w2
        s1 = E.sha_round(s1, KN[rr], w1, M); s2 = E.sha_round(s2, KN[rr], w2, M)
    # at round r: cascade offset that WOULD keep da=0
    casoff = E.find_w2(s1, s2, r, 0, M)
    # schedule values for W[r] on both paths: taps r-2, r-7, r-15, r-16.
    def wval(hist, Wp, idx):
        return hist[idx] if idx >= 57 else (Wp[idx] & MASK)
    sched1 = (M['s1'](wval(w1hist, W1p, r-2)) + wval(w1hist, W1p, r-7)
              + M['s0'](wval(w1hist, W1p, r-15)) + wval(w1hist, W1p, r-16)) & MASK
    sched2 = (M['s1'](wval(w2hist, W2p, r-2)) + wval(w2hist, W2p, r-7)
              + M['s0'](wval(w2hist, W2p, r-15)) + wval(w2hist, W2p, r-16)) & MASK
    w_r = free_words[r]
    g1 = (w_r - sched1) & MASK
    h = (casoff - ((sched2 - sched1) & MASK)) & MASK
    return g1, h


def rho_at_round(N, r, samples, seed=0):
    M = E.make_model(N); setup = E.find_M0(M); R = M['MASK'] + 1
    rng = random.Random(seed * 1000 + r)
    nA = nB = nboth = 0
    for _ in range(samples):
        fw = {rr: rng.randrange(R) for rr in range(57, r + 1)}
        g1, h = boundary_gaps_at(M, setup, r, fw)
        a = (g1 == 0); b = (h == 0)
        if a: nA += 1
        if b: nB += 1
        if a and b: nboth += 1
    pA = nA / samples; pB = nB / samples; pboth = nboth / samples
    rho = pboth / (pA * pB) if pA * pB > 0 else float('nan')
    return dict(r=r, pA=pA, pB=pB, pboth=pboth, rho=rho, nA=nA, nB=nB, nboth=nboth,
                uniform=1.0 / R)


def rho_exact_at_round(N, r):
    """EXACT rho_r by enumerating the FULL free-word grid up to round r (no MC noise).
    For round r the relevant free words are w57..w_r; we enumerate all R^(r-56) of them.
    Feasible for N=4 (R=16): r=58 ->16^2, r=59 ->16^3, r=60 ->16^4, r=61 ->16^5=1.05M."""
    M = E.make_model(N); setup = E.find_M0(M); R = M['MASK'] + 1
    if setup is None:
        return None
    from itertools import product
    nfree = r - 56
    nA = nB = nboth = total = 0
    for combo in product(range(R), repeat=nfree):
        fw = {57 + i: combo[i] for i in range(nfree)}
        g1, h = boundary_gaps_at(M, setup, r, fw)
        total += 1
        a = (g1 == 0); b = (h == 0)
        if a: nA += 1
        if b: nB += 1
        if a and b: nboth += 1
    pA = nA / total; pB = nB / total; pboth = nboth / total
    rho = pboth / (pA * pB) if pA * pB > 0 else float('nan')
    return dict(r=r, total=total, pA=pA, pB=pB, pboth=pboth, rho=rho,
                nA=nA, nB=nB, nboth=nboth)


def gap_rows_anchor():
    """Exact rho_60 from the REAL measured N=10 collision set (gap_rows.csv): over the
    sr=60 collisions, A={g1=0}, B={h=0}. This is the published-substrate anchor."""
    rows = list(csv.DictReader(open(sb.GAP_ROWS_CSV)))
    n = len(rows)
    nA = sum(1 for r in rows if int(r['g1']) == 0)
    nB = sum(1 for r in rows if int(r['h']) == 0)
    nboth = sum(1 for r in rows if int(r['g1']) == 0 and int(r['h']) == 0)
    pA = nA / n; pB = nB / n; pboth = nboth / n
    rho = pboth / (pA * pB) if pA * pB > 0 else float('nan')
    return dict(n=n, nA=nA, nB=nB, nboth=nboth, pA=pA, pB=pB, pboth=pboth, rho=rho)


def main():
    print("=== W5-TO2: Heyting-meet rho_r = mu(A^B)/(mu(A)mu(B)) across rounds ===\n")
    print("A={g1_r=0}, B={h_r=0}. rho~1 => meet factors (2^-2N exact). Card's ADD: is")
    print("rho_r ROUND-STRUCTURED (carry-sharing fingerprint) or flat ~1 (pure g1_|_h rename)?\n")

    # (1) EXACT per-round rho at N=4 (full enumeration, NO Monte-Carlo noise)
    N = 4
    print(f"[EXACT, full-grid enumeration at N={N}, uniform 2^-N = {1/(2**N):.5f}]")
    print(f"  round r | grid     | P(A=g1=0) | P(B=h=0) | P(A^B)   | rho_r")
    rows = []
    for r in (58, 59, 60, 61):
        d = rho_exact_at_round(N, r)
        rows.append(d)
        print(f"    {r}    | {d['total']:7d} |  {d['pA']:.5f}  | {d['pB']:.5f}  |"
              f" {d['pboth']:.6f} |  {d['rho']:.4f}   (both:{d['nboth']}/{d['total']})")
    rhos = [d['rho'] for d in rows]
    spread = max(rhos) - min(rhos)
    print(f"  rho_r across rounds 58..61: {[round(x,4) for x in rhos]}  spread={spread:.4f}\n")

    # (2) the ESTABLISHED anchor: exact rho_60 from the REAL N=10 measured collisions
    a = gap_rows_anchor()
    print(f"[ANCHOR: exact rho_60 over the REAL measured N=10 collision set (gap_rows.csv)]")
    print(f"  {a['n']} sr=60 collisions; P(g1=0)={a['pA']:.4f} P(h=0)={a['pB']:.4f}"
          f" P(both)={a['pboth']:.4f}")
    print(f"  rho_60 = {a['rho']:.4f}  (g1=0:{a['nA']} h=0:{a['nB']} both:{a['nboth']})")
    print(f"  ground truth (1.07e9 samples): 1.005  => g1 _|_ h INDEPENDENT (already established)\n")

    # (3) the verdict-driving question: does TO2 ADD a round-structured carry-sharing
    # fingerprint, or merely RE-DERIVE the established g1 _|_ h product?
    print("ADD-test (per RENAME rule): does rho_r show a round-structured departure from 1")
    print("that maps NEW carry-sharing, beyond restating g1 _|_ h at the r=60 boundary?")
    flat = spread < 0.5
    print(f"  -> exact rho_r across rounds: spread={spread:.3f};"
          f" {'no NEW round structure (re-derives g1_|_h product = RENAME)' if flat else 'structured (would be an ADD)'}")
    print()


if __name__ == '__main__':
    main()


if __name__ == '__main__':
    main()

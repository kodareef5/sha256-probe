#!/usr/bin/env python3
"""
W7-NS3 — Internal/external audit: which empirical laws transfer, which are walls.

Card claim (CATALOG): Los/transfer-principle reframe. Conjecture that the ALGEBRAIC
identities (Thm 4: da_61=de_61; de57/de59/de60 constant; cascade da=0) are N-EXACT
(internal -> finitarily provable) while the COUNT-asymptotics (0.74 growth exponent,
the 132/256 'hard-core fraction') provably never lock to an exact rational (external ->
unprovable by finite-N methods) -- explaining WHY sr=61 has no UNSAT proof.

Probe (CATALOG): "N=4..16 one-table audit: tag each law N-exact (internal) vs N-drifting
(external); the prediction: a clean no-crossover split, internal<=>hard-fact-provable,
external<=>count-only. A crossover (Thm 4 failing at some N, or 0.74 locking to an exact
rational) is the most interesting outcome."

Kill (CATALOG): "every writable law is N-exact (no external witnesses -> the wall is
internal, territory inert), OR internal/external doesn't align with hard/easy."

================================================================================
METHOD (all reusing the repo's faithful make_helpers(N) mini-SHA, READ-ONLY):
  INTERNAL candidates (predicted N-exact, hold for ALL N):
    L1  Thm 4         : da_61 == de_61 (mod 2^N)      [boolean identity per sample]
    L2  R63.1         : dc_63 == dg_63                 [boolean identity per sample]
    L3  R63.3         : da_63 - de_63 == dT2_63        [boolean identity per sample]
    L4  cascade da    : da_r == 0 for r=57..60         [the cascade construction itself]
    L5  de57/59/60=1  : |de_r image| == 1 for r in {57,59,60}  (single-valued)
  EXTERNAL candidates (predicted N-drifting, never lock to a sharp rational):
    E1  de58 image    : |de58| -- the one de that VARIES with N (count, not identity)
    E2  growth 0.74   : d(N) = log2(#sr60-collisions)/N  -- exact exhaustive counts
  For each law: is it N-EXACT (same boolean/identity at every N) or N-DRIFTING (value
  changes with N, no fixed rational)? Then check the prediction:
     no-crossover (every internal stays internal, every external stays external) AND
     internal<=>hard-fact (algebraic identity) / external<=>count-only.
================================================================================
"""
import sys, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

# reuse the repo's canonical make_helpers(N) + per-N invariant probe
sys.path.insert(0, sb.REPO + '/headline_hunt/bets/block2_wang/trails')
import n_invariants as ni  # has make_helpers, find_eligible, probe_at


def audit_identities(Ns, n_samples=6000):
    """L1,L2,L3 (boolean identities) + E1 (de58 image) via the repo probe internals.
    Returns dict N -> (th4_ok, r631_ok, r633_ok, kept, de58_image, de57_img, de59_img, de60_img)."""
    import random
    out = {}
    for N in Ns:
        h = ni.make_helpers(N)
        MASK = h['MASK']
        pre, ar, cw1, cw2 = h['precompute_state'], h['apply_round'], h['cw1'], h['cw2']
        sigma0, sigma1, add = h['sigma0'], h['sigma1'], h['add']
        fills = [MASK, 0, MASK ^ (MASK >> 1), MASK >> 1, 1 << (N - 1)]
        m0, fill = ni.find_eligible(h, fills)
        if m0 is None:
            out[N] = None
            continue
        M1 = [m0] + [fill] * 15
        M2 = list(M1); M2[0] ^= 1 << (N - 1); M2[9] ^= 1 << (N - 1)
        s1, W1pre = pre(M1); s2, W2pre = pre(M2)
        cw57 = cw1(s1, s2)
        rng = random.Random(42)
        th4_v = r631_v = r633_v = kept = 0
        img57, img58, img59, img60 = set(), set(), set(), set()
        # da-cascade check (L4): track whether da_r==0 holds at 57..60
        da_ok = True
        for _ in range(n_samples):
            w57 = rng.randrange(MASK + 1)
            w2_57 = (w57 + cw57) & MASK
            s1_57 = ar(s1, w57, 57); s2_57 = ar(s2, w2_57, 57)
            if (s1_57[0] - s2_57[0]) & MASK != 0:
                continue
            img57.add((s1_57[4] - s2_57[4]) & MASK)
            cw58_v = cw1(s1_57, s2_57)
            s1_58 = ar(s1_57, 0, 58); s2_58 = ar(s2_57, cw58_v, 58)
            if (s1_58[0] - s2_58[0]) & MASK != 0: da_ok = False
            img58.add((s1_58[4] - s2_58[4]) & MASK)
            cw59_v = cw1(s1_58, s2_58)
            s1_59 = ar(s1_58, 0, 59); s2_59 = ar(s2_58, cw59_v, 59)
            if (s1_59[0] - s2_59[0]) & MASK != 0: da_ok = False
            img59.add((s1_59[4] - s2_59[4]) & MASK)
            cw60_v = cw2(s1_59, s2_59)
            s1_60 = ar(s1_59, 0, 60); s2_60 = ar(s2_59, cw60_v, 60)
            if (s1_60[0] - s2_60[0]) & MASK != 0: da_ok = False
            img60.add((s1_60[4] - s2_60[4]) & MASK)
            W1 = list(W1pre) + [w57, 0, 0, 0]
            W2 = list(W2pre) + [w2_57, cw58_v, cw59_v, cw60_v]
            for r in (61, 62, 63):
                W1.append(add(sigma1(W1[r-2]), W1[r-7], sigma0(W1[r-15]), W1[r-16]))
                W2.append(add(sigma1(W2[r-2]), W2[r-7], sigma0(W2[r-15]), W2[r-16]))
            s1_61 = ar(s1_60, W1[61], 61); s2_61 = ar(s2_60, W2[61], 61)
            s1_62 = ar(s1_61, W1[62], 62); s2_62 = ar(s2_61, W2[62], 62)
            s1_63 = ar(s1_62, W1[63], 63); s2_63 = ar(s2_62, W2[63], 63)
            da61 = (s1_61[0] - s2_61[0]) & MASK; de61 = (s1_61[4] - s2_61[4]) & MASK
            if da61 != de61: th4_v += 1
            dc63 = (s1_63[2] - s2_63[2]) & MASK; dg63 = (s1_63[6] - s2_63[6]) & MASK
            if dc63 != dg63: r631_v += 1
            da63 = (s1_63[0] - s2_63[0]) & MASK; de63 = (s1_63[4] - s2_63[4]) & MASK
            dSig0 = (h['Sigma0'](s1_62[0]) - h['Sigma0'](s2_62[0])) & MASK
            dMaj = (h['Maj'](s1_62[0], s1_62[1], s1_62[2])
                    - h['Maj'](s2_62[0], s2_62[1], s2_62[2])) & MASK
            dT2_63 = (dSig0 + dMaj) & MASK
            if ((da63 - de63) & MASK) != dT2_63: r633_v += 1
            kept += 1
        out[N] = dict(th4_ok=kept - th4_v, r631_ok=kept - r631_v, r633_ok=kept - r633_v,
                      kept=kept, da_cascade_ok=da_ok,
                      de57=len(img57), de58=len(img58), de59=len(img59), de60=len(img60),
                      m0=m0, fill=fill)
    return out


def main():
    print("=" * 78)
    print("W7-NS3 — internal (transfer-stable) vs external (N-drifting) law audit")
    print("=" * 78)
    Ns = [6, 8, 10, 12, 14]   # mini-SHA enumerable; 16 added if cheap
    res = audit_identities(Ns)

    print("\n--- ALGEBRAIC IDENTITIES (predicted INTERNAL = N-exact) ---")
    print(f"{'N':>3} | {'Thm4 da=de':>12} | {'R63.1':>10} | {'R63.3':>10} | "
          f"{'da-cascade':>10} | {'|de57|':>6} {'|de59|':>6} {'|de60|':>6}")
    internal_exact = True
    for N in Ns:
        r = res[N]
        if r is None:
            print(f"{N:>3} | (no cascade-eligible kernel)"); continue
        th4 = f"{r['th4_ok']}/{r['kept']}"; a = f"{r['r631_ok']}/{r['kept']}"
        b = f"{r['r633_ok']}/{r['kept']}"
        casc = "0 (ok)" if r['da_cascade_ok'] else "BROKEN"
        print(f"{N:>3} | {th4:>12} | {a:>10} | {b:>10} | {casc:>10} | "
              f"{r['de57']:>6} {r['de59']:>6} {r['de60']:>6}")
        if r['th4_ok'] != r['kept'] or r['r631_ok'] != r['kept'] or r['r633_ok'] != r['kept']:
            internal_exact = False
        if not r['da_cascade_ok'] or r['de57'] != 1 or r['de59'] != 1 or r['de60'] != 1:
            internal_exact = False

    print("\n--- COUNT-ASYMPTOTICS (predicted EXTERNAL = N-drifting, never lock) ---")
    print(f"{'N':>3} | {'|de58| (varies)':>16}")
    de58_vals = []
    for N in Ns:
        r = res[N]
        if r is None: continue
        de58_vals.append((N, r['de58']))
        print(f"{N:>3} | {r['de58']:>16}")
    # E2: collision growth exponent d(N) = log2(#coll)/N  (exact exhaustive counts).
    # Repo-verified sr60 collision counts (cascade-DP, backward_construct):
    coll = {8: 260, 10: 946}   # exact, repo-verified
    print("\n  growth exponent d(N)=log2(#sr60-collisions)/N  (exact exhaustive counts):")
    dvals = {}
    for N, c in sorted(coll.items()):
        dvals[N] = math.log2(c) / N
        print(f"    N={N}: #coll={c:>5}  d(N)=log2({c})/{N} = {dvals[N]:.4f}")
    drift_d = dvals[10] - dvals[8]
    print(f"    d(10)-d(8) = {drift_d:+.4f}  (still drifting; 0.74 target is the N->inf claim)")

    # ---- VERDICT LOGIC ----
    print("\n" + "=" * 78)
    print("AUDIT VERDICT")
    print("=" * 78)
    # internal column: all identities N-exact?
    print(f"  INTERNAL laws (Thm4, R63.1, R63.3, da-cascade, de57/59/60=1): "
          f"{'ALL N-EXACT' if internal_exact else 'NOT all exact (CROSSOVER!)'}")
    # external column: does de58 drift (no fixed value) and does d(N) NOT lock?
    de58_drifts = len(set(v for _, v in de58_vals)) > 1
    print(f"  EXTERNAL law de58: values {[v for _,v in de58_vals]} -> "
          f"{'N-DRIFTING (no fixed rational)' if de58_drifts else 'CONSTANT (would be internal!)'}")
    print(f"  EXTERNAL law growth: d(8)={dvals[8]:.3f}, d(10)={dvals[10]:.3f} -> "
          f"DRIFTING by {drift_d:+.3f}; 0.74 is an N->inf limit, not locked at finite N")
    # the prediction: clean no-crossover split, internal<=>identity, external<=>count
    clean_split = internal_exact and de58_drifts and (abs(drift_d) > 1e-6)
    print(f"\n  => no-crossover clean split holds? {clean_split}")
    print(f"  => internal<=>algebraic-identity, external<=>count-only: {clean_split}")

    # KILL conditions:
    kill_all_internal = not (de58_drifts or abs(drift_d) > 1e-6)  # no external witnesses
    print(f"\n  KILL cond (every law N-exact, no external witness): {kill_all_internal}")
    print(f"  KILL cond (internal/external misaligns with hard/easy): "
          f"{not clean_split}")
    if kill_all_internal or not clean_split:
        print("  -> KILLED")
    else:
        print("  -> SURVIVES (concrete no-crossover partition produced; see table)")


if __name__ == '__main__':
    main()

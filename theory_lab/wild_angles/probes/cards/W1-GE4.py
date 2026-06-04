"""
W1-GE4 -- Davies-Meyer feed-forward as an Euler class.

Card probe: "N=4: enumerate s(M)=DeltaP + DeltaH_in; compute its Z/2 zero-support
per output bit; compare to the hard-core set; check the rounds-1..59 subproblem
section is everywhere-zeroable."
Kill: "Dead if the zero-support is just the diff-linear-rank statistic
re-expressed (no new bits, no new prediction)."
Skeptic: earns its keep only if the cocycle-support is computed by a *different
method* yet agrees with the hard core (132; regs a,b,e,f).

Davies-Meyer: H_out = H_in + P(M, H_in), P = the 64-round state transform.
Collision <=> Delta H_out = 0 <=> s(M) := Delta P + Delta H_in = 0 (the section vanishes).
WITHOUT feed-forward, Delta H_out = Delta P, and P is a bijection of the state for
fixed message => the difference bundle is 'trivial' (zeroable) => no obstruction.
WITH feed-forward, s can fail to vanish on a 'support' set of output bits = the
card's predicted Euler cocycle = (claim) the 132 hard core.

We compute, by a method INDEPENDENT of the diff-linear rank:
  (A) feed-forward ON vs OFF: how many output-diff bits are FORCED nonzero (never
      zeroable by any free-word choice) -- the 'section support'.  Card predicts:
      OFF => support 0 (everywhere-zeroable);  ON => support concentrated on a,b,e,f.
  (B) compare the ON support to the hard-core set (132 / regs a,b,e,f).
  (C) Euler-class sanity: the support should be a *parity/obstruction* (mod-2)
      count, candidate-independent.
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s
MASK = sb.MASK

def make_messages(m0, fill, bit):
    M1 = [m0] + [fill]*15
    M2 = list(M1); d = 1 << bit; M2[0] ^= d; M2[9] ^= d
    return M1, M2

def P_state(M, free4, feedforward):
    """Run 64 rounds; return the 8-register output.  feedforward=True adds IV
    (Davies-Meyer H_out = H_in + P); False returns bare P (the permutation)."""
    st, _ = s.full_compression(M, list(free4)+[0])
    if feedforward:
        return tuple((st[r] + sb.IV[r]) & MASK for r in range(8))
    return tuple(st[r] & MASK for r in range(8))

def out_diff(M1, M2, free4, feedforward):
    o1 = P_state(M1, free4, feedforward)
    o2 = P_state(M2, free4, feedforward)
    # XOR-difference per register
    return tuple((o1[r] ^ o2[r]) & MASK for r in range(8))

def section_support(M1, M2, feedforward, n_free_samples=400, seed=11):
    """'Section support' = output-diff bits that are NEVER zero over the sampled
    free-word space (forced nonzero => the section s cannot vanish there =>
    obstruction support).  Returns (total_support_bits, per_register[8])."""
    rng = random.Random(seed + (1 if feedforward else 0))
    ever_zero = [[False]*32 for _ in range(8)]
    seen_any = [[False]*32 for _ in range(8)]
    for _ in range(n_free_samples):
        free4 = tuple(rng.getrandbits(32) for _ in range(4))
        d = out_diff(M1, M2, free4, feedforward)
        for reg in range(8):
            for ob in range(32):
                seen_any[reg][ob] = True
                if not ((d[reg] >> ob) & 1):
                    ever_zero[reg][ob] = True
    # support = bits that are seen but NEVER zero (always 1 across all samples)
    per = [sum(1 for ob in range(32) if seen_any[reg][ob] and not ever_zero[reg][ob])
           for reg in range(8)]
    return sum(per), per

def out_diff_diffH(M1, M2, free4, dHin, feedforward):
    """Variant where the two messages run from DIFFERENT chaining inputs H_in
    (H_in2 = IV ^ dHin), so Delta H_in != 0 -- the regime where feed-forward could
    genuinely twist.  Returns the XOR output-diff per register."""
    def run_from(M, Hin):
        # replicate full_compression but with arbitrary Hin
        W = list(M) + [0]*48
        for i in range(16,57):
            W[i] = s.add(s.sigma1(W[i-2]), W[i-7], s.sigma0(W[i-15]), W[i-16])
        for i,v in enumerate(list(free4)+[0]):
            W[57+i] = v
        W[62] = s.add(s.sigma1(W[60]), W[55], s.sigma0(W[47]), W[46])
        W[63] = s.add(s.sigma1(W[61]), W[56], s.sigma0(W[48]), W[47])
        a,b,c,d,e,f,g,h = Hin
        for i in range(64):
            T1 = s.add(h, s.Sigma1(e), s.Ch(e,f,g), sb.K[i], W[i])
            T2 = s.add(s.Sigma0(a), s.Maj(a,b,c))
            h,g,f,e,d,c,b,a = g,f,e,s.add(d,T1),c,b,a,s.add(T1,T2)
        st = (a,b,c,d,e,f,g,h)
        if feedforward:
            return tuple((st[r] + Hin[r]) & MASK for r in range(8))
        return st
    Hin1 = tuple(sb.IV)
    Hin2 = tuple((sb.IV[r] ^ ((dHin[r]) & MASK)) & MASK for r in range(8))
    o1 = run_from(M1, Hin1); o2 = run_from(M2, Hin2)
    return tuple((o1[r]^o2[r]) & MASK for r in range(8))

def run():
    print("=== W1-GE4: Davies-Meyer feed-forward as an Euler class ===\n")
    print("[GROUND TRUTH] hard core = 132 on regs", sb.HARDCORE['full_registers'],
          "(a,b,e,f) fully + 4 dc\n")
    cands = [
        (0x17149975, 0xffffffff, 31, "champion msb"),
        (0xd1acca79, 0xffffffff, 28, "bit28"),
        (0x896ee41,  0xffffffff,  2, "bit2"),
    ]
    REGS = ['a','b','c','d','e','f','g','h']

    # [0] THE decisive structural test: for SAME-IV collisions (Delta H_in = 0,
    #     the actual attack), is the feed-forward EVER visible to the difference?
    #     H_out = H_in + P; Delta H_out = Delta H_in + Delta P = 0 + Delta P.
    print("[0] Is feed-forward visible to the SAME-IV difference?  (Delta H_in = 0)")
    print("    compare out_diff ON vs OFF bit-for-bit over 500 random free words:")
    mism = 0; total = 0
    for (m0, fill, bit, name) in cands:
        M1, M2 = make_messages(m0, fill, bit)
        rng = random.Random(5)
        for _ in range(500):
            f4 = tuple(rng.getrandbits(32) for _ in range(4))
            dOFF = out_diff(M1, M2, f4, False)
            dON  = out_diff(M1, M2, f4, True)
            total += 1
            if dOFF != dON: mism += 1
    print(f"    mismatches (ON != OFF): {mism} / {total}  -> feed-forward is "
          f"{'a CONSTANT shift, INVISIBLE to Delta (adds no obstruction)' if mism==0 else 'visible'}")

    # [A] section 'support' sampling (kept for completeness; note its weakness).
    print("\n[A] sampled section support (forced-nonzero bits), ON vs OFF:")
    print(f"    {'cand':>14} {'ff':>4} {'support':>8}   per-reg")
    for (m0, fill, bit, name) in cands:
        M1, M2 = make_messages(m0, fill, bit)
        for ff in (False, True):
            tot, per = section_support(M1, M2, ff, n_free_samples=400)
            print(f"    {name:>14} {('ON' if ff else 'OFF'):>4} {tot:>8}   {per}")
    print("    (support 0 both ways: random sampling -> every bit zero sometimes;")
    print("     not a discriminator -- the decisive test is [0].)")

    # [B] the OTHER regime: Delta H_in != 0 (where feed-forward COULD twist).
    print("\n[B] Delta H_in != 0 regime: does feed-forward then change the diff?")
    M1, M2 = make_messages(*cands[0][:3])
    rng = random.Random(7)
    dHin = tuple(rng.getrandbits(32) for _ in range(8))  # nonzero chaining diff
    mism2 = 0
    for _ in range(500):
        f4 = tuple(rng.getrandbits(32) for _ in range(4))
        a = out_diff_diffH(M1, M2, f4, dHin, False)
        b = out_diff_diffH(M1, M2, f4, dHin, True)
        if a != b: mism2 += 1
    print(f"    with Delta H_in != 0: ON != OFF in {mism2}/500 free words "
          f"-> feed-forward {'DOES' if mism2>0 else 'does NOT'} act on the difference here.")
    print("    (but the actual single-block attack has Delta H_in = 0, so [0] governs.)")

    # [C] DECISIVE on the kill's 'adds nothing' clause: does MODULAR feed-forward
    #     change the deterministic-control (hard-core) pattern vs bare P?  Compute
    #     controllability per output bit (corr>=thresh) with ff ON vs OFF.
    print("\n[C] hard-core (deterministic-control) pattern: modular feed-forward ON vs OFF")
    print("    output bit controlled iff some single free-bit flip toggles it in >=98% of bases.")
    def control_pattern(M1, M2, ff, n_bases=48, seed=3, thresh=0.98):
        rng = random.Random(seed)
        bases = [tuple(rng.getrandbits(32) for _ in range(4)) for _ in range(n_bases)]
        d0 = [out_diff(M1, M2, b, ff) for b in bases]
        controlled = [[False]*32 for _ in range(8)]
        for fw in range(4):
            for fb in range(32):
                mk = 1<<fb
                d1 = [out_diff(M1, M2, tuple(b[w]^(mk if w==fw else 0) for w in range(4)), ff)
                      for b in bases]
                for reg in range(8):
                    for ob in range(32):
                        obm=1<<ob
                        tog=sum(1 for k in range(n_bases) if ((d0[k][reg]^d1[k][reg])&obm))
                        if tog/n_bases>=thresh: controlled[reg][ob]=True
        per_hc=[sum(1 for ob in range(32) if not controlled[reg][ob]) for reg in range(8)]
        return sum(per_hc), per_hc
    M1, M2 = make_messages(*cands[0][:3])
    for ff in (False, True):
        tot, per = control_pattern(M1, M2, ff)
        print(f"    ff={'ON ' if ff else 'OFF'}: hard-core total={tot}  per-reg={per}")
    print("    -> if ON and OFF patterns are IDENTICAL, modular feed-forward adds NO new")
    print("       controllability structure (kill's 'no new bits' clause).")

    print("\n[interpretation]")
    print("  CORRECTION to naive view: SHA feed-forward is MODULAR add, so it DOES act on")
    print("  the XOR-difference even at Delta H_in=0 ([0]: 1500/1500). So it is NOT a")
    print("  trivial constant shift -- the clean 'invisible' KILL does not apply.")
    print("  But the cheap sampling instrument [A] is blind, and the faithful hard-core")
    print("  instrument IS the diff-linear correlation/rank the kill names. [C] tests")
    print("  whether ff changes that pattern at all. Read verdict from [C].")

if __name__ == '__main__':
    run()

"""
W1-GE2 -- Holonomy / winding around the W57 circle -> existence certificate.

Card probe: "N=6-8: compute residual H(W57)=D61 for all 2^N W57 (reuse
run_tail_rounds); check H=0 exactly at enumerator collisions; project to one
register coordinate, compute winding number around the circle; compare to actual
count."
Kill: "Dead if H(W57) is statistically indistinguishable from a fresh
pseudorandom function (winding ~ random-walk sqrt-scaling, no predictive zeros)."
Skeptic: "mod-2^N winding is delicate; carries make H jumpy -- must check winding
*predicts* the zero count."

Approach (genuine tail arithmetic, READ-ONLY repo lib via shabridge):
  * Take a real kernel candidate; build the two messages M1, M2 (kernel diff on
    words 0 and 9, the (0,9) attack pair).  Precompute state after round 56.
  * The 'W57 circle' = sweep the free word W[57] over all 2^N values (N small),
    holding W58,W59,W60 fixed.  For each W57 run the tail rounds for BOTH
    messages and read the residual difference D = (state1 - state2) at round 61.
  * The 'holonomy' projected to one coordinate = D[reg] as a signed value on
    Z/2^N.  Winding number = net number of times this coordinate wraps the
    circle (sum of sign of forward differences of the angle), an integer.
  * Test (i) zeros of D = round-collisions; (ii) does |winding| predict the #zeros
    of that coordinate; (iii) is D distinguishable from a fresh PRF (compare its
    winding & zero statistics to a seeded random function of the same range).
"""
import sys, random, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s

MASK = sb.MASK

def make_messages(m0, fill, bit):
    """(0,9)-kernel pair at full 32-bit width (messages are 32-bit words)."""
    M1 = [m0] + [fill]*15
    M2 = list(M1)
    d = 1 << bit
    M2[0] ^= d
    M2[9] ^= d
    return M1, M2

def residual_over_circle(M1, M2, w58, w59, w60, N, reg=4):
    """Sweep the free word W57 over a 2^N 'circle' (low N bits; high bits fixed=0),
    holding W58..W60.  Return list of signed residual D[reg] at round 61 for both
    messages (state1[reg]-state2[reg] mod 2^32), length 2^N."""
    st1, W1pre = s.precompute_state(M1)
    st2, W2pre = s.precompute_state(M2)
    vals = []
    span = 1 << N
    for w57 in range(span):
        # schedule tail for each message from its own W_pre + the 4 free words
        sw1 = s.build_schedule_tail(W1pre[:57], [w57, w58, w59, w60])
        sw2 = s.build_schedule_tail(W2pre[:57], [w57, w58, w59, w60])
        tr1 = s.run_tail_rounds(st1, sw1, start_round=57)   # tr[0]=before57; tr[k]=after round 56+k
        tr2 = s.run_tail_rounds(st2, sw2, start_round=57)
        # round 61 == 5 rounds after round56 -> index 5 (after 57,58,59,60,61)
        a1 = tr1[5][reg]; a2 = tr2[5][reg]
        d = (a1 - a2) & MASK
        vals.append(d)
    return vals

def winding_number(vals, N):
    """Winding of a signed coordinate around Z/2^N: sum of forward angular steps
    /2pi.  Map v in [0,2^N) to angle; accumulate shortest-arc steps; net/2pi."""
    span = 1 << N
    if not vals:
        return 0.0
    ang = [2*math.pi*(v % span)/span for v in [x & (span-1) for x in vals]]
    total = 0.0
    for i in range(len(ang)):
        d = ang[(i+1) % len(ang)] - ang[i]
        # shortest arc in (-pi, pi]
        while d > math.pi: d -= 2*math.pi
        while d <= -math.pi: d += 2*math.pi
        total += d
    return total/(2*math.pi)

def count_zeros(vals):
    return sum(1 for v in vals if v == 0)

def prf_baseline(seed, length, span_full=1<<32):
    rng = random.Random(seed)
    return [rng.randrange(span_full) for _ in range(length)]

def run():
    print("=== W1-GE2: holonomy / winding around the W57 circle ===\n")
    # champion candidate (verified sr=60): m0=0x17149975 fill=0xffffffff bit=31
    m0, fill, bit = 0x17149975, 0xffffffff, 31
    M1, M2 = make_messages(m0, fill, bit)
    REGS = ['a','b','c','d','e','f','g','h']
    for N in (6, 7, 8):
        span = 1 << N
        # fix W58..60 to a representative value (mid of the low-N circle)
        w58 = w59 = w60 = (span >> 1)
        print(f"--- N={N}  (W57 circle = {span} pts; W58=W59=W60=0x{w58:x}) ---")
        print(f"    {'reg':>3} {'#zeros':>7} {'winding':>9} {'|wind| pred?':>13}   vs PRF baseline (zeros, winding)")
        # PRF baseline with the SAME number of samples and a 32-bit range
        prf = prf_baseline(0xC0FFEE + N, span)
        prf_z = count_zeros(prf); prf_w = winding_number(prf, N)
        for reg in range(8):
            vals = residual_over_circle(M1, M2, w58, w59, w60, N, reg=reg)
            z = count_zeros(vals); w = winding_number(vals, N)
            pred = "yes" if (z > 0 and abs(round(w)) == z) else "no"
            print(f"    {REGS[reg]:>3} {z:>7} {w:>9.2f} {pred:>13}   PRF: z={prf_z} w={prf_w:.2f}")
        # also: residual on the full 8-register difference being exactly 0 = a real
        # round-61 collision of the tail; count those over the circle:
        full_zero = 0
        st1, W1pre = s.precompute_state(M1); st2, W2pre = s.precompute_state(M2)
        for w57 in range(span):
            sw1 = s.build_schedule_tail(W1pre[:57], [w57, w58, w59, w60])
            sw2 = s.build_schedule_tail(W2pre[:57], [w57, w58, w59, w60])
            t1 = s.run_tail_rounds(st1, sw1, 57)[5]
            t2 = s.run_tail_rounds(st2, sw2, 57)[5]
            if all(((t1[r]-t2[r]) & MASK) == 0 for r in range(8)):
                full_zero += 1
        print(f"    full 8-register round-61 collisions over this circle: {full_zero}\n")

    # ---- fairest shot for winding: project residual to a SMALL modulus 2^b so
    #      zeros are dense, and test whether winding on that small circle predicts
    #      the (now plentiful) zero count.  Degree theory says |winding| <= #zeros
    #      and for a genuine degree-d map they should MATCH; a PRF gives them
    #      uncorrelated.
    print("--- winding-predicts-zeros test on a SMALL projected circle (mod 2^b) ---")
    print("    project D[e]@round61 to its low b bits; sweep W57 over 2^N; the")
    print("    projected coord wraps a small circle, crossing 0 often.")
    print(f"    {'N':>3} {'b':>3} {'#zeros(proj)':>12} {'winding':>9} {'|w|==z?':>8} | PRF: zeros winding |w|==z?")
    for N in (8,):
        span = 1 << N
        w58 = w59 = w60 = (span >> 1)
        vals = residual_over_circle(M1, M2, w58, w59, w60, N, reg=4)
        for b in (2, 3, 4):
            mod = 1 << b
            proj = [v & (mod-1) for v in vals]
            z = count_zeros(proj); w = winding_number(proj, b)
            match = "yes" if abs(round(w)) == z else "no"
            prf = [random.Random(7*N+b).randrange(mod) for _ in range(span)]
            pz = count_zeros(prf); pw = winding_number(prf, b)
            pmatch = "yes" if abs(round(pw)) == pz else "no"
            print(f"    {N:>3} {b:>3} {z:>12} {w:>9.2f} {match:>8} | PRF: {pz:>4} {pw:>6.2f} {pmatch}")

    print("\n[interpretation] If D[reg] looks like the PRF (winding ~ O(1) random,")
    print("zeros ~ Poisson(span/2^32)~0, |winding| does NOT equal #zeros) the kill")
    print("fires.  Winding 'predicts' zeros only if |round(winding)| == #zeros.")

if __name__ == '__main__':
    run()

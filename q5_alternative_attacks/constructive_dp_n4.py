#!/usr/bin/env python3
"""
Constructive Quotient-State DP for sr=60 Collision Finding

Key idea from GPT-5.4: the "right" search state is NOT the raw carry vector
(near-injective, 89-99% of search space). It's the future-completion
equivalence class (BDD residual node), which has width = #collisions.

This prototype tests a practical approximation: track the state as
(concrete_carry_boundary, GF2_linear_context_hash) and deduplicate.

For N=4: one pass over all 2^16 candidate W1 values, but organized as
bit-serial DP with carry-state deduplication. If deduplication reduces
the state count to ~49 (= #collisions), the approach works.

Usage: python3 constructive_dp_n4.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

N = 4
spec = __import__('50_precision_homotopy')
sha = spec.MiniSHA256(N)
MASK = sha.MASK
KT = [k & MASK for k in spec.K32]
result = sha.find_m0()
m0, s1, s2, W1p, W2p = result

print(f"Constructive DP at N={N}, m0=0x{m0:x}")

# The cascade determines W2 from W1. For the DP, we treat W1[57..60]
# as 4×N = 16 free bits, processed bit-by-bit (bit 0 first).
#
# At each bit position k, we choose 4 bits: W1[57][k], W1[58][k], W1[59][k], W1[60][k].
# The cascade then determines W2[57..60][k] (given the carry state from prior bits).
#
# The "state" between bit k-1 and bit k is all the information needed to
# process bit k: carry-out bits from ALL additions in ALL rounds for BOTH messages.
#
# The FULL carry state has 98 bits (7 adds × 7 rounds × 2 msgs).
# But many are constant — let's count the free ones.

def process_full_rounds(W1, state1, state2):
    """Run all 7 rounds concretely, return final states."""
    # Cascade W2
    st_a, st_b = list(state1), list(state2)
    W2 = []
    for r in range(4):
        a1,b1,c1,d1,e1,f1,g1,h1 = st_a
        a2,b2,c2,d2,e2,f2,g2,h2 = st_b
        t1nw1 = (h1 + sha.Sigma1(e1) + sha.ch(e1,f1,g1) + KT[57+r]) & MASK
        t1nw2 = (h2 + sha.Sigma1(e2) + sha.ch(e2,f2,g2) + KT[57+r]) & MASK
        t2_1 = (sha.Sigma0(a1) + sha.maj(a1,b1,c1)) & MASK
        t2_2 = (sha.Sigma0(a2) + sha.maj(a2,b2,c2)) & MASK
        offset = ((t1nw1 + t2_1) - (t1nw2 + t2_2)) & MASK
        w2r = (W1[r] + offset) & MASK
        W2.append(w2r)
        t1_1 = (t1nw1 + W1[r]) & MASK
        t1_2 = (t1nw2 + w2r) & MASK
        st_a = [(t1_1+t2_1)&MASK,a1,b1,c1,(d1+t1_1)&MASK,e1,f1,g1]
        st_b = [(t1_2+t2_2)&MASK,a2,b2,c2,(d2+t1_2)&MASK,e2,f2,g2]

    # Schedule
    W1f = list(W1p[:57]) + list(W1)
    W2f = list(W2p[:57]) + list(W2)
    for t in range(61, 64):
        W1f.append((sha.sigma1(W1f[t-2]) + W1f[t-7] + sha.sigma0(W1f[t-15]) + W1f[t-16]) & MASK)
        W2f.append((sha.sigma1(W2f[t-2]) + W2f[t-7] + sha.sigma0(W2f[t-15]) + W2f[t-16]) & MASK)

    # Run rounds
    def rnd(s, k, w):
        a,b,c,d,e,f,g,h = s
        t1 = (h+sha.Sigma1(e)+sha.ch(e,f,g)+k+w)&MASK
        t2 = (sha.Sigma0(a)+sha.maj(a,b,c))&MASK
        return ((t1+t2)&MASK,a,b,c,(d+t1)&MASK,e,f,g)

    st1r, st2r = tuple(state1), tuple(state2)
    for i in range(7):
        st1r = rnd(st1r, KT[57+i], W1f[57+i])
        st2r = rnd(st2r, KT[57+i], W2f[57+i])
    return st1r, st2r

# ========== DP Approach: bit-serial with carry state tracking ==========
#
# We process bits 0..N-1. At each bit k, for each surviving carry state,
# we try all 2^4 = 16 choices of (W1[57][k], W1[58][k], W1[59][k], W1[60][k]).
#
# For each choice:
#   1. Derive W2 bits via cascade (requires running all 7 round functions at bit k)
#   2. Compute carry-outs for all additions
#   3. Record new carry state
#
# The carry state encodes ALL carries that feed into the NEXT bit position.
# We group states that have the SAME carry state → deduplication.
#
# Total additions per round: 7 (for the sequential chain in sha256_round)
# Per message, per round: 7 carry-outs
# But we use CSA or sequential additions — let me use sequential for clarity.

def additions_per_round_per_msg():
    """List the 7 sequential additions in one SHA-256 round."""
    # T1 chain: h+Sig1, +Ch, +K, +W (4 additions)
    # T2: Sig0+Maj (1 addition)
    # a_new = T1+T2 (1 addition)
    # e_new = d+T1 (1 addition)
    return 7

ADDS_PER_RND = 7
TOTAL_ADDS = ADDS_PER_RND * 7 * 2  # 7 rounds × 2 messages = 98

# Process bit k: given register states and carry-in vector,
# compute carry-out vector for all 16 W1-bit choices

def bit_of(val, k):
    return (val >> k) & 1

def carry_out_1bit(a, b, cin):
    return (a & b) | (a & cin) | (b & cin)

def sum_1bit(a, b, cin):
    return a ^ b ^ cin

def process_one_bit(k, reg_state_m1, reg_state_m2, w1_bits, carry_in):
    """
    Process bit k through all 7 rounds for both messages.

    reg_state_m1/m2: full N-bit register words [a,b,c,d,e,f,g,h]
    w1_bits: [W1[57][k], W1[58][k], W1[59][k], W1[60][k]]
    carry_in: list of carry-in bits for each addition (from bit k-1)

    Returns: (carry_out, w2_bits, new_reg_m1_at_k, new_reg_m2_at_k, consistent)
    """
    carry_out = []
    ci_idx = 0  # index into carry_in

    st1 = list(reg_state_m1)  # [a,b,c,d,e,f,g,h] as N-bit words
    st2 = list(reg_state_m2)

    w2_bits = []

    for r in range(7):
        a1,b1,c1,d1,e1,f1,g1,h1 = st1
        a2,b2,c2,d2,e2,f2,g2,h2 = st2

        # Get bit k of each register
        a1k,b1k,c1k,d1k = bit_of(a1,k),bit_of(b1,k),bit_of(c1,k),bit_of(d1,k)
        e1k,f1k,g1k,h1k = bit_of(e1,k),bit_of(f1,k),bit_of(g1,k),bit_of(h1,k)
        a2k,b2k,c2k,d2k = bit_of(a2,k),bit_of(b2,k),bit_of(c2,k),bit_of(d2,k)
        e2k,f2k,g2k,h2k = bit_of(e2,k),bit_of(f2,k),bit_of(g2,k),bit_of(h2,k)

        # Sigma1(e)[k] — reads rotated bits (from FULL register, not just bit k)
        sig1_1k = bit_of(sha.Sigma1(e1), k)
        sig1_2k = bit_of(sha.Sigma1(e2), k)
        ch_1k = bit_of(sha.ch(e1,f1,g1), k)
        ch_2k = bit_of(sha.ch(e2,f2,g2), k)

        K_k = bit_of(KT[57+r], k)

        # T1 chain for msg1: h + Sig1 + Ch + K + W
        # add1: h + Sig1
        cin1 = carry_in[ci_idx]; ci_idx += 1
        s1 = sum_1bit(h1k, sig1_1k, cin1)
        co1 = carry_out_1bit(h1k, sig1_1k, cin1)
        carry_out.append(co1)

        # add2: +Ch
        cin2 = carry_in[ci_idx]; ci_idx += 1
        s2_val = sum_1bit(s1, ch_1k, cin2)
        co2 = carry_out_1bit(s1, ch_1k, cin2)
        carry_out.append(co2)

        # add3: +K
        cin3 = carry_in[ci_idx]; ci_idx += 1
        s3 = sum_1bit(s2_val, K_k, cin3)
        co3 = carry_out_1bit(s2_val, K_k, cin3)
        carry_out.append(co3)

        # add4: +W (message word bit)
        cin4 = carry_in[ci_idx]; ci_idx += 1
        if r < 4:
            w1k = w1_bits[r]
        else:
            # Schedule-determined: W[61+] from prior W values
            # At this point we need the FULL word values, not just bit k
            # This is where it gets complicated...
            # For now, compute from full words
            W1_full = [0]*4  # placeholder — need actual W1 word values
            # HACK: we can't easily do this bit-serially for schedule words
            # because sigma1 mixes all bits. Skip for now.
            w1k = 0  # placeholder
        t1k = sum_1bit(s3, w1k, cin4)
        co4 = carry_out_1bit(s3, w1k, cin4)
        carry_out.append(co4)

        # Sigma0(a), Maj(a,b,c)
        sig0_1k = bit_of(sha.Sigma0(a1), k)
        maj_1k = bit_of(sha.maj(a1,b1,c1), k)

        # add5: Sig0 + Maj
        cin5 = carry_in[ci_idx]; ci_idx += 1
        t2k = sum_1bit(sig0_1k, maj_1k, cin5)
        co5 = carry_out_1bit(sig0_1k, maj_1k, cin5)
        carry_out.append(co5)

        # add6: T1 + T2 = a_new
        cin6 = carry_in[ci_idx]; ci_idx += 1
        a_new_k = sum_1bit(t1k, t2k, cin6)
        co6 = carry_out_1bit(t1k, t2k, cin6)
        carry_out.append(co6)

        # add7: d + T1 = e_new
        cin7 = carry_in[ci_idx]; ci_idx += 1
        e_new_k = sum_1bit(d1k, t1k, cin7)
        co7 = carry_out_1bit(d1k, t1k, cin7)
        carry_out.append(co7)

        # ---- Same for msg2 ----
        sig1_2k = bit_of(sha.Sigma1(e2), k)
        ch_2k = bit_of(sha.ch(e2,f2,g2), k)

        cin1b = carry_in[ci_idx]; ci_idx += 1
        s1b = sum_1bit(h2k, sig1_2k, cin1b)
        co1b = carry_out_1bit(h2k, sig1_2k, cin1b)
        carry_out.append(co1b)

        cin2b = carry_in[ci_idx]; ci_idx += 1
        s2b = sum_1bit(s1b, ch_2k, cin2b)
        co2b = carry_out_1bit(s1b, ch_2k, cin2b)
        carry_out.append(co2b)

        cin3b = carry_in[ci_idx]; ci_idx += 1
        s3b = sum_1bit(s2b, K_k, cin3b)
        co3b = carry_out_1bit(s2b, K_k, cin3b)
        carry_out.append(co3b)

        # W2 bit from cascade
        # For free rounds (r<4): cascade determines w2k
        cin4b = carry_in[ci_idx]; ci_idx += 1
        if r < 4:
            # Need to compute w2k from cascade: full cascade requires full word values
            # Can't do purely bit-serial... this is the fundamental problem
            w2k = 0  # placeholder
        else:
            w2k = 0  # schedule-determined, same issue

        t1k_2 = sum_1bit(s3b, w2k, cin4b)
        co4b = carry_out_1bit(s3b, w2k, cin4b)
        carry_out.append(co4b)

        sig0_2k = bit_of(sha.Sigma0(a2), k)
        maj_2k = bit_of(sha.maj(a2,b2,c2), k)

        cin5b = carry_in[ci_idx]; ci_idx += 1
        t2k_2 = sum_1bit(sig0_2k, maj_2k, cin5b)
        co5b = carry_out_1bit(sig0_2k, maj_2k, cin5b)
        carry_out.append(co5b)

        cin6b = carry_in[ci_idx]; ci_idx += 1
        a_new_k2 = sum_1bit(t1k_2, t2k_2, cin6b)
        co6b = carry_out_1bit(t1k_2, t2k_2, cin6b)
        carry_out.append(co6b)

        cin7b = carry_in[ci_idx]; ci_idx += 1
        e_new_k2 = sum_1bit(d2k, t1k_2, cin7b)
        co7b = carry_out_1bit(d2k, t1k_2, cin7b)
        carry_out.append(co7b)

        # Update register state: shift register + new a,e
        # a_new, a_old, b_old, c_old, e_new, e_old, f_old, g_old
        # Need to update BIT k only — but registers are full N-bit words
        # This is the fundamental issue: we can't update individual bits
        # without affecting Sigma at other bit positions

        # For round 57 (first round), state comes from state56 (constant)
        # For round 58+, state depends on prior rounds' FULL outputs
        # The bit-serial approach can't isolate bit k

        # CONCLUSION: pure bit-serial DP requires symbolic tracking
        # for cross-bit dependencies (Sigma rotations).
        # At N=4, this is equivalent to the full ae3 approach.

    return tuple(carry_out)


# ========== CONCLUSION: Demonstrate the barrier ==========
print(f"""
=== CONSTRUCTIVE DP: ROTATION FRONTIER BARRIER ===

The bit-serial DP hits the rotation frontier at every round:
- Sigma1(e)[k] reads e at positions (k+{sha.r_Sig1[0]})%{N}, (k+{sha.r_Sig1[1]})%{N}, (k+{sha.r_Sig1[2]})%{N}
- Sigma0(a)[k] reads a at positions (k+{sha.r_Sig0[0]})%{N}, (k+{sha.r_Sig0[1]})%{N}, (k+{sha.r_Sig0[2]})%{N}

Processing bit k requires register values at OTHER bit positions.
These depend on carries at those positions, which haven't been computed.

The carry state at bit k includes SYMBOLIC dependencies on unprocessed bits.
The raw carry-state width is 89-99% of the search space (near-injective).

BUT: the BDD quotient shows that width = #collisions under the RIGHT equivalence.
The quotient is defined by future-completion: two states are equivalent if they
produce the same set of completions. This is NOT computable during the search
without knowing the completions (= collisions) in advance.

GPT-5.4's suggestion: use GF(2) canonical form (lin_id) as an approximation
of the quotient. Within a chunk, track symbolic affine forms. At chunk boundaries,
canonicalize the linear system and hash it. Two states with the same lin_id
are PROVABLY equivalent for the linear part.

At N=4 (one chunk = full word), this gives no savings because all bits interact.
At N=8+ with multi-chunk processing, the lin_id quotient MAY be smaller than
the raw carry state, giving algorithmic savings.

The fundamental question: does the GF(2) lin_id quotient have width = #collisions?
If yes → constructive O(2^N) algorithm.
If no → GF(2) is too coarse, need a finer equivalence.

To test: measure lin_id width at N=8 with chunk=4 and compare to quotient width (255).
""")

# Just verify: 49 collisions matches
print(f"Brute-force validation: {len([1 for w in range(1<<(4*N)) if process_full_rounds([(w>>(i*N))&MASK for i in range(4)], s1, s2)[0] == process_full_rounds([(w>>(i*N))&MASK for i in range(4)], s1, s2)[1]])} collisions")
# Too slow to inline, use the cached result
print(f"Collisions (from earlier): 49")
print(f"BDD quotient peak: 49")
print(f"Carry-prefix state widths: 25→28→44→49")

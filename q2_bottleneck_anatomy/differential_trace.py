#!/usr/bin/env python3
"""
Script 78: Wang-Style Differential Analysis for sr=60

Analyzes the sr=59 collision trail round-by-round to understand:
1. Exactly which state bits differ at each round (57-63)
2. What conditions the free words W[57..60] must satisfy for sr=60
3. Whether message modification can steer the differential to zero at round 60

Wang's method: for each round, identify which input differences produce which
output differences, and which message bit modifications can neutralize them.

For SHA-256 sr=60, the "message words" are W[57..60] (4 free words per message).
The question: is there an assignment of W1[57..60], W2[57..60] such that the
state difference after round 63 is zero?
"""

import sys

# SHA-256 primitives
MASK = 0xFFFFFFFF
def ror(x, n): return ((x >> n) | (x << (32 - n))) & MASK
def Ch(e, f, g): return ((e & f) ^ ((~e & MASK) & g))
def Maj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c))
def S0(a): return ror(a, 2) ^ ror(a, 13) ^ ror(a, 22)
def S1(e): return ror(e, 6) ^ ror(e, 11) ^ ror(e, 25)
def s0(x): return ror(x, 7) ^ ror(x, 18) ^ (x >> 3)
def s1(x): return ror(x, 17) ^ ror(x, 19) ^ (x >> 10)
def hw(x): return bin(x).count('1')
def add(*args):
    s = 0
    for a in args: s = (s + a) & MASK
    return s

K = [
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
IV = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
      0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]


def precompute(M):
    """Run 57 rounds, return (state, W[0..56])."""
    W = list(M) + [0] * 41  # 16 + 41 = 57 entries
    for i in range(16, 57):
        W[i] = add(s1(W[i-2]), W[i-7], s0(W[i-15]), W[i-16])
    a, b, c, d, e, f, g, h = IV
    for i in range(57):
        T1 = add(h, S1(e), Ch(e, f, g), K[i], W[i])
        T2 = add(S0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
    return [a, b, c, d, e, f, g, h], W


def run_tail(state, Ws, start_round=57):
    """Run rounds start_round..start_round+len(Ws)-1, return per-round states."""
    a, b, c, d, e, f, g, h = state
    trace = [(a, b, c, d, e, f, g, h)]
    for i, Wi in enumerate(Ws):
        T1 = add(h, S1(e), Ch(e, f, g), K[start_round + i], Wi)
        T2 = add(S0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
        trace.append((a, b, c, d, e, f, g, h))
    return trace


def build_schedule_tail(W_pre, free_words):
    """Build W[57..63] given W[0..56] and free words W[57..60]."""
    W = list(W_pre) + list(free_words)
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    W.append(add(s1(W[59]), W[54], s0(W[46]), W[45]))
    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    W.append(add(s1(W[60]), W[55], s0(W[47]), W[46]))
    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    W.append(add(s1(W[61]), W[56], s0(W[48]), W[47]))
    return W[57:]


def analyze_differential(state1, state2, W1_tail, W2_tail):
    """Detailed round-by-round differential analysis."""
    reg_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    trace1 = run_tail(state1, W1_tail)
    trace2 = run_tail(state2, W2_tail)

    print("=" * 90)
    print("WANG-STYLE DIFFERENTIAL TRACE: Rounds 57-63")
    print("=" * 90)

    for r in range(len(trace1)):
        s1 = trace1[r]
        s2 = trace2[r]
        round_num = 56 + r  # state AFTER round_num

        total_hw = sum(hw(s1[i] ^ s2[i]) for i in range(8))

        if r == 0:
            print(f"\n--- State at entry (after round 56) ---")
        else:
            print(f"\n--- State after round {round_num} (W[{round_num}] applied) ---")
            dW = W1_tail[r-1] ^ W2_tail[r-1]
            print(f"  dW[{round_num}] = 0x{dW:08x} (hw={hw(dW)})")

        print(f"  Total state diff HW = {total_hw}")

        for i in range(8):
            d = s1[i] ^ s2[i]
            if d != 0:
                # Show which bits differ
                bits = [31 - b for b in range(32) if (d >> (31 - b)) & 1]
                top_bits = bits[:8]
                print(f"  d{reg_names[i]} = 0x{d:08x} (hw={hw(d):2d})  bits: {top_bits}{'...' if len(bits) > 8 else ''}")
            else:
                print(f"  d{reg_names[i]} = 0x00000000        ** ZERO **")

        # Check collision at this point
        if total_hw == 0:
            print(f"\n  *** COLLISION AT ROUND {round_num}! ***")

    return trace1, trace2


def sensitivity_analysis(state1, state2, W1_pre, W2_pre, W1_free4, W2_free4):
    """
    For each bit of each free word, flip it and see how the round-63 state changes.
    This tells us which message bits have the most influence on the collision condition.
    """
    print("\n" + "=" * 90)
    print("SENSITIVITY ANALYSIS: Bit-flip impact on round-63 state diff")
    print("=" * 90)

    W1_tail = build_schedule_tail(W1_pre, W1_free4)
    W2_tail = build_schedule_tail(W2_pre, W2_free4)

    base_trace1 = run_tail(state1, W1_tail)
    base_trace2 = run_tail(state2, W2_tail)
    base_diff = sum(hw(base_trace1[-1][i] ^ base_trace2[-1][i]) for i in range(8))

    print(f"\nBaseline round-63 state diff HW: {base_diff}")
    print(f"\nFlipping W1 bits (message 1 modifications):")
    print(f"{'Word':>6} {'Bit':>4} {'New HW63':>9} {'Delta':>7} {'Direction':>10}")
    print("-" * 42)

    best_flips = []

    for word_idx in range(4):
        for bit in range(32):
            # Flip one bit in W1
            mod_free = list(W1_free4)
            mod_free[word_idx] ^= (1 << bit)
            mod_tail = build_schedule_tail(W1_pre, mod_free)
            mod_trace = run_tail(state1, mod_tail)
            new_diff = sum(hw(mod_trace[-1][i] ^ base_trace2[-1][i]) for i in range(8))
            delta = new_diff - base_diff

            if delta < -2:  # Only show significant improvements
                direction = "BETTER" if delta < 0 else "worse"
                print(f"  W1[{57+word_idx}] {bit:4d}    {new_diff:4d}    {delta:+4d}   {direction}")
                best_flips.append((delta, f"W1[{57+word_idx}][{bit}]", new_diff))

    print(f"\nFlipping W2 bits (message 2 modifications):")
    print(f"{'Word':>6} {'Bit':>4} {'New HW63':>9} {'Delta':>7} {'Direction':>10}")
    print("-" * 42)

    for word_idx in range(4):
        for bit in range(32):
            mod_free = list(W2_free4)
            mod_free[word_idx] ^= (1 << bit)
            mod_tail = build_schedule_tail(W2_pre, mod_free)
            mod_trace = run_tail(state2, mod_tail)
            new_diff = sum(hw(base_trace1[-1][i] ^ mod_trace[-1][i]) for i in range(8))
            delta = new_diff - base_diff

            if delta < -2:
                direction = "BETTER" if delta < 0 else "worse"
                print(f"  W2[{57+word_idx}] {bit:4d}    {new_diff:4d}    {delta:+4d}   {direction}")
                best_flips.append((delta, f"W2[{57+word_idx}][{bit}]", new_diff))

    best_flips.sort()
    print(f"\n{'='*50}")
    print(f"TOP 20 MOST IMPACTFUL SINGLE-BIT MODIFICATIONS:")
    print(f"{'='*50}")
    for delta, name, new_hw in best_flips[:20]:
        print(f"  {name:20s}  delta={delta:+4d}  new_hw63={new_hw}")

    return best_flips


def greedy_hill_climb(state1, state2, W1_pre, W2_pre, W1_free4, W2_free4, max_steps=500):
    """
    Greedy hill-climbing: at each step, flip the single bit that most reduces
    the round-63 state diff HW.
    """
    print("\n" + "=" * 90)
    print("GREEDY HILL CLIMB: Iterative message modification")
    print("=" * 90)

    cur_w1 = list(W1_free4)
    cur_w2 = list(W2_free4)

    W1_tail = build_schedule_tail(W1_pre, cur_w1)
    W2_tail = build_schedule_tail(W2_pre, cur_w2)
    trace1 = run_tail(state1, W1_tail)
    trace2 = run_tail(state2, W2_tail)
    cur_hw = sum(hw(trace1[-1][i] ^ trace2[-1][i]) for i in range(8))

    print(f"Starting HW: {cur_hw}")
    history = [cur_hw]

    for step in range(max_steps):
        best_delta = 0
        best_move = None

        # Try all single-bit flips in W1 and W2
        for msg in [1, 2]:
            for word_idx in range(4):
                for bit in range(32):
                    if msg == 1:
                        mod = list(cur_w1)
                        mod[word_idx] ^= (1 << bit)
                        tail = build_schedule_tail(W1_pre, mod)
                        t = run_tail(state1, tail)
                        new_hw = sum(hw(t[-1][i] ^ trace2[-1][i]) for i in range(8))
                    else:
                        mod = list(cur_w2)
                        mod[word_idx] ^= (1 << bit)
                        tail = build_schedule_tail(W2_pre, mod)
                        t = run_tail(state2, tail)
                        new_hw = sum(hw(trace1[-1][i] ^ t[-1][i]) for i in range(8))

                    delta = new_hw - cur_hw
                    if delta < best_delta:
                        best_delta = delta
                        best_move = (msg, word_idx, bit, new_hw)

        if best_move is None or best_delta >= 0:
            print(f"Step {step}: STUCK at HW={cur_hw} (no improving move)")
            break

        msg, word_idx, bit, new_hw = best_move
        if msg == 1:
            cur_w1[word_idx] ^= (1 << bit)
        else:
            cur_w2[word_idx] ^= (1 << bit)

        # Recompute both traces
        W1_tail = build_schedule_tail(W1_pre, cur_w1)
        W2_tail = build_schedule_tail(W2_pre, cur_w2)
        trace1 = run_tail(state1, W1_tail)
        trace2 = run_tail(state2, W2_tail)
        cur_hw = sum(hw(trace1[-1][i] ^ trace2[-1][i]) for i in range(8))
        history.append(cur_hw)

        label = f"W{msg}[{57+word_idx}][{bit}]"
        print(f"Step {step:3d}: flip {label:20s}  HW: {cur_hw:3d} (delta={best_delta:+d})")

        if cur_hw == 0:
            print(f"\n*** COLLISION FOUND AT STEP {step}! ***")
            print(f"W1_free = {[f'0x{w:08x}' for w in cur_w1]}")
            print(f"W2_free = {[f'0x{w:08x}' for w in cur_w2]}")
            return cur_w1, cur_w2, history

    # Check intermediate rounds too
    print(f"\nFinal HW at each round:")
    for r in range(len(trace1)):
        rh = sum(hw(trace1[r][i] ^ trace2[r][i]) for i in range(8))
        label = f"round {56+r}" if r > 0 else "entry (r56)"
        print(f"  {label}: HW={rh}")

    print(f"\nFinal W1_free = {[f'0x{w:08x}' for w in cur_w1]}")
    print(f"Final W2_free = {[f'0x{w:08x}' for w in cur_w2]}")
    return cur_w1, cur_w2, history


def random_restart_climb(state1, state2, W1_pre, W2_pre, n_restarts=50, max_steps=200):
    """Multiple random restarts with greedy hill climbing."""
    import random

    print("\n" + "=" * 90)
    print(f"RANDOM RESTART HILL CLIMB: {n_restarts} restarts x {max_steps} steps")
    print("=" * 90)

    global_best_hw = 256
    global_best_w1 = None
    global_best_w2 = None

    for restart in range(n_restarts):
        # Random starting point
        w1 = [random.getrandbits(32) for _ in range(4)]
        w2 = [random.getrandbits(32) for _ in range(4)]

        W1_tail = build_schedule_tail(W1_pre, w1)
        W2_tail = build_schedule_tail(W2_pre, w2)
        t1 = run_tail(state1, W1_tail)
        t2 = run_tail(state2, W2_tail)
        cur_hw = sum(hw(t1[-1][i] ^ t2[-1][i]) for i in range(8))

        for step in range(max_steps):
            best_delta = 0
            best_move = None

            for msg in [1, 2]:
                for word_idx in range(4):
                    for bit in range(32):
                        if msg == 1:
                            mod = list(w1); mod[word_idx] ^= (1 << bit)
                            tail = build_schedule_tail(W1_pre, mod)
                            t = run_tail(state1, tail)
                            new_hw = sum(hw(t[-1][i] ^ t2[-1][i]) for i in range(8))
                        else:
                            mod = list(w2); mod[word_idx] ^= (1 << bit)
                            tail = build_schedule_tail(W2_pre, mod)
                            t = run_tail(state2, tail)
                            new_hw = sum(hw(t1[-1][i] ^ t[-1][i]) for i in range(8))

                        delta = new_hw - cur_hw
                        if delta < best_delta:
                            best_delta = delta
                            best_move = (msg, word_idx, bit, new_hw)

            if best_move is None or best_delta >= 0:
                break

            msg, word_idx, bit, new_hw = best_move
            if msg == 1:
                w1[word_idx] ^= (1 << bit)
            else:
                w2[word_idx] ^= (1 << bit)

            W1_tail = build_schedule_tail(W1_pre, w1)
            W2_tail = build_schedule_tail(W2_pre, w2)
            t1 = run_tail(state1, W1_tail)
            t2 = run_tail(state2, W2_tail)
            cur_hw = sum(hw(t1[-1][i] ^ t2[-1][i]) for i in range(8))

            if cur_hw == 0:
                print(f"\n*** COLLISION FOUND at restart {restart}, step {step}! ***")
                print(f"W1 = {[f'0x{w:08x}' for w in w1]}")
                print(f"W2 = {[f'0x{w:08x}' for w in w2]}")
                return w1, w2

        if cur_hw < global_best_hw:
            global_best_hw = cur_hw
            global_best_w1 = list(w1)
            global_best_w2 = list(w2)
            print(f"  Restart {restart:3d}: stuck at HW={cur_hw} after {step+1} steps  ** NEW BEST **")
        elif restart % 10 == 0:
            print(f"  Restart {restart:3d}: stuck at HW={cur_hw} (global best: {global_best_hw})")

    print(f"\nGlobal best HW: {global_best_hw}")
    print(f"Best W1 = {[f'0x{w:08x}' for w in global_best_w1]}")
    print(f"Best W2 = {[f'0x{w:08x}' for w in global_best_w2]}")
    return global_best_w1, global_best_w2


if __name__ == "__main__":
    # Published candidate
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = precompute(M1)
    state2, W2_pre = precompute(M2)
    assert state1[0] == state2[0], "da[56] != 0"

    print(f"Candidate M[0] = 0x{M1[0]:08x}")
    print(f"State1[0..3] = {[f'0x{v:08x}' for v in state1[:4]]}")
    print(f"State2[0..3] = {[f'0x{v:08x}' for v in state2[:4]]}")
    print(f"da[56] = 0x{state1[0] ^ state2[0]:08x} (should be 0)")

    # Known sr=59 free words (5 words each)
    sr59_W1 = [0x35ff2fce, 0x091194cf, 0x92290bc7, 0xc136a254, 0xc6841268]
    sr59_W2 = [0x0c16533d, 0x8792091f, 0x93a0f3b6, 0x8b270b72, 0x40110184]

    # Build full schedule tails for sr=59 (to see the collision at round 59)
    W1_tail_59 = list(sr59_W1)
    W1_tail_59.append(add(s1(sr59_W1[3]), W1_pre[55], s0(W1_pre[47]), W1_pre[46]))
    W1_tail_59.append(add(s1(sr59_W1[4]), W1_pre[56], s0(W1_pre[48]), W1_pre[47]))
    W2_tail_59 = list(sr59_W2)
    W2_tail_59.append(add(s1(sr59_W2[3]), W2_pre[55], s0(W2_pre[47]), W2_pre[46]))
    W2_tail_59.append(add(s1(sr59_W2[4]), W2_pre[56], s0(W2_pre[48]), W2_pre[47]))

    print("\n\n===== PART 1: sr=59 COLLISION TRAIL ANALYSIS =====")
    analyze_differential(state1, state2, W1_tail_59, W2_tail_59)

    # Now analyze sr=60 with the same W[57..60] (first 4 free words)
    W1_free4 = sr59_W1[:4]
    W2_free4 = sr59_W2[:4]
    W1_tail_60 = build_schedule_tail(W1_pre, W1_free4)
    W2_tail_60 = build_schedule_tail(W2_pre, W2_free4)

    print("\n\n===== PART 2: sr=60 WITH sr=59's W[57..60] =====")
    analyze_differential(state1, state2, W1_tail_60, W2_tail_60)

    # Sensitivity analysis
    print("\n\n===== PART 3: SENSITIVITY ANALYSIS =====")
    sensitivity_analysis(state1, state2, W1_pre, W2_pre, W1_free4, W2_free4)

    # Greedy hill climb from sr=59 starting point
    print("\n\n===== PART 4: GREEDY HILL CLIMB (from sr=59 start) =====")
    greedy_hill_climb(state1, state2, W1_pre, W2_pre, W1_free4, W2_free4, max_steps=300)

    # Random restart search
    if "--search" in sys.argv:
        print("\n\n===== PART 5: RANDOM RESTART SEARCH =====")
        random_restart_climb(state1, state2, W1_pre, W2_pre,
                            n_restarts=100, max_steps=300)

#!/usr/bin/env python3
"""
Hill-climbing search in cascade-constrained space.

Starting from a random (or given) (W[57], W[58], W[59]) triple with
cascade constraints applied, repeatedly perturb single bits of
(W1[58], W2[58], W1[59], W2[59]) and accept any perturbation that
reduces the total output HW at round 63.

If the landscape has exploitable local structure, this should beat
random sampling. If it doesn't, the minimum will plateau at the
same HW~75 as random.

Usage: python3 cascade_hillclimb.py [n_restarts] [steps_per_restart]
"""

import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def precompute_offsets(m0, fill):
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    dT2 = (T2_1 - T2_2) & MASK
    C_w57 = (dh + dSig1 + dCh + dT2) & MASK

    return s1, s2, W1_pre, W2_pre, C_w57


def one_round(s, w, i):
    T1 = add(s[7], Sigma1(s[4]), Ch(s[4], s[5], s[6]), K[i], w)
    T2 = add(Sigma0(s[0]), Maj(s[0], s[1], s[2]))
    return (add(T1, T2), s[0], s[1], s[2], add(s[3], T1), s[4], s[5], s[6])


def evaluate(s1_init, s2_init, W1_pre, W2_pre, C_w57,
             w1_57, w1_58, w2_58, w1_59, w2_59, w1_60):
    """Full evaluation with cascade constraints. Returns total HW at round 63."""
    w2_57 = (w1_57 + C_w57) & MASK

    s1 = one_round(s1_init, w1_57, 57)
    s2 = one_round(s2_init, w2_57, 57)
    s1 = one_round(s1, w1_58, 58)
    s2 = one_round(s2, w2_58, 58)
    s1 = one_round(s1, w1_59, 59)
    s2 = one_round(s2, w2_59, 59)

    dh59 = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    C_w60 = (dh59 + dSig1 + dCh) & MASK

    w2_60 = (w1_60 + C_w60) & MASK

    W1_tail = build_schedule_tail(W1_pre, [w1_57, w1_58, w1_59, w1_60])
    W2_tail = build_schedule_tail(W2_pre, [w2_57, w2_58, w2_59, w2_60])
    t1 = run_tail_rounds(s1_init, W1_tail)
    t2 = run_tail_rounds(s2_init, W2_tail)
    f1, f2 = t1[-1], t2[-1]
    total = sum(hw(f1[r] ^ f2[r]) for r in range(8))
    return total


def hill_climb(s1_init, s2_init, W1_pre, W2_pre, C_w57, rng, max_steps, start=None):
    """Single restart of hill climbing."""
    # Random start unless provided
    if start is None:
        state = [
            rng.getrandbits(32),  # w1_57
            rng.getrandbits(32),  # w1_58
            rng.getrandbits(32),  # w2_58
            rng.getrandbits(32),  # w1_59
            rng.getrandbits(32),  # w2_59
            rng.getrandbits(32),  # w1_60
        ]
    else:
        state = list(start)

    # These 6 free 32-bit words = 192 perturbable bits
    # (W[57] and W[60] are technically also free, but they're the cascade anchors)
    # Each step: flip one random bit in one of the 6 words, accept if HW decreases

    best_hw = evaluate(s1_init, s2_init, W1_pre, W2_pre, C_w57, *state)

    for step in range(max_steps):
        # Pick a random word and bit to flip
        word_idx = rng.randint(0, 5)
        bit = rng.randint(0, 31)
        state[word_idx] ^= (1 << bit)

        new_hw = evaluate(s1_init, s2_init, W1_pre, W2_pre, C_w57, *state)
        if new_hw < best_hw:
            best_hw = new_hw
            if new_hw == 0:
                return best_hw, state, step
        else:
            # Reject: undo the flip
            state[word_idx] ^= (1 << bit)

    return best_hw, state, max_steps


def main():
    n_restarts = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    steps_per_restart = int(sys.argv[2]) if len(sys.argv) > 2 else 2000

    m0 = 0x17149975
    fill = 0xFFFFFFFF

    print(f"Hill climbing in cascade-constrained space")
    print(f"Candidate: M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print(f"Restarts: {n_restarts}, Steps per restart: {steps_per_restart}")
    print(f"Total evaluations: ~{n_restarts * steps_per_restart:,}")
    print()

    s1, s2, W1_pre, W2_pre, C_w57 = precompute_offsets(m0, fill)
    rng = random.Random(42)

    t0 = time.time()
    global_best_hw = 256
    global_best_state = None
    hw_per_restart = []

    for r in range(n_restarts):
        best_hw, best_state, steps = hill_climb(
            s1, s2, W1_pre, W2_pre, C_w57, rng, steps_per_restart)
        hw_per_restart.append(best_hw)

        if best_hw < global_best_hw:
            global_best_hw = best_hw
            global_best_state = list(best_state)
            print(f"  [restart {r:>3}] NEW GLOBAL BEST: HW={best_hw}", flush=True)
            if best_hw == 0:
                print(f"  COLLISION! State = {[f'0x{w:08x}' for w in best_state]}")
                break
        elif r % 10 == 0:
            rate = (r + 1) * steps_per_restart / (time.time() - t0)
            print(f"  [restart {r:>3}] best_hw={best_hw}, global={global_best_hw}, "
                  f"{rate:.0f} eval/s", flush=True)

    t1 = time.time() - t0
    print(f"\nDone in {t1:.1f}s")
    print(f"Global best HW: {global_best_hw}")
    print(f"Mean restart best: {sum(hw_per_restart)/len(hw_per_restart):.1f}")
    print(f"Min restart best: {min(hw_per_restart)}")
    print(f"Max restart best: {max(hw_per_restart)}")


if __name__ == "__main__":
    main()

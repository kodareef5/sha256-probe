#!/usr/bin/env python3
"""
W2-CT1 (FLAGSHIP, Batch A) — Is the 132 hard-core mask the corank of the diff-linear control map?

Card claim: the 132 hard-core output bits = the uncontrollable subspace (cokernel of the
reachability/control map). Repo ground truth (writeups/hard_core_132_bits.md): from a diff-linear
controller census, 132 of 256 output bits have ZERO deterministic control = {a,b,e,f}@63 (128) + 4 dc.

This probe FAITHFULLY reproduces the repo's method: a single-bit-flip deterministic-control census on
the REAL modular sr=60 tail (rounds 57..63, carries included). For each free-schedule input bit i in
W[57..60] (128 input bits) and each output register bit j (256), input i "deterministically controls"
output j iff flipping i flips j for EVERY random base point. Output bits with 0 controllers = hard core.

Reuses lib.sha256 via shabridge. Full width N=32 (the 132 is a 32-bit-width phenomenon). Throttled.
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s

REG = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')
INPUT_BITS = 128          # W[57..60], 4 words x 32 bits
N_OUT = 256               # 8 registers x 32 bits at round 63
SAMPLES = 80              # >=30 makes a prob-1/2 bit surviving "always-flip" ~2^-80; 80 is overkill-safe

def tail_state63_packed(state56, Wpre, free):
    """Output the round-63 register state (a..h) packed into a 256-bit int. Only the tail depends on `free`."""
    sched = s.build_schedule_tail(Wpre, free)          # W[57..63] from the 4 free words
    states = s.run_tail_rounds(state56, sched, start_round=57)
    final = states[-1]                                  # (a,b,c,d,e,f,g,h) after round 63
    out = 0
    for k, w in enumerate(final):
        out |= (w & 0xffffffff) << (32 * k)
    return out

def main():
    rng = random.Random(20260603)
    # flip_count[j][i] = # of samples in which flipping input bit i flipped output bit j
    flip_count = [[0] * INPUT_BITS for _ in range(N_OUT)]
    for _ in range(SAMPLES):
        M = [rng.getrandbits(32) for _ in range(16)]
        state56, Wpre = s.precompute_state(M)           # 57-round precompute depends only on M
        free0 = [rng.getrandbits(32) for _ in range(4)]
        base = tail_state63_packed(state56, Wpre, free0)
        for i in range(INPUT_BITS):
            w, b = divmod(i, 32)
            free1 = list(free0); free1[w] ^= (1 << b)
            resp = tail_state63_packed(state56, Wpre, free1) ^ base
            if resp:
                row = flip_count
                jj = resp
                # iterate only set bits of resp
                while jj:
                    j = (jj & -jj).bit_length() - 1
                    row[j][i] += 1
                    jj &= jj - 1

    # deterministic controller of output j = input i that flips j in ALL samples
    controllers = [sum(1 for i in range(INPUT_BITS) if flip_count[j][i] == SAMPLES) for j in range(N_OUT)]
    hard = [j for j in range(N_OUT) if controllers[j] == 0]

    # per-register breakdown
    print(f"SAMPLES={SAMPLES}  INPUT_BITS={INPUT_BITS}  N_OUT={N_OUT}")
    print(f"{'reg':>4} | zero-control bits / 32 | controllers-per-bit range")
    per_reg_zero = {}
    for k, name in enumerate(REG):
        rng_bits = range(32 * k, 32 * k + 32)
        zero = [j for j in rng_bits if controllers[j] == 0]
        ctl = [controllers[j] for j in rng_bits]
        nz = [c for c in ctl if c > 0]
        per_reg_zero[name] = len(zero)
        rngtxt = f"{min(nz)}-{max(nz)}" if nz else "(all zero)"
        print(f"{name:>4} | {len(zero):>20}/32 | {rngtxt}")

    total_hard = len(hard)
    print(f"\nTOTAL hard-core (zero-control) output bits = {total_hard}   [repo ground truth: 132]")
    print(f"corank check: 256 - rank = {total_hard};  implied control rank = {256 - total_hard}  [repo: 124]")

    # support match: expect a,b,e,f fully (128) + a few dc
    abef = per_reg_zero['a'] + per_reg_zero['b'] + per_reg_zero['e'] + per_reg_zero['f']
    dc_hard = [j - 64 for j in hard if 64 <= j < 96]
    print(f"\nsupport: a,b,e,f zero-control total = {abef}/128 ;  dc zero-control bits = {per_reg_zero['c']} "
          f"(positions {sorted(dc_hard)})")
    print(f"d,g,h zero-control = {per_reg_zero['d']},{per_reg_zero['g']},{per_reg_zero['h']} (expect ~0 each)")

    verdict = ("MATCH-132" if total_hard == 132 else
               f"OFF-BY-{total_hard-132}" if abef == 128 else "STRUCTURE-DIFFERS")
    print(f"\n==> deterministic-control corank = {total_hard}; abef={abef}/128 -> {verdict}")

if __name__ == '__main__':
    main()

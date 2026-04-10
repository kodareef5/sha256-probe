#!/usr/bin/env python3
"""
GPU genetic algorithm for sr=61 — evolves (W57, W58, W59) triples.

After random brute force plateau (HW=76 across 172B samples) and
single-bit hill climbing (HW=78), neither pure random nor pure local
search can break the structural floor.

This tool maintains a POPULATION of (W57, W58, W59) triples, applies
mutation + crossover + tournament selection. Different from both:
- Random search: maintains state across generations (vs i.i.d.)
- Hill climb: population diversity escapes local minima

Fitness: -HW(state delta at round 63) under sr=61 schedule rules.

Population size: 65536 (thousands of "individuals" in parallel)
Generations: many thousands per hour
"""
import sys, os, time
import torch

K32 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]
IV32 = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]
MASK = 0xFFFFFFFF


def to_signed_i32(v):
    return v if v < 0x80000000 else v - 0x100000000


def precompute_state(M):
    def sigma0(x): return ((x>>7|x<<25)&MASK) ^ ((x>>18|x<<14)&MASK) ^ (x>>3)
    def sigma1(x): return ((x>>17|x<<15)&MASK) ^ ((x>>19|x<<13)&MASK) ^ (x>>10)
    W = list(M) + [0]*48
    for i in range(16, 64):
        W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & MASK
    a,b,c,d,e,f,g,h = IV32
    for i in range(57):
        S1 = ((e>>6|e<<26)&MASK) ^ ((e>>11|e<<21)&MASK) ^ ((e>>25|e<<7)&MASK)
        ch = (e&f) ^ ((~e&MASK)&g)
        T1 = (h + S1 + ch + K32[i] + W[i]) & MASK
        S0 = ((a>>2|a<<30)&MASK) ^ ((a>>13|a<<19)&MASK) ^ ((a>>22|a<<10)&MASK)
        maj = (a&b) ^ (a&c) ^ (b&c)
        T2 = (S0 + maj) & MASK
        h,g,f,e,d,c,b,a = g,f,e,(d+T1)&MASK,c,b,a,(T1+T2)&MASK
    return [a,b,c,d,e,f,g,h], W


def cpu_sigma0(x): return ((x>>7|x<<25)&MASK) ^ ((x>>18|x<<14)&MASK) ^ (x>>3)
def cpu_sigma1(x): return ((x>>17|x<<15)&MASK) ^ ((x>>19|x<<13)&MASK) ^ (x>>10)


def gpu_genetic(m0=0x17149975, fill=0xffffffff,
                pop_size=1<<16, hours=8.0,
                mutation_rate=0.01, crossover_rate=0.7,
                tournament_size=4):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"GPU sr=61 GENETIC algorithm", flush=True)
    print(f"Candidate: M[0]=0x{m0:08x}, fill=0x{fill:08x}", flush=True)
    print(f"Pop size: {pop_size}, mut rate: {mutation_rate}, "
          f"crossover: {crossover_rate}, tournament: {tournament_size}", flush=True)
    print(f"Device: {device}, hours: {hours}", flush=True)

    # Build messages and precompute states
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000
    state1, W1_pre = precompute_state(M1)
    state2, W2_pre = precompute_state(M2)
    assert state1[0] == state2[0]

    sched_C1 = [
        (W1_pre[53] + cpu_sigma0(W1_pre[45]) + W1_pre[44]) & MASK,
        (W1_pre[54] + cpu_sigma0(W1_pre[46]) + W1_pre[45]) & MASK,
        (W1_pre[55] + cpu_sigma0(W1_pre[47]) + W1_pre[46]) & MASK,
        (W1_pre[56] + cpu_sigma0(W1_pre[48]) + W1_pre[47]) & MASK,
    ]
    sched_C2 = [
        (W2_pre[53] + cpu_sigma0(W2_pre[45]) + W2_pre[44]) & MASK,
        (W2_pre[54] + cpu_sigma0(W2_pre[46]) + W2_pre[45]) & MASK,
        (W2_pre[55] + cpu_sigma0(W2_pre[47]) + W2_pre[46]) & MASK,
        (W2_pre[56] + cpu_sigma0(W2_pre[48]) + W2_pre[47]) & MASK,
    ]

    K_gpu = torch.tensor([to_signed_i32(K32[57+i]) for i in range(7)],
                          dtype=torch.int32, device=device)
    state1_gpu = torch.tensor([to_signed_i32(s) for s in state1],
                               dtype=torch.int32, device=device)
    state2_gpu = torch.tensor([to_signed_i32(s) for s in state2],
                               dtype=torch.int32, device=device)
    sched_C1_gpu = torch.tensor([to_signed_i32(c) for c in sched_C1],
                                 dtype=torch.int32, device=device)
    sched_C2_gpu = torch.tensor([to_signed_i32(c) for c in sched_C2],
                                 dtype=torch.int32, device=device)

    def ror(x, k):
        return ((x >> k) & ((1 << (32-k)) - 1)) | ((x << (32-k)))

    def Sigma0_g(x): return ror(x, 2) ^ ror(x, 13) ^ ror(x, 22)
    def Sigma1_g(x): return ror(x, 6) ^ ror(x, 11) ^ ror(x, 25)
    def sigma0_g(x): return ror(x, 7) ^ ror(x, 18) ^ ((x >> 3) & 0x1FFFFFFF)
    def sigma1_g(x): return ror(x, 17) ^ ror(x, 19) ^ ((x >> 10) & 0x003FFFFF)

    def do_round(state, Ki, Wi):
        a, b, c, d, e, f, g, h = state
        S1 = Sigma1_g(e); ch = (e & f) ^ (~e & g)
        T1 = h + S1 + ch + Ki + Wi
        S0 = Sigma0_g(a); maj = (a & b) ^ (a & c) ^ (b & c)
        T2 = S0 + maj
        return [T1+T2, a, b, c, d+T1, e, f, g]

    def evaluate(w57, w58, w59):
        """Compute HW of state delta at round 63 for population."""
        bs = w57.shape[0]
        # sr=61 schedule rules
        w1_60 = sigma1_g(w58) + sched_C1_gpu[0]
        w2_60 = sigma1_g(w58) + sched_C2_gpu[0]
        w1_61 = sigma1_g(w59) + sched_C1_gpu[1]
        w2_61 = sigma1_g(w59) + sched_C2_gpu[1]
        w1_62 = sigma1_g(w1_60) + sched_C1_gpu[2]
        w2_62 = sigma1_g(w2_60) + sched_C2_gpu[2]
        w1_63 = sigma1_g(w1_61) + sched_C1_gpu[3]
        w2_63 = sigma1_g(w2_61) + sched_C2_gpu[3]

        s1 = [state1_gpu[i].expand(bs).clone() for i in range(8)]
        for i, Wi in enumerate([w57, w58, w59, w1_60, w1_61, w1_62, w1_63]):
            s1 = do_round(s1, K_gpu[i], Wi)

        s2 = [state2_gpu[i].expand(bs).clone() for i in range(8)]
        for i, Wi in enumerate([w57, w58, w59, w2_60, w2_61, w2_62, w2_63]):
            s2 = do_round(s2, K_gpu[i], Wi)

        delta = [s1[i] ^ s2[i] for i in range(8)]
        hw = torch.zeros(bs, dtype=torch.int32, device=device)
        for d in delta:
            x = d
            x = x - ((x >> 1) & 0x55555555)
            x = (x & 0x33333333) + ((x >> 2) & 0x33333333)
            x = (x + (x >> 4)) & 0x0F0F0F0F
            x = (x * 0x01010101) >> 24
            hw = hw + (x & 0xFF)
        return hw

    # Initialize population
    print(f"Initializing population...", flush=True)
    pop_w57 = torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                             dtype=torch.int32, device=device)
    pop_w58 = torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                             dtype=torch.int32, device=device)
    pop_w59 = torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                             dtype=torch.int32, device=device)

    # Seed: include cert values as starting points
    cert_w57 = to_signed_i32(0x9ccfa55e)
    cert_w58 = to_signed_i32(0xd9d64416)
    cert_w59 = to_signed_i32(0x9e3ffb08)
    pop_w57[0] = cert_w57; pop_w58[0] = cert_w58; pop_w59[0] = cert_w59

    fitness = evaluate(pop_w57, pop_w58, pop_w59)
    best_hw = fitness.min().item()
    best_idx = fitness.argmin().item()
    print(f"Initial best: HW={best_hw}", flush=True)
    print(f"Initial cert (idx 0): HW={fitness[0].item()}", flush=True)

    t0 = time.time()
    last_log = t0
    gen = 0
    last_improve_gen = 0

    while time.time() - t0 < hours * 3600:
        gen += 1

        # --- Tournament selection ---
        # Pick tournament_size random indices for each slot, take the best
        tournament_idx = torch.randint(0, pop_size,
                                        (pop_size, tournament_size),
                                        dtype=torch.long, device=device)
        tournament_fit = fitness[tournament_idx]  # (pop, tournament)
        winner_idx_in_tournament = tournament_fit.argmin(dim=1)  # (pop,)
        winners = tournament_idx.gather(1, winner_idx_in_tournament.unsqueeze(1)).squeeze(1)

        new_w57 = pop_w57[winners].clone()
        new_w58 = pop_w58[winners].clone()
        new_w59 = pop_w59[winners].clone()

        # --- Crossover (uniform per word) ---
        cross_mask = torch.rand(pop_size, device=device) < crossover_rate
        if cross_mask.any():
            partner_idx = torch.randint(0, pop_size, (pop_size,),
                                          dtype=torch.long, device=device)
            partner_w57 = new_w57[partner_idx]
            partner_w58 = new_w58[partner_idx]
            partner_w59 = new_w59[partner_idx]
            # Per-bit uniform crossover
            cmask57 = torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                                     dtype=torch.int32, device=device)
            cmask58 = torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                                     dtype=torch.int32, device=device)
            cmask59 = torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                                     dtype=torch.int32, device=device)
            cross_active = cross_mask
            new_w57 = torch.where(cross_active,
                                   (new_w57 & cmask57) | (partner_w57 & ~cmask57),
                                   new_w57)
            new_w58 = torch.where(cross_active,
                                   (new_w58 & cmask58) | (partner_w58 & ~cmask58),
                                   new_w58)
            new_w59 = torch.where(cross_active,
                                   (new_w59 & cmask59) | (partner_w59 & ~cmask59),
                                   new_w59)

        # --- Mutation (vectorized) ---
        # Generate random uint32 masks, then keep only bits that should mutate.
        # Per-bit probability = mutation_rate. We use a sampled approach:
        # for each int32, generate ~32*mut_rate random bit positions to flip.
        # Approximation: use Bernoulli sampling at int32 level for low-rate mutation.
        # For mut_rate=0.01, expected ~0.32 bits flipped per word.
        # Generate 5-bit random positions and a "flip or not" mask.
        n_flips_expected = max(1, int(round(32 * mutation_rate)))
        # Easier: generate 32-bit random uints, AND with another 32-bit random uint,
        # AND again. P(bit set) = 1/8 with 3 ANDs, 1/16 with 4 ANDs, 1/32 with 5 ANDs.
        # mut_rate=0.01 ≈ 1/100, need ~7 ANDs. Use 6 for ~1/64 ≈ 0.016.
        if mutation_rate <= 0.02:
            n_ands = 6
        elif mutation_rate <= 0.04:
            n_ands = 5
        else:
            n_ands = 4
        mut_w57 = torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                                 dtype=torch.int32, device=device)
        mut_w58 = torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                                 dtype=torch.int32, device=device)
        mut_w59 = torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                                 dtype=torch.int32, device=device)
        for _ in range(n_ands - 1):
            mut_w57 = mut_w57 & torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                                                dtype=torch.int32, device=device)
            mut_w58 = mut_w58 & torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                                                dtype=torch.int32, device=device)
            mut_w59 = mut_w59 & torch.randint(-(1<<31), (1<<31)-1, (pop_size,),
                                                dtype=torch.int32, device=device)
        new_w57 = new_w57 ^ mut_w57
        new_w58 = new_w58 ^ mut_w58
        new_w59 = new_w59 ^ mut_w59

        # --- Evaluate new population ---
        new_fitness = evaluate(new_w57, new_w58, new_w59)

        # --- Elitism: keep best individual from old population ---
        old_best = fitness.min().item()
        old_best_idx = fitness.argmin().item()
        new_worst = new_fitness.max().item()
        new_worst_idx = new_fitness.argmax().item()
        if old_best < new_fitness.min().item():
            new_w57[new_worst_idx] = pop_w57[old_best_idx]
            new_w58[new_worst_idx] = pop_w58[old_best_idx]
            new_w59[new_worst_idx] = pop_w59[old_best_idx]
            new_fitness[new_worst_idx] = old_best

        pop_w57 = new_w57
        pop_w58 = new_w58
        pop_w59 = new_w59
        fitness = new_fitness

        cur_best = fitness.min().item()
        if cur_best < best_hw:
            best_hw = cur_best
            best_idx = fitness.argmin().item()
            elapsed = time.time() - t0
            last_improve_gen = gen
            print(f"  gen {gen}: NEW BEST HW={best_hw} "
                  f"W57={pop_w57[best_idx].item() & 0xFFFFFFFF:08x} "
                  f"W58={pop_w58[best_idx].item() & 0xFFFFFFFF:08x} "
                  f"W59={pop_w59[best_idx].item() & 0xFFFFFFFF:08x} "
                  f"[{elapsed:.0f}s]", flush=True)

        now = time.time()
        if now - last_log > 60:
            elapsed = now - t0
            mean_fit = fitness.float().mean().item()
            std_fit = fitness.float().std().item()
            print(f"  gen {gen}: best={best_hw} mean={mean_fit:.1f} "
                  f"std={std_fit:.1f} stagnant={gen - last_improve_gen} gens "
                  f"[{elapsed:.0f}s, {gen/elapsed:.1f} gen/s]", flush=True)
            last_log = now

        # If too stagnant, inject random individuals
        if gen - last_improve_gen > 500 and gen % 200 == 0:
            n_replace = pop_size // 4
            new_idx = torch.randperm(pop_size, device=device)[:n_replace]
            pop_w57[new_idx] = torch.randint(-(1<<31), (1<<31)-1, (n_replace,),
                                              dtype=torch.int32, device=device)
            pop_w58[new_idx] = torch.randint(-(1<<31), (1<<31)-1, (n_replace,),
                                              dtype=torch.int32, device=device)
            pop_w59[new_idx] = torch.randint(-(1<<31), (1<<31)-1, (n_replace,),
                                              dtype=torch.int32, device=device)
            fitness[new_idx] = evaluate(pop_w57[new_idx], pop_w58[new_idx], pop_w59[new_idx])

    elapsed = time.time() - t0
    print(f"\n{'='*60}", flush=True)
    print(f"COMPLETE: {gen} generations in {elapsed/3600:.2f}h", flush=True)
    print(f"Best HW: {best_hw}/256", flush=True)
    print(f"Best W57=0x{pop_w57[best_idx].item() & 0xFFFFFFFF:08x} "
          f"W58=0x{pop_w58[best_idx].item() & 0xFFFFFFFF:08x} "
          f"W59=0x{pop_w59[best_idx].item() & 0xFFFFFFFF:08x}", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    m0 = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x17149975
    fill = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0xffffffff
    hours = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
    gpu_genetic(m0, fill, hours=hours)

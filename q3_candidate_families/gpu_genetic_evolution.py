#!/usr/bin/env python3
"""
GPU Genetic Candidate Evolution for sr=60/sr=61.

Evolves (M[0], fill) pairs using GPU-accelerated fitness evaluation.
Instead of brute-force scanning 2^28 M[0] values with fixed fills,
this EVOLVES both M[0] and fill simultaneously using a genetic algorithm.

Fitness: min collision HW over K random free-word samples.
Lower HW = closer to collision = easier for SAT solver.

Population: thousands of candidates evaluated in parallel on GPU.
Selection: tournament selection on fitness.
Mutation: bit-flip, byte-swap, crossover.
Crossover: uniform crossover between (M[0], fill) pairs.

Runs for hours, continuously improving the population.

Usage: python3 gpu_genetic_evolution.py [sr_level] [hours]
  sr_level: 60 or 61 (default 61)
  hours: how long to run (default 4)
"""

import sys, os, time, random
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib.sha256 import K, IV, MASK, hw, add, Sigma0, Sigma1, Ch, Maj, sigma0 as cpu_sigma0, sigma1 as cpu_sigma1

K32 = K
IV32 = IV

def to_i32(v):
    v = v & 0xFFFFFFFF
    return v if v < 0x80000000 else v - 0x100000000

def popcount32(x):
    x = x - ((x >> 1) & 0x55555555)
    x = (x & 0x33333333) + ((x >> 2) & 0x33333333)
    x = (x + (x >> 4)) & 0x0F0F0F0F
    x = x + (x >> 8)
    x = x + (x >> 16)
    return x & 0x3F

def gpu_ror32(x, k):
    return ((x >> k) | (x << (32 - k))) & 0xFFFFFFFF

def gpu_Sigma0(a): return gpu_ror32(a,2)^gpu_ror32(a,13)^gpu_ror32(a,22)
def gpu_Sigma1(e): return gpu_ror32(e,6)^gpu_ror32(e,11)^gpu_ror32(e,25)
def gpu_sigma0(x): return gpu_ror32(x,7)^gpu_ror32(x,18)^((x>>3)&0xFFFFFFFF)
def gpu_sigma1(x): return gpu_ror32(x,17)^gpu_ror32(x,19)^((x>>10)&0xFFFFFFFF)

def gpu_round(state, Ki, Wi):
    a,b,c,d,e,f,g,h = state
    T1 = (h + gpu_Sigma1(e) + ((e&f)^((~e)&g)&0xFFFFFFFF) + Ki + Wi) & 0xFFFFFFFF
    T2 = (gpu_Sigma0(a) + ((a&b)^(a&c)^(b&c)) & 0xFFFFFFFF) & 0xFFFFFFFF
    return [(T1+T2)&0xFFFFFFFF, a, b, c, (d+T1)&0xFFFFFFFF, e, f, g]


def gpu_compress57(m0_batch, fill_batch, device):
    """
    GPU-parallel 57-round compression for batches of (M[0], fill).
    Returns (state1_batch, state2_batch, W1_batch, W2_batch).
    Each state is a list of 8 tensors of shape (batch,).
    """
    bs = m0_batch.shape[0]
    MSB = torch.tensor(to_i32(0x80000000), dtype=torch.int32, device=device)

    KN = [torch.tensor(to_i32(K32[i]), dtype=torch.int32, device=device) for i in range(57)]
    IVN = [torch.tensor(to_i32(IV32[i]), dtype=torch.int32, device=device) for i in range(8)]

    # Build M1, M2
    # M1[0] = m0, M1[1..15] = fill
    # M2[0] = m0 ^ MSB, M2[9] = fill ^ MSB, rest = fill
    W1 = [None]*57
    W2 = [None]*57
    W1[0] = m0_batch
    W2[0] = m0_batch ^ MSB
    for i in range(1, 16):
        if i == 9:
            W1[i] = fill_batch.clone()
            W2[i] = fill_batch ^ MSB
        else:
            W1[i] = fill_batch.clone()
            W2[i] = fill_batch.clone()

    # Schedule expansion
    for i in range(16, 57):
        W1[i] = (gpu_sigma1(W1[i-2]) + W1[i-7] + gpu_sigma0(W1[i-15]) + W1[i-16]) & 0xFFFFFFFF
        W2[i] = (gpu_sigma1(W2[i-2]) + W2[i-7] + gpu_sigma0(W2[i-15]) + W2[i-16]) & 0xFFFFFFFF

    # Compression
    a1,b1,c1,d1,e1,f1,g1,h1 = [iv.expand(bs).clone() for iv in IVN]
    a2,b2,c2,d2,e2,f2,g2,h2 = [iv.expand(bs).clone() for iv in IVN]

    for i in range(57):
        st1 = gpu_round([a1,b1,c1,d1,e1,f1,g1,h1], KN[i], W1[i])
        a1,b1,c1,d1,e1,f1,g1,h1 = st1
        st2 = gpu_round([a2,b2,c2,d2,e2,f2,g2,h2], KN[i], W2[i])
        a2,b2,c2,d2,e2,f2,g2,h2 = st2

    return ([a1,b1,c1,d1,e1,f1,g1,h1],
            [a2,b2,c2,d2,e2,f2,g2,h2],
            W1, W2)


def evaluate_fitness(m0_batch, fill_batch, device, sr=61, n_samples=512):
    """
    Evaluate fitness of a batch of (M[0], fill) candidates.
    Fitness = negative of min collision HW over n_samples random free-word assignments.
    Lower HW = better fitness.

    Returns: (fitness, da56_zero_mask) tensors
    """
    bs = m0_batch.shape[0]

    # Step 1: 57-round compression
    s1, s2, W1_pre, W2_pre = gpu_compress57(m0_batch, fill_batch, device)

    # Step 2: check da[56]=0
    da56 = s1[0] ^ s2[0]
    da56_zero = (da56 == 0)

    # Step 3: for da56=0 candidates, evaluate collision proximity
    # with random free words
    fitness = torch.full((bs,), 256, dtype=torch.int32, device=device)

    valid_idx = da56_zero.nonzero(as_tuple=True)[0]
    if len(valid_idx) == 0:
        return fitness, da56_zero

    # Extract valid candidates
    n_valid = len(valid_idx)

    for sample in range(0, n_samples, max(1, n_samples // 4)):
        actual_samples = min(n_samples // 4, n_samples - sample)
        if actual_samples <= 0:
            break

        for vi in range(n_valid):
            idx = valid_idx[vi].item()
            # Sample random free words
            ns = actual_samples
            if sr == 60:
                w1_57 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w1_58 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w1_59 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w1_60 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w2_57 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w2_58 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w2_59 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w2_60 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
            else:  # sr=61: 3 free words
                w1_57 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w1_58 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w1_59 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w2_57 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w2_58 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                w2_59 = torch.randint(-2**31, 2**31, (ns,), dtype=torch.int32, device=device)
                # W[60] is schedule-determined from W[58]
                w1_60 = gpu_sigma1(w1_58) + W1_pre[53][idx] + torch.tensor(to_i32(cpu_sigma0(W1_pre[45][idx].item() & 0xFFFFFFFF)), dtype=torch.int32, device=device) + W1_pre[44][idx]
                w2_60 = gpu_sigma1(w2_58) + W2_pre[53][idx] + torch.tensor(to_i32(cpu_sigma0(W2_pre[45][idx].item() & 0xFFFFFFFF)), dtype=torch.int32, device=device) + W2_pre[44][idx]

            # Schedule W[61..63]
            w1_61 = gpu_sigma1(w1_59) + W1_pre[54][idx] + torch.tensor(to_i32(cpu_sigma0(W1_pre[46][idx].item() & 0xFFFFFFFF)), dtype=torch.int32, device=device) + W1_pre[45][idx]
            w2_61 = gpu_sigma1(w2_59) + W2_pre[54][idx] + torch.tensor(to_i32(cpu_sigma0(W2_pre[46][idx].item() & 0xFFFFFFFF)), dtype=torch.int32, device=device) + W2_pre[45][idx]
            w1_62 = gpu_sigma1(w1_60) + W1_pre[55][idx] + torch.tensor(to_i32(cpu_sigma0(W1_pre[47][idx].item() & 0xFFFFFFFF)), dtype=torch.int32, device=device) + W1_pre[46][idx]
            w2_62 = gpu_sigma1(w2_60) + W2_pre[55][idx] + torch.tensor(to_i32(cpu_sigma0(W2_pre[47][idx].item() & 0xFFFFFFFF)), dtype=torch.int32, device=device) + W2_pre[46][idx]
            w1_63 = gpu_sigma1(w1_61) + W1_pre[56][idx] + torch.tensor(to_i32(cpu_sigma0(W1_pre[48][idx].item() & 0xFFFFFFFF)), dtype=torch.int32, device=device) + W1_pre[47][idx]
            w2_63 = gpu_sigma1(w2_61) + W2_pre[56][idx] + torch.tensor(to_i32(cpu_sigma0(W2_pre[48][idx].item() & 0xFFFFFFFF)), dtype=torch.int32, device=device) + W2_pre[47][idx]

            Ws1 = [w1_57, w1_58, w1_59, w1_60, w1_61, w1_62, w1_63]
            Ws2 = [w2_57, w2_58, w2_59, w2_60, w2_61, w2_62, w2_63]

            K_tail = [torch.tensor(to_i32(K32[57+j]), dtype=torch.int32, device=device) for j in range(7)]
            st1 = [s1[k][idx].expand(ns) for k in range(8)]
            st2 = [s2[k][idx].expand(ns) for k in range(8)]

            for j in range(7):
                st1 = gpu_round(st1, K_tail[j], Ws1[j])
                st2 = gpu_round(st2, K_tail[j], Ws2[j])

            hw_total = torch.zeros(ns, dtype=torch.int32, device=device)
            for k in range(8):
                hw_total += popcount32(st1[k] ^ st2[k])

            min_hw = hw_total.min().item()
            if min_hw < fitness[idx].item():
                fitness[idx] = min_hw

    return fitness, da56_zero


def run_evolution(sr=61, hours=4, pop_size=2048, n_samples=256):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"GPU Genetic Evolution for sr={sr}", flush=True)
    print(f"Device: {device}, Population: {pop_size}, Samples/eval: {n_samples}", flush=True)
    print(f"Running for {hours}h", flush=True)
    print(flush=True)

    # Initialize population: random (M[0], fill) pairs
    m0_pop = torch.randint(-2**31, 2**31, (pop_size,), dtype=torch.int32, device=device)
    fill_pop = torch.randint(-2**31, 2**31, (pop_size,), dtype=torch.int32, device=device)

    # Seed with known good fills
    known_fills = [0xFFFFFFFF, 0x00000000, 0x55555555, 0xAAAAAAAA, 0x0F0F0F0F,
                   0xF0F0F0F0, 0x000000F0, 0x000000AA, 0x00000055, 0x000000A5]
    for i, f in enumerate(known_fills[:min(len(known_fills), pop_size//10)]):
        fill_pop[i] = torch.tensor(to_i32(f), dtype=torch.int32, device=device)

    best_ever_hw = 256
    best_ever_m0 = 0
    best_ever_fill = 0
    gen = 0
    t0 = time.time()
    da56_hits_total = 0

    while time.time() - t0 < hours * 3600:
        gen += 1

        # Evaluate fitness in batches (57-round compression is memory-heavy)
        BATCH = 256
        all_fitness = torch.full((pop_size,), 256, dtype=torch.int32, device=device)
        all_valid = torch.zeros(pop_size, dtype=torch.bool, device=device)

        for start in range(0, pop_size, BATCH):
            end = min(start + BATCH, pop_size)
            fit, valid = evaluate_fitness(
                m0_pop[start:end], fill_pop[start:end],
                device, sr=sr, n_samples=n_samples)
            all_fitness[start:end] = fit
            all_valid[start:end] = valid

        n_valid = all_valid.sum().item()
        da56_hits_total += n_valid

        # Track best
        if n_valid > 0:
            valid_fit = all_fitness[all_valid]
            best_idx = all_fitness.argmin().item()
            best_hw = all_fitness[best_idx].item()

            if best_hw < best_ever_hw:
                best_ever_hw = best_hw
                best_ever_m0 = m0_pop[best_idx].item() & 0xFFFFFFFF
                best_ever_fill = fill_pop[best_idx].item() & 0xFFFFFFFF
                elapsed = time.time() - t0
                print(f"  gen {gen}: NEW BEST hw={best_ever_hw} "
                      f"M[0]=0x{best_ever_m0:08x} fill=0x{best_ever_fill:08x} "
                      f"({n_valid} da56=0, {elapsed:.0f}s)", flush=True)

        if gen % 20 == 0:
            elapsed = time.time() - t0
            print(f"  gen {gen}: best={best_ever_hw}, da56_hits={da56_hits_total}, "
                  f"{elapsed:.0f}s ({elapsed/3600:.1f}h)", flush=True)

        # Selection: tournament (size 4)
        new_m0 = torch.empty_like(m0_pop)
        new_fill = torch.empty_like(fill_pop)
        for i in range(pop_size):
            # Pick 4 random individuals, select best fitness
            candidates = torch.randint(0, pop_size, (4,))
            best_c = candidates[all_fitness[candidates].argmin()]
            new_m0[i] = m0_pop[best_c]
            new_fill[i] = fill_pop[best_c]

        # Crossover (50% chance per pair)
        for i in range(0, pop_size - 1, 2):
            if random.random() < 0.5:
                # Uniform crossover on M[0]
                mask = torch.randint(0, 2, (32,), device=device)
                cross_mask = 0
                for bit in range(32):
                    if mask[bit]: cross_mask |= (1 << bit)
                cross_t = torch.tensor(to_i32(cross_mask), dtype=torch.int32, device=device)
                m0_a = (new_m0[i] & cross_t) | (new_m0[i+1] & ~cross_t)
                m0_b = (new_m0[i+1] & cross_t) | (new_m0[i] & ~cross_t)
                new_m0[i] = m0_a
                new_m0[i+1] = m0_b
            if random.random() < 0.3:
                # Crossover fill
                new_fill[i], new_fill[i+1] = new_fill[i+1].clone(), new_fill[i].clone()

        # Mutation (bit-flip, 2% per bit)
        for i in range(pop_size):
            if random.random() < 0.3:
                bit = random.randint(0, 31)
                new_m0[i] ^= (1 << bit)
            if random.random() < 0.1:
                bit = random.randint(0, 31)
                new_fill[i] ^= (1 << bit)

        # Elitism: keep top 10%
        if n_valid > 0:
            top_k = max(1, pop_size // 10)
            _, top_idx = all_fitness.topk(top_k, largest=False)
            new_m0[:top_k] = m0_pop[top_idx]
            new_fill[:top_k] = fill_pop[top_idx]

        # Inject fresh random individuals (5%)
        n_fresh = pop_size // 20
        new_m0[-n_fresh:] = torch.randint(-2**31, 2**31, (n_fresh,), dtype=torch.int32, device=device)
        new_fill[-n_fresh:] = torch.randint(-2**31, 2**31, (n_fresh,), dtype=torch.int32, device=device)

        m0_pop = new_m0
        fill_pop = new_fill

    elapsed = time.time() - t0
    print(f"\n{'='*60}", flush=True)
    print(f"EVOLUTION COMPLETE: {gen} generations, {elapsed:.0f}s ({elapsed/3600:.1f}h)", flush=True)
    print(f"Best: hw={best_ever_hw} M[0]=0x{best_ever_m0:08x} fill=0x{best_ever_fill:08x}", flush=True)
    print(f"Total da56=0 hits: {da56_hits_total}", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    sr = int(sys.argv[1]) if len(sys.argv) > 1 else 61
    hours = float(sys.argv[2]) if len(sys.argv) > 2 else 4
    run_evolution(sr=sr, hours=hours)

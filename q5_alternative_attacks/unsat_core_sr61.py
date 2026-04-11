#!/usr/bin/env python3
"""
UNSAT Core Extraction for sr=61

Both external reviewers recommended this: instead of just "sr=61 no solution,"
find EXACTLY which schedule bits/round constraints create the contradiction.

Method: encode sr=61 at N=8 with schedule compliance bits as ACTIVATION LITERALS.
Then use incremental SAT (CaDiCaL assumptions) to find which constraints are
necessary for UNSAT. The minimal UNSAT core tells us the precise obstruction.

Approach:
1. Encode sr=60 (known SAT) as the base formula
2. Add each W[60] schedule bit as a soft constraint with its own activation literal
3. Use CaDiCaL with assumptions to find which bits are needed for UNSAT
4. Binary search for the minimal UNSAT core
"""
import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 600

spec = __import__('50_precision_homotopy')
sha = spec.MiniSHA256(N)
MASK_N = sha.MASK; MSB = sha.MSB
K32 = spec.K32; KT = [k & MASK_N for k in K32]
m0, s1, s2, W1_pre, W2_pre = sha.find_m0()
if m0 is None:
    print(f"No candidate at N={N}"); sys.exit(1)
ops = {'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1, 'r_sig0': sha.r_sig0,
       's_sig0': sha.s_sig0, 'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1}

print(f"UNSAT Core Extraction for sr=61 at N={N}")
print(f"Candidate: M[0]=0x{m0:x}")
print(f"Method: activation literals on W[60] schedule bits")
print(flush=True)

def make_cnf_with_activation():
    """Encode sr=60 base + W[60] schedule constraints as soft clauses."""
    cnf = spec.MiniCNFBuilder(N)
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    # 3 free words (W[57..59]) for sr=61 encoding
    w1f = [cnf.free_word(f"W1_{57+i}") for i in range(3)]
    w2f = [cnf.free_word(f"W2_{57+i}") for i in range(3)]

    # W[60] as free variables (sr=60 style)
    w1_60_free = cnf.free_word("W1_60")
    w2_60_free = cnf.free_word("W2_60")

    # W[60] schedule-determined values
    def sw(x): return cnf.sigma1_w(x, ops['r_sig1'], ops['s_sig1'])
    w1_60_sched = cnf.add_word(cnf.add_word(sw(w1f[1]), cnf.const_word(W1_pre[53])),
                               cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[45])), cnf.const_word(W1_pre[44])))
    w2_60_sched = cnf.add_word(cnf.add_word(sw(w2f[1]), cnf.const_word(W2_pre[53])),
                               cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[45])), cnf.const_word(W2_pre[44])))

    # Activation literals: for each bit of W[60], an activation literal
    # When activation[bit] is TRUE, W[60][bit] must equal schedule value
    activations = []
    for bit in range(N):
        # W1[60][bit] = W1_60_sched[bit] when act is TRUE
        act1 = cnf.new_var()
        # act1 → (w1_60_free[bit] = w1_60_sched[bit])
        # Equiv: ¬act1 ∨ (w1_60_free[bit] ↔ w1_60_sched[bit])
        # Which is: (¬act1 ∨ ¬f ∨ s) ∧ (¬act1 ∨ f ∨ ¬s)
        f_var = w1_60_free[bit]
        s_var = w1_60_sched[bit]
        cnf.clauses.append([-act1, -f_var, s_var])
        cnf.clauses.append([-act1, f_var, -s_var])

        act2 = cnf.new_var()
        f_var2 = w2_60_free[bit]
        s_var2 = w2_60_sched[bit]
        cnf.clauses.append([-act2, -f_var2, s_var2])
        cnf.clauses.append([-act2, f_var2, -s_var2])

        activations.append((act1, act2, bit))

    # Build rest of schedule
    W1s = list(w1f) + [w1_60_free]
    W2s = list(w2f) + [w2_60_free]

    w1_61 = cnf.add_word(cnf.add_word(sw(w1f[2]), cnf.const_word(W1_pre[54])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(cnf.add_word(sw(w2f[2]), cnf.const_word(W2_pre[54])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[46])), cnf.const_word(W2_pre[45])))
    w1_62 = cnf.add_word(cnf.add_word(sw(W1s[3]), cnf.const_word(W1_pre[55])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(cnf.add_word(sw(W2s[3]), cnf.const_word(W2_pre[55])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(cnf.add_word(sw(w1_61), cnf.const_word(W1_pre[56])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(cnf.add_word(sw(w2_61), cnf.const_word(W2_pre[56])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[48])), cnf.const_word(W2_pre[47])))
    W1s.extend([w1_61, w1_62, w1_63]); W2s.extend([w2_61, w2_62, w2_63])

    for i in range(7):
        st1 = cnf.sha256_round(st1, KT[57+i], W1s[i], ops)
        st2 = cnf.sha256_round(st2, KT[57+i], W2s[i], ops)
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf, activations

cnf, activations = make_cnf_with_activation()
td = tempfile.mkdtemp(prefix=f"unsat_core_N{N}_")
cf = os.path.join(td, "sr61_core.cnf")
nv, nc = cnf.write_dimacs(cf)
print(f"CNF: {nv} vars, {nc} clauses")
print(f"Activation literals: {len(activations)} pairs ({2*len(activations)} total)")
print(flush=True)

# Phase 1: Verify sr=60 is SAT (no activations forced)
print(f"\n=== Phase 1: sr=60 (no schedule enforcement) ===")
t0 = time.time()
r = subprocess.run(["kissat", "-q", "--seed=1", cf], capture_output=True, timeout=timeout)
elapsed = time.time() - t0
status = "SAT" if r.returncode == 10 else ("UNSAT" if r.returncode == 20 else f"rc={r.returncode}")
print(f"  {status} in {elapsed:.1f}s")

# Phase 2: Verify sr=61 is UNSAT (all activations forced)
# Add unit clauses for all activation literals
print(f"\n=== Phase 2: sr=61 (all {N} bits enforced) ===")
cf_full = os.path.join(td, "sr61_full.cnf")
with open(cf) as f_in:
    content = f_in.read()

# Append assumption clauses
extra_clauses = []
for act1, act2, bit in activations:
    extra_clauses.append(f"{act1} 0\n")
    extra_clauses.append(f"{act2} 0\n")

# Rewrite header with updated clause count
lines = content.split('\n')
for i, line in enumerate(lines):
    if line.startswith('p cnf'):
        parts = line.split()
        new_nc = int(parts[3]) + len(extra_clauses)
        lines[i] = f"p cnf {parts[2]} {new_nc}"
        break

with open(cf_full, 'w') as f_out:
    f_out.write('\n'.join(lines) + '\n')
    for ec in extra_clauses:
        f_out.write(ec)

t0 = time.time()
try:
    r = subprocess.run(["kissat", "-q", "--seed=1", cf_full], capture_output=True, timeout=timeout)
    elapsed = time.time() - t0
    status = "SAT" if r.returncode == 10 else ("UNSAT" if r.returncode == 20 else f"rc={r.returncode}")
except subprocess.TimeoutExpired:
    elapsed = timeout; status = "TIMEOUT"
print(f"  {status} in {elapsed:.1f}s")

if status != "UNSAT":
    print(f"  Expected UNSAT for sr=61 but got {status}")
    if status == "SAT":
        print(f"  *** sr=61 is SAT at N={N}??? Verify immediately! ***")
    print("Done."); sys.exit(0)

# Phase 3: Find minimal UNSAT core via binary search
print(f"\n=== Phase 3: Minimal UNSAT Core Search ===")
print(f"  Testing which W[60] bits are NECESSARY for UNSAT...")

# Test each bit individually: if removing bit k makes it SAT, then k is necessary
necessary_bits = []
for target_bit in range(N):
    cf_partial = os.path.join(td, f"sr61_skip{target_bit}.cnf")

    partial_clauses = []
    for act1, act2, bit in activations:
        if bit != target_bit:
            partial_clauses.append(f"{act1} 0\n")
            partial_clauses.append(f"{act2} 0\n")

    lines_copy = content.split('\n')
    for i, line in enumerate(lines_copy):
        if line.startswith('p cnf'):
            parts = line.split()
            new_nc = int(parts[3]) + len(partial_clauses)
            lines_copy[i] = f"p cnf {parts[2]} {new_nc}"
            break

    with open(cf_partial, 'w') as f_out:
        f_out.write('\n'.join(lines_copy) + '\n')
        for pc in partial_clauses:
            f_out.write(pc)

    t0 = time.time()
    try:
        r = subprocess.run(["kissat", "-q", "--seed=1", cf_partial],
                           capture_output=True, timeout=timeout)
        elapsed = time.time() - t0
        status = "SAT" if r.returncode == 10 else ("UNSAT" if r.returncode == 20 else f"rc={r.returncode}")
    except subprocess.TimeoutExpired:
        elapsed = timeout; status = "TIMEOUT"

    is_necessary = (status == "SAT")  # If removing bit makes it SAT, that bit is necessary
    necessary_bits.append((target_bit, is_necessary, status, elapsed))
    marker = "*** NECESSARY ***" if is_necessary else ""
    print(f"  Skip bit {target_bit}: {status} in {elapsed:.1f}s {marker}", flush=True)

print(f"\n=== UNSAT Core Summary ===")
n_necessary = sum(1 for _, n, _, _ in necessary_bits if n)
n_redundant = sum(1 for _, n, s, _ in necessary_bits if not n and s == "UNSAT")
n_timeout = sum(1 for _, _, s, _ in necessary_bits if s == "TIMEOUT")
print(f"  Necessary bits (removing makes SAT): {n_necessary}/{N}")
print(f"  Redundant bits (still UNSAT without): {n_redundant}/{N}")
print(f"  Timeout (unknown): {n_timeout}/{N}")

for bit, is_nec, status, elapsed in necessary_bits:
    label = "NECESSARY" if is_nec else ("redundant" if status == "UNSAT" else "timeout")
    print(f"    Bit {bit}: {label} ({status} in {elapsed:.1f}s)")

if n_necessary > 0:
    nec_bits = [b for b, n, _, _ in necessary_bits if n]
    print(f"\n  The sr=61 obstruction requires enforcing W[60] bits: {nec_bits}")
    print(f"  These {len(nec_bits)} bits form the CRITICAL CORE of the sr=60/61 boundary.")

print(f"\nDone.", flush=True)

#!/usr/bin/env python3
"""
Critical pair scan for sr=61.

For each pair of W[60] schedule bits (i,j), free those two bits
(don't enforce schedule compliance) and test if sr=61 becomes SAT.

At N=8: pair (4,5) is the only critical pair.
At N=10: C(10,2) = 45 pairs to test.

Usage: python3 critical_pair_scan.py [N] [timeout_per_pair] [n_parallel]
"""
import sys, os, time, subprocess, tempfile, itertools
from multiprocessing import Pool, cpu_count

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
TIMEOUT = int(sys.argv[2]) if len(sys.argv) > 2 else 300
N_PARALLEL = int(sys.argv[3]) if len(sys.argv) > 3 else min(cpu_count(), 10)

print(f"=== Critical Pair Scan for sr=61 at N={N} ===")
print(f"Pairs to test: C({N},2) = {N*(N-1)//2}")
print(f"Timeout per pair: {TIMEOUT}s")
print(f"Parallel workers: {N_PARALLEL}")
print(flush=True)

spec = __import__('50_precision_homotopy')
sha = spec.MiniSHA256(N)
MASK_N = sha.MASK; MSB = sha.MSB
K32 = spec.K32; KT = [k & MASK_N for k in K32]
m0, s1, s2, W1_pre, W2_pre = sha.find_m0()
if m0 is None:
    print(f"No candidate at N={N}"); sys.exit(1)
ops = {'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1, 'r_sig0': sha.r_sig0,
       's_sig0': sha.s_sig0, 'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1}
print(f"Candidate: M[0]=0x{m0:x}")

def make_pair_cnf(skip_bits):
    """Encode sr=61 with specified W[60] bits freed (not schedule-enforced)."""
    cnf = spec.MiniCNFBuilder(N)
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    # 3 free words for sr=61
    w1f = [cnf.free_word(f"W1_{57+i}") for i in range(3)]
    w2f = [cnf.free_word(f"W2_{57+i}") for i in range(3)]

    # W[60] as free variables
    w1_60_free = cnf.free_word("W1_60")
    w2_60_free = cnf.free_word("W2_60")

    # Schedule-determined W[60]
    def sw(x): return cnf.sigma1_w(x, ops['r_sig1'], ops['s_sig1'])
    w1_60_sched = cnf.add_word(cnf.add_word(sw(w1f[1]), cnf.const_word(W1_pre[53])),
                               cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[45])), cnf.const_word(W1_pre[44])))
    w2_60_sched = cnf.add_word(cnf.add_word(sw(w2f[1]), cnf.const_word(W2_pre[53])),
                               cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[45])), cnf.const_word(W2_pre[44])))

    # Enforce schedule compliance EXCEPT for skip_bits
    def eq_bit(cnf, a, b):
        """Enforce a == b via clauses."""
        if cnf._is_known(a) and cnf._is_known(b):
            if cnf._get_val(a) != cnf._get_val(b):
                cnf.clauses.append([])
            return
        if cnf._is_known(a):
            cnf.clauses.append([b] if cnf._get_val(a) else [-b])
            return
        if cnf._is_known(b):
            cnf.clauses.append([a] if cnf._get_val(b) else [-a])
            return
        cnf.clauses.append([-a, b])
        cnf.clauses.append([a, -b])

    for bit in range(N):
        if bit in skip_bits:
            continue  # Don't enforce this bit
        eq_bit(cnf, w1_60_free[bit], w1_60_sched[bit])
        eq_bit(cnf, w2_60_free[bit], w2_60_sched[bit])

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

    return cnf

def test_pair(args):
    """Test one (i,j) pair. Returns (i, j, status, time)."""
    i, j = args
    try:
        cnf = make_pair_cnf({i, j})
        td = tempfile.mkdtemp(prefix=f"pair_{i}_{j}_")
        cf = os.path.join(td, "sr61.cnf")
        cnf.write_dimacs(cf)

        t0 = time.time()
        try:
            r = subprocess.run(["kissat", "-q", "--seed=1", cf],
                               capture_output=True, timeout=TIMEOUT)
            elapsed = time.time() - t0
            if r.returncode == 10:
                status = "SAT"
            elif r.returncode == 20:
                status = "UNSAT"
            else:
                status = f"rc={r.returncode}"
        except subprocess.TimeoutExpired:
            elapsed = TIMEOUT
            status = "TIMEOUT"

        # Cleanup
        os.unlink(cf)
        os.rmdir(td)

        return (i, j, status, elapsed)
    except Exception as e:
        return (i, j, f"ERROR: {e}", 0.0)


if __name__ == '__main__':
  import multiprocessing
  multiprocessing.set_start_method('fork')

  # Generate all pairs
  pairs = list(itertools.combinations(range(N), 2))
  print(f"\nLaunching {len(pairs)} pair tests on {N_PARALLEL} workers...\n")
  print(flush=True)

  t_start = time.time()

  # Run in parallel
  with Pool(N_PARALLEL) as pool:
    results = pool.map(test_pair, pairs)

  t_total = time.time() - t_start

  # Report
  print(f"\n=== Results (N={N}, {len(pairs)} pairs, {t_total:.1f}s total) ===\n")
  print(f"| Pair (i,j) | Status | Time (s) |")
  print(f"|------------|--------|----------|")

  sat_pairs = []
  unsat_pairs = []
  timeout_pairs = []

  for i, j, status, elapsed in sorted(results):
    marker = " ***" if status == "SAT" else ""
    print(f"| ({i},{j}) | {status} | {elapsed:.1f} |{marker}")
    if status == "SAT":
        sat_pairs.append((i, j))
    elif status == "UNSAT":
        unsat_pairs.append((i, j))
    else:
        timeout_pairs.append((i, j))

  print(f"\nSummary:")
  print(f"  SAT pairs (critical): {len(sat_pairs)} — {sat_pairs}")
  print(f"  UNSAT pairs: {len(unsat_pairs)}")
  print(f"  TIMEOUT pairs: {len(timeout_pairs)}")
  print(f"  Total time: {t_total:.1f}s")

  if sat_pairs:
    print(f"\n*** CRITICAL PAIRS AT N={N}: {sat_pairs} ***")
    print(f"These W[60] bit pairs, when freed from schedule compliance,")
    print(f"allow sr=61 collisions to exist.")
  print(flush=True)

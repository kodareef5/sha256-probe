#!/usr/bin/env python3
"""
Script 58: Carry Homotopy -- staged carry reintroduction

HYPOTHESIS: There is a specific set of carry bundles whose introduction
causes the SAT->UNSAT transition for the sr=60 collision problem.

METHOD:
  Level 0: ALL additions in rounds 57-63 replaced with XOR (carry-free).
           This should be trivially SAT since XOR-addition is much weaker.
  Level 1: Round 57 uses REAL carries; rounds 58-63 use XOR-addition.
  Level 2: Rounds 57-58 use REAL carries; rounds 59-63 use XOR-addition.
  Level 3: Rounds 57-59 real; 60-63 XOR.
  Level 4: Rounds 57-60 real; 61-63 XOR.
  Level 5: Rounds 57-61 real; 62-63 XOR.
  Level 6: Rounds 57-62 real; 63 XOR.
  Level 7: All rounds 57-63 real (full problem = baseline).

"XOR addition" means: add_word(A, B) = [xor2(A[i], B[i]) for i in range(32)].
No carry propagation at all. Applied to ALL add_word calls in a round
(T1 final add, T2, a_new, e_new), and also to the CSA final add_word.

The message schedule (W[61], W[62], W[63]) is computed in Python with real
arithmetic regardless of level, since those are precomputed constants.

Candidate: M[0]=0x17149975, all-ones padding, sr=60.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


class CarryHomotopyCNF(enc.CNFBuilder):
    """
    CNFBuilder subclass that can switch between real addition (ripple-carry)
    and XOR-addition (no carries) on a per-call basis.
    """

    def __init__(self):
        super().__init__()
        self._use_xor_add = False

    def set_xor_addition(self, enabled):
        """When True, add_word does bitwise XOR instead of ripple-carry."""
        self._use_xor_add = enabled

    def add_word(self, A, B, track_carries=False):
        """
        C = A + B (mod 2^32).
        When _use_xor_add is True: C[i] = A[i] XOR B[i] (no carries).
        Otherwise: standard ripple-carry addition.
        """
        if self._use_xor_add:
            C = [self.xor2(A[i], B[i]) for i in range(32)]
            if track_carries:
                # No real carries; return dummy zeros
                dummy = [self._const(False)] * 32
                return C, dummy
            return C
        else:
            # Standard ripple-carry from parent
            C = []
            carries = []
            carry = self._const(False)
            for i in range(32):
                if self._is_known(carry) and not self._get_val(carry):
                    s, carry = self.half_adder(A[i], B[i])
                else:
                    s, carry = self.full_adder(A[i], B[i], carry)
                C.append(s)
                carries.append(carry)
            if track_carries:
                return C, carries
            return C


def encode_homotopy(level, mode="sr60"):
    """
    Encode sr=60 collision with carry homotopy.

    level: 0..7
      0 = all XOR-addition (rounds 57-63)
      k = rounds 57..56+k use real carries, rounds 57+k..63 use XOR
      7 = all real carries (full baseline)

    Real-carry rounds: 57 .. 56+level  (empty set if level=0)
    XOR-add rounds:    57+level .. 63   (all 7 rounds if level=0)
    """
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    n_free = 4  # sr=60

    cnf = CarryHomotopyCNF()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]

    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    # --- Message schedule enforcement using REAL addition in Python ---
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    # These use real add_word (carries enabled) because the schedule
    # constraints must be exact -- they couple the free variables.
    cnf.set_xor_addition(False)  # always real for schedule

    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])),
                     cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])),
                     cnf.const_word(W2_pre[45])))
    W1_schedule.append(w1_61)
    W2_schedule.append(w2_61)

    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    w60_idx = 3
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w60_idx]),
                     cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])),
                     cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w60_idx]),
                     cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])),
                     cnf.const_word(W2_pre[46])))

    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    w61_idx = 4
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w61_idx]),
                     cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])),
                     cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w61_idx]),
                     cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])),
                     cnf.const_word(W2_pre[47])))

    W1_schedule.extend([w1_62, w1_63])
    W2_schedule.extend([w2_62, w2_63])

    # --- Encode 7 rounds with homotopy ---
    # Rounds 57..56+level use real carries (level=0 means none)
    # Rounds 57+level..63 use XOR-addition
    real_rounds = set(range(57, 57 + level))  # e.g., level=3 -> {57,58,59}

    st1, st2 = s1, s2
    for r in range(7):
        round_num = 57 + r
        use_xor = (round_num not in real_rounds)
        cnf.set_xor_addition(use_xor)

        # --- Message 1 round ---
        a1, b1, c1, d1, e1, f1, g1, h1 = st1
        K_word = cnf.const_word(enc.K[round_num])
        sig1_1 = cnf.Sigma1(e1)
        ch1 = cnf.Ch(e1, f1, g1)

        # T1 via CSA tree: CSA layers are carry-free by nature (they are
        # just XOR+MAJ per column). The final add_word in the CSA respects
        # our xor_addition setting.
        s1_csa, c1_csa = cnf.csa_layer(h1, sig1_1, ch1)
        s2_csa, c2_csa = cnf.csa_layer(s1_csa, K_word, W1_schedule[r])
        s3_csa, c3_csa = cnf.csa_layer(c1_csa, s2_csa, c2_csa)
        t1_m1 = cnf.add_word(s3_csa, c3_csa)

        sig0_1 = cnf.Sigma0(a1)
        mj1 = cnf.Maj(a1, b1, c1)
        t2_m1 = cnf.add_word(sig0_1, mj1)
        a_new1 = cnf.add_word(t1_m1, t2_m1)
        e_new1 = cnf.add_word(d1, t1_m1)
        st1 = (a_new1, a1, b1, c1, e_new1, e1, f1, g1)

        # --- Message 2 round ---
        a2, b2, c2, d2, e2, f2, g2, h2 = st2
        sig1_2 = cnf.Sigma1(e2)
        ch2 = cnf.Ch(e2, f2, g2)

        s1_csa2, c1_csa2 = cnf.csa_layer(h2, sig1_2, ch2)
        s2_csa2, c2_csa2 = cnf.csa_layer(s1_csa2, K_word, W2_schedule[r])
        s3_csa2, c3_csa2 = cnf.csa_layer(c1_csa2, s2_csa2, c2_csa2)
        t1_m2 = cnf.add_word(s3_csa2, c3_csa2)

        sig0_2 = cnf.Sigma0(a2)
        mj2 = cnf.Maj(a2, b2, c2)
        t2_m2 = cnf.add_word(sig0_2, mj2)
        a_new2 = cnf.add_word(t1_m2, t2_m2)
        e_new2 = cnf.add_word(d2, t1_m2)
        st2 = (a_new2, a2, b2, c2, e_new2, e2, f2, g2)

    # --- Collision constraints ---
    cnf.set_xor_addition(False)  # no add_word here, but be clean
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    real_str = f"{sorted(real_rounds)}" if real_rounds else "none"
    cnf_file = f"/tmp/sr60_homotopy_L{level}.cnf"
    nv, nc = cnf.write_dimacs(cnf_file)
    return cnf_file, nv, nc, real_str


def run_kissat(cnf_file, timeout, verbose=False):
    """Run Kissat and return (status, elapsed, conflicts_per_sec)."""
    t0 = time.time()
    try:
        args = ["timeout", str(timeout), "kissat", cnf_file]
        if not verbose:
            args.insert(3, "-q")
        r = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout + 30)
        elapsed = time.time() - t0

        # Extract conflict rate from kissat output
        conflicts = None
        for line in r.stdout.split('\n'):
            if 'conflicts' in line.lower() and 'per' in line.lower():
                # e.g. "c       12345 conflicts,    1234.5 per second"
                parts = line.split()
                for j, p in enumerate(parts):
                    if p == 'conflicts,' and j > 0:
                        try:
                            conflicts = int(parts[j-1])
                        except ValueError:
                            pass

        cps = conflicts / elapsed if conflicts and elapsed > 0 else None

        if r.returncode == 10:
            return "SAT", elapsed, cps
        elif r.returncode == 20:
            return "UNSAT", elapsed, cps
        else:
            return "TIMEOUT", elapsed, cps
    except subprocess.TimeoutExpired:
        return "TIMEOUT", time.time() - t0, None


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 120

    print("=" * 74, flush=True)
    print("CARRY HOMOTOPY: Staged carry reintroduction for sr=60", flush=True)
    print("=" * 74, flush=True)
    print(f"Candidate: M[0]=0x17149975, all-ones padding", flush=True)
    print(f"Timeout per level: {timeout}s", flush=True)
    print(f"", flush=True)
    print(f"Level 0: ALL rounds use XOR-addition (no carries)", flush=True)
    print(f"Level k: Rounds 57..56+k use real carries, rest XOR", flush=True)
    print(f"Level 7: ALL rounds use real carries (full baseline)", flush=True)
    print(f"Schedule enforcement (W[61..63]) always uses real addition.", flush=True)
    print("=" * 74, flush=True)

    results = []

    for level in range(8):
        print(f"\n{'='*60}", flush=True)
        print(f"LEVEL {level}", flush=True)
        print(f"{'='*60}", flush=True)

        t_enc_start = time.time()
        cnf_file, nv, nc, real_str = encode_homotopy(level)
        t_enc = time.time() - t_enc_start

        print(f"  Real-carry rounds: {real_str}", flush=True)
        print(f"  Encoding time:     {t_enc:.1f}s", flush=True)
        print(f"  Variables:         {nv}", flush=True)
        print(f"  Clauses:           {nc}", flush=True)
        print(f"  Running Kissat ({timeout}s)...", flush=True)

        status, elapsed, cps = run_kissat(cnf_file, timeout, verbose=True)
        cps_str = f"{cps:.0f} conf/s" if cps else "N/A"
        print(f"  >>> {status} in {elapsed:.1f}s  ({cps_str})", flush=True)

        results.append({
            'level': level,
            'real_rounds': real_str,
            'vars': nv,
            'clauses': nc,
            'status': status,
            'time': elapsed,
            'cps': cps,
        })

        # Early insight: if we just transitioned from SAT to non-SAT, note it
        if len(results) >= 2:
            prev = results[-2]
            curr = results[-1]
            if prev['status'] == 'SAT' and curr['status'] != 'SAT':
                print(f"  *** TRANSITION DETECTED: Level {prev['level']} SAT -> "
                      f"Level {curr['level']} {curr['status']}", flush=True)

    # === Summary table ===
    print(f"\n{'='*74}", flush=True)
    print("RESULTS SUMMARY", flush=True)
    print(f"{'='*74}", flush=True)
    hdr = (f"{'Level':>5}  {'Real-carry rounds':<22}  {'Vars':>7}  "
           f"{'Clauses':>8}  {'Result':>8}  {'Time':>8}  {'Conf/s':>10}")
    print(hdr, flush=True)
    sep = (f"{'-'*5}  {'-'*22}  {'-'*7}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*10}")
    print(sep, flush=True)
    for r in results:
        rr = r['real_rounds'] if r['real_rounds'] != 'none' else 'none (all XOR)'
        cps_str = f"{r['cps']:.0f}" if r['cps'] else "N/A"
        print(f"{r['level']:>5}  {rr:<22}  {r['vars']:>7}  "
              f"{r['clauses']:>8}  {r['status']:>8}  {r['time']:>7.1f}s  {cps_str:>10}",
              flush=True)

    # === Transition analysis ===
    print(f"\n{'='*74}", flush=True)
    print("TRANSITION ANALYSIS", flush=True)
    print(f"{'='*74}", flush=True)

    sat_levels = [r['level'] for r in results if r['status'] == 'SAT']
    unsat_levels = [r['level'] for r in results if r['status'] == 'UNSAT']
    timeout_levels = [r['level'] for r in results if r['status'] == 'TIMEOUT']

    if sat_levels:
        print(f"  SAT at levels:     {sat_levels}", flush=True)
    if unsat_levels:
        print(f"  UNSAT at levels:   {unsat_levels}", flush=True)
    if timeout_levels:
        print(f"  TIMEOUT at levels: {timeout_levels}", flush=True)

    # Find the transition point
    transition = None
    for i in range(1, len(results)):
        if results[i-1]['status'] == 'SAT' and results[i]['status'] != 'SAT':
            transition = i
            break

    if transition is not None:
        prev_level = results[transition-1]['level']
        curr_level = results[transition]['level']
        fatal_round = 57 + curr_level - 1  # the round whose carries broke SAT
        print(f"\n  TRANSITION: Level {prev_level} (SAT) -> "
              f"Level {curr_level} ({results[transition]['status']})", flush=True)
        print(f"  FATAL ROUND: {fatal_round}", flush=True)
        print(f"  Introducing real carries in round {fatal_round} is what "
              f"causes the SAT->{'UNSAT' if results[transition]['status']=='UNSAT' else 'TIMEOUT'} "
              f"transition.", flush=True)
        print(f"  This means the carry propagation in round {fatal_round}'s additions "
              f"(T1, T2, a_new, e_new) creates constraints that make the "
              f"collision impossible or intractable.", flush=True)
    elif all(r['status'] == 'SAT' for r in results):
        print(f"\n  ALL LEVELS SAT -- carries are not the barrier for this candidate!", flush=True)
    elif all(r['status'] != 'SAT' for r in results):
        print(f"\n  NO LEVEL WAS SAT -- even XOR-addition is insufficient. "
              f"The collision structure itself (Ch, Maj, Sigma) blocks solutions.", flush=True)
    else:
        print(f"\n  Non-monotonic pattern detected. The carry barrier is not "
              f"cleanly round-sequential.", flush=True)

    # Size growth analysis
    print(f"\n{'='*74}", flush=True)
    print("SIZE GROWTH (shows carry clause overhead per round)", flush=True)
    print(f"{'='*74}", flush=True)
    for i in range(1, len(results)):
        dv = results[i]['vars'] - results[i-1]['vars']
        dc = results[i]['clauses'] - results[i-1]['clauses']
        print(f"  Level {results[i-1]['level']}->{results[i]['level']}: "
              f"+{dv} vars, +{dc} clauses (round {56+results[i]['level']} carries)",
              flush=True)


if __name__ == "__main__":
    main()

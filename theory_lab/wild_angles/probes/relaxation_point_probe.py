#!/usr/bin/env python3
"""
relaxation_point_probe.py — the RELAXATION-POINT sweep (last cheap-probe stone in
the sr=61 investigation).

QUESTION
--------
The sr-ladder forces the cascade-DP free words W[57..60] one at a time, backward:
    W[60] <-> sr60 -> 61   W[59] <-> 61 -> 62   W[58] <-> 62 -> 63   W[57] <-> 63 -> 64
The W[60] step costs 2^-2N = TWO independent conditions g1=0 (per-message value
match) AND h=0 (inter-message difference compatibility), independence ratio ~1.00
(repo: RESULT_sr61_is_2minus2N.md, gap_analysis.c). Is round 60 the *cheapest*
place to have the sr-boundary, or does some other free word W[r] have its two
conditions COUPLED (cost 2^-N) or one AUTO-SATISFIED (cost 2^-N or free)? If so the
boundary should move there and the sr-push is cheaper.

This also settles whether EVERY sr-step is uniformly 2^-2N (=> sr=62 = 2^-4N) or
whether some step is cheaper (the WE1 dissent claimed the 2nd step is 2^-N — resolve
by direct per-step MEASUREMENT, not argument).

WHAT THIS DOES
--------------
1. Generalizes the validated C enumerator gap_analysis.c -> relax_gap.c, which for
   EACH free word r in {57,58,59,60} computes, over the full cascade-DP sweep:
        sched_i[r] = sigma1(Wi[r-2]) + Wi[r-7] + sigma0(Wi[r-15]) + Wi[r-16]   (i=1,2)
        g1(r)=W1[r]-sched1[r]   g2(r)=W2[r]-sched2[r]   h(r)=(W2[r]-W1[r])-(sched2-sched1)
   and reports, per round: P(g1=0), P(h=0), P(both), the independence ratio over the
   huge de61=0 hit set, uniformity peaks, the marginal counts over the genuine sr=60
   collisions, and a de57..de60 image table + a round-58/de58 coupling stratification.
   Compiled & run at N=8/N=10, MSB + one exotic kernel.
   Companion C tools (also beside this file, compiled to /tmp):
     - uncond_indep.c : the INTRINSIC (unconditional, no-de61-filter) per-round g1_|_h
                        independence ratio over each round's exact free-word domain.
                        This is the decisive table (de61-conditioning can fake sub-1
                        ratios at rounds 58/59; unconditional gives ratio 1.0000).
     - h57_scan.c     : h(57) over ALL cascade-eligible (kernel,M0) — is it ever 0?
     - h58_scan.c     : h(58)'s restricted image and whether 0 is reachable, per kernel.
2. CROSS-CHECKS the C g1/g2/h numbers against the VALIDATED Python engine
   (_w5co_engine + neutral_bit_probe.evaluate machinery) on the known C-enumerator
   collisions, generalized here to all four free words (evaluate_all_rounds).

RESULT (see relaxation_point_RESULT.md): no round beats 2^-2N; W[59]/W[60] are 2^-2N
(ratio 1.0000) at every kernel; W[58] is 2^-2N-or-IMPOSSIBLE (restricted h-image);
W[57] is IMPOSSIBLE (h(57) a nonzero constant). Round 60 is the optimal sr-boundary.

READ-ONLY toward the repo. No SAT. Throttled (OMP_NUM_THREADS=2, taskpolicy -b).

Run:  OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/relaxation_point_probe.py
"""
import os, sys, subprocess, time

LAB = '/Users/mac/Desktop/sha256_theory_lab'
sys.path.insert(0, f'{LAB}/wild_angles/probes/cards')
sys.path.insert(0, f'{LAB}/wild_angles/probes/kernels')
import _w5co_engine as eng          # validated tail engine (49 @N4, 260 @N8)
import shabridge as sb              # noqa: F401  ground-truth pins

# Known sr=60 collisions from the C enumerator (M0 auto, fill=MASK, MSB kernel).
# (w57,w58,w59,w60). We re-derive g1(r),g2(r),h(r) for ALL FOUR free words in
# Python and demand they match the C enumerator's per-round numbers.
KNOWN = {
    8:  [(131, 70, 82, 92), (131, 140, 71, 87)],
    10: [(309, 594, 54, 698), (310, 477, 913, 139)],
}


# --------------------------------------------------------------------------- #
#  Python ground truth: compute (g1,g2,h) for EVERY free word r in {57..60}.   #
#  Mirrors _w5co_engine.run_tail / neutral_bit_probe.evaluate EXACTLY. The     #
#  schedule target for free word r is                                          #
#     sched_i[r] = sigma1(Wi[r-2]) + Wi[r-7] + sigma0(Wi[r-15]) + Wi[r-16].    #
#  For r=57,58 the r-2 word (55,56) is a PRECOMPUTE word (Wp); for r=59,60 it   #
#  is a FREE word (w57,w58). All other terms are precompute words.             #
# --------------------------------------------------------------------------- #
def evaluate_all_rounds(M, setup, w57, w58, w59, w60):
    MASK = M['MASK']; KN = M['KN']; s0 = M['s0']; s1f = M['s1']
    st1, W1p = setup['st1'], setup['W1']
    st2, W2p = setup['st2'], setup['W2']

    s1, s2 = st1, st2
    w57b = eng.find_w2(s1, s2, 57, w57, M)
    s1 = eng.sha_round(s1, KN[57], w57, M); s2 = eng.sha_round(s2, KN[57], w57b, M)
    w58b = eng.find_w2(s1, s2, 58, w58, M)
    s1 = eng.sha_round(s1, KN[58], w58, M); s2 = eng.sha_round(s2, KN[58], w58b, M)
    w59b = eng.find_w2(s1, s2, 59, w59, M)
    s59a = eng.sha_round(s1, KN[59], w59, M); s59b = eng.sha_round(s2, KN[59], w59b, M)
    casoff = eng.find_w2(s59a, s59b, 60, 0, M)
    w60b = (w60 + casoff) & MASK

    # full collision check (so we only cross-check on genuine sr=60 collisions)
    a = eng.sha_round(s59a, KN[60], w60,  M)
    b = eng.sha_round(s59b, KN[60], w60b, M)
    W1_61 = (s1f(w59)  + W1p[54] + s0(W1p[46]) + W1p[45]) & MASK
    W2_61 = (s1f(w59b) + W2p[54] + s0(W2p[46]) + W2p[45]) & MASK
    W1_62 = (s1f(w60)  + W1p[55] + s0(W1p[47]) + W1p[46]) & MASK
    W2_62 = (s1f(w60b) + W2p[55] + s0(W2p[47]) + W2p[46]) & MASK
    W1_63 = (s1f(W1_61) + W1p[56] + s0(W1p[48]) + W1p[47]) & MASK
    W2_63 = (s1f(W2_61) + W2p[56] + s0(W2p[48]) + W2p[47]) & MASK
    a = eng.sha_round(a, KN[61], W1_61, M); b = eng.sha_round(b, KN[61], W2_61, M)
    a = eng.sha_round(a, KN[62], W1_62, M); b = eng.sha_round(b, KN[62], W2_62, M)
    a = eng.sha_round(a, KN[63], W1_63, M); b = eng.sha_round(b, KN[63], W2_63, M)
    collide = (a == b)

    # per-round schedule targets (r-2 term per the rule above)
    W1 = {57: w57, 58: w58, 59: w59, 60: w60}
    W2 = {57: w57b, 58: w58b, 59: w59b, 60: w60b}
    wm2_1 = {57: W1p[55], 58: W1p[56], 59: w57, 60: w58}
    wm2_2 = {57: W2p[55], 58: W2p[56], 59: w57b, 60: w58b}
    out = {}
    for r in (57, 58, 59, 60):
        sc1 = (s1f(wm2_1[r]) + W1p[r-7] + s0(W1p[r-15]) + W1p[r-16]) & MASK
        sc2 = (s1f(wm2_2[r]) + W2p[r-7] + s0(W2p[r-15]) + W2p[r-16]) & MASK
        g1 = (W1[r] - sc1) & MASK
        g2 = (W2[r] - sc2) & MASK
        h = (((W2[r] - W1[r]) & MASK) - ((sc2 - sc1) & MASK)) & MASK
        out[r] = dict(g1=g1, g2=g2, h=h, ident_ok=((g1 + h) & MASK) == g2)
    out['collide'] = collide
    return out


def python_crosscheck(N):
    print(f"\n[py-xcheck N={N}] generalized evaluate_all_rounds on C-enumerator collisions:")
    M = eng.make_model(N); setup = eng.find_M0(M)
    if setup is None:
        print("   no cascade-eligible M0; skip"); return
    all_ok = True
    for tup in KNOWN.get(N, []):
        r = evaluate_all_rounds(M, setup, *tup)
        line = f"   {tup}: collide={r['collide']} | "
        for rr in (57, 58, 59, 60):
            d = r[rr]
            line += f"r{rr}(g1={d['g1']},g2={d['g2']},h={d['h']},id={'ok' if d['ident_ok'] else 'BAD'}) "
            if not d['ident_ok']:
                all_ok = False
        if not r['collide']:
            all_ok = False
        print(line)
    # sanity: r60 g1,h must match the values neutral_bit_probe validated against C
    REF60 = {8: {(131,70,82,92): (28,249), (131,140,71,87): (207,89)},
             10:{(309,594,54,698): (277,609), (310,477,913,139): (981,452)}}
    for tup, (g1c, hc) in REF60.get(N, {}).items():
        d = evaluate_all_rounds(M, setup, *tup)[60]
        ok = (d['g1'] == g1c and d['h'] == hc)
        print(f"   [r60 vs C] {tup}: g1={d['g1']}(C={g1c}) h={d['h']}(C={hc}) -> "
              f"{'MATCH' if ok else 'MISMATCH'}")
        all_ok = all_ok and ok
    print(f"   => cross-check {'PASS' if all_ok else 'FAIL'} (g2=g1+h identity + r60 vs C)")
    return all_ok


# --------------------------------------------------------------------------- #
#  Drive the C enumerator: compile (if needed) and run at N x kernel.          #
# --------------------------------------------------------------------------- #
PROBE_DIR = f'{LAB}/wild_angles/probes'
OMP = ['-Xclang', '-fopenmp', '-I/opt/homebrew/opt/libomp/include',
       '-L/opt/homebrew/opt/libomp/lib', '-lomp']


def compile_c(src_name, N, kernbit, use_omp=True):
    """Compile a probe C file (src_name beside this probe) at (N, kernbit) -> /tmp binary."""
    src = f'{PROBE_DIR}/{src_name}'
    if not os.path.exists(src):
        print(f"   [missing C source {src}]"); return None
    binp = f'/tmp/{src_name[:-2]}_N{N}_k{kernbit}'
    cmd = (['gcc', '-O3', '-march=native'] + (OMP if use_omp else []) +
           [f'-DN={N}', f'-DKERNBIT={kernbit}', '-o', binp, src, '-lm'])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"   [compile FAIL {src_name} N={N} k={kernbit}]\n{r.stderr}"); return None
    return binp


def run_c(binp, timeout=1800, grep=None):
    env = dict(os.environ, OMP_NUM_THREADS='2')
    t0 = time.time()
    r = subprocess.run(['taskpolicy', '-b', binp], env=env, timeout=timeout,
                       capture_output=True, text=True)
    out = r.stdout
    if grep:
        out = "\n".join(l for l in out.splitlines() if any(g in l for g in grep))
    print(out)
    if r.returncode != 0:
        print(f"   [run rc={r.returncode}] {r.stderr}")
    print(f"   [wall {time.time()-t0:.1f}s]")
    return r.stdout


if __name__ == '__main__':
    HEAVY = os.environ.get('RELAX_HEAVY', '0') == '1'  # set RELAX_HEAVY=1 to also run relax_gap (2^40 @N=10)
    print("=" * 74)
    print("RELAXATION-POINT SWEEP — per-round marginal sr-step cost (g1,h independence)")
    print("=" * 74)

    # 1) Python cross-check of the per-round (g1,g2,h) formulas vs the validated engine
    for N in (8, 10):
        python_crosscheck(N)

    # 2) DECISIVE table: intrinsic (unconditional) per-round g1_|_h independence.
    #    MSB + exotic(bit-4) kernel; N=8 and N=10 (W[60] collapsed -> fast at N=10).
    for (N, kb) in [(8, 7), (8, 4), (10, 9), (10, 4)]:
        print("\n" + "#" * 74)
        print(f"# INTRINSIC per-round g1_|_h (uncond_indep)  N={N}  kernbit={kb}  "
              f"({'MSB' if kb == N-1 else 'exotic'})")
        print("#" * 74)
        binp = compile_c('uncond_indep.c', N, kb)
        if binp:
            run_c(binp, timeout=1800)

    # 3) Round-57 / Round-58 special-round scans over ALL cascade-eligible kernels.
    for tool in ('h57_scan.c', 'h58_scan.c'):
        for N in (8, 10):
            print("\n" + "#" * 74)
            print(f"# {tool}  N={N}  (over all cascade-eligible kernels/M0)")
            print("#" * 74)
            binp = compile_c(tool, N, N - 1, use_omp=False)
            if binp:
                run_c(binp, timeout=600)

    # 4) (OPTIONAL, heavy) full relax_gap profile: de61-conditioned + collision-set +
    #    de-image table + round-58/de58 stratification. N=10 sweeps 2^40 -> minutes.
    if HEAVY:
        for (N, kb) in [(8, 7), (8, 4), (10, 9)]:
            print("\n" + "#" * 74)
            print(f"# FULL relax_gap profile  N={N}  kernbit={kb}")
            print("#" * 74)
            binp = compile_c('relax_gap.c', N, kb)
            if binp:
                run_c(binp, timeout=5400 if N >= 10 else 1200)
    else:
        print("\n[skipped heavy relax_gap full profile; set RELAX_HEAVY=1 to run it]")

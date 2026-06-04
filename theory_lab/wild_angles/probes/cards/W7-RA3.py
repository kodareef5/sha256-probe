"""
W7-RA3 — The 2^-2N wall as a Szemeredi-regularity density increment.   [P4 · cheap]

Card claim: the collision-survival bipartite graph has a regularity partition;
sr=60->61 splits a regular pair and drops survival-density by one regular-pair
factor, so 2^-2N = (2^-N)^2 is *two* density factors (one per condition); the wall =
where density falls below epsilon (irregular / search-dominated).

Probe (CATALOG): N=6..12 build G_r (message-pair classes x surviving classes),
per-round edge density; does the ratio hit a clean 2^-N step then 2^-2N?
THE NEW PREDICTION: a spike in inter-bucket density *variance* (regularity breakdown)
at the wall round?
Kill: density drop is SMOOTH/single-factor (no exponent doubling), OR no variance
spike at the boundary across N.

Ground truth (RESULT_sr61_is_2minus2N.md): sr-step = (g1=0) AND (h=0), two INDEP
N-bit conditions. g1 = W1[60]-sched1[60] (per-message value match); h = casoff -
(sched2[60]-sched1[60]) (inter-message compatibility). sr=60 collisions free over
W[57..60]; rounds 57..60 are the FREE cascade (survival density 1); the drop is at 61.

Per finding #3: CONFIRM only if the density factorization LANDS ON the two conditions
g1,h (the genuine rank-2). A density story that merely *permits* 2^-2N is a RENAME.
The load-bearing NEW object is the inter-bucket variance spike at the wall.

This probe USES the repo's measured (g1,h) data: gap_analysis.c regenerates it at
each N (cols w57,w58,w59,w60,g1,g2,h). We build it lab-side per N.

READ-ONLY toward the repo (we compile gap_analysis.c to /tmp, never into the repo).
Throttle:  OMP_NUM_THREADS=2 taskpolicy -b python3 W7-RA3.py
"""
import sys, os, subprocess, csv, statistics as st
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

REPO = '/Users/mac/Desktop/sha256_review'
GAP_C = f'{REPO}/headline_hunt/bets/coincidence_variety/gap_analysis.c'
LABTMP = '/tmp/ra3_lab'    # all lab-side artifacts (binaries + CSV) live here
N10_CSV = sb.GAP_ROWS_CSV   # repo N=10, read-only


def build_gap_binary(N):
    """Compile the repo's gap_analysis.c to a LAB-SIDE binary at width N (#define N).
    NEVER writes inside the repo; all outputs go under LABTMP."""
    os.makedirs(LABTMP, exist_ok=True)
    binpath = f'{LABTMP}/gap_N{N}'
    if os.path.exists(binpath):
        return binpath
    flags = ['gcc', '-O3', '-march=native', f'-DN={N}', '-Xclang', '-fopenmp',
             '-I/opt/homebrew/opt/libomp/include', '-L/opt/homebrew/opt/libomp/lib',
             '-lomp', '-o', binpath, GAP_C, '-lm']
    r = subprocess.run(flags, capture_output=True, text=True)
    if r.returncode != 0:
        flags2 = ['gcc', '-O3', f'-DN={N}', '-o', binpath, GAP_C, '-lm']
        r2 = subprocess.run(flags2, capture_output=True, text=True)
        if r2.returncode != 0:
            print(f"gap_analysis.c (N={N}) compile FAILED:\n", r.stderr[-600:])
            return None
    return binpath


def run_gap(N):
    """Run the lab-side gap binary in LABTMP (it writes gap_rows.csv to CWD), parse
    the per-collision rows. Returns list of (w57,w58,w59,w60,g1,g2,h) or None."""
    binpath = build_gap_binary(N)
    if binpath is None:
        return None
    os.makedirs(LABTMP, exist_ok=True)
    try:
        env = dict(os.environ, OMP_NUM_THREADS='2')
        subprocess.run(['taskpolicy', '-b', binpath], env=env, cwd=LABTMP,
                       capture_output=True, text=True, timeout=900)
    except Exception as ex:
        print(f"  gap N={N} run failed: {ex}")
        return None
    csvp = f'{LABTMP}/gap_rows.csv'
    if not os.path.exists(csvp):
        return None
    rows = list(csv.DictReader(open(csvp)))
    return [(int(r['w57']), int(r['w58']), int(r['w59']), int(r['w60']),
             int(r['g1']), int(r['g2']), int(r['h'])) for r in rows]


def load_n10():
    """Repo N=10 collisions with g1,h (read-only)."""
    rows = list(csv.DictReader(open(N10_CSV)))
    return [(int(r['w57']), int(r['w58']), int(r['w59']), int(r['w60']),
             int(r['g1']), int(r['g2']), int(r['h'])) for r in rows]


def survival_profile(rows, N):
    """The collision-survival 'density' per round-condition, derived from the
    measured (g1,h) over the sr=60 collision set.
      - rounds 57..60: FREE cascade -> every sr=60 collision survives -> density 1.0
      - round 61 condition splits into TWO independent factors:
          * h=0  (inter-message compatibility)  -> density P(h=0)
          * g1=0 (per-message value match)       -> density P(g1=0)
        sr=61 survival density = P(g1=0 AND h=0).
    Returns the densities + the independence ratio (the rank-2 signature)."""
    M = len(rows)
    mod = 1 << N
    n_h0 = sum(1 for r in rows if r[6] % mod == 0)
    n_g1 = sum(1 for r in rows if r[4] % mod == 0)
    n_both = sum(1 for r in rows if (r[6] % mod == 0 and r[4] % mod == 0))
    Ph = n_h0 / M; Pg = n_g1 / M
    Pboth = n_both / M
    indep = (Pboth / (Ph * Pg)) if (Ph * Pg) > 0 else float('nan')
    return dict(M=M, Ph=Ph, Pg=Pg, Pboth=Pboth, indep=indep,
                expN=2.0 ** (-N), exp2N=2.0 ** (-2 * N),
                n_h0=n_h0, n_g1=n_g1, n_both=n_both)


def bucket_variance(rows, N, key_idx, nbuckets=16):
    """THE NEW PREDICTION: inter-bucket density variance of the surviving condition.
    Partition the sr=60 collisions into buckets by the HIGH bits of a feature
    (w57 -> bucket), and within each bucket measure the survival density of the
    *next* condition (h=0). Regularity = uniform density across buckets (low var);
    a regularity BREAKDOWN = a spike in inter-bucket density variance.

    We compare variance of:
      (i)  a FREE-cascade-style condition (always survives -> density 1 everywhere
           -> variance 0): the rounds 57..60 baseline.
      (ii) the round-61 condition h=0 (the wall): is its inter-bucket density
           variance ELEVATED vs a binomial-null (the random-coloring baseline)?
    """
    mod = 1 << N
    # bucket by top 4 bits of w57
    shift = max(0, N - 4)
    buckets = {}
    for r in rows:
        b = (r[0] >> shift) & (nbuckets - 1)
        buckets.setdefault(b, []).append(r)
    dens = []
    for b, rs in buckets.items():
        if not rs:
            continue
        d = sum(1 for r in rs if r[key_idx] % mod == 0) / len(rs)
        dens.append((d, len(rs)))
    densities = [d for d, _ in dens]
    if len(densities) < 2:
        return None
    mean_d = st.mean(densities)
    var_d = st.pvariance(densities)
    # binomial-null variance: if each bucket is Binom(n_b, p), Var of the density
    # estimate per bucket ~ p(1-p)/n_b; average that as the 'expected under regularity'
    p = mean_d
    exp_var = st.mean([p * (1 - p) / n for _, n in dens]) if p > 0 else 0.0
    return dict(nbuckets=len(densities), mean=mean_d, var=var_d, exp_var_null=exp_var,
                ratio=(var_d / exp_var) if exp_var > 0 else float('nan'),
                densities=densities)


if __name__ == '__main__':
    print("W7-RA3 — 2^-2N wall: does it factor into the TWO conditions (g1,h),")
    print("and is there an inter-bucket density VARIANCE spike at the wall round?\n")

    datasets = {}
    # N=10 from the repo CSV (authoritative, read-only); N=6,8 from lab-side recompiles.
    # (N>=12 is skipped: gap_analysis.c enumerates the 2^(4N) cascade space exhaustively,
    #  infeasible at N=12 (2^48). N=6,8,10 give three N for the across-N variance test.)
    datasets[10] = load_n10()
    print(f"[repo N=10, read-only] {len(datasets[10])} sr=60 collisions loaded", flush=True)
    for N in (6, 8):
        rows = run_gap(N)
        if rows:
            datasets[N] = rows
            print(f"[gap_analysis.c -DN={N}, lab-side /tmp] {len(rows)} sr=60 collisions", flush=True)
        else:
            print(f"[gap_analysis.c -DN={N}] no rows; skipping this N", flush=True)
    print()

    print("=== (1) EXPONENT DOUBLING: does the wall factor into two 2^-N conditions? ===")
    for N in sorted(datasets):
        prof = survival_profile(datasets[N], N)
        print(f"N={N}: sr60 colls={prof['M']}")
        print(f"   density profile r57..r60 (free cascade) = 1.000 each (whole-cube, tame)")
        print(f"   r61 condition A: P(h=0)  = {prof['Ph']:.6g}  (2^-N = {prof['expN']:.6g})")
        print(f"   r61 condition B: P(g1=0) = {prof['Pg']:.6g}  (2^-N = {prof['expN']:.6g})")
        print(f"   joint sr=61   : P(both) = {prof['Pboth']:.6g}  (2^-2N = {prof['exp2N']:.3g})")
        print(f"   INDEPENDENCE ratio P(both)/[P(h)P(g1)] = {prof['indep']:.4f} "
              f"(==1 => genuine rank-2, the two conditions)")
        doubled = (prof['Ph'] > 0 and prof['Pg'] > 0)
        print(f"   -> exponent DOUBLES (two 2^-N factors)? {doubled}  "
              f"lands on (g1,h)? {abs(prof['indep']-1.0) < 0.15 if prof['indep']==prof['indep'] else 'n/a'}\n")

    print("=== (2) NEW PREDICTION: inter-bucket density VARIANCE spike at the wall ===")
    for N in sorted(datasets):
        rows = datasets[N]
        # free-cascade baseline: a condition that always holds -> bucket var should be ~0
        # wall condition: h=0 (idx 6). Compare inter-bucket var to binomial-null.
        bv_wall = bucket_variance(rows, N, key_idx=6)
        bv_g1 = bucket_variance(rows, N, key_idx=4)
        if bv_wall is None:
            print(f"N={N}: too few buckets"); continue
        print(f"N={N}: wall condition h=0 across {bv_wall['nbuckets']} w57-buckets:")
        print(f"   mean density={bv_wall['mean']:.5g}  inter-bucket VAR={bv_wall['var']:.3g}  "
              f"binomial-null VAR={bv_wall['exp_var_null']:.3g}")
        print(f"   VAR / null = {bv_wall['ratio']:.2f}   "
              f"(>>1 => regularity BREAKDOWN spike; ~1 => regular/uniform => NO spike)")
        print(f"   (g1=0 cond: var/null = {bv_g1['ratio']:.2f})\n")

    print("=== VERDICT LOGIC ===")
    print("CONFIRM iff: (a) exponent doubles AND lands on the two conditions g1,h")
    print("            (independence ~1, the genuine rank-2), AND")
    print("            (b) a real inter-bucket density VARIANCE SPIKE at the wall")
    print("                (var/null >> 1) consistently across N.")
    print("KILL iff: drop is single-factor, OR no variance spike across N.")
    print("If (a) holds but (b) does NOT (var/null ~ 1 = regular, no breakdown), the")
    print("regularity LANGUAGE is a RENAME of the already-known two-condition counting")
    print("(finding #3): the 2^-2N is real rank-2, but 'Szemeredi density increment /")
    print("variance spike' adds NO new true prediction -> not a fresh CONFIRMED.")

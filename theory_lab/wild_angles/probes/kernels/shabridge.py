"""
shabridge.py — shared probe kit for the wild_angles execution sweep.

READ-ONLY toward ../../../sha256_review. Re-exports the repo's SHA-256 primitives
(never reimplemented), pins the ground-truth numbers every probe checks against, and
provides generic numeric helpers (GF(2) corank, top-eigenvalue, table loaders, a
background-QoS subprocess runner).

Use from a probe:
    import sys
    sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
    import shabridge as sb
    s = sb.s                      # s == repo lib.sha256
    print(sb.HARDCORE['total'])   # 132
"""
import os, sys, csv, subprocess

REPO = '/Users/mac/Desktop/sha256_review'
LAB  = '/Users/mac/Desktop/sha256_theory_lab'

# --- re-export the repo's SHA-256 primitives (NEVER reimplement these) ---
sys.path.insert(0, REPO)
from lib import sha256 as s                                              # noqa: E402
from lib.sha256 import (K, IV, MASK, ROR, SHR, Ch, Maj, Sigma0, Sigma1,  # noqa: E402,F401
                        sigma0, sigma1, add, hw, precompute_state,
                        build_schedule_tail, run_tail_rounds, full_compression)

# =====================================================================
# GROUND TRUTH  (from recon: writeups/ + coincidence_variety/ results)
# Every probe's kill_criterion is judged against these.
# =====================================================================

# The 132 hard-core output-difference bits: registers a,b,e,f FULLY at round 63
# (4 * 32 = 128) PLUS 4 scattered dc[63] bits = 132. Zero deterministic control.
HARDCORE = dict(total=132, full_registers=('a', 'b', 'e', 'f'),
                bits_per_register=32, full_count=128, dc_scattered=4,
                plateau_HW=74,  # expected output Hamming weight ~ half of 132 + cascade
                source=f'{REPO}/writeups/hard_core_132_bits.md')

# de-set cardinalities (|de57|, |de58|, |de59|, |de60|) vs word width N.
# de57 = de59 = de60 = 1 ALWAYS. Only de58 varies: de58 = 2**hw(db56) for N<=14,
# carry-collapsed at large N (1024 at N=32, vs 2**17 if it were XOR-linear).
DE_SIZES = {4: (1, 2, 1, 1), 6: (1, 8, 1, 1), 8: (1, 8, 1, 1), 10: (1, 16, 1, 1),
            11: (1, 32, 1, 1), 12: (1, 512, 1, 1), 13: (1, 32, 1, 1), 14: (1, 32, 1, 1),
            16: (1, 256, 1, 1), 32: (1, 1024, 1, 1)}
DE_LAW = 'de58 = 2**hw(db56) (exact for N<=14); de57 = de59 = de60 = 1 always'
DE_SOURCE = f'{REPO}/writeups/paper_figures_data.md'

# sr=60 -> sr=61 boundary: each enforced round costs 2**-2N -- TWO independent N-bit
# conditions g1=0 AND h=0 (per-message schedule match AND inter-message compatibility),
# empirically independent (ratio 1.005 at N=10 over ~1.07e9 hits).
SR61 = dict(rate='2**(-2*N) per enforced round', conditions=('g1=0', 'h=0'),
            independence_ratio_at_N10=1.005, P_h0='~2**-N', P_g1_0='~2**-N',
            source=f'{REPO}/headline_hunt/bets/coincidence_variety/RESULT_sr61_is_2minus2N.md')

# growth: # collisions ~ 2**(0.74 N); 132/256 hard-core bits -> HW~74 search plateau.
GROWTH_EXPONENT = 0.74

# data files on disk
GAP_ROWS_CSV = f'{REPO}/headline_hunt/bets/coincidence_variety/gap_rows.csv'  # N=10, cols w57,w58,w59,w60,g1,g2,h
PAPER_FIGS   = f'{REPO}/writeups/paper_figures_data.md'

# =====================================================================
# GENERIC NUMERIC HELPERS  (generic linear algebra / not lib primitives)
# =====================================================================

def gf2_rref(rows, n_cols):
    """RREF over GF(2). rows = list of row-bitmask ints (bit j = column j).
    Returns (pivot_cols, reduced_rows)."""
    m = (1 << n_cols) - 1
    rows = [r & m for r in rows]
    pivots, r = [], 0
    for col in range(n_cols):
        bit = 1 << col
        sel = next((i for i in range(r, len(rows)) if rows[i] & bit), None)
        if sel is None:
            continue
        rows[r], rows[sel] = rows[sel], rows[r]
        for i in range(len(rows)):
            if i != r and (rows[i] & bit):
                rows[i] ^= rows[r]
        pivots.append(col)
        r += 1
        if r == len(rows):
            break
    return pivots, rows

def gf2_rank(rows, n_cols):
    return len(gf2_rref(rows, n_cols)[0])

def gf2_corank(rows, n_cols):
    """corank = n_cols - rank = dim of the kernel / free-variable space."""
    return n_cols - gf2_rank(rows, n_cols)

def top_eigenvalue(mat, iters=5000, tol=1e-13):
    """Largest-magnitude eigenvalue (Perron) via power iteration. mat = square list-of-lists.
    Pure python, no numpy needed. Returns (lambda, eigenvector)."""
    n = len(mat)
    v = [1.0] * n
    lam = 0.0
    for _ in range(iters):
        w = [sum(mat[i][j] * v[j] for j in range(n)) for i in range(n)]
        nrm = max(abs(x) for x in w) or 1.0
        v = [x / nrm for x in w]
        if abs(nrm - lam) < tol:
            lam = nrm
            break
        lam = nrm
    return lam, v

def load_gap_rows(path=GAP_ROWS_CSV):
    """Parse the N=10 collision CSV -> list of dict rows (string values)."""
    with open(path) as f:
        return list(csv.DictReader(f))

def run_throttled(cmd_list, omp=2, timeout=900, cwd=None):
    """Run a command at BACKGROUND QoS (taskpolicy -b, prefers E-cores, yields to your
    foreground apps) with limited OpenMP threads. Returns CompletedProcess."""
    env = dict(os.environ, OMP_NUM_THREADS=str(omp))
    return subprocess.run(['taskpolicy', '-b'] + cmd_list, env=env, timeout=timeout,
                          capture_output=True, text=True, cwd=cwd)

if __name__ == '__main__':
    print('[selftest] lib.sha256 IV ok :', IV[0] == 0x6a09e667)
    print('[selftest] add wrap ok      :', add(0xffffffff, 1) == 0)
    print('[selftest] hw(0xff)         :', hw(0xff), '(expect 8)')
    print('[selftest] gf2_corank       :', gf2_corank([0b011, 0b110], 3), '(expect 1)')
    lam, _ = top_eigenvalue([[0.0, 1.0], [1.0, 1.0]])
    print('[selftest] golden eig       :', round(lam, 5), '(expect ~1.61803)')
    print('[selftest] DE_SIZES[32]     :', DE_SIZES[32], ' HARDCORE total:', HARDCORE['total'])
    print('[selftest] gap_rows on disk :', os.path.exists(GAP_ROWS_CSV))
    print('[selftest] precompute_state :', 'ok' if callable(precompute_state) else 'MISSING')

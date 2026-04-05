#!/usr/bin/env python3
"""
Script 85: Scaling Analysis — sr=60 SAT solve time vs word width

Compile all precision homotopy results and analyze the scaling trend.
Key question: does the solve time grow polynomially (tractable at N=32)
or exponentially (intractable)?
"""

# All known results from precision homotopy runs
results = [
    # N, result, time_seconds, vars, clauses, m0
    (8,  "SAT",    4.31,   2544,  10656, 0x67),
    (9,  "UNSAT",  0.18,   2911,  12193, 0x1e),   # DEGENERATE (rotation cancellation)
    (10, "SAT",   82.08,   3258,  13635, 0x34c),
    (11, "SAT",   None,    3592,  15056, 0x25f),   # from 82_extract run
    (12, "SAT",   None,    3936,  16481, 0x22b),   # from 82_extract run
    (13, "SAT",  219.62,   4274,  17902, 0x7),
    (14, "SAT",  425.47,   4611,  19337, 0x2f71),
    (15, "SAT",  265.80,   4982,  20909, 0x1596),
    # N=16: TIMEOUT at 600s (from earlier run)
    (16, "TIMEOUT", 600,   5324,  22309, None),
    # N=32: UNSAT for known candidates
    (32, "UNSAT/TIMEOUT", None, 10988, 46255, 0x17149975),
]

print("=" * 80)
print("sr=60 PRECISION HOMOTOPY: COMPLETE SCALING PICTURE")
print("=" * 80)

print(f"\n{'N':>4} {'Result':>10} {'Time(s)':>8} {'Vars':>6} {'Clauses':>8} {'M[0]':>12}")
print("-" * 60)
for r in results:
    N, result, t, v, c, m0 = r
    t_str = f"{t:.1f}" if t is not None else "-"
    m0_str = f"0x{m0:x}" if m0 is not None else "-"
    note = ""
    if N == 9:
        note = " (degenerate)"
    print(f"{N:4d} {result:>10} {t_str:>8} {v:6d} {c:8d} {m0_str:>12}{note}")

# Scaling analysis (exclude degenerate N=9 and TIMEOUT/UNSAT)
sat_results = [(N, t) for N, res, t, v, c, m0 in results
               if res == "SAT" and t is not None and N != 9]

print(f"\n{'='*60}")
print("SCALING TREND (SAT instances only, excl. N=9 degenerate)")
print(f"{'='*60}")

if len(sat_results) >= 2:
    import math
    # Fit exponential: T = a * b^N
    # log(T) = log(a) + N*log(b)
    ns = [N for N, t in sat_results]
    ts = [t for N, t in sat_results]
    log_ts = [math.log(t) for t in ts]

    # Simple linear regression on (N, log(T))
    n_pts = len(ns)
    sum_n = sum(ns)
    sum_lt = sum(log_ts)
    sum_nlt = sum(n * lt for n, lt in zip(ns, log_ts))
    sum_n2 = sum(n * n for n in ns)

    slope = (n_pts * sum_nlt - sum_n * sum_lt) / (n_pts * sum_n2 - sum_n * sum_n)
    intercept = (sum_lt - slope * sum_n) / n_pts

    b = math.exp(slope)
    a = math.exp(intercept)

    print(f"\nExponential fit: T = {a:.4f} * {b:.3f}^N")
    print(f"  Doubling every {math.log(2)/slope:.1f} bits of word width")

    print(f"\nExtrapolations:")
    for N_ext in [16, 20, 24, 28, 32]:
        T_ext = a * (b ** N_ext)
        if T_ext < 60:
            print(f"  N={N_ext}: {T_ext:.0f}s")
        elif T_ext < 3600:
            print(f"  N={N_ext}: {T_ext/60:.0f}min")
        elif T_ext < 86400:
            print(f"  N={N_ext}: {T_ext/3600:.1f}h")
        elif T_ext < 86400 * 365:
            print(f"  N={N_ext}: {T_ext/86400:.0f}d")
        else:
            print(f"  N={N_ext}: {T_ext/86400/365:.0f}y")

    print(f"\nPer-step scaling:")
    for i in range(1, len(sat_results)):
        N1, t1 = sat_results[i-1]
        N2, t2 = sat_results[i]
        if t1 > 0 and t2 > 0:
            ratio = t2 / t1
            per_bit = ratio ** (1.0 / (N2 - N1))
            print(f"  N={N1}→{N2}: {ratio:.1f}x ({per_bit:.2f}x per bit)")

    print(f"\n{'='*60}")
    print("KEY OBSERVATION")
    print(f"{'='*60}")
    print(f"""
The scaling is highly non-monotonic:
  N=10: 82s, N=13: 220s, N=14: 425s, N=15: 266s

N=15 is FASTER than N=14! This non-monotonicity means:
1. The difficulty depends heavily on the specific candidate, not just N
2. Extrapolation to N=32 is unreliable
3. The "barrier" may be candidate-dependent, not fundamental

If we could find the RIGHT candidate at N=32, the solve time might be
much less than the exponential fit suggests. The challenge is finding
that candidate in the sparse da[56]=0 space.
""")

print(f"\n{'='*60}")
print("dW[61] HW AT EACH WORD WIDTH (from collision analysis)")
print(f"{'='*60}")
dw61_data = [
    (8, 6, "SAT"),
    (10, 5, "SAT"),
    (11, 8, "SAT"),
    (12, 3, "SAT"),
    # N=13,14,15 pending extraction
    (32, 17, "UNSAT (sr=59 trail)"),
]
print(f"{'N':>4} {'dW[61] HW':>10} {'Status':>8}")
print("-" * 30)
for N, dhw, status in dw61_data:
    print(f"{N:4d} {dhw:10d} {status:>8}")
print(f"\nCorrelation: lower dW[61] HW → more likely SAT")
print(f"At N=32, dW[61] HW=17 is the highest — explains UNSAT")

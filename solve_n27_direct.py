#!/usr/bin/env python3
"""Direct solve of N=27 with output capture. Run with long timeout."""
import subprocess, sys, time

CNF = "/tmp/extract_N27_lw00kmdd/m0_2bfb506_fill_3ffffff.cnf"
OUT = "/tmp/n27_final_solution.txt"

print(f"Starting kissat on {CNF}", flush=True)
print(f"Output will be saved to {OUT}", flush=True)
t0 = time.time()

proc = subprocess.run(
    ["kissat", CNF],
    capture_output=True, text=True, timeout=14400  # 4 hour timeout
)

elapsed = time.time() - t0
print(f"Kissat finished: rc={proc.returncode} in {elapsed:.1f}s ({elapsed/3600:.2f}h)", flush=True)

with open(OUT, 'w') as f:
    f.write(proc.stdout)

if proc.returncode == 10:
    v_lines = [l for l in proc.stdout.split('\n') if l.startswith('v ')]
    print(f"SAT! Found {len(v_lines)} 'v' lines", flush=True)
    print(f"Solution saved to {OUT}", flush=True)
elif proc.returncode == 20:
    print("UNSAT!", flush=True)
else:
    print(f"Unknown result (rc={proc.returncode})", flush=True)
    if proc.stderr:
        print(f"stderr: {proc.stderr[:200]}", flush=True)

#!/usr/bin/env python3
"""
Race multiple solvers on the N=27 CNF to extract a collision certificate quickly.
Uses kissat with multiple seeds and cadical.
"""
import sys, os, time, subprocess, signal

CNF = "/tmp/extract_N27_lw00kmdd/m0_2bfb506_fill_3ffffff.cnf"

# Launch multiple solver configurations
configs = [
    ["kissat", "--seed=0", CNF],
    ["kissat", "--seed=1", CNF],
    ["kissat", "--seed=2", CNF],
    ["cadical", CNF],
]

print(f"Racing {len(configs)} solvers on {CNF}...")
procs = []
for i, cmd in enumerate(configs):
    solver = cmd[0]
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        procs.append((i, solver, cmd, p, time.time()))
        print(f"  [{i}] {' '.join(cmd)} (pid={p.pid})")
    except FileNotFoundError:
        print(f"  [{i}] {solver} not found, skipping")

print(f"\nWaiting for first SAT result...", flush=True)

while procs:
    for j, (i, solver, cmd, p, t0) in enumerate(procs):
        ret = p.poll()
        if ret is not None:
            elapsed = time.time() - t0
            stdout = p.stdout.read().decode('utf-8', errors='replace')
            if ret == 10:
                print(f"\n*** SAT *** [{i}] {solver} in {elapsed:.1f}s ({elapsed/3600:.2f}h)")
                # Kill other solvers
                for k, (_, _, _, p2, _) in enumerate(procs):
                    if k != j:
                        p2.kill()
                        p2.wait()

                # Save the solution
                out_path = "/tmp/n27_solution.txt"
                with open(out_path, 'w') as f:
                    f.write(stdout)
                print(f"Solution saved to {out_path}")
                print(f"Solution size: {len(stdout)} bytes")

                # Count v lines
                v_lines = [l for l in stdout.split('\n') if l.startswith('v ')]
                print(f"Found {len(v_lines)} 'v' lines")

                sys.exit(0)
            elif ret == 20:
                print(f"  [{i}] {solver} UNSAT in {elapsed:.1f}s", flush=True)
            else:
                print(f"  [{i}] {solver} rc={ret} in {elapsed:.1f}s", flush=True)
            procs.pop(j)
            break
    else:
        time.sleep(1)
        # Progress update every 5 minutes
        elapsed = time.time() - procs[0][4]
        if int(elapsed) % 300 == 0 and int(elapsed) > 0:
            print(f"  ... {elapsed/60:.0f} min elapsed, {len(procs)} solvers running", flush=True)

print("All solvers finished without SAT")

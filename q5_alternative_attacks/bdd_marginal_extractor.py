#!/usr/bin/env python3
"""
BDD Marginal Extractor — Extract collision-bit statistics for SAT guidance.

Reads collision coordinates, computes per-bit marginal probabilities
(P(bit=1 | collision)), and outputs phase hints for Kissat.

The idea (from both Gemini and GPT-5.4): the N=12 BDD encodes the exact
collision manifold. Extract the statistical backbone and use it to guide
N=32 SAT solving via phase initialization.

Usage:
  grep '^COLL' solver_output.txt | python3 bdd_marginal_extractor.py N [output.phases]
"""
import sys
from collections import defaultdict

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
out_file = sys.argv[2] if len(sys.argv) > 2 else None

# Read collision coordinates from stdin
collisions = []
for line in sys.stdin:
    parts = line.strip().split()
    if len(parts) >= 4:
        if parts[0] == 'COLL':
            parts = parts[1:]
        try:
            w57, w58, w59, w60 = [int(x, 16) for x in parts[:4]]
            collisions.append((w57, w58, w59, w60))
        except ValueError:
            continue

if not collisions:
    print("No collisions read from stdin")
    sys.exit(1)

print(f"Read {len(collisions)} collisions at N={N}")
print(f"Variables: 4×{N} = {4*N} bits\n")

# Compute per-bit marginal probabilities
# For each bit position in each word: P(bit=1 | collision)
bit_counts = defaultdict(int)  # (word_idx, bit) -> count of 1s

for w57, w58, w59, w60 in collisions:
    words = [w57, w58, w59, w60]
    for wi, w in enumerate(words):
        for b in range(N):
            if (w >> b) & 1:
                bit_counts[(wi, b)] += 1

total = len(collisions)

print("=" * 60)
print("Per-bit marginal probabilities P(bit=1 | collision)")
print("=" * 60)
print(f"{'Word':>6} {'Bit':>4} {'P(1)':>8} {'Count':>8} {'Bias':>8} {'Phase':>6}")
print("-" * 60)

phase_hints = {}  # var_index -> suggested_phase (True/False)
strong_biases = []

for wi, wname in enumerate(["W57", "W58", "W59", "W60"]):
    for b in range(N):
        count = bit_counts.get((wi, b), 0)
        prob = count / total
        bias = abs(prob - 0.5)

        # Interleaved variable index: var = 4*b + wi
        var_idx = 4 * b + wi

        # Phase hint: if strongly biased, suggest that phase
        phase = None
        if prob > 0.7:
            phase = True   # suggest var=1
            phase_hints[var_idx] = True
        elif prob < 0.3:
            phase = False  # suggest var=0
            phase_hints[var_idx] = False

        phase_str = "1" if phase is True else ("0" if phase is False else "-")
        marker = " ***" if bias > 0.2 else ""
        print(f"{wname:>6} [{b:>2}]  {prob:>7.3f}  {count:>6}/{total}  {bias:>7.3f}  {phase_str:>5}{marker}")

        if bias > 0.2:
            strong_biases.append((wname, b, prob, bias))

print(f"\n{'=' * 60}")
print(f"Summary:")
print(f"  Total collisions: {total}")
print(f"  Variables with strong bias (>0.2): {len(strong_biases)}/{4*N}")
print(f"  Phase hints generated: {len(phase_hints)}/{4*N}")
print()

if strong_biases:
    print("Strongly biased bits:")
    for wname, b, prob, bias in sorted(strong_biases, key=lambda x: -x[3]):
        direction = "→1" if prob > 0.5 else "→0"
        print(f"  {wname}[{b}]: P(1)={prob:.3f} (bias={bias:.3f}) {direction}")

# Cross-bit correlation analysis
print(f"\n{'=' * 60}")
print("Word-level statistics:")
for wi, wname in enumerate(["W57", "W58", "W59", "W60"]):
    values = [c[wi] for c in collisions]
    unique = len(set(values))
    print(f"  {wname}: {unique} unique values out of {total} collisions ({unique/total*100:.0f}% unique)")

# Output phase file for Kissat
if out_file or True:
    fname = out_file or f"/tmp/collision_phases_n{N}.txt"
    with open(fname, "w") as f:
        f.write(f"c Phase hints from {total} collisions at N={N}\n")
        f.write(f"c {len(phase_hints)} variables with strong bias\n")
        for var_idx in sorted(phase_hints.keys()):
            phase = phase_hints[var_idx]
            # Map to the SAT variable numbering (1-indexed)
            sat_var = var_idx + 1
            if phase:
                f.write(f"{sat_var}\n")
            else:
                f.write(f"-{sat_var}\n")
    print(f"\nPhase hints saved to {fname}")

# Also output as assumption clauses that can be appended to CNF
assumption_file = f"/tmp/collision_assumptions_n{N}.cnf"
with open(assumption_file, "w") as f:
    f.write(f"c Assumption clauses from {total} collisions at N={N}\n")
    f.write(f"c Use as soft constraints or initial assumptions\n")
    for var_idx in sorted(phase_hints.keys()):
        phase = phase_hints[var_idx]
        sat_var = var_idx + 1
        if phase:
            f.write(f"{sat_var} 0\n")
        else:
            f.write(f"-{sat_var} 0\n")
print(f"Assumption clauses saved to {assumption_file}")

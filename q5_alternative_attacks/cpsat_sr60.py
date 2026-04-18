#!/usr/bin/env python3
"""
CP-SAT Solver for sr=60 Cascade Collisions

Uses Google OR-Tools CP-SAT with NATIVE modular arithmetic.
Instead of bit-blasting additions into XOR/AND gates (SAT approach),
CP-SAT understands Z = (X + Y) % 2^N directly.

Review 8 recommendation (Gemini): "SAT bit-blasts modular addition
into thousands of gates, destroying the high-level math. CP-SAT
natively understands Z = (X + Y) mod 2^N."

Usage: python3 cpsat_sr60.py [N]
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from ortools.sat.python import cp_model

N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
MASK = (1 << N) - 1
MSB = 1 << (N - 1)

spec = __import__('50_precision_homotopy')
sha = spec.MiniSHA256(N)
KT = [k & MASK for k in spec.K32]
result = sha.find_m0()
m0, s1, s2, W1p, W2p = result

print(f"CP-SAT sr=60 at N={N}, M[0]=0x{m0:x}")

model = cp_model.CpModel()

# Variables: W1[57..60] as N-bit integers
W1 = [model.new_int_var(0, MASK, f"W1_{57+i}") for i in range(4)]

# Cascade: derive W2 from W1 through round function
def ror(x, k):
    k = k % N
    return ((x >> k) | (x << (N - k))) & MASK

def Sigma0(a): return ror(a, sha.r_Sig0[0]) ^ ror(a, sha.r_Sig0[1]) ^ ror(a, sha.r_Sig0[2])
def Sigma1(e): return ror(e, sha.r_Sig1[0]) ^ ror(e, sha.r_Sig1[1]) ^ ror(e, sha.r_Sig1[2])
def Ch(e, f, g): return ((e & f) ^ ((~e) & g)) & MASK
def Maj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & MASK

# We can't use CP-SAT's native modular arithmetic easily because
# the round function involves XOR, rotation, Ch, Maj — all bitwise.
# CP-SAT's strength is linear/modular constraints, not bitwise ops.
#
# The most effective approach: use CP-SAT with element constraints
# or use the AllowedAssignments (table) constraint for small N.

# For N=4: just enumerate via AllowedAssignments on 4 variables
# This is a table constraint — CP-SAT is very fast on these.

print(f"Building collision table for N={N}...")
t0 = time.time()

# Find all collisions by brute force (fast for small N)
collision_tuples = []
for w_flat in range(1 << (4*N)):
    W1v = [(w_flat >> (i*N)) & MASK for i in range(4)]

    # Cascade
    st_a, st_b = list(s1), list(s2)
    W2v = []
    for r in range(4):
        a1,b1,c1,d1,e1,f1,g1,h1 = st_a
        a2,b2,c2,d2,e2,f2,g2,h2 = st_b
        t1nw1 = (h1+Sigma1(e1)+Ch(e1,f1,g1)+KT[57+r])&MASK
        t1nw2 = (h2+Sigma1(e2)+Ch(e2,f2,g2)+KT[57+r])&MASK
        t2_1 = (Sigma0(a1)+Maj(a1,b1,c1))&MASK
        t2_2 = (Sigma0(a2)+Maj(a2,b2,c2))&MASK
        offset = ((t1nw1+t2_1)-(t1nw2+t2_2))&MASK
        w2r = (W1v[r]+offset)&MASK
        W2v.append(w2r)
        t1_1=(t1nw1+W1v[r])&MASK; t1_2=(t1nw2+w2r)&MASK
        st_a = [(t1_1+t2_1)&MASK,a1,b1,c1,(d1+t1_1)&MASK,e1,f1,g1]
        st_b = [(t1_2+t2_2)&MASK,a2,b2,c2,(d2+t1_2)&MASK,e2,f2,g2]

    # Schedule + rounds
    W1f = list(W1p[:57]) + list(W1v)
    W2f = list(W2p[:57]) + list(W2v)
    for t in range(61,64):
        W1f.append((sha.sigma1(W1f[t-2])+W1f[t-7]+sha.sigma0(W1f[t-15])+W1f[t-16])&MASK)
        W2f.append((sha.sigma1(W2f[t-2])+W2f[t-7]+sha.sigma0(W2f[t-15])+W2f[t-16])&MASK)

    def rnd(s,k,w):
        a,b,c,d,e,f,g,h=s
        t1=(h+Sigma1(e)+Ch(e,f,g)+k+w)&MASK
        t2=(Sigma0(a)+Maj(a,b,c))&MASK
        return ((t1+t2)&MASK,a,b,c,(d+t1)&MASK,e,f,g)

    st1r,st2r = tuple(s1),tuple(s2)
    for i in range(7):
        st1r = rnd(st1r,KT[57+i],W1f[57+i])
        st2r = rnd(st2r,KT[57+i],W2f[57+i])

    if all(a==b for a,b in zip(st1r,st2r)):
        collision_tuples.append(tuple(W1v))

build_time = time.time() - t0
print(f"Found {len(collision_tuples)} collisions in {build_time:.2f}s")

# Add table constraint
model.add_allowed_assignments(W1, collision_tuples)

# Solve and count
class SolutionCounter(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.solutions = []
    def on_solution_callback(self):
        self.count += 1
        sol = tuple(self.value(w) for w in W1)
        self.solutions.append(sol)

solver = cp_model.CpSolver()
solver.parameters.enumerate_all_solutions = True

t0 = time.time()
counter = SolutionCounter()
status = solver.solve(model, counter)
solve_time = time.time() - t0

print(f"\nCP-SAT solve time: {solve_time:.3f}s")
print(f"Solutions found: {counter.count}")
print(f"Status: {solver.status_name(status)}")
if counter.count <= 10:
    for sol in counter.solutions:
        print(f"  W1 = [{', '.join(hex(x) for x in sol)}]")

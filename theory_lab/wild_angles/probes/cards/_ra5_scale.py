"""W7-RA5 decisive scale check (finding #4): does the Ramsey number that would
*force* the RED clique SHA needs DWARF SHA's dimensions (64 rounds, K~few-dozen
words)?  And is the boundary collapse a Ramsey-threshold-in-K phenomenon or a
round-function fact independent of K?

Ramsey facts (standard):
  * R(s,s) lower bound (Erdos):  R(s,s) > 2^(s/2)   => to FORCE a monochromatic
    size-s clique you need vertex count K >= ~2^(s/2).
  * Diagonal Ramsey R(3,3)=6, R(4,4)=18, R(5,5) in [43,48], R(6,6) in [102,165].
A 'multi-word collision family' SHA needs is a clique of size s = a few words
(the cascade has ONE free axis -> the needed RED clique is essentially s=2..4).

Two independent nails:
  (1) Scale: K to FORCE even a size-6 RED clique ~ 2^3 = 8; size-10 ~ 2^5=32.
      These are TINY; the threshold is met at trivial K -> non-predictive
      (the card's own 'weakest of the five' caveat). Meanwhile a REAL vdW/Ramsey
      object would need K astronomically larger than 64.
  (2) K-independence: vary K at FIXED round; if the RED-clique fraction (de=0
      survivors / K) is ~constant in K (not a sharp onset at some K*), the collapse
      is a round-function fact, NOT a Ramsey-in-K forcing.
"""
import sys, math, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as E
import _hc_family as HC


def survivors_at(N, K, r, seed):
    """Fraction of K random vertices that are de=0 (cascade-alive) through round r."""
    M = E.make_model(N); setup = E.find_M0(M)
    MASK = M['MASK']; rng = random.Random(seed)
    cnt = 0
    for _ in range(K):
        v = (rng.randint(0, MASK), rng.randint(0, MASK),
             rng.randint(0, MASK), rng.randint(0, MASK))
        tr, _ = HC.tail_trace(M, setup, *v)
        if tr[r][4] == 0:  # de == 0
            cnt += 1
    return cnt, K


print("=== (1) RAMSEY SCALE vs SHA dimensions ===")
print("To FORCE a monochromatic clique of size s, need K >= ~2^(s/2) (Erdos bound).")
print("SHA's needed multi-word collision clique: s = 2..4 (ONE free cascade axis).")
for s in (2, 3, 4, 6, 10, 64):
    K_force = 2 ** (s / 2)
    print(f"  size-{s:>2} RED clique: forcing K ~ 2^({s}/2) = {K_force:.1f} vertices")
print("  -> SHA needs s<=4 -> K~4 suffices (trivially met). A REAL Ramsey threshold")
print("     for s comparable to 64 rounds would need K ~ 2^32 -> DWARFS SHA. The")
print("     relevant cliques are tiny => Ramsey forcing is NON-PREDICTIVE here.\n")

print("=== (2) Is the round-61 collapse a Ramsey-in-K onset, or K-independent? ===")
print("de=0 survivor FRACTION at round r, as K grows (should be ~flat if round-function fact):")
for N in (4, 8):
    print(f"  N={N}:")
    for r in (60, 61, 62):
        fracs = []
        for K in (16, 64, 256, 1024):
            c, _ = survivors_at(N, K, r, seed=100 + r + K)
            fracs.append((K, c / K))
        s = "  ".join(f"K={K}:{f:.3f}" for K, f in fracs)
        tag = " <== boundary" if r == 61 else ""
        print(f"    r={r}: {s}{tag}")
print("\n  If the r=61 fraction is ~constant across K (no onset at a special K*),")
print("  the collapse is the schedule condition (a round-function fact), NOT a")
print("  Ramsey-number-vs-vertex-count forcing. Round 60 fraction ~1.0 = free cascade.")

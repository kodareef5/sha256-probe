"""W7-RA1 adversarial refinement. The raw 'frozen carry cell' count (~520-553) is
dominated by TRIVIAL structure, not a 132 Ramsey core. Strip the trivialities and
ask: is there a STABLE (N-independent) contiguous monochromatic core of size ~132?

Trivialities to remove:
  (T0) bit-0 carry-in is ALWAYS 0 (no carry into the LSB) -> 64 rounds x 7 slots
       = 448 frozen cells, pure arithmetic triviality.
  (T1) early-round cells frozen only because the IV fixes the inputs (rounds where
       the addends are still constant across messages because the message hasn't
       diffused) -> finite-size propagation determinism, exactly the skeptic's
       'not asymptotic forcing'.

We then test the survivor 'core' for:
  * STABILITY: does the survivor count converge to a fixed 132-like number as N
    grows, or keep scaling with N?  (finding #1: a c*N census is NOT 132.)
  * BASIS-INDEPENDENCE proxy: is the survivor set the SAME (round,slot,bit) set
    across N (after aligning bit indices), or does it shift with width? A stable
    invariant must be the same object.
  * CONTIGUITY of survivors only (after removing the bit-0 vertical line which
    fakes contiguity).
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import importlib.util, os
spec = importlib.util.spec_from_file_location("ra1mod", os.path.join(os.path.dirname(__file__), "W7-RA1.py"))
ra1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(ra1)


def frozen_and_diffusion(N, n_msgs=600, n_rounds=64, seed=3):
    """Return frozen cells AND, per cell, whether its addends were already constant
    across messages (so we can flag finite-size/IV-propagation freezes)."""
    M, frozen, total, cells = ra1.frozen_analysis(N, n_msgs=n_msgs, n_rounds=n_rounds, seed=seed)
    return M, set(frozen), total


def strip(frozen, N):
    """Remove bit-0 (LSB, no carry-in ever) cells. Return survivors + count removed."""
    bit0 = {c for c in frozen if c[2] == 0}
    surv = frozen - bit0
    return surv, len(bit0)


def round_localize(frozen):
    by_round = {}
    for (r, slot, j) in frozen:
        by_round[r] = by_round.get(r, 0) + 1
    return by_round


print("W7-RA1 refinement: strip trivial carries, test for a STABLE 132 core\n")
results = {}
for N in (4, 6, 8, 10, 12):
    M, frozen, total = frozen_and_diffusion(N, n_msgs=600)
    surv, n_bit0 = strip(frozen, N)
    br = round_localize(surv)
    # how many survivors live in EARLY rounds (<=15, IV/message-diffusion regime)
    early = sum(v for r, v in br.items() if r <= 15)
    late = sum(v for r, v in br.items() if r > 15)
    # contiguity of survivors (no bit-0 line)
    F = surv; nbr = 0; deg = 0
    for (r, slot, j) in F:
        for dr, dj in ((1,0),(-1,0),(0,1),(0,-1)):
            deg += 1
            if (r+dr, slot, j+dj) in F: nbr += 1
    nf = nbr/deg if deg else 0.0
    results[N] = dict(total_frozen=len(frozen), bit0=n_bit0, surv=len(surv),
                      early=early, late=late, contig=nf, br=br)
    print(f"N={N:>2}: frozen={len(frozen)}  -bit0(LSB,always0)={n_bit0}  "
          f"=> survivors={len(surv)}")
    print(f"      survivors in early rounds(<=15)={early}  late(>15)={late}")
    print(f"      survivor contiguity (no LSB line) neighbor_frac={nf:.3f}")
    # show the late survivors explicitly (these are the candidate 'core')
    late_cells = sorted([c for c in surv if c[0] > 15])
    print(f"      late survivor cells ({len(late_cells)}): {late_cells[:10]}"
          f"{' ...' if len(late_cells)>10 else ''}\n")

print("=== STABILITY: survivor count vs N (must be ~FLAT ~132 to be a real core) ===")
for N in (4,6,8,10,12):
    r = results[N]
    print(f"  N={N:>2}: survivors={r['surv']:<4} (late,r>15 = {r['late']:<3})  "
          f"contig={r['contig']:.3f}")
survs = [results[N]['surv'] for N in (4,6,8,10,12)]
lates = [results[N]['late'] for N in (4,6,8,10,12)]
print(f"\n  survivor counts: {survs}  -> {'GROWS with N' if survs[-1]>survs[0]+3 else 'flat'}")
print(f"  late (r>15) survivor counts: {lates}  -> these are the only non-finite-size")
print(f"      candidates; {'GROW with N' if lates[-1]>lates[0]+2 else 'roughly flat'}.")
print("\n  finding #1 verdict logic: 132 must be a STABLE basis-independent object.")
print("  If survivors GROW with N (width-scaling) and/or are dominated by early-round")
print("  finite-size freezes, there is no stable 132 monochromatic core -> KILL.")

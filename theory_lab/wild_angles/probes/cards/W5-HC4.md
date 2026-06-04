# W5-HC4 — VC-dimension: 0.74 and 132 as two faces of one Sauer–Shelah quantity   ·   VERDICT: KILLED

**Card claim:** the collision family as a concept class; forced coordinates (never shattered)
= the 132 hard-core bits; VC-dim d gives #collisions via Sauer–Shelah, so
log-count ≈ d·log2(4N/d) = 0.74N solves for d. (Both 0.74 and 132 from one quantity.)

**Probe run:** the exact sr=60 collision families at N=4 (49), N=8 (260), N=10 (946), each
collision a 4N-bit free-word vector (the concept class on the 4N free coordinates). Counted
forced coordinates, computed VC-dimension (exhaustive over a balanced-coordinate pool), and
checked Sauer–Shelah vs |S| and the implied exponent. Pure-python, throttled.

**Result (numbers):**
| N | 4N | \|S\| | forced coords | =132? | VC-dim | log2\|S\| | SS ≥ \|S\|? | c = log2\|S\|/N |
|---|----|----|----|----|----|----|----|----|
| 4 | 16 | 49 | **2** | no | 4 | 5.61 | yes | 1.404 |
| 8 | 32 | 260 | **0** | no | 6 | 8.02 | yes | 1.003 |
| 10| 40 | 946 | **0** | no | 8 | 9.89 | yes | 0.989 |

- **Forced coordinates → ~0** (2, 0, 0), nowhere near 132, nor 0.516·4N, nor the 4N+4 census
  scaling (20, 36, 44). The "forced coords = 132 hard core" identity is false.
- **VC-dim = 4, 6, 8** — just ⌊log2|S|⌋-ish (the family is tiny, so VC-dim is trivially
  capped by log2(count)); it scales with N, not toward a 132 hard core.
- **Sauer–Shelah holds only as a loose upper bound** (|S| ≪ Σ_{i≤d} C(4N,i)); it does not
  derive a sharp 0.74. c = log2|S|/N = 1.40 / 1.00 / 0.99; verified slope 260@8→946@10 =
  **0.932**; repo fit 0.673. The card's d·log2(4N/d)=0.74N has two free unknowns, so it can be
  *fit* but pins nothing.

**Kill_criterion:** "forced-coordinate count doesn't track 132/256, OR Sauer–Shelah count
wildly off with no N-trend." — **fired? YES** (first clause decisively: forced coords ≈ 0, not
132; and the Sauer–Shelah "0.74" is the same noisy growth exponent, not a derived constant).

**Verdict reasoning:** KILLED — both faces fail, exactly as findings #1 and #2 predicted.
(132 face) The hard-core 132 is an *output*-space single-bit-flip control census ({a,b,e,f}@63
+ 4dc, scaling 4N+4), which has nothing to do with "coordinates never shattered" by the
*input* concept class — and the actual forced input coordinates are ≈ 0. (0.74 face) VC-dim is
a trivial log2|S| artifact of a tiny family, Sauer–Shelah is a loose upper bound (the card's
own skeptic flags this), and the implied exponent is the noisy 0.67–1.0 collision-growth slope,
not a sharp 0.74. So "132 and 0.74 are two faces of one Sauer–Shelah quantity" is unsupported:
the two numbers are unrelated objects, and neither is reproduced by the VC machinery.

**Cross-check / skeptic note:** The VC-dim ≈ log2|S| coincidence is the tell — a family of |S|
points can shatter at most ⌊log2|S|⌋ coordinates, so "VC-dim grows like 0.8N" is forced by
|S| ≈ 2^{0.7–1.0 N} and carries no extra structure. Independent corroboration of #1 (forced
coords ≠ 132; cf. W2-CT1, W5-HC2) and #2 (no sharp 0.74; cf. W2-NT1, W2-CT4). A defender might
move the concept class to the output bits, but collisions have identically-zero output diff, so
no coordinate is shattered there at all (VC-dim 0) — still not 132.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-HC4.py`

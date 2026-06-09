---
date: 2026-06-09
author: subagent (fable session)
evidence_level: EVIDENCE
status: twist 9 — "linear distance" of SHA-256; quantifies the Ch/Maj nonlinearity budget vs carries
---

# Twist 9 — the linear distance of SHA-256

**Question.** Twist 5 showed SHA-256's diffusion comes MORE from modular-add
carries than from Ch/Maj (R=4 avalanche drop 25.5 for carries vs 14.5 for
Ch=Maj=0). This twist quantifies the OTHER half: how close is the round
function to a fully GF(2)-affine (trivially collidable) hash? Ch and Maj are
the *only* true Boolean nonlinearity (Sigma/sigma are already GF(2)-linear; the
adds are nonlinear only through carries). Replace Ch/Maj with their best linear
approximations, optionally turn the adds into XOR, and measure how the
differential behaviour collapses toward determinism.

Method: for a fixed 1-bit input difference, run R rounds from 200 random bases
with a fixed (shared, cancelling) schedule; an output-diff bit is
**deterministic** if it is constant across all bases. A GF(2)-affine round makes
the output diff a pure linear function of the input diff, so *every* bit is
deterministic (100%). `det%` = fraction of 256 output-diff bits that are
constant across bases, averaged over 40 input-diff positions (8 registers × 5
offsets). Deterministic. `lib/sha256` primitives.

## Part 1 — bias of the linear approximations (exhaustive)

Ch and Maj are bitwise, so the per-bit truth table (8 input triples) is
exhaustive and identical across all 32 positions.

| function | best affine approx | agreement |
|---|---|---|
| Ch(e,f,g) | **g** (also f, or e^g) | **0.750** |
| Maj(a,b,c) | **a^b^c** (linear part, up to offset) | **0.750** |

Both best approximations sit at the classic **0.75 agreement** (bias 1/4) — the
maximum for these 3-input gadgets. Ch is well-approximated by any single "later"
input (g/f) because Ch is a multiplexer selecting f or g; Maj's only nonzero
linear correlation is to the full parity a^b^c. (`a^b^c` prints "agree 0.250"
= its complement/NXOR agrees 0.750; the affine offset cancels in any difference,
so the linear part a^b^c is what matters.)

## Part 2 — fully-linearized variant is deterministic (sanity + collapse)

Ch/Maj -> linear AND adds -> XOR => round is GF(2)-affine. Confirmed: a fixed
input difference forces a fixed output difference, **det% = 100.0 at every R**.

| R | full SHA det% / hw | fully-linear det% / hw |
|---|---|---|
| 2 | 75.3% / 18.1 | 100.0% / 9.5 |
| 3 | 53.3% / 41.2 | 100.0% / 23.6 |
| 4 | 30.1% / 68.7 | 100.0% / 42.9 |
| 6 |  4.8% / 114.6 | 100.0% / 84.8 |
| 8 |  0.1% / 127.3 | 100.0% / 109.2 |

Full SHA-256's determinism **decays exponentially** with R (75%→53%→30%→5%→0.1%):
the round budget of nonlinearity is consumed within ~6 rounds, after which the
output difference is fully base-dependent. The fully-linear hash never leaves
det=100% — every difference is predictable, hence trivially collidable.

## Part 3 — nonlinearity-budget partition (R=4, determinism gained vs L0)

| level | det% | aval-hw | det-gain vs full |
|---|---|---|---|
| L0 full SHA-256 | 30.3 | 69.0 | +0.0 |
| L1a **Ch linear only** | 34.5 | 67.4 | **+4.2** |
| L1b **Maj linear only** | 30.2 | 71.5 | **-0.1** |
| L2 Ch+Maj linear | 34.5 | 70.0 | +4.2 |
| C **carries->XOR only** | 78.7 | 44.2 | **+48.4** |
| B Ch=Maj=0 | 46.7 | 54.5 | +16.4 |
| L3 FULLY LINEAR | 100.0 | 42.9 | +69.7 |

**Determinism unlocked by removing each nonlinearity source (R=4):**

- remove carries (adds->XOR): **+48.4 pts**  ← dominant
- linearize Ch: +4.2 pts
- linearize Maj: -0.1 pts (negligible / within noise)
- linearize both Ch+Maj: +4.2 pts (no synergy)

**Ranking of nonlinearity contribution: CARRIES ≫ Ch > Maj (≈0).**

Two independent lenses agree on carry dominance. Twist 5 used avalanche-HW
(carries drop 25.5 vs booleans 14.5, ratio **1.76×**). This twist uses
determinism, a sharper linear-distance metric, and the gap is far larger:
carries unlock **+48.4** determinism pts vs **+4.2** for both booleans — a
**~11×** ratio. Determinism separates the two sources much more cleanly than
avalanche does, because the affine carry-free path makes diffs *exactly*
predictable while still spreading them (note carries->XOR keeps a high hw of
44.2 yet 78.7% determinism — diffusion without nonlinearity).

A striking single fact: **Maj contributes essentially nothing** to per-round
linear distance at R=4 (-0.1 pts; its linearization slightly *raised* avalanche
hw). Ch carries the entire Boolean budget — consistent with Ch sitting on the
nonlinear T1 path (with Sigma1, fed by the fast-mixing register e), while Maj
sits on T2 fed by the slow register a (cf. Twist 4: a/b are the slow-diffusing
end). The famous "two Boolean functions" are not equal partners: Ch >> Maj.

## Part 4 — how many rounds become trivial as nonlinearity is removed

det% vs R (~100 => round behaves linearly/trivially for that input diff):

| level | R1 | R2 | R3 | R4 | R5 | R6 | R8 | R12 | R16 |
|---|---|---|---|---|---|---|---|---|---|
| full | 94 | 76 | 55 | 31 | 12 | 5 | 0 | 0 | 0 |
| Ch-lin | 95 | 80 | 59 | 36 | 15 | 6 | 0 | 0 | 0 |
| Maj-lin | 94 | 77 | 54 | 31 | 12 | 5 | 0 | 0 | 0 |
| both-lin | 95 | 80 | 59 | 36 | 15 | 6 | 0 | 0 | 0 |
| **fully-lin** | **100** | **100** | **100** | **100** | **100** | **100** | **100** | **100** | **100** |

Linearizing the Booleans buys only a few extra rounds of near-determinism
(both-lin reaches det≈0 at R8, same as full; the curve shifts right by **<1
round**). The carries are what kill determinism: with carries intact, even a
fully Boolean-linear round drops below 50% det by R≈3 and to 0 by R≈8. **Only
when carries are also removed does the hash become trivial at all R.**

## Verdict (honest)

- **No attack.** Linearizing Ch/Maj alone moves SHA-256's linear distance by a
  few points (+4.2 det pts at R=4) and shifts the rounds-to-trivial curve by
  <1 round. The Boolean functions are NOT where the irreducible nonlinearity
  lives, so a linear/affine approximation attack on the Ch/Maj layer gains
  almost nothing — the carries remain and re-randomize the differential within
  ~6 rounds. Full SHA-256 is far from affine: determinism is already 0 by R=8.
- **Rounds made trivial by removing nonlinearity:** removing the Booleans makes
  ~0 extra rounds trivial (curve shift <1 round). Only the *fully* linear hash
  (carries also gone) is trivial — and then it is trivial at ALL 64 rounds
  (det=100% everywhere), i.e. a single GF(2) collision construction works. That
  is the floor the carries are protecting against.
- **Where the irreducible nonlinearity sits:** **carries (~48 det pts) ≫ Ch
  (~4 pts) > Maj (~0 pts)**. Twist 5's carry-dominance result is confirmed and
  sharpened ~11× under the determinism metric, and refined: within the small
  Boolean budget, **Ch dominates Maj almost entirely**. SHA-256's collision
  resistance is overwhelmingly an artifact of modular-add carries, secondarily
  of Ch, and essentially not of Maj — which is the single most attackable
  Boolean component but contributes too little to matter.

Caveats: per-round / state-path probe (schedule sigmas not linearized here);
determinism uses 200 bases × 40 input-bit positions (sampling, deterministic
seeds); "trivially collidable" for the affine limit is exact (it's a GF(2)
linear map), the per-round determinism for partial levels is an empirical proxy.
Consistent with Twist 2 (no single carry load-bearing): the carry resistance is
distributed AND dominant.

## Reproduce
```
python3 headline_hunt/twisted_probes/twist9_linear_distance.py
```

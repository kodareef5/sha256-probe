# W4-LG4 — Center vortices → the 132 hard-core as vortex-pierced plaquettes   ·   VERDICT: KILLED

**Card claim:** Long carry chains = Z₂ center vortices; the 132 hard-core = plaquettes pierced in nearly every collision (topologically pinned → HW~74). Probe: extract carry chains + bit-footprints; test piercing-correlation above a carry-density baseline; vortex free energy = collision-cost of forcing a chain to terminate, area-law only at 61.

**Probe run:** (1) Per-output-(register,bit) deterministic single-bit controllability at width N=4,5,8 (`/tmp/hardcore_census.c`, primitives/MSB-kernel VERBATIM from the repo enumerator) — reproduces the hard-core. (2) Carry-difference "vortex" footprint from the real width-N field (`/tmp/wfield8.txt`, 260 collisions). (3) Free-energy 59→61 = the string tension σ(r) from W4-LG1. Throttled.

**Result (numbers):**
- Hard-core (registers with ZERO deterministic single-bit control) at round 63: at every N, **registers a, b, e, f are FULLY uncontrolled** (N/N), d and h fully controlled (0/N), c and g partial — the exact 32-bit pattern.
- TOTAL hard-core count: **N=4 → 23, N=5 → 28, N=8 → 46.** It grows LINEARLY with N (≈ 4N + c,g partials). The 32-bit value 132 = 4 registers × 32 + 4 scattered dc bits — it **tracks width, not topology.**
- Carry-vortex footprint: per-bit carry-diff frequency (bits 0..7) = [0, 131, 510, 520, 387, 278, 269, 243]; mean **8.99 piercings/collision** on a 56-edge lattice — a DENSITY that scales with lattice area, never approaching a fixed 132.
- Free energy σ(r) over r57..61 = 0.434, 0.485, 0.182, 0.000, 0.000 — smooth decay to zero by r60; **no area-law onset at 61.**

**Kill_criterion:** "hard-core positions independent of chain footprints (vs carry-density baseline), or no free-energy change 59→61" — **fired? YES (both).**

**Verdict reasoning:** KILLED, and it re-commits the **132 category error** (prior finding #1). (a) The 132 is the OUTPUT-CONTROLLABILITY CENSUS (a,b,e,f registers uncontrolled), which scales linearly with word width (23→28→46 for N=4,5,8); a genuine vortex/topological count would be width-independent. 132 is the 32-bit census in disguise, not a stable basis-independent corank. (b) The hard-core is REGISTER-selective (which of a..h, uniform over all bit positions), while carry vortices are ROUND/BIT-distributed across the lattice — orthogonal index sets, so hard-core positions are independent of vortex footprints (the carry-density baseline is uniform across bits; the hard-core does not track it). (c) The vortex "free energy" (σ) shows no 59→61 change — it decays smoothly to zero (consistent with W4-LG1, finding #4). Both kill conditions fire.

**Cross-check / skeptic note:** The hard-core structure (a,b,e,f uncontrolled; d,h controlled; c,g partial) reproduces the repo's `hard_core_132_bits.md` register-by-register at small N, confirming the census is the real object. The skeptic's tautology warning is exactly what happens: without a genuine connection, "linking = loop crosses chain" is vacuous, and the piercing count is just carry density — it never converges to 132. Bit 0 has zero carry-diff frequency because the LSB has no carry-in (the adder's free bit, per Lipmaa–Moriai), not a vortex. A defender would need a width-independent topological count that lands on ~132 *and* correlates with the a,b,e,f register structure above baseline; neither exists.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-LG4.py`

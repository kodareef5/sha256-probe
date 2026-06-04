# W4-LG1 — Wilson-loop confinement → the wall as a deconfinement→confinement transition   ·   VERDICT: KILLED

**Card claim:** Horizontal Z₂ links = carry-difference across bit boundaries; plaquette = frustration; ⟨W(C)⟩ obeys perimeter-law (deconfined, findable) below the wall and area-law (confined) at round 61, with string tension σ → 2^-2N. The SHA-256 "wall" is a deconfinement→confinement phase transition.

**Probe run:** Faithful width-N model (N=8), carry-difference field dumped by `/tmp/wilson_field.c` (width-N round primitives + cascade-offset + MSB-kernel setup copied VERBATIM from the repo enumerator `backward_construct_n10.c`; READ-ONLY). Lattice = (rounds 57..63) × (8 bits). Horizontal link U_h[r][i] = real bit-serial carry-IN difference (path1 ⊕ path2) of the round-r e-update modular add. Plaquette = curl; Wilson loop W(t×w) = (-1)^(enclosed plaquette parity), averaged over the full 260-collision ensemble and all bit-anchors. Throttled (`taskpolicy -b`, OMP=2).

**Result (numbers):**
- Link/energy density ρ(r) over rounds 57..63: **0.442, 0.451, 0.231, 0.000, 0.000, 0.000, 0.000**.
- ⟨W⟩ by anchor round (1×1…3×3 loops): r57–r59 decay (e.g. ⟨W(3×3)@r57⟩=0.10, @r59=0.34); **r60 and r61: ⟨W⟩ = 1.000 for every loop size** (trivial).
- Per-round string tension σ(r) = -⟨log|W|⟩/Area: **0.434, 0.485, 0.182, 0.000, 0.000** for r57..r61. σ at r61 = 0, NOT 2^-2N = 1.5e-5.
- Sharpness: σ sequence is a smooth monotone decay; max/mean jump ratio = 2.26 (no isolated sharp step at 60/61).
- Gauge-law test: under a genuine Z₂ gauge transform on the horizontal links (U_h[r][i] → g(r,i) ⊕ U_h[r][i] ⊕ g(r,i+1)), ⟨W(2×2)@r58⟩ changed **0.335 → 0.037 — NOT invariant.**

**Kill_criterion:** "same law both sides, or ⟨W⟩≈1 everywhere" — **fired? YES.**

**Verdict reasoning:** Three independent strikes. (1) ⟨W⟩ ≡ 1 (trivial) at rounds 60–63 — the post-wall region is exactly the "⟨W⟩≈1 everywhere" kill. (2) There is NO deconfinement→confinement transition: the carry-diff field is *active* at r57–59 and *vanishes* at the wall, i.e. active→trivial (forced by the collision constraint zeroing the tail), not trivial→confined; σ→0 at 61, not →2^-2N. The "transition" is the cascade bookkeeping (finding #4: no real round-60 knee), and it points the *wrong way*. (3) The horizontal-link "connection" fails the gauge transformation law, so the Wilson loops are not physical observables; the temporal/vertical link is the imposed parity the skeptic flagged, and here it is vacuous (U_v=0), so loops never close gauge-invariantly. The angle is dead as stated.

**Cross-check / skeptic note:** σ(r) here is the same quantity LG4 needs for its "vortex free energy 59→61"; both see smooth decay with no 61 onset, mutually consistent. A defender could argue a *different* link/temporal-gauge definition might confine — but any such field must (a) transform as a connection and (b) produce a real area-law onset at 61; the natural carry-difference field does neither. The collision constraint forcing the tail to zero (so density→0 by r63) is structural, not a phase transition.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-LG1.py`

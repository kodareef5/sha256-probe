# W4-FP2 — S-transform zero-atom → 132 from SHR rank-loss   ·   VERDICT: KILLED

**Card claim:** SHR drops bits → rank-deficient Jacobians → an atom at 0; under ⊠ zero-atoms compound to saturation = the cokernel → conjecturally 132/256.

**Probe run:** N=4,6,8 (compression-round Jacobian) and N=8,16,32 (message schedule — the literal 32-bit width, since that's where SHR actually lives), throttled. Real coranks (over ℝ, where S-transforms/free-prob live): (a) exact local GF(2) compression-round difference-Jacobian; (b) the message-schedule small-sigma maps σ0=ROR7⊕ROR18⊕SHR3, σ1=ROR17⊕ROR19⊕SHR10; (b') the full 16-word schedule companion map (16N×16N); (c) the SHR-removal counterfactual (replace SHR^c by ROR^c).

**Result (numbers):**
- (a) compression-round corank = **0** at every base point, N=4,6,8 (8N=32/48/64). SHR is not even in the compression round.
- (b) σ0 corank = **0**, σ1 corank = **0** at N=8,16,32. Min singular values 0.16–0.65 (>> ε), i.e. genuinely full-rank.
- (b') companion corank = **0** at N=8,16,32 (16N up to 512); min sv ≈ 0.23.
- (c) SHR-removal: σ0 corank 0→0, companion 0→0 at all N. Removing SHR changes nothing.
- 132/0.516 check at N=32: corank/N = **0.000** (need 0.516); corank = **0** (need 132).

**Kill_criterion:** "direct corank ≈0 or ≈1, or SHR-removal barely changes it" — **fired? YES (both: direct corank=0 AND SHR-removal 0→0).**

**Verdict reasoning:** Every relevant real Jacobian is full-rank (corank 0), so there is no atom at 0, nothing for ⊠ to compound, and no saturation toward 132. The card's own skeptic note is exactly right and is what the data show: over ℝ the bits SHR drops are *refilled* by the two ROR terms it is XORed with (the small-sigma maps have min sv 0.16–0.65 at N=32, far from zero). The SHR-removal test — the card's discriminator — moves the corank from 0 to 0.

**Cross-check / skeptic note:** This re-commits the 132-category error flagged in prior finding #1 (confirmed 7 ways): 132 is the GF(2)/output-census count of forced output-difference bits (registers a,b,e,f fully at round 63 = 128, plus 4 scattered dc[63] bits), NOT a real corank of any round Jacobian. A real, basis-independent corank here is 0/128, exactly as the prior pattern predicted. The only way SHR's bit-drop becomes a genuine rank statement is over GF(2) where there is no refill — but that is a finite-field fact classical free probability / the S-transform cannot see, so the ⊠ zero-atom mechanism is the wrong lens.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-FP2.py`

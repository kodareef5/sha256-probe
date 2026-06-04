# W4-LG3 — Lattice Gauss law → de58 is the unique charged column   ·   VERDICT: SURVIVES

**Card claim:** da=0 clean propagation = ∇·E=0; a forced differential = a source. de57/de59/de60 constant = source-free; de58 grows = the lone charged column. Probe: per-round divergence D(r) ≈ 0 for r∈{57,59,60}, ≠0 growing for 58; must show locality (pinned to a column, not smeared).

**Probe run:** ADDITIVE (modular) per-round e-difference image cardinality |de_r| for r=57..60, over the full cascade-feeding free-word sweep, at N=4 and N=8. Faithful width-N model: primitives + cascade-offset + MSB-kernel copied VERBATIM from the repo enumerator `backward_construct_n10.c` (`/tmp/de58_add.c`, `/tmp/de58_xor.c`). The Gauss-law "divergence" D(r) := (|de_r| > 1) — is the column charged? Plus the XOR-db56 Hamming weight for the 2^hw law. Throttled.

**Result (numbers):**
- N=4: **(|de57|,|de58|,|de59|,|de60|) = (1, 2, 1, 1)** — matches ground-truth DE_SIZES[4]=(1,2,1,1).
- N=8: **(|de57|,|de58|,|de59|,|de60|) = (1, 8, 1, 1)** — matches ground-truth DE_SIZES[8]=(1,8,1,1).
- So de57, de59, de60 are source-free (cardinality 1); **de58 is the unique charged column** (cardinality > 1). Locality holds exactly.
- |de58| = 2^hw(db56_XOR): N=4 → db56_XOR=0x2, hw=1, 2^1 = 2 = |de58| ✓; N=8 → db56_XOR=0x92, hw=3, 2^3 = 8 = |de58| ✓.

**Kill_criterion:** "sourced at columns ≠de58, or zero everywhere, or linking vacuous" — **fired? NO.** The source is pinned to exactly de58, is nonzero (cardinality 2 / 8), and is not smeared across columns.

**Verdict reasoning:** SURVIVES — the locality claim is real and reproduced (the (1, V, 1, 1) column structure is exact at N=4 and N=8), so the kill_criterion does not fire. BUT, per **prior finding #5** (de58 thread CLOSED), this is RESTATE-not-derive, so it is NOT promoted to CONFIRMED: the Gauss-law / ∇·E lens is a faithful *relabelling* of the known cascade table, and the "charge" V = 2^hw(db56_XOR) is the known Maj/AND image count (db56 is the active difference feeding the round-57 Maj; the e-path inherits exactly hw(db56) binary DOF). The gauge framing names the observation; it does not derive the count from any charge-conservation principle. CONFIRMED was reserved for an actual derivation of 2^hw(db56), which is absent.

**Cross-check / skeptic note:** The additive-diff convention was essential — an XOR-diff image overcounts (|de57| came out 25, |de58| 40, spuriously "charged" everywhere); with modular subtraction the (1,V,1,1) structure is clean and matches the repo's `state_invariants.md` (de57 additive constant; de58 varies; de60≡0). The skeptic's "modular-only conservation → group is Z/2^k not Z₂" is correct and reinforces RESTATE: the conserved object lives in Z/2^N (additive), not a Z₂ gauge charge, so the "Gauss law" is an analogy, not the mechanism. N=6 had no cascade-eligible M0 under the MSB/fill=MASK setup (sparse), so N=4,8 carry the verdict; both are unambiguous.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-LG3.py`

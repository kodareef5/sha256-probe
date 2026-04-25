
## 00:48 EDT — Theorem 4 boundary pinpointed: r=61 modular = 100%, r=62 = 0%

Per-round da-de equality check across 5000 samples on priority candidate:
  r=61: da_mod==de_mod 100% (Theorem 4 confirmed empirically), da_xor==de_xor only 0.04%
  r=62: BOTH forms 0% — round 62 breaks the equality
  r=63: 0% (divergence continues)
Sharpens earlier 'Theorem 4 fails at r=63' to: holds modularly at r=61, breaks completely at r=62.
**Possible bug flagged**: cascade_aux force-mode SPEC enforces XOR-form dA[61]=dE[61], but Theorem 4 is modular. XOR-form is a stricter (and incorrect-by-form) constraint that admits only 0.04% of valid samples. SPEC may need correction.
Writeup: `bets/mitm_residue/results/20260425_theorem4_pinpoint.md`

## 01:17 EDT — Retraction: previous SPEC-bug claim was wrong

Verified the cert (sr=60 collision) has da=de=0 starting at r=60 — XOR-equality and modular-equality BOTH hold trivially from r=60 onward.
Mode B's XOR-equality encoding admits the cert. The 0.04% rate I observed was on RANDOM cascade-held residuals, not on collision-solution paths.
Retracting the SPEC-bug flag from `20260425_theorem4_pinpoint.md`.
The boundary-pinpoint (r=61 modular = 100%, r=62 = 0%) STANDS — that's an independent finding.
Mode B's ≥10x SPEC claim remains separately refuted at 90-min budget for unrelated reasons.
Writeup: `bets/mitm_residue/results/20260425_spec_bug_retraction.md`

## 02:00 EDT — Theorem 4 structural proof: r=62 breakage formula identified

Derived and empirically confirmed: `da_62 − de_62 ≡ dT2_62 (mod 2^32)` exactly.
1000/1000 samples match: dT2_62 generically nonzero (da_61 nonzero generically) → da_62 ≠ de_62.
Theorem 4's natural domain is r=61 SPECIFICALLY. Earlier 'r ≥ 61' language in writeups/sr60_sr61_boundary_proof.md is technically true (vacuously at higher rounds when collision forces zeros) but potentially misleading.
At the cert: da_61=0 makes everything vacuous. At random cascade-held: Theorem 4 is the maximum 'da-de relationship' available — doesn't extend.
Writeup: `bets/mitm_residue/results/20260425_theorem4_structural_proof.md`

## 02:17 EDT — Theorem 4 unified extension: da_r − de_r ≡ dT2_r mod 2^32 for r ∈ {61,62,63}

Single unified formula derived + empirically verified 1000/1000 each at r=62 and r=63.
At r=61: dT2_61 = 0 (recovers Theorem 4 original); at r=62, 63: dT2_r generically nonzero but structurally bounded.
Key insight: shift-register propagates cascade-zero in d through all of r=61,62,63; c picks up nonzero only at r=63 via b_62=a_61.
Implication: 3 modular constraints (da-de=dT2 at r=61,62,63) usable for cascade-aware SAT propagation or block2_wang trail bounding.
Recommends precision update to writeups/sr60_sr61_boundary_proof.md Theorem 4.
Writeup: `bets/mitm_residue/results/20260425_theorem4_unified.md`

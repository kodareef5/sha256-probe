
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

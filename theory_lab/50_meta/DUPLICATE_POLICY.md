# Duplicate policy — deciding `novelty` honestly

Before a row leaves `captured`, run this three-step check against `../00_repo_digest/`. The `novelty`
tag is the output. Getting this right is the lab's reason to exist: the prior one-shot scan
(`april28_explore`) overclaimed novelty because it never built repo/literature context first.

## The check

1. **Is it already a repo framing?** Search `../00_repo_digest/established_framings.md` for the lens
   and locus. If the repo already does essentially this → `repo-established`. (Log it anyway, as a
   baseline NULL row, so future ideas can diff against it.)
2. **Did the repo already kill it?** Search `../00_repo_digest/graveyard_digest.md` and
   `../sha256_review/headline_hunt/registry/negatives.yaml`, AND the april28 probed verdicts in
   `../00_repo_digest/prior_scan_digest.md`. If a probe killed it → `repo-killed`; copy the **reopen
   trigger** into the kill_criterion and do not re-propose without meeting it.
   - ⚠️ **Sub-reading trap.** A field can be *part* killed and *part* open. Example: 2-adic **Hensel-lift**
     is `repo-killed` (april28 probe_03c), but the 2-adic **span/Newton-slope** reading was never probed
     and is `genuinely-new`. Always ask *which specific reading* was killed.
3. **Did an external model flag it?** Search `../10_community_scan/` and the repo consultations. If a
   GPT/Gemini review named it but the repo never pursued → `flagged-unpursued`. If it's a known
   adjacent-field tool not pointed at SHA-256 here → `adjacent-untested`. If none of the above →
   `genuinely-new`.

## Tie-breakers
- "I'd implement it differently" is **not** novelty. The *construction* must differ (e.g. lattice
  unknowns = carries, not messages — that is why `carry-lifted-lattice` is `genuinely-new` despite
  april28 item_07 touching lattices).
- When in doubt, tag the **less** novel tier. Over-claiming novelty is the failure mode this lab exists
  to prevent.
- Re-run step 1–2 whenever `SNAPSHOT.md` is refreshed: a `genuinely-new` row becomes `repo-established`
  the day the repo ships a matching bet.

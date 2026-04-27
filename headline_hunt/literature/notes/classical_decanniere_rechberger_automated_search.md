# de Cannière / Rechberger 2006 — Automated Characteristic Search for SHA-1/SHA-2

**Cite as**: de Cannière, C., Rechberger, C. *"Finding SHA-1
Characteristics: General Results and Applications."* ASIACRYPT 2006.

**Read status**: structural-summary from public knowledge + Viragh 2026
literature-table reference. Foundational for AUTOMATED differential
trail search (vs Wang 2005's hand-constructed characteristics).

## Position in the literature

Wang 2005 and Wang/Yin/Yu 2005 manually constructed differential
characteristics. de Cannière/Rechberger 2006 introduced **automated
search** for valid differential characteristics — converting an
ad-hoc art into an algorithmic, reproducible methodology.

Specifically:
- Define a 5-letter signed-bit alphabet for representing partial state
  conditions ('-', 'x', 'n', 'u', '?') beyond just '+/−/0/1'
- Treat finding a characteristic as a **constraint propagation problem**
- Use guess-and-verify with backtracking
- Apply to SHA-1 first, then extended to SHA-2 family

This automated approach is the direct predecessor of:
- Mendel/Nad/Schläffer 2013 (signed-DC + SAT search for SHA-256)
- Li et al. 2024 (MILP-based characteristic search)
- Alamgir et al. 2024 (CaDiCaL-p with programmatic propagation)

## Why this matters for block2_wang and yale's guarded probe

### For block2_wang

The bet's eventual implementation needs a SHA-256 differential
characteristic search engine. Wang 2005's hand-constructed approach
won't scale to the project's 9 exact-symmetry cands (F27) — each
needs its own characteristic.

de Cannière/Rechberger's automated framework IS that engine. The
project would either:
1. Reimplement automated DC search for SHA-256 (significant
   engineering)
2. Adapt an existing tool (Mendel's SAT-based, Li's MILP-based,
   or a fresh implementation)
3. Use the structural F-series findings (F25/F26/F27 residual
   structures) as STARTING POINTS for narrower automated search

### For yale's guarded message-space probe

Yale's commit f2edeed builds a "guarded message repair" operator with
adaptive perturbation. This is structurally analogous to dCR 2006's
constraint propagation backtracking — yale's "guarded a57=0" is a
constraint, "defect57 reduction" is an objective.

If yale's probe were translated into dCR 2006 vocabulary:
- yale's "guarded prefix" = signed bitcondition vector
- yale's "operators" = dCR's local modifications
- yale's "fiber" = dCR's constraint propagation domain
- yale's "manifold thinness" = dCR's "characteristics with low
  probability"

The 2006 framework's key contribution is REPLACING THE OBJECTIVE:
instead of "find a characteristic that succeeds" (Wang's framing),
they search "find a characteristic with maximum probability."

## Methodology summary

### Bit alphabet (extended from Wang)

| Symbol | Meaning |
|---|---|
| 0 | both messages have bit 0 |
| 1 | both messages have bit 1 |
| u | M₁=0, M₂=1 (upward signed difference) |
| n | M₁=1, M₂=0 (downward signed difference) |
| x | difference, sign undetermined |
| - | no difference, value undetermined |
| ? | unknown |

Signed alphabet captures more than XOR-domain: distinguishes
"both 0" from "both 1" from "+/−" sign.

### Search procedure (sketch)

1. Initialize: characteristic = all '?' at every state bit
2. Propagate forward: round operations (+,XOR,Maj,Ch) constrain bits
3. Propagate backward: known final state bits constrain earlier
4. If contradiction → backtrack
5. If complete → emit valid characteristic
6. Else: guess one '?' bit, recurse

### Why this is "automated"

Wang 2005 hand-constructed characteristics over weeks of analysis.
dCR 2006 generates characteristics in HOURS. Each generated
characteristic comes with:
- Probability estimate (XOR transition tables)
- Bitcondition list (what to satisfy via message modification)
- Round-by-round structure

For SHA-256 specifically, dCR's results were extended (Mendel et al.
2009-2013) to find characteristics for round-reduced SHA-256.

## Connection to this project's F-series

The F-series found structural properties of cascade-1 chamber
images and round-63 residuals. To translate these to dCR 2006's
framework:

1. **F12 cascade-1 chamber**: per-chamber de58 has size 1. In dCR
   notation: at slot 58 input, the SIGNED bitcondition is
   determined by W57. F12's de58_size=1 = the cand has a UNIQUE
   signed characteristic at slot 58 per W57.

2. **F25 round-63 residual structure**: each min-HW residual is a
   SPECIFIC bit pattern. dCR's "characteristic up to round 63"
   would have THIS pattern as endstate. Probability ~ 2^-(HW * average
   probability per bit).

3. **F26/F27 a_61 = e_61 symmetry**: 9 cands have this
   structural feature. In dCR's language, these cands have a SHARED
   bitcondition between a_61 and e_61 — a 32-bit constraint that's
   automatically satisfied for these 9 cands.

If a future implementation translates the F-series into dCR's
characteristic-search framework, the project would have:
- Auto-generated characteristics for each registry cand
- Per-cand probability bounds
- Wang-modifiable bitcondition lists

That's a CONCRETE path from "structural data" (F-series) to
"absorbable trail" (block2_wang's target).

## Action items for paper integration

1. **Section 2 (Background)**: cite dCR 2006 alongside Wang 2005 as
   the automated-search precursor. Note that this work makes
   characteristic search REPRODUCIBLE.

2. **Section 5.5 (yale guarded probe)**: explicitly map yale's
   "guarded message-space probe" to dCR's "constraint propagation
   over signed bitconditions." This positions yale's work in the
   dCR lineage.

3. **Section 6 (Discussion)**: propose dCR-framework reformulation
   of the F-series structural findings as future work.

## Action items for the project (concrete)

1. **For block2_wang**: implement (or adapt) a SHA-256 automated
   differential-characteristic engine. Inputs: F25 residual + cand
   parameters. Outputs: bitcondition list + probability bound.

2. **For yale's structural track**: translate "guarded fiber" findings
   into dCR's "characteristic with bitconditions" formalism.

3. **Cross-reference**: the 9 exact-symmetry cands (F27) should be
   re-analyzed under dCR 2006's bit alphabet — check if the symmetry
   corresponds to a SIGNED structural feature, not just XOR.

## Status

- Read status: STRUCTURAL_SUMMARY based on public knowledge of dCR
  2006 + Mendel-line extensions. Full PDF read PENDING.
- This note unblocks the "deCannière/Rechberger" item from
  literature.yaml should_read list.

EVIDENCE-level: HYPOTHESIS — based on indirect references and standard
cryptanalysis knowledge. Direct PDF study would harden specific
claims about the 5-letter bit alphabet and propagation algorithms.

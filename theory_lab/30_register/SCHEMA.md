# Register schema & classification taxonomy

`ideas.yaml` is the **single source of truth**. `INDEX.md` and `30_register/views/*.md` are
generated from it by `infra/rebuild_views.py`; never hand-edit them. `infra/validate_ideas.py`
rejects any entry missing a required axis or a `kill_criterion`.

## The 9 classification axes

| Axis | Card. | Meaning | Allowed values |
|---|---|---|---|
| `lens` | single | primary math machinery | `algebraic-geometry` · `commutative-algebra` · `boolean-function` · `automata-transducer` · `coding-theory` · `lattice` · `number-theory-padic` · `prob-combinatorics` · `graph-spectral` · `tensor-network` · `knowledge-compilation` · `proof-complexity` · `communication-complexity` · `statistical-physics` · `differential-crypto` · `information-theory` · `dynamical-systems` · `other` |
| `locus` | multi | where in SHA-256 it acts | `message-schedule` · `round-function` · `carries` · `differential-trail` · `state-cross-section` · `feed-forward` · `whole-function` |
| `mechanism` | single | the win it targets | `solve` · `reduce` · `lower-bound` · `reframe` · `bridge-scales` · `structural-invariant` · `count` |
| `reframes` | object | repo framing(s) it competes with + the delta | `{competes_with: [framing-id...], delta: "<one clause>"}` (empty list = orthogonal) |
| `novelty` | single | triage vs repo + external flags | `repo-established` · `repo-killed` · `flagged-unpursued` · `adjacent-untested` · `genuinely-new` |
| `plausibility` | int 1–5 | chance of a real foothold | `1` numerology … `5` near-certain to *say something* (even a clean negative) |
| `probe_cost` | single | cost to **falsify**, not to exploit | `trivial` (<1h think) · `cheap` (small-N Python, hours) · `moderate` (lib spike, days) · `heavy` (solver fleet — out of charter; hand to repo) |
| `kill_criterion` | string | REQUIRED falsifier | "This angle is dead if ___." No entry leaves `captured` without it. |
| `status` | single | lifecycle state | `captured` · `triaged` · `deep-dive` · `probe-designed` · `probed` · `promoted` · `archived` |

Repo-framing ids used in `reframes.competes_with` are defined in
`../00_repo_digest/established_framings.md`: `cascade_dp`, `carry_automaton`, `transducer_window`,
`bdd_poly`, `anf_degree`, `modular_carry`, `sr60_61_phase`, `hard_core_132`, `rotation_kernels`,
`three_filter_da_de`, `kernel_fill_phase_diagram`, `n_invariant_scaling`.

## Metadata fields (not axes)

`source` (`community-paper` | `adjacent-analogy` | `external-model:<name>` | `generated` | `human`) ·
`depends_on` (idea ids or repo bet/tool names) · `repo_refs` (relative paths into `../sha256_review/`) ·
`external_refs` (bib keys / URLs) · `created` · `updated` · `notes` · `dive` (path or null).

## Entry schema (YAML)

```yaml
- id: <kebab-slug, stable, never reused>
  title: <one human sentence>
  one_liner: <=20 words; this is what INDEX.md shows
  lens: <enum>
  locus: [<enum>...]
  mechanism: <enum>
  reframes: {competes_with: [<framing-id>...], delta: <one clause>}
  novelty: <enum>
  plausibility: <1-5>
  probe_cost: <enum>
  kill_criterion: <"Dead if ...">
  status: <enum>
  source: <enum>
  depends_on: [<id>...]
  repo_refs: [<path>...]
  external_refs: [<key/url>...]
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  notes: <free, append-only>
  dive: <path | null>
```

---

## Worked example 1 — `repo-established` (the novelty baseline)

```yaml
- id: carry-automaton-entropy-bijection
  title: Carry-difference finite automaton with entropy = log2(#collisions)
  one_liner: Carry diffs form a deterministic automaton; carry-entropy counts collisions exactly.
  lens: automata-transducer
  locus: [carries, state-cross-section]
  mechanism: count
  reframes: {competes_with: [carry_automaton, cascade_dp, bdd_poly], delta: "none — this IS the repo's framing; logged as the baseline to diff fresh ideas against"}
  novelty: repo-established
  plausibility: 5
  probe_cost: trivial
  kill_criterion: "Established (carry entropy = log2(#collisions) exact at N=4,6,8; branching <=2). Dead as a NEW angle — revive only a VARIANT if a non-raw-carry quotient beats brute force >10x at N=8 (the repo's own reopen trigger)."
  status: archived
  source: human
  repo_refs: [../sha256_review/CLAIMS.md, ../sha256_review/headline_hunt/registry/negatives.yaml]
  external_refs: [lipmaaMoriai2001]
  notes: "Baseline/NULL entry. Repo already proved raw-carry DP gives ZERO speedup and forward-completion-quotient width ~ collision count (Myhill-Nerode). Any new carry-lens idea must state how it escapes those two negatives."
  dive: null
```

## Worked example 2 — `flagged-unpursued` (external model flagged; repo never ran it)

```yaml
- id: expansion-code-min-distance
  title: Minimum-distance bound on the SHA-256 message-expansion code (Jutla-Patthak technique)
  one_liner: Linearize the schedule to a GF(2) code; a min-distance bound caps how sparse a compliant difference can be.
  lens: coding-theory
  locus: [message-schedule, differential-trail]
  mechanism: lower-bound
  reframes: {competes_with: [sr60_61_phase, anf_degree], delta: "turns 'each enforced round costs 2^-2N' into a static, message-independent sparsity budget"}
  novelty: flagged-unpursued
  plausibility: 3
  probe_cost: cheap
  kill_criterion: "Dead if a low-weight-codeword search (Stern/Canteaut-Chabaud) on the linearized SHA-256 expansion matrix shows the min weight confined to the last K rounds is NEITHER high enough to forbid sparse late trails NOR low enough to seed a surprise trail — i.e. it just reproduces the known degree bound."
  status: probe-designed
  source: community-paper
  repo_refs: [../sha256_review/writeups/anf_deep_dive.md, ../sha256_review/16_gf2_kernel_search.py]
  external_refs: [jutla2005code]
  notes: "Reed-Muller/syndrome views are on the repo's flagged list, but nobody ran an actual min-distance bound on SHA-256's expansion. Necessary-not-sufficient: low XOR-weight need not survive carries. Realistic prize = a structural 'why the wall' bound or a sparse-trail seed, not a finished collision."
  dive: 40_deep_dives/dive_expansion-code-min-distance.md
```

## Worked example 3 — `genuinely-new` (the headline fresh angle)

```yaml
- id: 2adic-carry-valuation-newton
  title: 2-adic valuation flow of carry propagation (FCSR-span + Newton-polygon obstruction)
  one_liner: Put a 2-adic metric on carries; a monotone v2/Newton-slope trend would be a global no-collision obstruction.
  lens: number-theory-padic
  locus: [carries, message-schedule, whole-function]
  mechanism: lower-bound
  reframes: {competes_with: [carry_automaton, sr60_61_phase, hard_core_132], delta: "carries treated 2-adically (a METRIC) rather than combinatorially (GF(2) automaton)"}
  novelty: genuinely-new
  plausibility: 3
  probe_cost: cheap
  kill_criterion: "Dead if (a) FCSR/2-adic-span synthesis on the deltaW difference-sequence of a known sr=60 pair returns ~maximal span AND (b) v2(deltaH) shows no monotone trend vs enforced rounds AND (c) the per-round Newton polygon over Z_2 has no monotone slope. (april28 probe_03c already killed the DISTINCT Hensel-LIFT reading; this survives only in the un-probed span/slope readings.)"
  status: probe-designed
  source: adjacent-analogy
  depends_on: []
  repo_refs: [../sha256_review/april28_explore/items/item_03_padic.md, ../sha256_review/THE_THERMODYNAMIC_FLOOR.md, ../sha256_review/lib/sha256.py]
  external_refs: [anashin2006nonarch, klapperGoresky1997fcsr, klapperGoresky1995rational]
  notes: "Sharpened to be NON-redundant with april28: item_03 killed Hensel-LIFT (lifts uniform-random); the Newton-slope / 2-adic-span reading was reasoned but never probed. Must contend with THE_THERMODYNAMIC_FLOOR (XOR-only sr=60 also times out at N=32 => barrier isn't carry-LENGTH; the 2-adic claim is about the schedule recurrence + additive invariant, a different quantity)."
  dive: 40_deep_dives/dive_2adic-carry-valuation-newton.md
```

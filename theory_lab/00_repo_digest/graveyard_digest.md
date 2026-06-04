# Graveyard Digest — killed angles + reopen triggers

These angles are **already dead** in the working repo. Each has a **reopen
trigger** — the specific thing that would have to be true to revisit it. **The lab
must not re-propose any of these without meeting its trigger.** A row here that
gets re-proposed naively is the exact failure mode this digest exists to prevent.

Sources: `../sha256_review/headline_hunt/graveyard/closed_bets/`,
`../sha256_review/headline_hunt/registry/negatives.yaml`, plus the two PROBED
negatives from `../sha256_review/april28_explore/`.

## Quick table

| killed angle | why dead (one line) | reopen trigger |
|---|---|---|
| `chunk_mode_dp_with_modes` | forward-DP min layer width = collision count (Myhill-Nerode minimal); exponential | a variable **ORDER** (not just a mode tuple) whose minimal-automaton max layer width is provably poly in N |
| `programmatic_sat_propagator` | Theorem-4/Rule-4 fires only in preprocessing; finite ~977-fire ceiling | a **generative** (not constant-pruning) rule, OR an IPASIR-UP advance, OR a candidate vanilla-cadical can't solve but the propagator can |
| `linear_lever_gaps` | decoupled t-7/t-16 boundary levers no better than σ1; trigger-count says ≥4 free words ⇒ sr≤60 is the real ceiling | a new lever family (t-7+t-16 combined, or σ0 t-15) scoring above current best; or a da[56]=0-layered sr=61 variant with well-shaped freedom |
| `coincidence_variety` | confirmed sr=61 rate is 2^-2N, not 2^-N (completed audit) | a non-cascade-DP single-block construction whose sr-step is shown 2^-N (not 2^-2N) |
| `raw_carry_state_dp` (negatives) | carry-diff state 89–99% near-injective on full input space | a quotient state (not raw carries) giving >10× reduction at N=8 from scratch |
| `gf2_linearization` (negatives) | carry nonlinearity fundamental; 0/30 linear slices SAT | a GF(2)-equivalent quotient that absorbs the carry structure (probably a different group) |
| `d4_standard_n8` (negatives) | treewidth ~110 exceeds d4's ceiling; cache thrashes | cascade-aux (or other) drops treewidth below ~80 at N=8 |
| `bottom_up_sdd_blowup` (negatives) | Apply has exponential intermediates (10.5 GB SDD at N=4) despite poly final BDD | an SDD vtree (or top-down d-DNNF) that stays poly through Apply |
| `rotation_aligned_kernels_not_structural` (negatives) | ~20% yield boost, within solver noise | a specific (bit, fill, M[0]) with >2× solve-time gain on TRUE sr=61; or kernel-pair theory |
| `naive_multiblock` (negatives) | residual HW=7+ at N=8 too large for trivial absorption | a Wang-style tailored block-2 trail (→ became `block2_wang`) |
| `single_block_cascade1_sat_sr60` (negatives) | 67/67 cands UNSAT, 802+ W-witnesses, ~99.97% of HW distribution, 0 SAT | online Pareto sampler finds a SAT W-witness; or a new candidate (m0/fill outside the 67) admits SAT; or HW>120 region SAT |
| `seed_farming` (negatives) | more seeds on unchanged CNF = no info (reopened narrowly) | a predictor identifies un-farmed promising candidates *(partial reopen 2026-04-30: clause-injected short-budget cube use saw −9.10% conflicts)* |
| **april28 #03** cascade-1 is HARD NON-HENSEL | 0/1200 lift-compatible; lift residuals uniform-random; small-N ⊥ large-N | a lift map that recovers low-N bits with bit-error tolerance, OR a Newton-polygon SLOPE (not lift) reading — *see `prior_scan_digest.md`: the slope reading was never probed* |
| **april28 #35** cascade corpus is MPS-HOSTILE | bond dim scales linearly with corpus (BD/corpus ≈ 0.55 at N=8 & N=10); MPS ~80× slower than naive | bond dim shown sub-linear in corpus at some N, OR a tensor decomposition other than round-cut MPS that compresses cascade-1 |

## Detail on the repo-killed mechanisms (graveyard memos)

### `chunk_mode_dp_with_modes` — closed 2026-05-25
The design hope was a compact DP whose state is a *future-completion quotient*
(boundary modes + canonical residual) rather than raw carries. **Killed** because the
BDD completion quotient **IS** the Myhill-Nerode minimal forward-automaton layer width
for the round-ordered variable order, and it peaks at **255/260 collisions** at N=8
(near-injective). By minimality, **no** mode/quotient abstraction in this order can be
smaller than ~collision-count → every forward-DP design has exponential frontier. This
also explains the BDD paradox: O(N^4.8) is total nodes *summed over layers*; a DP must
materialize the per-layer width. *Reopen:* a variable ORDER with provably poly max
layer width. Source: `graveyard/closed_bets/chunk_mode_dp_with_modes.md`,
`negatives.yaml#forward_completion_quotient_min_width_near_collision_count`.

### `programmatic_sat_propagator` — closed 2026-04-25
A CaDiCaL/IPASIR-UP external propagator exposing carry modes, cascade offsets, and
schedule-derived W[60]. ~750 LOC shipped and ran end-to-end. **Killed** because the
cascade-aware rules (Rule 4 @ r61/r62) fire **heavily during preprocessing and go
SILENT during deep search** — CDCL navigates by diff-aux variables, not actual register
values; Rule 4 caps at a finite ~977 fires regardless of trigger (the algebra has a
finite implied-literal set). Refuted at three trigger strategies (sample-based,
continuous, decision-shaping). *Reopen:* a **generative** pruning rule (vs constant
pruning), an IPASIR-UP advance, or a specific candidate where vanilla cadical fails but
the propagator succeeds. Engineering substrate preserved. Source:
`graveyard/closed_bets/programmatic_sat_propagator/KILL_MEMO.md`.

### `linear_lever_gaps` — closed 2026-05-30 (kill #2)
Idea: the sr=61 wall is conditioned on the σ1 (t-2) enforcement lever; enforce boundary
schedule equations via the **linear t-7/t-16** feedback terms instead, giving each
boundary word its own independent knob (decoupling, since σ0/σ1 are full-rank
bijections at N=32). **Killed:** the linear-lever sr=60 instance showed no SAT and no
speed advantage over the σ1 baseline across 5 seeds × 2 solvers; trigger-counting shows
**≥4 free words ⇒ sr≤60 is the real ceiling**. Pivoted to the block2_wang connection.
*Reopen:* a new lever family (t-7+t-16 combined, or σ0 t-15) scoring above current best;
or a da[56]=0-layered / extra-free-word sr=61 variant with nonzero well-shaped freedom.
Source: `graveyard/closed_bets/linear_lever_gaps.md`.

### `coincidence_variety` — closed 2026-05-30 (completed audit)
Not a failed bet but a completed **correction**: it established that each held
expansion equation is TWO independent per-message conditions (value match `g1=0`,
difference compatibility `h=0`), so the Theorem-5 sr=61 rate is **2^-2N, not 2^-N**
(g1 ⊥ h, ratio 1.005 over 1e9 samples). Propagated into the boundary proof + CLAIMS.
*Reopen:* a non-cascade-DP single-block construction whose sr-step is shown 2^-N.
Source: `headline_hunt/bets/coincidence_variety/RESULT_sr61_is_2minus2N.md`.

## Detail on the negatives.yaml closed doors

- **`raw_carry_state_dp`** (VERIFIED) — carry-diff state width 89–99% of the full
  2^{4N} search space; bounded width applies only to the *solution set*. *Reopen:* a
  non-carry quotient giving >10× reduction at N=8 from scratch.
- **`gf2_linearization`** (VERIFIED) — 0/30 linear slices SAT; 90% of slices have
  power-of-2 collision counts yet the function is not affine. *Reopen:* a GF(2)-equiv
  quotient (different group) that absorbs carries.
- **`d4_standard_n8`** (VERIFIED) — d4 on standard N=8 CNF doesn't complete in 67 h
  (treewidth ~110). *Reopen:* treewidth dropped below ~80. (Derived encoding made it
  *worse* — 181 — separately killed.)
- **`bottom_up_sdd_blowup`** (VERIFIED) — 10.5 GB SDD at N=4; the polynomial-BDD
  paradox in compiler form. *Reopen:* a vtree/top-down construction staying poly
  through Apply.
- **`rotation_aligned_kernels_not_structural`** (EVIDENCE) — 20% yield, within noise.
  *Reopen:* a (bit,fill,M[0]) with >2× TRUE-sr=61 solve gain, or kernel-pair theory.
- **`naive_multiblock`** (VERIFIED) — min residual HW=7 at N=8 too large for untailored
  absorption. *Reopen:* a Wang-style tailored block-2 trail = `block2_wang` (live).
- **`single_block_cascade1_sat_sr60`** (VERIFIED) — the empirical capstone: 67/67
  registry cands, 802+ W-witnesses, [44,120] HW (~99.97% of the natural distribution),
  3 solvers, 225M-conflict deep budget → **0 SAT**. Single-block sr=60 cascade-1
  collisions are empirically impossible at this compute scale (the known m17149975
  cert is a measure-zero point, not in this set — "collisions are point-singular, not
  basin-singular"). *Reopen:* a SAT W-witness from the Pareto sampler, a new candidate
  outside the 67 that's SAT, or HW>120 SAT.
- **`seed_farming`** (EVIDENCE, narrowly reopened) — more seeds on unchanged sr=61 CNF
  yields no SAT/no info at deep budgets. **Partially reopened 2026-04-30:** F343
  mined-clause injection gave −9.10% σ=2.68% conflicts at 60 s budget (saturates by
  5 min) → cube-and-conquer pipelines gain, single deep-solves don't. *Reopen (full):*
  a predictor that identifies un-farmed promising candidates.

## The two april28 PROBED negatives (not in negatives.yaml)

### Cascade-1 is HARD NON-HENSEL (april28 items 03 / 03b / 03c)
Probed empirically: N=8 cascade-1 dm patterns do **not** lift to N=10 with low-bit
consistency — **0/1200** Hensel-compatible across 5 N-pairs (4→6 … 12→14), and the
lift residuals are **statistically indistinguishable from uniform random** (mean
XOR-distance 32.06 ≈ 32; per-register ≈ 4.0). So small-N solutions are statistically
*independent* of large-N solutions — you cannot bootstrap N=8 → N=32 even with
bit-error tolerance. Formally explains a prior bit-correlation retraction (F91). Only
the structural SHAPE (cascade trajectory, filter mechanism) is N-invariant; the
specific solutions are not. **Reopen trigger:** a lift/bootstrap that recovers low-N
bits with tolerance — OR (critically) the **Newton-polygon SLOPE** reading of item 03,
which was *reasoned but never probed* (only the Hensel-LIFT reading was probed and
killed). Source: `../sha256_review/april28_explore/items/item_03_padic.md`.

### Cascade corpus is MPS-HOSTILE (april28 item 35)
Probed: the bond dimension of the cascade-1 survivor corpus (round-cut MPS) **scales
linearly with corpus size** — BD/corpus ≈ 0.554 at N=8 (260 records, BD 144), ≈ 0.537
at N=10 (1048 records, BD 563). MPS contraction is O(N·BD²) which grows *quadratically*
with corpus while naive enumeration grows *linearly*, so **MPS is ~80× slower than
naive and gets worse at larger N**. Even 90%-energy SVD truncation needs BD≈100.
**Reopen trigger:** bond dimension shown *sub-linear* in corpus at some N, or a
non-round-cut tensor decomposition that compresses cascade-1. Source:
`../sha256_review/april28_explore/99_FINAL_REPORT.md` (item 35 updates).

---

### Combined picture these negatives paint
Cascade-1 resists *every* standard compression/decomposition/lifting tool tried:
**not analytic** (non-Hensel), **not low-rank tensor** (MPS-hostile), **not
low-treewidth** (d4-hostile), **not GF(2)-linear** (carry nonlinearity), **not
BDD-friendly to build** (bottom-up Apply blowup), **not forward-DP-compact**
(Myhill-Nerode near-injective). Any new compression/decomposition idea must say which
of these walls it crosses and *how*.

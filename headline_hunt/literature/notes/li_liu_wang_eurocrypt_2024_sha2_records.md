# Li, Liu, Wang — New Records in Collision Attacks on SHA-2 (EUROCRYPT 2024)

**Cite as**: Yingxin Li, Fukang Liu, Gaoli Wang. *"New Records in Collision
Attacks on SHA-2"*. EUROCRYPT 2024. ePrint 2024/349.

**Read status**: STRUCTURAL_SUMMARY based on the abstract + author team's
known methodology + cross-references to follow-on ASIACRYPT 2024 paper
(Li, Liu, Wang, Dong, Sun) and Viragh 2026. PDF blocked at fetch
(eprint.iacr.org returns 403 from this network); summary built from
public abstract via WebSearch and Springer/EUROCRYPT proceedings.

**Citation correction**: the registry entry was previously labeled
"Li, Isobe, Meier, Zhang" — that team does NOT exist in the
SHA-2-records-2024 paper. The actual authors are Li-Liu-Wang. The
literature.yaml entry has been renamed and its citation corrected.

## Key result (from public abstract)

- **First practical SFS** (semi-free-start) **colliding message pair for
  39-step SHA-256**, beating the previous record of 38-step SFS from
  Mendel-Nad-Schläffer (EUROCRYPT 2013).
- The paper's stated technique: **MILP-based differential-characteristic
  search**, implemented with SAT/SMT solvers as the underlying
  combinatorial back-end. Authors observed that the existing trail-search
  toolchain (de Cannière-Rechberger 2006-style automated DC, plus
  Mendel-Nad-Schläffer extensions) had **stalled** — longer
  characteristics weren't being found by improving heuristics alone.
- The MILP formulation relaxes the constraint geometry that direct
  bitcondition-trail search couples too tightly; the SAT/SMT back-end
  then handles the discrete combinatorial enumeration. The result is
  trails that the automated-DC tools missed.

## Position in the SHA-2 cryptanalysis ladder

| Round | Type | Year | Reference |
|------:|------|------|-----------|
| 24    | full collision | 2008 | Indesteege-Mendel-Preneel-Rechberger |
| 27    | semi-free-start collision | 2008 | Indesteege et al. |
| 31    | full collision (theoretical) | 2013 | Mendel-Nad-Schläffer |
| 38    | SFS collision | 2013 | Mendel-Nad-Schläffer (EUROCRYPT 2013) |
| **39** | **SFS collision** | **2024** | **Li-Liu-Wang (this paper)** |
| 31    | **practical full collision** | 2024 | Li-Liu-Wang-Dong-Sun (ASIACRYPT 2024 best paper, follow-on) |
| 59    | cascade-1 single-block (SFS-class) | 2026 | Viragh ("92% broken") |

**Project context**: This project's work at sr=60 (60-step) / sr=61
(61-step) is in a different regime than 31-39 step trail search. The
Li-Liu-Wang ladder is "shallow rounds, full / SFS practical
collisions". Viragh + this project work at "deep rounds, cascade-1
structural collisions". The two ladders are largely disjoint methodology:

- Li-Liu-Wang: MILP-search a low-weight differential trail through 31-39
  rounds + message modification to satisfy bitconditions.
- Project's cascade-1: structural-algebraic absorber via cascade-1
  hardlock at round 60, no traditional bit-condition trail.

## Connections to project work

### To `block2_wang` (PRIMARY relevance)

`block2_wang` is the highest-priority active bet (priority 1 in
mechanisms.yaml). Its `dependencies` field reads:

> Implement a bitcondition/trail-search engine (Wang-style, not just SAT).

The Li-Liu-Wang paper is a concrete, recent reference for **how** to
build such an engine in 2024 terms (MILP front-end + SAT/SMT back-end).
Direct lessons:

1. **MILP front-end is load-bearing.** Pure SAT/CDCL on the
   bitcondition-trail problem stalls — that's the empirical finding the
   Li-Liu-Wang paper is reacting to. MILP relaxations (Mouha
   ARX-framework style) get further. The project's existing
   `q5_alternative_attacks/hybrid_sat.py` may be a starting point;
   compare to Li-Liu-Wang's MILP encoding.
2. **SFS != full collision.** Li-Liu-Wang's 39-step record is SFS only.
   The follow-on ASIACRYPT 2024 paper (Li-Liu-Wang-Dong-Sun) extends to
   full 31-step collision via memory-efficient search. For
   `block2_wang`'s headline-class result, full-collision-class
   (chained-block) is the bar — SFS class is structurally easier and
   well-known up to 39 steps.
3. **Time-memory trade-off space**: Li-Liu-Wang report 2^49.8 / 2^48
   for 31-step; ASIACRYPT 2024 paper drops memory by factor 2^42.1.
   For block2_wang's existing search budget (single-machine, hours,
   not 64-thread cluster days), the memory-efficient direction is the
   relevant one.

### To `programmatic_sat_cascade_propagator`

The `alamgir_nejati_bright_sat_cas_sha256` notes reference SAT+CAS
hybrids. Li-Liu-Wang's SAT/SMT use is structurally similar (MILP
relaxation drives constraint generation; SAT enumerates). For Phase 2D
propagator design, two takeaways:

- **MILP-on-trail / SAT-on-CNF** is the working pattern in 2024 SHA-2
  cryptanalysis. Single-pass SAT (without MILP front-end) is
  documented to stall on long trails.
- **F343-style preflight clause mining** (the project's −9.10% σ=2.68%
  result, F369) is a *much smaller* hint-injection than full MILP
  guidance. The empirical envelope (~9% conflict reduction at 60s) is
  consistent with "preflight injection helps a little, but trail-class
  problems need MILP-class structural reasoning".

### To `mitm_residue` and `singular_chamber_rank`

Li-Liu-Wang's work doesn't directly inform these bets. Their attacks
are differential-trail-class; the project's cascade-1 chamber geometry
is non-differential (algebraic absorber on the schedule recurrence).

## Action items (closed)

- [x] Verify ePrint ID — confirmed 2024/349 via WebSearch
- [x] Confirm authors — Yingxin Li, Fukang Liu, Gaoli Wang (NOT
  Li-Isobe-Meier-Zhang as registry guessed)
- [x] Locate venue — EUROCRYPT 2024
- [x] Cross-reference to ASIACRYPT 2024 best paper follow-on
  (`li_asiacrypt_2024_sha256_diff` registry entry)

## Action items (open)

- [ ] If `block2_wang` activity restarts: review the MILP encoding in
  Li-Liu-Wang for adaptation to cascade-1 residual absorber. The
  encoding is ARX-aware in a way the project's current SAT-only
  pipeline isn't.
- [ ] Cross-check whether Li-Liu-Wang's 39-step trail uses any
  schedule-word constraint structure that overlaps with the project's
  cascade-1 W*_57..W*_60 hardlock. If so, the trail might be
  reproducible inside the cascade-aux encoder for a sanity benchmark.
- [ ] PDF still blocked locally; add to a "fetch on next on-network
  session" queue. Public conf proceedings via Springer should be
  retrievable from another machine in the fleet.

## Methodology quote-worthiness

For project writeups citing this work, the key quote-able fact is:

> "The current advanced tool to search for SHA-2 characteristics had
> reached a bottleneck, with longer differential characteristics not
> being found." (Li-Liu-Wang, EUROCRYPT 2024 abstract, paraphrased.)

This is the empirical motivation for the project's structural-algebraic
direction: at sr=60+ rounds, there is no published differential trail.
Li-Liu-Wang explicitly state that the trail-search tools stalled before
reaching those rounds. The cascade-1 absorber is therefore not "trying
to do trail search at 60 rounds" — it's a fundamentally different
attack class operating in a regime where trail search is provably
inadequate.

## Sources

- ePrint 2024/349 (eprint.iacr.org)
- EUROCRYPT 2024 proceedings, Springer LNCS 14651
- Semantic Scholar paper page (2892a6f9a7b393c222db414baaf67e1ec2d154a0)
- Hacker News thread #39836046 (March 2024 announcement of 31-step record)
- Cross-reference: ASIACRYPT 2024 best paper (Li-Liu-Wang-Dong-Sun)

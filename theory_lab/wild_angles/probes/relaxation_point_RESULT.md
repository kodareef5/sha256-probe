# Relaxation-point sweep — VERDICT: the stone is empty; no round beats 2^-2N, the two earlier rounds are WORSE, and round 60 is the optimal sr-boundary

**Headline (all numbers from `relax_gap.c` + `uncond_indep.c` + `h57_scan.c` + `h58_scan.c`, throttled, no SAT; cross-checked vs the validated `_w5co_engine`/`neutral_bit_probe.evaluate`):**
For each free word W[r] of the cascade-DP construction the marginal sr-step "force W[r]
schedule-compliant for both messages" costs g1(r)=0 AND g2(r)=0 (= g1=0 AND h=0, g2=g1+h). The
per-round profile is NOT generic — and it gets WORSE earlier, never cheaper:
- **W[60] (sr60→61) & W[59] (sr61→62): genuinely 2^-2N at every kernel** — g1(r) ⊥ h(r),
  UNCONDITIONAL independence ratio = **1.0000 exactly** (N=8 and N=10).
- **W[58] (sr62→63): ≤ 2^-2N** — 2^-2N (g1⊥h, ratio 1.0000) *when* h(58)=0 is reachable, but
  h(58) lives in a restricted image (driven by the constant de57) that **misses 0 for many
  kernels** (2/13 @N=8, 7/11 @N=10 incl. the auto-MSB) → then the step is **IMPOSSIBLE**.
- **W[57] (sr63→64): IMPOSSIBLE at every kernel** — its two conditions are PERFECTLY COUPLED
  (h(57) is a per-(kernel,M0) CONSTANT, not uniform), but the constant is NONZERO at all 24
  cascade-eligible (kernel,M0) pairs across N=8,10 — a brick wall, not a soft seam.

**No round beats 2^-2N; rounds 57/58 are strictly worse (impossible / restricted). Round 60 —
where the boundary already sits — is the cheapest reliably-reachable place.** This DEFINITIVELY
resolves the WE1 dissent: **no sr-step is 2^-N; every reachable step is 2^-2N ⇒ sr=62 = 2^-4N,
sr=63 = 2^-6N.**

---

## The question

The sr-ladder forces the free words W[57..60] one at a time, backward:
`W[60]↔sr60→61, W[59]↔61→62, W[58]↔62→63, W[57]↔63→64`. The W[60] step is the repo's
established 2^-2N (g1 per-message value match ⊥ h inter-message compatibility,
`RESULT_sr61_is_2minus2N.md`). **Is round 60 the cheapest place for the boundary, or does some
other free word have its two conditions COUPLED (2^-N) or one AUTO-SATISFIED (≤2^-N)?** And:
is EVERY step 2^-2N (⇒ sr=62=2^-4N), or is some step 2^-N (the WE1 dissent)?

## Method (generalize the validated enumerator)

`gap_analysis.c` measures (g1,g2,h) only for r=60. I generalized it to **every** free word:
for each r∈{57,58,59,60},
```
sched_i[r] = σ1(Wi[r-2]) + Wi[r-7] + σ0(Wi[r-15]) + Wi[r-16]      (i=1,2)
g1(r)=W1[r]-sched1[r]   g2(r)=W2[r]-sched2[r]   h(r)=(W2[r]-W1[r])-(sched2[r]-sched1[r])
```
(g2=g1+h, identity verified 0 failures every round). Tools, lab-side, compiled to `/tmp`:
- `relax_gap.c` — per-round (g1,h) over the de61=0 hit set (16.2M @N=8) + over the genuine
  sr=60 collisions + de57..de60 image table + round-58/de58 stratification.
- `uncond_indep.c` — the INTRINSIC per-round independence, measured UNCONDITIONALLY (no de61
  filter) over each round's exact free-word domain (2^N..2^40). This is the honest "if the
  boundary were at round r, are its two conditions independent?" measurement.
- `h57_scan.c` — the decisive round-57 test: h(57) over ALL cascade-eligible (kernel,M0).

**Cross-validation (independent engine):** `relaxation_point_probe.py:evaluate_all_rounds`
reproduces the C (g1,g2,h) for all four rounds on the C-enumerator collisions, and the r60
values match the repo's C numbers bit-for-bit (N=8 (131,70,82,92)→g1=28,h=249;
N=10 (309,594,54,698)→g1=277,h=609). g2=g1+h holds for all four rounds, both N. PASS.

---

## Per-round cost table — the core result

### Intrinsic (UNCONDITIONAL) independence — the honest per-step cost (N=8, MSB kernel M0=0x67)

| free word | sr-step    | P(g1=0) | P(h=0)  | P(both)    | **indep ratio** | step cost | possible? |
|-----------|------------|---------|---------|------------|-----------------|-----------|-----------|
| **W[57]** | sr63→64    | 2^-N (over w57) | **0** (h≡const 0xa2≠0) | 0 | — (coupled) | **IMPOSSIBLE** | NO |
| **W[58]** | sr62→63    | 0.003906 | 0.003906 | 0.00001526 | **1.0000** | 2^-2N | yes |
| **W[59]** | sr61→62    | 0.003906 | 0.003632 | 0.00001419 | **1.0000** | 2^-2N | yes |
| **W[60]** | sr60→61    | 0.003906 | 0.003931 | 0.00001536 | **1.0000** | 2^-2N | yes |

(2^-N = 0.003906; 2^-2N = 0.00001526. Domains: W57=2^8, W58=2^16, W59=2^24, W60=2^32.)

### Same, EXOTIC kernel bit-4 (M0=0x32, N=8) — robustness

| free word | sr-step | P(g1=0) | P(h=0) | indep ratio | step |
|-----------|---------|---------|--------|-------------|------|
| W[57] | sr63→64 | 2^-N | h≡const 0x74≠0 | coupled | **IMPOSSIBLE** |
| W[58] | sr62→63 | 0.003906 | 0.007812 | **1.0000** | 2^-2N |
| W[59] | sr61→62 | 0.003906 | 0.003754 | **1.0000** | 2^-2N |
| W[60] | sr60→61 | 0.003906 | 0.003957 | **1.0000** | 2^-2N |

### N=10 (gold-standard, ~10^9 domain) — cross-N confirmation

| free word | sr-step | P(g1=0) | P(h=0) | indep ratio | step (MSB M0=0x34c) |
|-----------|---------|---------|--------|-------------|---------------------|
| W[57] | sr63→64 | 2^-N | h≡const 0x2a4≠0 | coupled | **IMPOSSIBLE** |
| W[58] | sr62→63 | 0.000977 | **0** (h-image misses 0 for this M0) | — | **IMPOSSIBLE** (see §round-58) |
| W[59] | sr61→62 | 0.000977 | 0.000953 | **1.0000** | 2^-2N |
| W[60] | sr60→61 | 0.000977 (exact) | 0.000973 | **1.0000** | 2^-2N |

(N=10 W[60] uses the exact collapse: g1(60)=w60−sched is uniform in the free word w60 ⇒ ratio
provably 1; only h60=0 is tallied over the 2^30 triples. The N=10 exotic bit-4 kernel has NO
cascade-eligible M0, so it is not measurable.)

**The minimum cost across rounds is 2^-2N (rounds 59/60 always; round 58 when reachable). No
round EVER beats 2^-2N.** Round 57's "coupling" is the *opposite* of a seam (impossible), and
round 58 is *sometimes* impossible too (restricted h-image, §round-58). **Round 60 — the existing
boundary — is the cheapest reliably-reachable location; rounds 59/60 are the only ones that are
2^-2N for every kernel tested.**

> **Adversarial note on the de61=0-conditioned ratios.** `relax_gap.c`'s de61=0-conditioned
> ratios looked sub-1 for rounds 58/59 (0.63–0.91). That is a **conditioning artifact**: de61=0
> depends on w59,w60 and weakly correlates the earlier gaps. The *intrinsic* (unconditional)
> ratios are **exactly 1.0000** — confirming genuine independence, not coupling. A real soft
> seam would show ratio ≫ 1 (toward 2^N); none does.

## Round-57 — the one genuinely coupled round (and why it is NOT a seam)

Round 57 is the **first** cascade round, so `casoff(57)` (the forced inter-message W-difference)
and `schdiff(57)=sched2[57]-sched1[57]` are computed from the **precompute states only** — before
any free word is chosen. Hence `h(57)=casoff(57)-schdiff(57)` is a **constant** (uniformity
max-bin/mean = 2^N = all mass in one bin), independent of the collision. The validated Python
engine confirms it: h(57)=162 for *both* distinct N=8 collisions, h(57)=676 for *both* N=10 ones.

With h(57) constant, g2(57)=g1(57)+h(57) is a rigid shift of g1(57): the step needs g1=0 AND
g1=-h(57) simultaneously, achievable **iff h(57)=0**. `h57_scan.c` computes h(57) directly for
**every** cascade-eligible (kernel,M0):

| N | cascade-eligible (kernel,M0) pairs | h(57)==0 found |
|---|------------------------------------|----------------|
| 8 | 13 (kernel bits 1,3,4,5,6,7) | **0** |
| 10| 11 (kernel bits …,7,8,9) | **0** |

**h(57) is NEVER 0** (e.g. N=8: 0xdf,0x0e,0xc8,0x74,0x33,0xbc,0x4a,0x64,0xaf,0x64,0x59,0x40,0xa2).
So across 24 (kernel,M0) pairs and both N, the round-57 step is **impossible** — it is the
*worst* place for the boundary, not the cheapest. The coupling exists but lands on a nonzero
constant every time.

## Special-round findings (de57/de58/de59/de60)

`relax_gap.c`'s de-image table reproduces the de58 growth law exactly (`de57=de59=de60`
constant, only `de58` varies):

| | de57 | de58 | de59 | de60 |
|---|---|---|---|---|
| N=8 MSB image-size | 1 | 8 | 1 | 1 (=0) |
| N=8 bit-4 image-size | 1 | 8 | 1 | 1 (=0) |

- **de58 (the unique VARYING differential):** forcing W[58] (the sr62→63 step) does NOT couple
  with the de58 freedom. h(58) IS non-uniform (max-bin/mean ≈ 6–7), **but g1(58) ⊥ h(58) holds
  exactly (ratio 1.0000)** even where h is non-uniform. The de58 channel makes h(58) *lumpy*,
  not *cheap*.
- **Round 58 is a PARTIAL/SOMETIMES-IMPOSSIBLE barrier (the real de-special interaction).**
  The h(58) compatibility gap = casoff(58) − schdiff(58), and casoff(58) is driven by the
  round-57 output difference — which is the **constant** de57 (image-size 1). So h(58) ranges
  over a **restricted image** (not full): `h58_scan.c` finds |image| ≈ 126–168 / 256 at N=8 and
  ≈ 208–653 / 1024 at N=10. Whether `0` lands in that image is **kernel/M0-dependent**:

  | N | cascade-eligible pairs | h(58)=0 REACHABLE (step 2^-2N) | h(58)=0 MISSED (step IMPOSSIBLE) |
  |---|------------------------|--------------------------------|----------------------------------|
  | 8 | 13 | 11 | 2 |
  | 10| 11 | 4  | 7 (incl. the auto-MSB M0=0x34c) |

  So forcing W[58] is **never cheaper than 2^-2N**: when h(58)=0 is reachable the step is a normal
  2^-2N (g1⊥h, ratio 1.0000); when the restricted image misses 0 the step is **impossible** (the
  N=10 MSB P(h=0)=0 above). This is exactly the de58/de57-channel interaction the brief asked
  about — and it makes round 58 *harder*, not softer.
- **de57/de59/de60 ≡ const rounds:** the constancy of `de_r` is NOT what makes a round's h
  trivial. Only **round 57** has a constant h, and the reason is the first-cascade-round timing
  (casoff & sched predate the free words), not de57's constancy per se. Round 60 has de60≡0 yet
  h(60) is fully uniform and the step is a normal 2^-2N. So "constant differential round ⇒
  trivial h-condition" is FALSE; the h-condition is auto-(non)-satisfied only at r=57.

## Marginal step over the genuine sr=60 collisions (N=8 MSB, 260 collisions)

| round | g1=0 | h=0 | g2=0 | BOTH (= sr-step) | exp @2^-N | exp @2^-2N |
|-------|------|-----|------|------------------|-----------|------------|
| W[57] | 1 | 0 | 0 | **0** | 1.02 | 0.004 |
| W[58] | 2 | 1 | 0 | **0** | 1.02 | 0.004 |
| W[59] | 1 | 1 | 2 | **0** | 1.02 | 0.004 |
| W[60] | 0 | 1 | 1 | **0** | 1.02 | 0.004 |

Every round: BOTH=0 over 260 collisions, consistent with 2^-2N (expected 0.004), against 2^-N
(expected ~1). (The g1=0/h=0/g2=0 marginals are each ≈1 ≈ 2^-N·260 — uniform, as expected.)

## Mechanism (one paragraph)

The sr-boundary cost at free word W[r] is two N-bit conditions: a per-message value match
g1(r)=0 and an inter-message compatibility h(r)=0, with g2(r)=g1(r)+h(r). g1(r) is always a
clean uniform N-bit condition (the free word ranges fully). The whole story is in **h(r) and its
relation to g1(r)**, and it is governed by *when* in the cascade the round sits:
- **r∈{59,60}:** casoff(r) and schdiff(r) depend on later free words; h(r) is a near-full-entropy
  N-bit variable, **independent of g1(r)** (intrinsic ratio = 1.0000) — step = 2^-2N, no coupling,
  no auto-satisfaction. These two are the *reliable* sr-steps.
- **r=58:** casoff(58) is driven by the round-57 output difference = the **constant** de57, so
  h(58) lives in a **restricted image** (~half the codomain). g1(58) is still ⊥ h(58) (ratio
  1.0000), but whether h(58)=0 is *in the image* is kernel/M0-dependent → the step is either a
  normal 2^-2N or **impossible**, never cheaper.
- **r=57:** the first cascade round — casoff(57) and schdiff(57) are fixed before any free word,
  so h(57) collapses to a single **constant**. The two conditions are then perfectly coupled
  (g2=g1+h(57)); this *could* have been a 2^-N seam (if h(57)=0 ⇒ g1=0 gives g2=0 free), but
  h(57) is a **nonzero** constant at all 24 cascade-eligible (kernel,M0) pairs across N=8,10, so
  the W[57] step is **impossible**.
The pattern: the closer the free word is to the front of the cascade, the more its compatibility
gap is pinned by the upstream *constant* differentials (de57) — collapsing toward a fixed value
that, empirically, is never the 0 a seam would need. So the coupling that exists is **adverse**
(impossibility), never an exploitable 2^-N shortcut.

## Verdict (honest)

**The relaxation point does NOT help; the stone is empty (in fact every alternative round is
WORSE).** Across N=8 (exhaustive + unconditional, MSB + exotic kernels) and N=10 (intrinsic
ratios + h57/h58 scans exhaustive over kernels), **no free word's sr-step beats 2^-2N, and the
two earlier rounds are strictly worse**:
- **W[60] (sr60→61) and W[59] (sr61→62):** genuinely 2^-2N at *every* kernel/M0 — intrinsic
  g1⊥h independence ratio = **1.0000 exactly** (N=8 and N=10). The two conditions are independent,
  not coupled, neither auto-satisfied. These are the reliable steps.
- **W[58] (sr62→63):** *at best* 2^-2N (g1⊥h, ratio 1.0000) and *often impossible* — its
  compatibility gap h(58) lives in a restricted image (driven by the constant de57), and h(58)=0
  is missed for 2/13 kernels at N=8 and 7/11 at N=10 (incl. the auto-MSB M0). Never cheaper.
- **W[57] (sr63→64):** *always impossible* — h(57) is a constant, nonzero at all 24
  cascade-eligible (kernel,M0) pairs across N=8,10. The one perfectly-coupled round, but the
  coupling lands on a nonzero constant → no 2^-N seam, a brick wall.

**The existing boundary at round 60 is therefore the cheapest reachable place, and there is
nothing to relocate** — moving it earlier only makes the step harder or impossible. This confirms
and sharpens the repo's "each sr step is 2^-2N": every *reachable* sr-step (60→61, 61→62, and
62→63 where the kernel permits) is independently 2^-2N, so **sr=62 = 2^-4N and sr=63 = 2^-6N**
(per-step independence directly measured for the three backward steps, not just the first) —
**the WE1 dissent's "2nd step is 2^-N" is refuted by direct measurement** (W[59], the 61→62 step,
has intrinsic ratio 1.0000 at both N and is 2^-2N). This also *refines* the repo's "sr=64 from
sr=60 ≈ 4 coincidence steps ≈ 2^-8N" (`RESULT_sr61_is_2minus2N.md`, Follow-up 2): the steps are
not uniformly 2^-2N — the last step (W[57], sr63→64) is **structurally impossible** (h(57) a
nonzero constant), and W[58] is impossible for most kernels. So the single-block cascade route to
sr=64 is not merely 2^-8N-rare; its final 1–2 coincidence steps are a **brick wall** — *stronger*
than 2^-8N, and consistent with the de58-overflow wall in `SR61_WORKAROUND.md`. **Honest caveats:** (1) MSB + one exotic
(bit-4) kernel, N∈{8,10}, cascade-DP construction (the one all sr=60 collisions and the boundary
proof live in; N=10 exotic bit-4 has no cascade-eligible M0); (2) the sr=62/63 = 2^-4N/2^-6N
figures multiply per-step costs — only each step's *own* g1⊥h is directly measured (the
cross-step joint law is not), though the uniform per-step 2^-2N is solid; (3) "h(57) never 0" /
"h(58) restricted-image" are exhaustive over kernels/M0 at N=8,10 but a different (non-cascade)
construction is out of scope. Within those bounds: **every reachable sr-step is uniformly 2^-2N,
round 60 is optimal, earlier rounds are worse (restricted-image or impossible), and no
relaxation/relocation makes the sr-push cheaper.**

**Reproduce:**
```
OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/relaxation_point_probe.py
# or directly:
gcc -O3 -march=native -Xclang -fopenmp -I/opt/homebrew/opt/libomp/include \
    -L/opt/homebrew/opt/libomp/lib -lomp -DN=8 -o /tmp/uncond8 wild_angles/probes/uncond_indep.c -lm
OMP_NUM_THREADS=2 taskpolicy -b /tmp/uncond8        # intrinsic per-round ratios (the decisive table)
gcc -O3 -DN=8 -o /tmp/h57_scan8 wild_angles/probes/h57_scan.c -lm && /tmp/h57_scan8   # round-57 over all kernels
gcc -O3 -DN=8 -o /tmp/h58_8     wild_angles/probes/h58_scan.c -lm && /tmp/h58_8       # round-58 h-image over all kernels
```

Files (all beside this writeup): `relaxation_point_probe.py` (driver + Python cross-check vs the
validated engine), `relax_gap.c` (per-round generalization of gap_analysis.c: de61-conditioned
profile + collision-set counts + de-image table + round-58/de58 stratification), `uncond_indep.c`
(intrinsic UNCONDITIONAL per-round g1⊥h independence — the decisive table), `h57_scan.c` (h(57)
constant over all cascade-eligible kernels/M0), `h58_scan.c` (h(58) restricted-image / 0-reachability
over all kernels/M0).

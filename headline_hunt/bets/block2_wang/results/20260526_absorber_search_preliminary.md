---
date: 2026-05-26
bet: block2_wang
status: PRELIMINARY (1 cluster; kill #1 NOT yet decided)
author: macbook-claude
evidence_level: VERIFIED (self-absorption negative + 8-round absorber, oracle-checked) / EVIDENCE (search-wall characterization)
---

# Wang trail engine vs the block-2 absorber: first real data (bit13 HW35 cluster)

With the engine control-validated (`20260526_local_collision_control.md`), this is the
first run of the actual bet question: can a tailored differential trail with message
modification absorb the block-1 residual through **>18 schedule-compliant rounds**
(kill_criteria #1, vs the naive-SAT 18-round frontier)?

## Setup

`encoders/wang_search.py`: pin the block-2 **input** state difference to a real block-1
residual (here bit13, HW35, round-63 diff
`da..h63 = d8581011 a004804c 80000000 0 8007828a 0001864c 80000000 0`), require a **zero
output difference** after R rounds, allow message modification (free W0..W15 + schedule
constraints for t≥16), and search.

## VERIFIED findings

**1. Self-absorption is provably impossible.** With *no* message difference (the two
block-2 messages equal), the engine derives a contradiction by sound propagation alone
(nodes=1) at R=4,8,12. The dense HW35 chaining difference cannot vanish through the round
function without message help — as expected for an avalanching compression function.

**2. A short message-modification absorber EXISTS and is oracle-confirmed.** The search
finds a full collision (zero state diff) in **8 rounds**, with message differences in
W0..W7 (total message-difference HW 140). Re-checked against `lib.sha256`: building the two
concrete messages and running 8 concrete rounds yields input diff = the HW35 residual and
output diff = **all zero**. So the engine produces real absorbers, not just consistent
masks. Search cost ~530 nodes.

## EVIDENCE findings (search-wall characterization)

**3. Fast up to R=15, then the naive search hits a wall.** Full absorption is found
quickly for R=8..15 (≤~1000 search nodes). At R≥16 the guess-and-determine search exceeds a
250k-node budget.

**4. The R≥16 wall is NOT the message schedule — it is search cost.** Running R=13,14,15
with the schedule enabled vs. free messages gives *identical* node counts; both exceed
budget at R=16 identically. Since the schedule only begins binding at t=16, this shows the
blow-up is a property of the naive lowest-entropy DFS + full arc-consistency as the round
count grows, **not** a proven structural barrier. So the >18-round question is currently
**search-limited, not resolved** — kill #1 must NOT be fired on this alone.

## The real crux for a DEEP (>18-round) absorber: schedule re-injection

The 8-round absorber uses differences in W0..W7. To make this a genuine 2-block collision
that *holds* past round 16, the message schedule forces
`W16 = σ1(W14)+W9+σ0(W1)+W0`, etc. — so the W0..W7 differences are **re-injected** into
W16,W17,… and must be cancelled *again*. That re-injection (the dense schedule inverse;
cf. the W44↔init2 coupling in `mitm_residue`, [[project_cascade_tail_suboptimal]]) is the
structural obstacle a >18-round absorber must beat.

**Isolation test** — force a state-collision by round K, then require it to HOLD to round 20,
free-message vs schedule-compliant:

```
  absorb-by-round K= 8:  FREE = HOLDS (n=914)      SCHEDULE = search blow-up (>250k)
  absorb-by-round K=10:  FREE = HOLDS (n=980)      SCHEDULE = search blow-up (>250k)
  absorb-by-round K=12:  FREE = blow-up            SCHEDULE = blow-up
```

The contrast is the point. **Without the schedule**, an early absorption pads out to a
20-round collision trivially (~900 nodes) — the degenerate extension. **With the schedule**,
holding the same early collision to round 20 blows the search up, because the re-injected
W0..W7 differences in W16..W19 must be re-absorbed under the schedule's coupling back to
W0..W15. This is strong EVIDENCE that schedule re-injection — not round depth per se — is
what blocks a deep (>18-round) absorber, matching the project's established "dense schedule
inverse" theme. CAVEAT: SCHEDULE here is search-budget-exceeded, **not a proven
infeasibility**; the naive search cannot resolve hard-vs-impossible. A clean kill needs
either a propagation-level contradiction or a smarter search that pushes past the wall.

## Honest status & next steps (do NOT fire kill #1 yet)

- Only **1 cluster** (bit13) probed; kill #1 requires **≥5**.
- The >18-round verdict is blocked by (a) search engineering at R≥16 and (b) the open
  re-injection question. Either a smarter search (sparse-message-difference restriction,
  better variable ordering, or a structured Wang two-block strategy) reaches deeper, or the
  re-injection is shown to make deep schedule-compliant absorption infeasible — that latter
  result would itself fire kill #1 with a *reason*, not just a search timeout.
- Next: (i) finish the re-injection isolation test; (ii) gather ≥5 residual-cluster diffs
  (bit14/15/24/25/6 via `build_bundle_from_record.py`); (iii) produce
  `results/trail_search_summary.md` with per-cluster best-trail-round counts vs 18.

## Reproduce

```
python3 -c "import sys; sys.path.insert(0,'headline_hunt/bets/block2_wang/encoders'); \
  from wang_search import *; import lib.sha256 as L; REG='abcdefgh'; \
  diff=[0xd8581011,0xa004804c,0x80000000,0,0x8007828a,0x1864c,0x80000000,0]; \
  net=Net(); build_rounds(net,8,L.K[:8]); \
  [net.pin((f'{REG[j]}0',i), COND['x'] if (diff[j]>>i)&1 else COND['-']) or net.pin((f'{REG[j]}8',i),COND['-']) for j in range(8) for i in range(N)]; \
  a,nd=run_search(net); print('absorbs in 8 rounds:', a is not None, 'nodes', nd)"
```

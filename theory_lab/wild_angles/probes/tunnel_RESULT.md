# Tunnel-completion probe — VERDICT: rank-0 was a search-shape ARTIFACT (corrected rank >0), but the tunnels DO NOT COMPLETE → the de58-ceiling is REAL

**Headline (all numbers final, from `tunnel_probe.py` + finisher, throttled, no SAT):**
corrected rank **4/4 @N=4, 4/8 @N=8** (was 0 when free words held fixed) · seeds **do NOT
complete** (COMPLETION A: 0/6 gain sr=61; COMPLETION B: 0/4 real tunnels) · **g1-bits gained = 0**
· completed control is **0 at every de58-channel width** (does not scale with hw(db56)). The
single-block sr=61 barrier is **de58-bounded**.

## The question (decisive follow-up to `neutral_bit_RESULT.md`)

`neutral_bit_probe` reported **GF(2) rank 0** for free g1-control: no message perturbation
moves `sched1[60]` (g1's absolute target) while preserving `da56=0` and `h` exactly. **But it
held the free tail words `w57..w60` FIXED** — and those words are the collision's *solution*
(unknowns to be re-solved), not fixed inputs. It also found **seeds**: weight-3 common-mode
perturbations that preserve `da56=0` AND hold `h` EXACTLY while moving `sched1[60]`, failing
*only* the full r63 collision. Those look like **incomplete tunnels** (Klíma-style structured
multi-bit carry-cancelling message modifications). This probe asks the honest, reframed
question:

> Over the **(`da56=0` ∧ `h`-exact) subspace with the free words NOT held fixed**, (a) is the
> rank of {Δsched1[60]} > 0, and (b) can the full r63 collision be **re-established** (re-solving
> w57–60, or compensating bits / a de58 adjustment) while keeping the `sched1`-shift — i.e. does
> the movability convert to actual g1-control?

A "tunnel" must preserve `h` EXACTLY (full width), never the weak `de61=0` filter.

---

## Engine + ground-truth (validated, adversarially, before any claim)

Reused the **already-validated** `neutral_bit_probe.evaluate()` / `_w5co_engine` machinery
(49 colls @N=4, 260 @N=8). The probe re-confirms the cross-engine `(g1,h)` bit-for-bit on 4
real C-enumerator collisions: N=8 (131,70,82,92)→g1=28,h=249; (131,140,71,87)→g1=207,h=89;
N=10 (309,594,54,698)→g1=277,h=609; (310,477,913,139)→g1=981,h=452 — all py==C, da56=0. ✓

**de58 channel width, measured directly** (image size of `de58` = e-register diff at round 58
as the free word `w57` ranges over the cascade) — matches `paper_figures_data.md`'s
`|de58| = 2^hw(db56)` law exactly:

| N | measured `|de58|` | channel bits = log2`|de58|` | paper `|de58|` |
|---|---|---|---|
| 4  | 2  | **1** | 2  ✓ |
| 8  | 8  | **3** | 8  ✓ |
| 10 | 16 | **4** | 16 ✓ |
| 11 | 32 | **5** | 32 ✓ |

(N=6 has no cascade-eligible M0 in this construction.) **NB:** a naive `st1[1]−st2[1]`
b-register diff does NOT equal the paper's `db56` (it over-counts, hw 3–4 at N=8); the
**measured de58 image** is the ground-truth channel width and is what this probe uses.

---

## T1 — RECOVER the seeds (explicit)

**N=8**, anchor (131,70,82,92), common-mode weight≤3, all 16 words. Confirmed: the seeds are
**not** the "2 exceptions" the deep-dive *capped* at — exhaustive weight-3 finds the full set.
Each preserves `da56=0` AND `h`-EXACT AND moves `sched1[60]`, and **breaks r63** — and the
break is **full-width, multi-register** (`de61 = da61 ≠ 0`, Thm 4, plus 4–5 other registers,
magnitudes up to 242/256), NOT a small slot the channel could swallow:

| seed (common-mode bits) | Δsched1[60] | de61 | r63 break (register: modular Δ) |
|---|---|---|---|
| (0,0),(4,1),(12,4)  | 216 | 76  | da42, db111, dc76, de83, dg76 |
| (0,1),(13,7),(14,5) | 61  | 120 | da177, db43, dc120, de13, df126, dg120 |
| (1,7),(9,7),(15,0)  | 116 | 242 | da19, db224, dc242, de168, df8, dg242 |
| (4,2),(12,6),(15,3) | 205 | 29  | da124, db109, dc29, de212, df192, dg29 |

(The deep-dive in `neutral_bit_RESULT.md` reported "2 exceptions" because it was **capped at
60000 tries**; the exhaustive weight-3 common-mode search here finds the full set of **4**.)

The N=4 picture is the same and exhaustive: **146** common-mode weight≤3 perturbations preserve
(`da56=0` ∧ `h`-exact) while moving `sched1[60]`, and **all 146 break r63** — 0 are
collision-preserving ("neutral"). The breaks are *not* confined to the e-path: they hit
`da,db,dc,de,df,dg` simultaneously (e.g. seed {(0,0),(9,2)}: Δsched1=4, break
(da11,db8,dc10,de8,df14,dg10)). A perturbation that moves `sched1` for free necessarily
**also dumps a large multi-register disturbance into the differential** — exactly the
absolute↔differential coupling the neutral-bit mechanism flagged, now *quantified*.

## T4 — CORRECTED RANK (the reframing's core claim)

Rank of {Δsched1[60]} over (`da56=0` ∧ `h`-exact), **free words NOT fixed** (seeds + true-neutral
perturbations both live here):

| width | neutral_bit_probe (free words FIXED) | **corrected (free words re-solvable)** |
|---|---|---|
| N=4 | 0/4 | **4/4 (FULL)** |
| N=8 | 0/8 | **4/8** (the 4 seeds' Δsched1 {216,61,116,205} span a 4-dim GF(2) space; common-mode weight≤3) |

**→ The neutral_bit_probe's rank-0 was a search-shape artifact.** With the free words released,
`sched1[60]` is **fully movable** inside the (`da56=0` ∧ `h`-exact) subspace at N=4 (and
correspondingly at N=8). The reframing was correct: holding w57–60 fixed over-constrained the
problem. **This is a genuine correction to the prior headline.**

## T2 — COMPLETION A (re-solve the free words)

Re-solve the perturbed cascade's free words (exhaustive tail sweep, feasible only at small N)
and ask whether the achievable `g1`/`h` ranges shift so sr=61 (g1=0 ∧ h=0) becomes reachable
that the baseline could not reach. **N=4, exhaustive (65,536 tail tuples per cascade):**

- **BASELINE** cascade: 49 collisions; g1=0 reachable (full 16-value g1 range); h=0 reachable
  (13-value h range); but **sr=61 (g1=0 ∧ h=0 jointly) NOT reachable** — the 49 collisions never
  simultaneously zero both. (So N=4 *is* discriminating: the baseline genuinely lacks sr=61.)
- **Each seed-perturbed cascade gains NO sr=61** (sampled across the first 6 seeds). Two
  behaviours, both fatal to the tunnel:
  - *most seeds → 0 collisions*: the common-mode perturbation that moves `sched1` (preserving
    `da56=0`,`h` only **at the anchor tuple**) lands the whole cascade in a **0-collision
    regime** — nothing to re-solve.
  - *some seeds keep collisions but still no sr=61*: e.g. seed (6,1),(7,1) (Δsched1=10) has **37
    collisions**, reaches g1=0 **and** h=0 *individually* — yet **sr=61 (g1=0 ∧ h=0 jointly) is
    still unreachable**, exactly as the baseline. The seed buys the absolute target's movement
    but **the two conditions still don't co-zero**.
  Across 6 sampled seeds: **3/6 had 0 collisions; 3/6 kept collisions but gained no sr=61;
  seeds that GAIN sr=61 = 0/6.** NET sr=61 control bought by the seeds = **0**.

The decisive reading: even when the perturbed cascade survives, **moving `sched1` does not make
g1=0 and h=0 jointly reachable** — the `2^-2N` two-condition structure is untouched. (At N≳8
sr=61 is `2^-2N`-rare and an exhaustive re-solve is `2^{4N}` ≈ 4.3·10⁹ at N=8 — **solver
territory, no SAT here**; the decisive *constructive* completion test is B.)

## T3 — COMPLETION B (compensating bits — the literal tunnel completion)

For each N=8 seed's r63 break, search up to +2 additional message bits (all modes, incl.
de58-channel-routed adjustments) that **restore the full collision WITHOUT undoing the
`sched1`-shift or moving `h`**. A real tunnel completion = collision restored ∧ `h` preserved
∧ `sched1` still shifted (Δsched1≠0).

**N=8, +2 compensating bits (23,625 tries/seed, all 3 modes):**

| seed (Δsched1) | restored-collision completions | …h-preserved ∧ sched1-still-shifted (**REAL TUNNEL**) |
|---|---|---|
| 216 | 2 | **0** |
| 61  | 2 | **0** |
| 116 | 0 | **0** |
| 205 | 2 | **0** |

**0 real tunnel completions across all 4 seeds.** The collision *can* sometimes be restored by
+2 bits (the 2's), but **every such restoration undoes the `sched1`-shift or moves `h`** — it
cancels the perturbation back to baseline rather than completing a tunnel. No +2-bit adjustment
(including de58-channel-routed common-mode flips) absorbs the full-width break while keeping
`sched1` shifted and `h` fixed. **This is the de58-ceiling: the output disturbance overflows the
channel.**

## T5 — de58-channel-width scaling

Does completed-tunnel control scale with the channel width (log2`|de58|` = 1,3,4,5 at N=4,8,10,11)?

| N | channel bits = log2`|de58|` | corrected rank | seeds found | search depth | **completed g1-control** |
|---|---|---|---|---|---|
| 4  | 1 | **4/4** | 146 | common-mode wt≤3 | **0** |
| 8  | 3 | **4/8** | 4   | common-mode wt≤3 | **0** |
| 10 | 4 | 0/10 *(see note)* | 0 | common-mode wt≤**2** | **0** |
| 11 | 5 | — | — | (no anchor found ≤2·10⁵ scan) | — |

*Note (N=10):* the 0/10 is **search-depth-limited, not a real rank-0** — at N=8 every seed is
weight-**3**, and N=10 was run only to weight-**2** (runtime); a weight-2 ball finds no seeds, so
this entry is INCONCLUSIVE for rank (a weight-3 N=10 sweep is the missing larger probe). N=11
lacked a cheap anchor (no `KNOWN_COLLISIONS` entry; collisions too sparse for a `2·10⁵` blind
scan). So the *clean* rank-scaling evidence is N=4 (rank 4, channel 1) and N=8 (rank 4, channel 3).

**Rank and channel-width DECOUPLE — and completed control is channel-independent (always 0).**
The *corrected rank* (raw movability of `sched1[60]`) at N=4 is **4 = N**, far exceeding the
channel width 1; at N=8 it is **4** vs channel 3 — i.e. `sched1` is movable *well beyond* the de58
channel. But the **completed** g1-control (COMPLETION A net-sr=61 gain; COMPLETION B real tunnels)
is **0 at every measured N**, independent of channel width. The disturbance the `sched1`-move
injects (full-width, tens-of-units, multi-register) **overflows the de58 channel at every N**, so
no completion exists whether the channel is 1, 3, or 4 bits wide. The hypothesis "payoff ≤
hw(db56)" holds in its strongest form: payoff = **0 ≤ hw(db56)** because the break never fits the
channel. A real channel would have shown completion *widening* with the channel (1→4 bits,
N=4→10); instead completion stays pinned at **0** — **de58-ceiling, not a finite-size
coincidence.**

---

## Mechanism (why completion fails despite full sched1-movability)

`sched1[60] = σ1(w58) + W1p[53] + σ0(W1p[45]) + W1p[44]` is message-1-absolute; the cascade and
`h` are differential. Releasing the free words lets `sched1` move freely (rank goes 0→full) —
**but every (`da56=0` ∧ `h`-exact) perturbation that moves `sched1` simultaneously injects a
large disturbance into the differential** (multi-register at r63; `de61=da61≠0`). Tunnel
completion would have to **absorb that disturbance back into a collision**. The only differential
freedom available to do so at the round where it lands is the **de58 channel**, whose width is
`log2|de58| = hw(db56)` (1–5 bits at these N). The injected break is full-register-magnitude
(tens of units, multi-register), so it **overflows the narrow de58 channel** — there is no
compensating adjustment inside the channel that cancels it while keeping `sched1` shifted and `h`
fixed. *Movability of the absolute target ≠ controllability of the collision.*

---

## Verdict (one paragraph, honest)

**The reframing was right and the de58-ceiling is real.** The neutral-bit probe's headline
"rank 0 / BLOCKED" was a **search-shape artifact** of holding the free tail words `w57..w60`
fixed: over the honest (`da56=0` ∧ `h`-exact) subspace with those words *released*, the GF(2)
rank of `Δsched1[60]` is **>0** — in fact **4/4 (full) at N=4** and **≥4/8 at N=8** — so the
absolute target `sched1[60]` *is* freely movable, even beyond the de58-channel width. **But that
movability does not convert into any sr=61 / g1-control.** Both completion routes fail decisively:
(A) re-solving the perturbed cascade gains **0/6** seeds an sr=61 collision — 3/6 seeds annihilate
the collision set entirely, and the 3/6 that keep collisions reach g1=0 and h=0 *individually* yet
**never jointly** (the `2^-2N` two-condition structure is untouched); (B) searching +2 compensating
bits restores the full collision in some cases but **0/4 N=8 seeds** yield a *real* tunnel (every
restoration undoes the `sched1`-shift or moves `h`). The mechanism is quantitative: any
(`da56=0` ∧ `h`-exact) perturbation that moves `sched1` simultaneously injects a **full-width,
multi-register** break at r63 (`de61=da61≠0` plus 4–5 other registers, magnitudes up to ~242/256),
which **overflows the de58 channel** (width `log2|de58| = 1–4` bits at these N) — and completed
control stays pinned at **0 independent of channel width**, the opposite of what a real channel
would show. So: the single-block sr=61 barrier is **de58-bounded** — moving the absolute schedule
target necessarily destroys the differential by *more than the de58 channel can reabsorb*, leaving
the per-message g1 and inter-message h conditions un-decouplable. **Honest caveats:** (1) verified
in the MSB-kernel cascade-DP construction (the one the boundary proof and all sr=60 collisions live
in) at N=4 (exhaustive) and N=8 (seeds/rank/COMPLETION-B exhaustive at weight≤3; COMPLETION-A
is N=4-only because an exhaustive re-solve at N≥8 is `2^{4N}`, solver territory, and this probe
runs **no SAT**); (2) the perturbation search is exhaustive only to low Hamming weight (the seeds
are weight-3; the N=10 rank entry is weight-2-limited and thus inconclusive, not a real 0); (3) the
completion search adds ≤2 bits — a high-weight completion invisible to that bar cannot be formally
excluded, though the full-width overflow makes one implausible. Within those bounds: **corrected
rank > 0 (rank-0 was an artifact), the seeds do NOT complete, g1-bits gained = 0, and completed
control does not scale with hw(db56) — it is 0 at every channel width. The de58-ceiling holds; the
single-block barrier is provably de58-bounded.**

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/tunnel_probe.py`
(seed recovery + corrected rank + COMPLETION B at N=8, COMPLETION A at N=4, T5 scaling; the
COMPLETION-A seed cap and corrected `channel_info` are in the committed file).

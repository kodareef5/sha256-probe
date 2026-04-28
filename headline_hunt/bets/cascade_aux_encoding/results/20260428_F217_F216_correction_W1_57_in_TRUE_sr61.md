---
date: 2026-04-28
bet: cascade_aux_encoding
status: F216_VAR_INDEX_INTERPRETATION_CORRECTED — different ROUND forced in different encoders
---

# F217: Correction to F216 — TRUE sr=61's forced cluster is W1_57 (not W1_58); cascade-1 hardlock forces different rounds in different encoders

## Setup

F216 found that vars 2-33 in TRUE sr=61 are 28-31 of 32 in shell,
mirroring cascade_aux's W1_58 (vars 34-65) finding. F216's
interpretation labeled vars 2-33 as if they were W1_57 in cascade_aux's
mapping. F217 verifies the actual var-index → SHA-semantics mapping
in TRUE sr=61 by reading the encoder source.

## TRUE sr=61 encoder source

Found at `./encode_sr61_cascade.py`:

```python
state1, W1_pre = enc.precompute_state(M1)
state2, W2_pre = enc.precompute_state(M2)
assert state1[0] == state2[0], f"da[56] != 0: {state1[0]:#x} vs {state2[0]:#x}"

s1 = tuple(cnf.const_word(v) for v in state1)   # 0 vars (constants)
s2 = tuple(cnf.const_word(v) for v in state2)   # 0 vars

w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(3)]   # 3 free words
w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(3)]
```

**TRUE sr=61 uses n_free = 3** (free rounds 57, 58, 59), while
cascade_aux uses n_free = 4 (free rounds 57, 58, 59, 60). This
matches the SPEC: sr=61 has 3 free rounds, sr=60 has 4.

So the variable allocation for TRUE sr=61 is:

```
vars 2..33   = W1_57 (32 bits)   ← bit 0 of W1_57 at var 2
vars 34..65  = W1_58 (32 bits)
vars 66..97  = W1_59 (32 bits)
vars 98..129 = W2_57 (32 bits)
vars 130..161 = W2_58 (32 bits)
vars 162..193 = W2_59 (32 bits)
```

## Corrected F216 interpretation

```
TRUE sr=61 CNFs - shell counts by ACTUAL semantic round
                                      | W1_57 | W1_58 | W1_59 | W2_57 | W2_58 | W2_59
                                      | 2-33  | 34-65 | 66-97 | 98-129| 130-161|162-193
sr61_cascade_m09990bd2_f80000000_bit25 | 31/32 |  2/32 | (n/a) | (n/a) |  1/32 |  0/32
sr61_cascade_m11f9d4c7_fffffffff_bit26 | 28/32 |  1/32 |       |       |  2/32 |  0/32
sr61_cascade_m17149975_fffffffff_bit31 | 31/32 |  0/32 |       |       |  0/32 |  0/32
sr61_cascade_m17454e4b_fffffffff_bit29 | 29/32 |  1/32 |       |       |  1/32 |  0/32
sr61_cascade_m189b13c7_f80000000_bit31 | 30/32 |  2/32 |       |       |  0/32 |  0/32
```

(My F216 script also reported vars 66-97 and 98-129 ranges but didn't
slice them out for TRUE sr=61. Will rerun with corrected layout in
follow-up.)

## Headline finding

**The cascade-1 hardlock forces a DIFFERENT round in different encoders:**

| Encoder | Forced round | Strictness |
|---|---|---|
| cascade_aux (n_free=4) | **W1_58** | strict 32/32 universal |
| TRUE sr=61 (n_free=3) | **W1_57** | near-strict 28-31/32 |

This is a real structural difference. Cascade_aux's force-mode aux
vars create explicit Tseitin chains that fully reduce W1_58 to a
function of W1_57 (and W_pre constants). TRUE sr=61's encoder
encodes the cascade-1 relation at a different position — apparently
at W1_57 itself.

### Why W1_57 vs W1_58?

Both encoders work on cascade-eligible cands (da[56]=0). The
hardlock relation derives from this:

For cascade-1: a[57] = a[57]' (registers equal at round 57). The
SHA round equation a[t+1] = T1 + T2 = (...) + Σ0(a[t]) + ... means
that for a[57] = a[57]', specific constraints hold on
W[57] (and earlier) + the working-state register relations.

In cascade_aux (sr=60, 4 free rounds):
- The hardlock manifests as constraints on W1_58 = f(W1_57, W_pre)
- Specifically the round-58 schedule recurrence + hardlock interact
- Result: W1_58 entirely forced by W1_57 + constants

In TRUE sr=61 (sr=61, 3 free rounds):
- One fewer free round; the forced position shifts earlier
- Apparently the constraint structure at W1_57 is what gets force-
  reduced to a clean function of W_pre (not requiring later rounds)
- Result: W1_57 near-fully forced

This is a subtle but important encoder-design trade-off: **cascade_aux's
"sr=60 / 4 free rounds" puts the structurally-redundant word at W1_58;
TRUE sr=61's "sr=61 / 3 free rounds" puts it at W1_57**. The forced-round
shifts with the schedule level.

### Implication for F211 decoder

The decoder's "skip the forced word" optimization is round-specific
per encoder:

```
Encoder         | Skip in BP messages
cascade_aux     | W1_58 (vars 34-65)
TRUE sr=61      | W1_57 (vars 2-33)
```

If the decoder targets BOTH encoders, it should detect which round
is forced from each CNF's structure rather than hardcoding a var-
index range.

A general rule: **find the 32-var schedule cluster with ≥28/32 vars
in shell, and skip that word**. The script
`cross_validate_W1_58.py` already finds this empirically.

## Updated effective active-schedule for TRUE sr=61

For TRUE sr=61 (n_free=3, 6 schedule words total, 192 schedule bits):

| Word | bits in shell (mean across 5 CNFs) | bits free |
|---|---:|---:|
| W1_57 | 29.8 | 2.2 |
| W1_58 | 1.2 | 30.8 |
| W1_59 | (untested) | ~32 |
| W2_57 | (untested) | ~32 |
| W2_58 | 0.8 | 31.2 |
| W2_59 | 0.0 | 32.0 |

Estimated active schedule for TRUE sr=61: ~157-160 bits (M1: 65, M2: 95).

Compared to cascade_aux's ~177 bits, TRUE sr=61 has 17 bits less
"effective freedom" — partly because it has 1 fewer free round, but
also because more bits are forced by the encoder.

## Concrete next probes

(a) **Re-run F215 on TRUE sr=61 with proper round labels** including
    W1_59 / W2_57 — the F216 script omitted these. Likely vars 66-97
    are W1_59 and vars 98-129 are W2_57.

(b) **Check whether W1_59 / W2_57 are also partially forced**: the
    F216 results suggest vars 130-161 (W2_58) is mostly in core (only
    1-2 of 32 in shell), but I haven't checked W1_59 and W2_57. If
    those have intermediate force counts, the picture is richer.

(c) **Generic forced-cluster detector**: write a lightweight tool that,
    given any CNF, identifies which schedule-word var-range has the
    highest shell-elimination ratio. This becomes the decoder's
    "preprocess: skip the forced word" auto-detector.

## Discipline

- 0 SAT compute (encoder source reading + corrected interpretation)
- 0 solver runs
- F217 corrects F216's misapplied var-index labels by reading the
  actual TRUE sr=61 encoder
- The cascade-1 structural fact persists across encoders (one
  schedule word is near-fully forced) but the SPECIFIC ROUND
  shifts based on n_free / encoder choice
- Strategic implication: F211 decoder design should auto-detect the
  forced cluster rather than hardcoding W1_58

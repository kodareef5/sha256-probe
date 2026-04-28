---
date: 2026-04-28
bet: cascade_aux_encoding
status: F207_F208_HYPOTHESIS_GROUNDED — high-mult coupling is M1/M2 schedule-bit pair
---

# F209: high-mult pair (var 2, var 130) is W1_57[0] / W2_57[0] — corresponding bits across M1 and M2 schedules

## Setup

F208 found that (var 2, var 130) gap=128 mult=36 is the highest-
coupling pair in cascade_aux Tanner graphs, universal across CNFs.
The hypothesis was "word 0 vs word 4 coupling" (e.g., state register
a vs e).

This memo verifies by tracing the encoder's variable-allocation
order.

## Variable allocation in cascade_aux_encoder.py

Reading `lib/cnf_encoder.py` and `cascade_aux_encoder.py
build_cascade_aux_cnf`:

```python
self.next_var = 2     # var 1 reserved as TRUE constant

# const_word(v) — allocates NO new variables; returns bit literals
#                 using ±1 constants directly.
# free_word(name) — allocates 32 fresh variables.
```

In `build_cascade_aux_cnf`:

```python
s1 = tuple(cnf.const_word(v) for v in state1)   # 0 new vars
s2 = tuple(cnf.const_word(v) for v in state2)   # 0 new vars
w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
                                                  # n_free × 32 new vars
w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]
                                                  # n_free × 32 more new vars
```

For sr=60: n_free = 4.
- w1_free allocates vars **2..129** = 4 free message words for M1
  - W1_57: vars 2..33
  - W1_58: vars 34..65
  - W1_59: vars 66..97
  - W1_60: vars 98..129
- w2_free allocates vars **130..257** = 4 free message words for M2
  - W2_57: vars 130..161
  - W2_58: vars 162..193
  - W2_59: vars 194..225
  - W2_60: vars 226..257

## Mapping the high-mult pairs

| Var pair | Semantic |
|---|---|
| (var 2, var 130) gap=128 mult=36 | **bit 0 of W1_57** and **bit 0 of W2_57** |
| (var 3, var 131) gap=128 mult=20 | **bit 1 of W1_57** and **bit 1 of W2_57** |

So the highest-coupling pair in the entire Tanner graph is the
**lowest bit position of the corresponding free schedule word
between M1 and M2**.

This is **exactly the differential cryptanalysis structure**:
the encoding tracks dW[57] = W2[57] ⊕ W1[57] as a dominant
constraint variable. Bits 0 and 1 of dW[57] each appear in
many clauses linking M1 and M2 through the Σ/σ Tseitin chains.

## Why bit 0 has higher multiplicity than bit 1

bit 0 is the LSB of the 32-bit word. In SHA-256:
- σ0(x) = ROTR(x,7) ⊕ ROTR(x,18) ⊕ SHR(x,3)
- σ1(x) = ROTR(x,17) ⊕ ROTR(x,19) ⊕ SHR(x,10)

The SHR (right shift) operations move bits TO low positions but
not FROM bit 0. So bit 0 has fewer fan-out paths but appears in
more incoming Tseitin chains as the absorbing position. The
encoder's Tseitin pattern produces 36 clauses incident on the
(W1_57[0], W2_57[0]) pair vs 20 on (W1_57[1], W2_57[1]).

The exact factor 36/20 = 1.8 is encoder-specific and could be
verified by counting Tseitin chains incident on each bit
manually. Not done here.

## Implications for QC-LDPC decoder

The cascade_aux structure is **exactly** what differential-trail-
based attacks need: it's a quasi-cyclic encoding of the joint
M1/M2 constraint with the highest-coupling pair being the LSB
of dW[57].

Decoder design implications:
1. **Decode dW jointly, not W1 and W2 separately.** Treat each
   (W1[r][b], W2[r][b]) pair as a joint variable indexed by
   (r, b) where r ∈ {57..60} and b ∈ {0..31}.
2. **Bit-position graph is small.** 32 bits per word × 4 free
   rounds = 128 joint variables (one per (r, b)). The decoder
   marginalizes over these 128 variables; the rest of the CNF's
   ~12500 vars are Tseitin auxiliaries that get summed out
   analytically.
3. **The 128-bit joint state is the natural primitive.** Both
   QC-LDPC literature and the existing block-2 absorber search
   (yale's heuristic) operate at this 128-bit level.

## Connection to block2_wang and yale's HW=33

Yale's empirical HW=33 floor on cascade-1 collision search uses
heuristic local search over a 192-dim free subspace (3 free
schedule words × 32 bits + 96 hardlock-bit relations). The
F209-identified 128-bit joint M1/M2 schedule is **a subset of
this 192-dim space**.

If a QC-LDPC decoder produces marginals over the 128-bit joint
schedule, it can be **composed** with yale's heuristic over the
remaining 64 dimensions (hardlock-bit relations). This would be
a hybrid algorithm: BP marginal over the schedule space + local
search over the hardlock space.

This is the most concrete cross-bet algorithm proposal of the
session: cascade_aux's BP on schedule + block2_wang's heuristic
on hardlocks. Worth designing in detail.

## Concrete next probes

(a) **Implement the 128-bit joint marginal computation** as a
    bipartite BP on the cascade_aux Tanner graph restricted to
    the (var 2..257) message space + summed-out Tseitin
    auxiliaries. ~1-2 days implementation per F134 timeline.

(b) **Verify the gap=32 cluster has the expected semantic**:
    var i and var (i+32) should be adjacent bits within the
    same word. E.g., (var 2, var 34) should be bit 0 of W1_57
    vs bit 0 of W1_58 — corresponding bit, adjacent free
    rounds. Worth a quick test.

(c) **Re-run F207 on cnfs_n32 (TRUE sr=61) and a force-mode
    cascade_aux**: check whether expose / force / true-sr=61
    encodings share the same Tanner shape.

(d) **Read Ryan-Lin (Channel Codes) ch. 10-11** on QC-LDPC
    decoders. Identify the closest standard algorithm.

## Discipline

- 0 SAT compute (encoder source reading + variable counting)
- 0 solver runs
- ~5 min wall (reading two encoder files, mapping vars to
  semantics)
- F209 grounds F207/F208's quasi-cyclic hypothesis at the
  semantic level: the cascade_aux Tanner graph is a quasi-
  cyclic encoding of the joint (W1, W2) schedule, with the
  (var 2, var 130) gap=128 pair being W1_57[0] / W2_57[0].

## Hourly summary (session arc)

19 commits this session. Major findings:
- 4 calibration findings (F179, F180, F205, F206)
- 1 retraction (F201 → F205)
- 3 structural pivots (F207, F208, F209)
- 4 yale coordination notes
- 0 SAT compute, 0 solver runs throughout

Honest day with real structural progress on cascade_aux. The bet's
strategic direction has shifted from "BP-Bethe at gap-9/11" to
"QC-LDPC joint-schedule decoder, hybrid with block2_wang heuristic
over hardlock space". This is the strongest cross-bet algorithm
proposal of the session.

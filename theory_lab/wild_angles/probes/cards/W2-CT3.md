# W2-CT3 — Schedule as an IIR filter → poles predict the N=10 interference   ·   VERDICT: KILLED

**Card claim:** the schedule recurrence `W[i]=σ1(W[i-2])+W[i-7]+σ0(W[i-15])+W[i-16]` is a linear IIR filter; in the bit-rotation DFT basis it block-diagonalizes into N scalar sub-filters with poles `z(ω)`. A dominant pole whose natural period is commensurate with the word width selects the constructive-interference N (claimed **N=10**), and the empirical masked-schedule difference-echo envelope should **track the dominant pole modulus**.

**Probe run:** (a) numpy `roots` of the degree-16 schedule characteristic polynomial `z^16 − s1·z^14 − z^9 − s0·z − 1 = 0` per rotation-DFT frequency k (ROR caricature: `s1=ω^17+ω^19`, `s0=ω^7+ω^18`; plus a SHR-attenuation correction), giving the dominant pole modulus per N. (b) Empirical difference-echo: inject a 1-bit diff into the input words of a width-N schedule, run the **real** recurrence forward, measure mean `HW(δW[i])` vs round i, fit its per-round envelope rate. N = 8,10,11,12,16. Throttled.

**Result (numbers):**

| N | dom\|z\| (ROR-caric) | dom\|z\| (+SHR) | echo rate/round | echo plateau HW |
|---|---|---|---|---|
| 8 | 1.471 | **1.682** | 1.0071 | 3.98 |
| 10 | 1.471 | 1.668 | 1.0114 | 4.94 |
| 11 | 1.471 | 1.675 | 1.0120 | 5.46 |
| 12 | 1.471 | 1.659 | 1.0163 | 6.05 |
| 16 | 1.471 | 1.664 | **1.0178** | **8.05** |

- Dominant pole modulus is **~1.66–1.68, essentially flat across N** (caricature exactly constant at 1.471 for all N) — argmax over N is **N=8**, not N=10.
- Empirical echo rate is **~1.01, monotonically increasing in N** — argmax **N=16**. Echo plateau HW also monotone in N (argmax N=16).
- The two diverge by ~60× in growth magnitude (pole predicts |z|≈1.66 explosive growth; the real schedule echo barely grows at 1.01). Ratio echo/pole ≈ 0.60 across all N. **Opposite N-trends** (pole flat/slightly-down, echo up).
- At N=10 the per-frequency poles peak trivially at k=0 (DC, 1.668); no commensurate-period resonance singles out N=10.

**Kill_criterion:** "Dead if the echo envelope doesn't track the dominant pole modulus at small N (linearization too lossy)." — **fired? YES.**

**Verdict reasoning:** KILLED. The linearized IIR poles do not track the empirical difference echo: magnitudes are off by ~60× and the N-dependence runs in *opposite directions* (pole modulus flat-to-down vs echo rate up). And N=10 is not singled out by either object — the poles are flat in N (no commensurability peak) and the echo grows monotonically with N. The skeptic's worry is exactly what happened: SHR breaks the clean cyclic diagonalization, and the linearized poles (all |z|>1, predicting explosive divergence) bear no quantitative relation to the gently-growing real difference echo. The "N=10 is special" interference claim gets no support from a schedule-pole analysis.

**Cross-check / skeptic note:** The mismatch is robust to the SHR-correction toggle (caricature and +SHR give the same flat-in-N story). One could argue the *right* object is poles of the per-frequency map including the full nonlinear carry, but the card explicitly asks for the linear z-transform poles, and those simply don't predict the echo. Note also that "N=10 special" is itself only weakly grounded — the de58-growth table peaks at **N=12** (de58=512), not N=10, so the premise that N=10 is the constructive-interference width is shaky to begin with; this probe finds no pole-period mechanism for it either way.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W2-CT3.py`

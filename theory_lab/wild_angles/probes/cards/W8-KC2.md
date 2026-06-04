# W8-KC2 — Isostatic jamming -> de58 = the one floppy mode; 2^-2N = 2 surplus contacts   ·   VERDICT: KILLED

**Card claim:** Maxwell count DOF(r)−C(r) hits isostaticity (DOF==constraints) at exactly round 60 with ONE residual floppy mode (de58, "1-D in W57"); sr=61's two conditions = two surplus contacts → jammed, cost 2^-2N. Derives 2^-2N from counting.

**Probe run:** Measured DOF(r) = log2(realized difference-image size |de_r|) per tail round r=57..61, where the image is taken over all reachable free schedule words. Computed it three ways: (A) exact full sweep at N=4 (2^16, exact carry, faithful repo model via `_w5co_engine`); (B) 60k-sample lower bound at N=8; (C) repo-pinned `DE_SIZES` for N=4..32. Constraint count C(r)=r−56 (one da=0 cascade condition per tail round). Then checked the "2 surplus contacts" against the real N=10 gating data (g1,h) in `gap_rows.csv`. Throttled.

**Result (numbers):**
- **DOF(60) = log2|de60| = log2(1) = 0**, NOT ≈1. |de60|=1 always (exact N=4 sweep AND N=8 sub-sample confirm a single realized de60 value). Kill condition #1 fires.
- The named "one floppy mode" = de58, but **|de58| = 8 at N=8 → DOF=3.00**, and 1024 at N=32 → DOF=10.00 (= 2^hw(db56), prior finding #4). It is hw(db56) modes, NOT one. The "1 mode" appears ONLY at N=4 (|de58|=2, hw(db56)=1) — a small-N artifact.
- **No isostatic zero-crossing at round 60.** At N=4 the DOF−C ledger is (57:−1, 58:−1, 59:−3, 60:−4, 61:−1). DOF(r)≤3 throughout while C(r) grows 1→5; DOF−C is negative from the start and is most negative at round 60, never 0 there.
- **2 surplus contacts → 2^-2N:** gap_rows (N=10, 946 colls) confirms P(g1=0)=P(h=0)=0 in-sample (each ~2^-N) and sr=61 ⇔ g1=0 AND h=0 → rate 2^-2N. The count "2" matches ONLY by identifying the two contacts with the known conditions g1,h (rank-2, prior finding #3); the bare Maxwell DOF count does not derive it.

**Kill_criterion:** "DOF(60) not ≈1, or surplus at 61 ≠2, or the zero-crossing ≠ round 60" — **fired? YES (DOF(60)=0≠1, and no zero-crossing at 60).**

**Verdict reasoning:** Two of three kill clauses fire directly from the measured image sizes. The naive scalar Maxwell count the card explicitly asks for (DOF = image-entropy, the "non-matroid complement") does NOT reproduce "1 floppy mode at 60" (it gives 0), does NOT cross isostaticity at 60, and its de58 mode-count is hw(db56) (3–10 bits), not 1. The only piece that "lands" — 2 surplus contacts = 2^-2N — is a rename of the already-confirmed rank-2 (g1,h) fact (prior finding #3), not a derivation from counting. Per the NOTES rule, a rename is not a CONFIRMED. The card's own skeptic line (Maxwell ignores constraint redundancy) is exactly why the bare count fails.

**Cross-check / skeptic note:** The de-image sizes match the repo-pinned `DE_SIZES` ground truth at every N (exact at N=4; N=8 sub-sample hits |de58|≥8 = the pinned value), so this isn't a model-fidelity artifact. Could a *redundancy-corrected* (rigidity-matroid) count land on 60? Possibly — but that's the explicitly-disjoint rigidity-matroid card, and the card here demands the NAIVE count, which fails. de58's "floppy mode" interpretation is the closed de58 thread (prior #4): it's a carry-collapse/Maj-image count, not a single zero-energy mode.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W8-KC2.py`

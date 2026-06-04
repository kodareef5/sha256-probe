# W4-CS3 — The feed-forward collider d-separates the two halves → the de58 anomaly   ·   VERDICT: KILLED

**Card claim:** out = IV + state_64 is a collider; forcing a collision conditions on it, opening a back-door between the IV-path and the compression-path; **round 60** = where the opened path dominates (d-separation breaks), and de58 carries it.

**Probe run:** Reuse QI3's validated cascade (cascade-1 keeps da=0; de_k = e-register difference after round k; dh60=de57, dg60=de58, df60=de59, de60=de60). N=4,6,8,10; 8 held-cascade chambers each; full w57 sweep. Per chamber: (1) the *opening round* = first round whose internal-difference image jumps from 1 to >1 (the d-separation break-point); (2) whether de58 is the uniquely-open channel; (3) the DERIVATION/CONFIRM bar — does the framing yield |de58| = 2^hw(db56), or only re-observe de58 is open?

**Result (numbers):**
 - **Opening round = 58 in 8/8 chambers at EVERY N** (histogram {58: 8} at N=4,6,8,10). There is **no round-60-localized knee**.
 - **de58 uniquely open: 8/8 at every N** (de57=de59=de60 frozen at image size 1).
 - **|de58| = 2^hw(db56): only 3/8, 0/8, 1/8, 3/8** (N=4,6,8,10) on these random-fill chambers — the exact 2^hw law is the all-ones-fill MSB-kernel fact, so the framing does **not** even reproduce it here, let alone derive it. No round-60 quantity is produced.

**Kill_criterion:** "no round-localized jump, or de58 not special." — **fired? YES (both clauses).** The jump is at round 58 (the de58 slot itself, since dg60 ≡ de58 by the shift register), NOT a round-60 d-separation break as the card requires; and de58 is "special" only as the already-known open channel, with no new derivable property.

**Verdict reasoning:** KILLED as a **restate** of QI3 monogamy in do-calculus vocabulary. The card's two distinctive predictions both fail: (a) there is no emergent **round-60** collider-opening — the internal-difference image opens at round 58, which is just the de58 channel by definition (dg60 = de58), so the "round 60 = where the opened path dominates" claim is unsupported; (b) the framing **derives no new number** — it re-finds "de58 is the unique open channel" (exactly QI3's monogamy localization) and the de58 size is the carry/Maj image count (finding #4, CLOSED), not a d-separation quantity. Per the CONFIRM bar (NOTES + prior #4), a collider story that only relabels QI3's localization is a rename, not a mechanism.

**Cross-check / skeptic note:** The "opening at 58" is structural and robust (8/8 at all four N). One could object that conditioning on the *final* collision (rather than the cascade da=0 constraint) is the true collider — but on a deterministic core that conditioning is degenerate, and the realizable de_k support measured here is already the post-cascade-conditioned support, which is the natural collider-conditioned object. The 2^hw(db56) law failing to hold (3/8 etc.) on random-fill chambers underlines that even the one real de58 number is a kernel/fill-specific carry count, not something the d-sep framing predicts. de58 being the only open channel is real — but it is QI3's result, with no new prediction added.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-CS3.py`

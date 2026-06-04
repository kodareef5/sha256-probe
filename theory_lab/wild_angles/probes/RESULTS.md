# Probe sweep — results ledger

Execution pass over the 185 `wild_angles/` cards (top-to-bottom), running each card's cheapest small-N
probe and recording a **verdict against its own `kill_criterion`**. Per-card detail in `cards/<ID>.md`;
probe code in `cards/<ID>.py`. Method + ground truth in `NOTES.md`.

**Compute policy:** ≤3 concurrent subagents · every probe under `taskpolicy -b` (E-core/background QoS),
`OMP_NUM_THREADS=2` · N held small. Read-only toward `../../../sha256_review`. No SAT.

**Verdicts:** ✅ CONFIRMED (reproduced the predicted number) · 🟢 SURVIVES (kill didn't fire, not yet
positively confirmed) · ❌ KILLED (kill_criterion fired) · ⚪ INCONCLUSIVE (cheap probe can't decide) ·
🔧 REBUILD-NEEDED (needs a bigger shared kernel first).

## Tally
_(updated as the sweep proceeds)_

| | ✅ | 🟢 | ❌ | ⚪ | 🔧 | done / 185 |
|---|---|---|---|---|---|---|
| running total | 11 | 25 | 147 | 2 | 0 | **185 ✓** |

## Ledger

| card | verdict | finding (key number) | N |
|---|---|---|---|
| _— sweep begins below; newest appended per wave —_ | | | |

<!-- WAVE 1 -->
| W1-PH1 | ✅ CONFIRMED | g2=g1+h exact for all 946 N=10 collisions; entropy-rank 1.999 → 2^-2N is rank-2 | N=8,10 |
| W1-PH2 | ❌ KILLED | control-dim decays linearly (≈N/round), no knee, rotation-invariant (even identity-rot) | N=8,10,12 |
| W1-PH3 | ⚪ INCONCLUSIVE | GF(2) carry-coupling gives trivial c=1, not 0.74; real saddle needs complex Gauss-sum | N=6,8,10 |
| W1-PH4 | 🟢 SURVIVES | closure rate 2^-2N (−log2/N=2.013), P injective; but add-vs-XOR same rate (localization undistinguished) | N=8,10 |
| W1-PH5 | ❌ KILLED | no commensurability peak at N=10; N=10 is a yield trough (N=9 peak, 9.7×) | N=4..16 |
| W1-GE1 | ❌ KILLED | 43 active adders, 0 LM-incompatible (repo+probe): sections always glue, Ȟ¹≡0 everywhere | N=4–6, 32 |
| W1-GE2 | ❌ KILLED | residual D61(W57) is PRF-like; winding≠#zeros (68 zeros vs winding 32) | N=6–8 |
| W1-GE3 | 🟢 SURVIVES | b₀ branches (max 12/50) so kill misses, but 74/132 not reproduced; basin-growth −0.66 vs +0.74 | N=4,5 / 32 |
| W1-GE4 | ⚪ INCONCLUSIVE | modular feed-forward DOES act on diff (1500/1500) so not trivial; support not cheaply extractable | N=full |
| W1-GE5 | 🟢 SURVIVES | min Ollivier-Ricci κ vs hard_lb ρ=−0.31 (beats de58) BUT ≈de58 in disguise (ρ=−0.40); test(i) flat | N=32, 36 cands |
| W1-GE6 | ❌ KILLED | writhe of 946 real N=10 collisions ≡ random (0.02 sd separation); braid carries no collision signal | N=10 |
| W1-DY1 | ❌ KILLED | no normalization gives log2 λmax=0.74 (prob-norm λ≡1, count-norm λ=2^N); repo refit slope 0.673, spread 0.72–1.04 | N=4,6,8,10 |
| W1-DY2 | ❌ KILLED | Bowen root β*≡1 (vacuous); only "kink" is a leaky-matrix eigenvalue-crossover artifact | N=6,8 |
| W1-DY3 | 🟢 SURVIVES | robust seed-stable 2-D unstable subspace, but the "2" = #written lanes (a,e), not the sr-cliff's 2 | N=4,6,8,10 |
| W1-DY4 | ❌ KILLED | carry-SFT is the full shift (density 1.0) → shadowing trivial → no barrier certificate | N=6,8,10 |
| W1-IN1 | ❌ KILLED | pre-add modular diffs 2-adically uniform (KL≤0.0017); the "one non-injective adder" doesn't exist | N=4,6,8 |
| W1-IN2 | ❌ KILLED | support-product c=1 = universal Donoho–Stark floor (every function); robust support flat/shrinking — no barrier | N=4..16 |
| W1-IN3 | 🟢 SURVIVES | correction-word cost jumps 0→1/cond sharply at 60→61; matches 2^-2N two-condition law | N=4,6 |
| W1-IN4 | ❌ KILLED | round-cut boundary-rank defect ≡ 0 (volume-law); no area-law entanglement anisotropy | N=4,6 |
| W1-IN5 | ❌ KILLED | no low→full comm-rank transition; MITM is an upper-bound sweet-spot, not a barrier | N=4,6 |

<!-- WAVE 2 --> _(appended in completion order)_
| W2-CT1 | ❌ KILLED | 132 reproduces ONLY as deterministic census; real reachability corank 0/128, never 132 (FLAGSHIP) | N=32 |
| W2-CT2 | ❌ KILLED | reachability rank saturates at round 8 (=8N), no collapse; rotation-invariant | N=8,10,12 |
| W2-CT3 | ❌ KILLED | dominant pole \|z\|~1.66 flat in N; N=10 not singled out | N=8..16 |
| W2-CT4 | ❌ KILLED | extra_codim=0 (not 2N) on full-rank R; g1/h nonlinear-modular; slope 0.93 not 0.74 | N=10 |
| W2-CT5 | ❌ KILLED | GF(2) observability corank=0 at all N incl 32 (never 132); self-duality at 0/0 | N=8..32 |
| W2-NT1 | ❌ KILLED | no Euler product (overshoots R +24 bits @N=8); repo slope 0.673 not 0.74 | N=4,8 |
| W2-NT2 | ❌ KILLED | \|S(a,b)\| smooth unimodal, no Weil dichotomy; cancelling frac 0.947 not 132/256 | N=8 |
| W2-NT3 | ❌ KILLED | Weyl can't single out de58 (one #/N, shrinks); true law 2^hw(db56)=Maj-image | N=4,8,10 |
| W2-NT4 | ✅ CONFIRMED | g2=g1+h exact (946/946); 2D char sum factorizes C_g1·C_h null-calibrated; g1⊥h χ²/dof≈1 | N=8,10 |
| W2-NT5 | ❌ KILLED | collision vs random height identical (KS=0.057); 0x55 high not low height | N=8,10 |
| W2-RG1 | 🟢 SURVIVES | clause A (isostatic-60) KILLED: rank-incr [5,0,0,10,20,5]≠2, no knee; clause B codim-2 g2=g1+h 946/946 CONFIRMED | N=10 |
| W2-RG2 | ❌ KILLED | rigidity-matrix self-stress corank 128(pt)/0(generous), never 132; 132 only as carry census | N=32 |
| W2-RG3 | 🟢 SURVIVES | carry-coupling graph percolates (rank=2V−3); TRUE≡XOR-linear, carry edges redundant (div=0) | N=8..16 |
| W2-RG4 | 🟢 SURVIVES | sr61 codim-2 ✓ but the "2" is linear not quadratic; N=10 marginal-mode prediction failed (flat 0.67) | N=8,10,12 |
| W2-QI1 | ❌ KILLED | contextual magic rank saturates by round 4, flat after; no growth toward 59 | N=4,5,6 |
| W2-QI2 | ❌ KILLED | schedule code distance grows linearly +N/round, no jump@59; logical 16N≠124 | N=2,3,4 |
| W2-QI3 | 🟢 SURVIVES | all differential slack localizes to de58 (30/30 chambers), de57/59/60≡1; doesn't derive 2^hw(db56) | N=4..12 |
| W2-QI4 | ❌ KILLED | cumulative affine-piece χ saturates at round 3; Σlog2χ strictly linear, no explosion@59 | N=2,3,4 |
| W2-SO1 | ❌ KILLED | output HW~Binomial(k≈60-80,½); descent smooth, no min-cut at plateau; renames it | N=10 |
| W2-SO2 | ❌ KILLED | μ-sweep smooth (max jump 3.6 HW); no error threshold; high-μ Binomial = SO1 | N=10 |
| W2-SO3 | ❌ KILLED | carry cascade geometric (ξ<1 bit, subcritical branching); α≈3.8-5.4 drifts, ≠0.74 | N=8,10,12 |
| W2-SO4 | ❌ KILLED | GF(2) corank=0 not 132; unstable-mode energy on {a,b,e,f}=0.51=chance (5th category-error) | N=8,10 |
| W2-PC1 | ❌ KILLED | boundary expansion FLAT all rounds (0 / 1/N); the "61 flip" = free-word counting | N=4,6,8 |
| W2-PC2 | ❌ KILLED | PC/ANF degree FLAT (incr 0, not +2); refute-degree=1; 2 gens/round but no slope-2 | N=3..6 |
| W2-PC3 | ❌ KILLED | absorber separator = [h(z)==0], O(N)-gate modular zero-test; small circuit exists | N=3,4,5 |
| W2-PC4 | ❌ KILLED | pebble count flat=1 thru 61; Gaifman radius ≤2 (stays local), smooth growth | N=4,5 |
| W2-PC5 | ❌ KILLED | XOR-linearize→Gauss-trivial, NOT Tseitin; thesis BACKWARDS — carries ARE the obstruction | N=4,5 |

<!-- WAVE 3 --> _(appended in completion order)_
| W3-OT1 | ✅ CONFIRMED | forward push-forward concentrates at exponent 2.013→2^-2N, factorizes (ratio 0.92); Brenier non-regularity | N=8,10 |
| W3-OT2 | ❌ KILLED | Sinkhorn H/N monotone in ε, floors at 1.000, never crosses 0.74, no plateau | N=6,8 |
| W3-OT3 | ❌ KILLED | carry-HW OT map agrees with cascade 0-8%; cost degenerate (cost-0 off-translation pairs) | N=5,6 |
| W3-OT4 | ❌ KILLED | plateau+2-bit-trap real but locked-fraction 0.00-0.09≠0.52; no a,b,e,f hard core | N=6,8 |
| W3-OT5 | 🟢 SURVIVES | Hopcroft-Karp perfect matching at sr=60; Hall deficiency exponent 2.013→2^-2N | N=6,8 |
| W3-OT6 | ❌ KILLED | N=10 phase-coherence #9/11, yield peaks N=9; "rot 10∈Σ1" false (3rd N=10 kill) | N=4..14 |
| W3-IE1 | ❌ KILLED | 3-IET orbit-slope 0.166 not special (0.84σ); actual χ₁≈1.97/round, not 0.74/0.673 | N=4..14 |
| W3-IE2 | ❌ KILLED | monotone IET tower-height can't derive non-monotone hw(db56) (spike 9@12, drop 5@13); MAE 1.88 | N=4..32 |
| W3-IE3 | ✅ CONFIRMED | g1,h two distinct codim-1 endpoints P=2^-8 each, P(both)=2^-16, exp 2.013, indep 0.92 (6th 2^-2N) | N=8,10 |
| W3-IE4 | ❌ KILLED | carry-billiard orbit count flat=17 (slope 0); diverges from collisions; walls data-dependent | N=4..10 |
| W3-IE5 | ❌ KILLED | three-distance fires at 100% of N (no discrimination); misnames N=10 trough as spike | N=4..40 |
| W3-LL1 | 🟢 SURVIVES | S=e·p(d+1) crosses 1 at 60→61 but the crossing is degree-independent (fit, not LLL) | N=8,10 |
| W3-LL2 | ✅ CONFIRMED | Moser–Tardos emits VERIFIED sr60 collision (entropy-compression); diverges at sr61 (0 in 2^4N) | N=4,5 |
| W3-LL3 | ❌ KILLED | Shearer Z never flips sign (p→p² moves it wrong way); precondition corr=null not negative | N=8,10 |
| W3-LL4 | ❌ KILLED | tap-coverage r=0.08/0.17<0.3; N=10 rank-5/9 (N=9 peak); fixed-pts 14≠132 | N=4..20 |
| W3-LL5 | 🟢 SURVIVES | E[X] crosses 1 exactly at 60→61 (260/946 verified); but 0.74 sub-clause weak (slope 0.634) | N=4..12 |
| W3-CR1 | ❌ KILLED | difference-CRN is deficiency-zero (δ=0) all N; never 2, doesn't jump to 3 at r61 | N=3,4,5 |
| W3-CR2 | ✅ CONFIRMED | minimal siphons = {a},{e} = the two cascade heads exactly (core claim); moiety dim=0 not 132 | N=4,5,6 |
| W3-CR3 | ❌ KILLED | compressibility smooth ramp→plateau; saturation shoulder r≈10-14 fixed, not →60 | N=3,4,5 |
| W3-CR4 | ❌ KILLED | ADD fiber uniform=2^N; exp 1.0≠0.74; de58=2^hw not 2^N | N=3..8 |
| W3-CR5 | ❌ KILLED | mass-action net robustly injective→monostationary; ≤1 steady state, can't be 2^0.74N | N=3,4,5 |
| W3-CA1 | 🟢 SURVIVES | clean 3-way lens partition {GetPut→0,PutGet→g1,PutPut→h}, ratio→1.005; faithful RENAME of g1/h | N=8,10 |
| W3-CA2 | 🟢 SURVIVES | de58=2^hw(db56) exact but fibre not a subgroup/coset; lone-fibre restated, NOT derived | N=8..12 |
| W3-CA3 | ❌ KILLED | sound {def,⊤} AI over-marks to 192/256 (⊤ carry-contagious); real 132 is the census | N=32 |
| W3-CA4 | 🟢 SURVIVES | skeleton P is F₂-bijection (corank 0), ADD owns 100%; restates Davies–Meyer, no new content | N=4,6,8 |

| W3-GN1 | ❌ KILLED | odd-N counts NONZERO (N=5→356, N=7→3999); "period-2" was a fill=0 artifact; quasi-poly vacuous | N=5,6,7 |
| W3-GN2 | ❌ KILLED | per-round survivor factor is 2^-N (not 2^-2N); full tail 2^-3N; mis-locates the one-time sr-step cost | N=8,10 |
| W3-GN3 | ❌ KILLED | zonotope-generator corank=128 (tracks 4N), not 132; HW mode 128 not 74 (6th category error) | N=8,32 |
| W3-GN4 | ❌ KILLED | LP integrality gap O(1) (0.985→1.082, slope≈0); vertices ill-posed for modular system | N=8,10 |

<!-- WAVE 4 --> _(appended in completion order)_
| W4-FP1 | ❌ KILLED | free vs direct edge 31-51% off (no N-conv); per-round edge 2.97-5.01, not ~0.74 | N=4,6,8 |
| W4-FP2 | ❌ KILLED | real corank=0 everywhere incl N=32; SHR-removal 0→0; 132/0.516 absent | N=4..32 |
| W4-FP3 | ❌ KILLED | ARX freeness defect 0.29-0.70 non-monotone (no shrink); commutator ~2.3× | N=4..10 |
| W4-FP4 | ❌ KILLED | two-conditions real (946/946) but free-entropy χ misses 2N & de-pattern: rename | N=4,6,10 |
| W4-FP5 | ❌ KILLED | subordination FLAT across all 4 factors (spread 0); 2^hw(db56) non-monotone untrackable | N=4..10 |
| W4-IG1 | ❌ KILLED | honest Fisher corank=0/128 (not 132); "132" only at threshold τ≈0.49, no plateau (census in disguise) | N=32 |
| W4-IG2 | ✅ CONFIRMED | g2≡g1+h exact (rank-2); cross-Fisher→0; slope −2.006 (≠−1 rename), codim-2 (9th 2^-2N) | N=8,10 |
| W4-IG3 | ❌ KILLED | KL flat in de57..60; only "jump"=control-horizon entropy log2 2^N; Pythagoras holds both sides | N=8 |
| W4-IG4 | ❌ KILLED | cascade da-zeroing algebraic (no graded step); stall decouples from Fisher-flat=0 | N=8 |
| W4-IG5 | ❌ KILLED | 0.74=collision-count fit, indistinguishable from 0.673 (pair-spread 0.33); √det slope 8.4≠0.74 | N=8..12 |
| W4-CS1 | ❌ KILLED | do-orphan count=0/256 (every bit reachable); "132" only on control arm = census (category error) | N=32 |
| W4-CS2 | ❌ KILLED | instrument→target id rank=2 not 1; full id not a deficit (card inverted); 2^-2N real, mechanism wrong | N=8 |
| W4-CS3 | ❌ KILLED | de-image opens at round 58 not 60; no derivation; QI3 monogamy restated in do-calculus | N=4..10 |
| W4-CS4 | ❌ KILLED | counterfactual rigidity not elevated (Δ+0.002); rigid set={d,h}=complement of hard core, ≠132 | N=8 |
| W4-SH1 | ❌ KILLED | dim ker(L)=0 (not log2-count 5.6–11.5); λ1 RISES at 60→61 (ratio 0.70), no knee | N=2..12 |
| W4-SH2 | ❌ KILLED | real sheaf H¹=0 at every N (DAG→full row rank), ratio 0.000≠0.516, never 132 (10th category error) | N=2,3,4 |
| W4-SH3 | ❌ KILLED | harmonic proj keeps a/de60 energy (proportional share) ≠ cascade fixed pt; peaks sr=59 | N=2,3,4 |
| W4-SH4 | ❌ KILLED | spectral clause dead (N modes/round, ≠2,≠2N, no 60→61 knee); rank-2 g2=g1+h CONFIRMED 946/946 separately | N=3..10 |
| W4-SH5 | ❌ KILLED | carry filtration leaves ker FLAT (GF2-linear = net-zero); 0.74 unsharp (pair-spread 0.330) | N=3,4,5 |
| W4-LG1 | ❌ KILLED | string tension σ highest @r57-58, →0 @r60-63 (inverted); Wilson loops fail Z₂ gauge transform | N=8 |
| W4-LG2 | ❌ KILLED | slope 0.634 (matches 0.673 not 0.74), class-spread 0.63-1.04; geometric model = 4N−3.33N relabel | N=4..12 |
| W4-LG3 | 🟢 SURVIVES | de58 unique charged column (1,8,1,1)@N8; but restates 2^hw(db56), not derives | N=4,8 |
| W4-LG4 | ❌ KILLED | hard-core 23,28,46 = 4N+4 census (tracks WIDTH not topology), not 132 (11th category error) | N=4,5,8 |

<!-- WAVE 5 --> _(appended in completion order)_
| W5-KR1 | ❌ KILLED | first group element at r=55 (period 12), round-invariant; no jump at 61 | N=2,3 |
| W5-KR2 | ❌ KILLED | carry monoid group-free (flip-flop {K,P,G}, holonomy=1); does NOT derive 2^hw(db56) | N≥6 |
| W5-KR3 | ❌ KILLED | aperiodicity identical r=57..61, flickers per base-state; no 60→61 flip | N=2,3 |
| W5-KR4 | ❌ KILLED | γ(r)≥1 (m=12) from r=55 on; no first-group-factor-at-61, m not ~4 | N=2 |
| W5-KR5 | ❌ KILLED | rounds-only is a large permutation group (order 36864); group in rotations NOT ADD alone | N=2,3 |
| W5-ER1 | ❌ KILLED | R_eff partition INVERTED: recompute {a,b,e,f} are LOWEST-R (AUC=0.000), not high-R | N=8..12 |
| W5-ER2 | ❌ KILLED | matrix-tree slope wrong for all 9 weightings (−1.0..+1.2), none in [0.70,0.78] | N=4..12 |
| W5-ER3 | ❌ KILLED | two-conditions real (946/946) but W[60]-shortcut false (dim-drop=0, corr −0.015): rename | N=8,10 |
| W5-ER4 | ❌ KILLED | Foster budget uniform per-round (0.0154±0.0002); only "knee" is chain-terminus r62 (13th no-knee) | N=8,12 |
| W5-CO1 | ❌ KILLED | backward quotient blows up (1→32→3454→58362); colliding basin is singleton sink, not fat block | N=4 |
| W5-CO2 | ❌ KILLED | HM distinguishing set = log-sized set-cover (size 9, Jaccard 0.000); fraction falls 0.28→0.14 | N=4..10 |
| W5-CO3 | 🟢 SURVIVES | up-to-context shrinks 2^N/free-word, unsound at 61 (1337×); but 61 = message-schedule 2^-2N re-described | N=4 |
| W5-CO4 | ❌ KILLED | behavior map injective (fibers size 1); cross-path not pow-2; slope 0.60 not 0.74 | N=4,8 |
| W5-HC1 | ❌ KILLED | collision family 0% down-closed (no conflict-hypergraph exists); slope 0.93/0.99 not 0.74 | N=4..10 |
| W5-HC2 | ❌ KILLED | "bits common to all collisions"=0 hash bits; a,b carry ZERO diff (OPPOSITE of 132-story) | N=4..10 |
| W5-HC3 | ❌ KILLED | family shift-rigid (0/30366 in-family shifts); max-HW not preserved (24→30); no 74 | N=4..10 |
| W5-HC4 | ❌ KILLED | forced coords ≈0 (not 132); VC-dim=⌊log2|S|⌋ trivial; Sauer–Shelah ~1.0 not 0.74 | N=4..10 |
| W5-HC5 | ❌ KILLED | de-law RESTATED not derived; "petal+fiber=0.74" is a tautology = log2(#coll)/N = 0.93 | N=4..32 |
| W5-HY1 | ✅ CONFIRMED | CAT(0) empty-square codim-2 = 2^-2N: P(g1=0)=P(h=0)=2^-N, indep ratio 1.00, not coupled | N=4 (+repo 8,10) |
| W5-HY2 | ❌ KILLED | 49 collision-loops with NO feed-forward gluing; min-act=6 flat, no HW-1 systole | N=4 |
| W5-HY3 | ❌ KILLED | branching peaks round 57 not de58; δ=0 trivial (graph IS a tree, E=V−1) | N=4 |
| W5-HY4 | 🟢 SURVIVES | flat 4-cube (span=4N), 61 not co-bounding; but a faithful reframe of HY1, no new number | N=4..6 |
| W5-HY5 | ❌ KILLED | 132={a,b,e,f}+4dc=4N+4 census; fraction drifts to 0.5, not scale-invariant Gromov dim (13th) | N=4..8 |
| W5-HY6 | 🟢 SURVIVES | carry-on/off control derives |de58|=2^hw(db56) (carry-collapse) but re-derives closed thread | N=4 |
| W5-TO1 | 🟢 SURVIVES | δ_r=1.0 thru 60, crash to ~2^-N at 61; knee = free→schedule boundary (rename) | N=4 |
| W5-TO2 | 🟢 SURVIVES | ρ_r=μ(A∧B)/μ(A)μ(B)=1.0000 EXACT every round; reproduces g1⊥h, no fingerprint (rename) | N=4 |
| W5-TO3 | ❌ KILLED | deep-frac=1.0 (not .52), unimodal, count=8N (not 4N+4/132), reg-id unstable (14th category error) | N=4..8 |
| W5-TO4 | ❌ KILLED | sheaf gap maximal at r57, closes to 0 by r63; gluing RISES at 61 (inverted mechanism) | N=4 |
| W5-TO5 | ❌ KILLED | MITM fiber fattest at r57, faithful=1.0 AT and PAST 61 (inverted); = W1-IN5 | N=4 |

<!-- WAVE 6 --> _(appended in completion order)_
| W6-OC1 | ❌ KILLED | rank s_r=N (full) every round incl 61; no singular arc (‖·‖_F drop smooth) | N=8,10 |
| W6-OC2 | ✅ CONFIRMED | codim=2 "two conditions one control": w60 moves g1 but structurally CAN'T move h | N=8,10 |
| W6-OC3 | ❌ KILLED | costate kernel dim=4N exactly (128 at N=32={a,b,e,f}), scales with N, not a frozen 132 (15th) | N=8,10 |
| W6-OC4 | ❌ KILLED | costate rank=8N full every round incl 61; never degenerates (no conjugate point) | N=8,10 |
| W6-OC5 | ❌ KILLED | switching-gradient descent ~ random; dT1_61=0 surface true-but-useless as a guide | N=4,5 |
| W6-OM1 | ❌ KILLED | cube=1 solid cell r≤60 (free cascade); 260/260 cells at r61, no progressive explosion | N=4,8 |
| W6-OM2 | ❌ KILLED | Pila–Wilkie split degenerate (off-alg empty, de60≡0); LS slope 0.617 not 0.74 | N=4..12 |
| W6-OM3 | ❌ KILLED | alt(r≤60)=0; alt/m DECREASES 0.13→0.03 with N; no block shattered — no IP | N=4..8 |
| W6-OM4 | ❌ KILLED | de58 law re-derives but mass-share 0.18→0.37 unstable (2^hw non-monotone); restate | N=4..32 |
| W6-OM5 | ❌ KILLED | ANF degree 0(free)→N exactly at r61; no bounded-QE-depth regime (dense ANF) | N=4..8 |
| W6-OM6 | ❌ KILLED | r61 membership all-1 (tame, H=0); sieve only at r63 terminus — wall misplaced | N=4..8 |
| W6-FR1 | ❌ KILLED | honest carry-branching = 2^0.92, collision base 2^1.0, not 0.757; LAST 0.74 candidate dies | N=4..10 |
| W6-FR2 | ✅ CONFIRMED | g1=0,h=0 each EXACTLY 2^-N, independent R=0.97; OSC holds thru 60, fails at 61 → 2^-2N | N=4..10 |
| W6-FR3 | ❌ KILLED | width-10 collisions nest into width-8 with 0.0000 overlap; no scaling map (de58 carry-collapsed) | N=8,10 |
| W6-FR4 | ❌ KILLED | hard-core fraction drifts 0.72→0.66→0.5 (width census); middle band integer count=1 | N=8..12 |
| W6-MA1 | ❌ KILLED | honest matroid corank width-scaling (N/4N/8N+4N), never 132; 128@N=32 (FLAGSHIP category error, 16th) | N=8..32 |
| W6-MA2 | ❌ KILLED | linear collision code C=ker(A) TRIVIAL (dim 0); no codewords, count all carry-nonlinear; slope 0.696 | N=4..10 |
| W6-MA3 | ✅ CONFIRMED | 2^-2N = corank 1→2 on {g1,h}: g2=g1+h, g1⊥h r=1.005, not proportional (chirotope decorative) | N=8,10 |
| W6-MA4 | ❌ KILLED | λ flat-1 through 61 (no knee); free/sched connector = 2N not 2 (no Tutte 2-separation) | N=4,6 |

<!-- WAVE 7 --> _(appended in completion order)_
| W7-CG1 | ❌ KILLED | de57/59 nonzero (not 0-heaps); de58 = group-free carry image (no nimber), moved by w57 not w58 | N=8,10 |
| W7-CG2 | ❌ KILLED | temperature ≡ 0 at free rounds 57-60 (flat free-cascade); crossing at 57 not 61, no cool-down | N=8,10 |
| W7-CG3 | ❌ KILLED | g2=g1+h 946/946 = rename; but MEASURES sr=62 = 2^-4N (not card's 2^-3N) — Batch-B forward test! | N=8,10 |
| W7-CG4 | ❌ KILLED | normal/misère P-sets coincide; wall = schedule identity g1=0∧h=0, orientation-independent (intrinsic) | N=8,10 |
| W7-CG5 | ❌ KILLED | de58 produced once (singleton move-set); no size-indexed nim-sequence → octal undefined | N=8,10 |
| W7-CG6 | ❌ KILLED | mean HW=½·#soft (hardcore stuck-0) = binomial restate; spread SUPER-binomial (ratio 1.21) | N=8,10 |
| W7-FC1 | ❌ KILLED | meet-irreducible attrs = 6N-1 (23@N4,47@N8) over {a,b,c,e,f,g}, not {a,b,e,f}; dc,dg irreducible (17th) | N=4,8 |
| W7-FC2 | ❌ KILLED | below-60 |B|=2 flat; sr=61 ×2 but a generic indep pair gives ×2.5 (no 60→61 kink) | N=8,10 |
| W7-FC3 | ❌ KILLED | DG base size-2 stems already below 60; 2^-2N control also needs size-2 (rename of two-conditions) | N=8,10 |
| W7-FC4 | ❌ KILLED | σ=1.0 for ALL de-rounds incl de58 (no separation); growth 2^0.5N; derives nothing | N=8,10 |
| W7-FC5 | ❌ KILLED | double-arrows uniform across all 5 cols (3,3,3,3,3); target share=0.40=col-proportion, no localization | N=8,10 |
| W7-RA1 | ❌ KILLED | frozen carry cells 520-553 (≠132); 448=trivial LSB col, rest width-scaling + K-artifact (18th) | N=4..12 |
| W7-RA2 | ❌ KILLED | zero-diff line only at n*=1, independent of round count; generic cube has no line | N=8 |
| W7-RA3 | ❌ KILLED | (g1,h) indep~1.0 BUT Szemerédi variance-spike ABSENT (VAR/null 1.71→1, uniform) — rename | N=6..10 |
| W7-RA4 | ❌ KILLED | de58 AP-excess vanishes vs same-affine-span null; dominant d = free-bit translate, unstable | N=4..11 |
| W7-RA5 | ❌ KILLED | Ramsey clique s≤4 (trivial, K~4); comparable-to-64-rounds clique needs K~2^32 (dwarfs SHA) | N=4..10 |
| W7-QW1 | ❌ KILLED | Szegedy gap is a relabel (rev_gap=0); "doubling" ratio 2.0000 = the pre-existing 2^-2N, not a gap | N=6..10 |
| W7-QW2 | ❌ KILLED | log2 s_max(D)=0 (edge pinned at 1, mass-conserving), ≠0.74; = Perron(P) relabel | N=6..10 |
| W7-QW3 | ❌ KILLED | honest discriminant corank=0 (slides 0→0.625 w/ threshold); 132 is output census (19th) | N=6..10 |
| W7-QW4 | ❌ KILLED | no s₁−s₂ dip at N=10 (it's a gap MAX); N=10 yield trough (N=9/N=10=2.68×) — 5th N=10 kill | N=8..12 |
| W7-QW5 | 🟢 SURVIVES | α-step at 58 = ½log2|de58|/N + 2^-2N cliff at 61, but restates de58 law, derives nothing | N=8..14 |
| W7-NS2 | ❌ KILLED | f,h→0.5 (width/HW) but d→1.0 (growth exp); no common Loeb limit (spread 0.49 flat) | N=6..14 |
| W7-NS3 | 🟢 SURVIVES | clean internal/external split: identities 6000/6000 internal, de58/growth external (a real partition) | N=6..14 |
| W7-NS1 | ❌ KILLED | wall is a clean integer STEP not a cut: cond1=+1, cond2=+2, increment=+2.000 all N | N=6..10 |
| W7-NS4 | ❌ KILLED | no sharp round: de flips at 58, at 61 only free-word count drops 1→0 (pure DOF/counting) | N=6..14 |

<!-- WAVE 8 --> _(appended in completion order)_
| W8-CL1 | ❌ KILLED | casoff TOTAL (no division) all rounds 57-62; pole_order(61)=0 (cascade Laurent throughout) | N=8..12 |
| W8-CL2 | 🟢 SURVIVES | sr=62=2^-4N confirmed (log2=-4N) but g1,h mixed-sign (signfrac~0.5), not c-vectors — rename | N=8..12 |
| W8-CL3 | ❌ KILLED | de-transfer nilpotent shift; #pos maximal minors=0 ≠ log2|de58|; TNN doesn't derive 2^hw | N=8..12 |
| W8-CL4 | ❌ KILLED | exchange graph 93-94% isolated (mean deg 0.07), not regular; 0.74 only asymptotic slope | N=8,10 |
| W8-WE1 | 🟢 SURVIVES | rename (Q=0 @57-60, Q=2 @61); BUT measures sr=62=2^-3N (free-word exhaustion) — CONFLICTS w/ CG3/CL2's 2^-4N ⚠ | N=5,8 |
| W8-WE2 | ❌ KILLED | DFS backtracking certifies strong sr=61 (g1=g2=0) with 5-state memory; no WKL→ACA jump | N=5,8 |
| W8-RD1 | ❌ KILLED | R(0)=log2(#colls), finite-N density ~1.0 not 0.74; de58 channel yields 0 collision codewords | N=8..12 |
| W8-RD2 | ❌ KILLED | rename: +2N gap = −log2 P(A∧B) for indep g1,h; sr=62=2^-4N reproduced (32/40 bits) [3-1 vs WE1] | N=8,10 |
| W8-RD3 | ❌ KILLED | "132" = width-scaling 4N+4 census ({a,b,e,f}=4N); not basis-indep IB dim (20th category error) | N=8..12 |
| W8-KC1 | ❌ KILLED | active-diff 2-core width-scaling (|2-core(60)|=1103≈34W), no 60→61 collapse (0.97×) | N=32 |
| W8-KC2 | ❌ KILLED | DOF(60)=log2|de60|=0 not 1; de58 DOF=hw(db56) (3@N8); no isostasis@60; rename | N=4..32 |
| W8-KC3 | ❌ KILLED | frozen-fraction=0/32 (not 0.516), entropy 1.003 (not 0.74), 257 clusters | N=8 |
| W8-KC4 | ❌ KILLED | flat k_max=5 (no nucleation); inner shell=384 wires≠128; contiguity 0.98→0.15 on shuffle (AP artifact) | N=32 |

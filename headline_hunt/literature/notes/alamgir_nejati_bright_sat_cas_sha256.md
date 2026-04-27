# Alamgir / Nejati / Bright — SAT/CAS for SHA-256 collision search

**Cite as**: Alamgir, M., Nejati, S., Bright, C. *"SAT/CAS Approach to
SHA-256 Cryptanalysis"* (2024). Likely arXiv:2406.20072 or ePrint
2024/2017 — IDENTIFIER STILL AMBIGUOUS, both candidates plausible.

**Read status**: STRUCTURAL_SUMMARY based on public knowledge of
SAT+CAS hybrid systems and Curtis Bright's research line (2018-2024
on combinatorial search via SAT solvers + computer algebra systems).

## Position in the literature

The SAT+CAS approach is a third pillar alongside Wang/Yin/Yu 2005
hand-crafted differentials, dCR 2006 automated DC search, and Mouha
2010+ MILP. It combines:
- **SAT solver** (kissat, CaDiCaL, MapleSAT) for combinatorial
  enumeration
- **Computer algebra system** (Maple, Mathematica, SageMath) for
  algebraic constraint reasoning
- **External programmatic propagator** (IPASIR-UP API) connecting
  the two

For SHA-256 cryptanalysis specifically, SAT+CAS approaches:
1. Encode the SHA-256 collision search as a SAT problem (standard
   CNF of SHA-256 + cascade-aux constraints)
2. Use external CAS to detect impossible state combinations early
   (e.g., modular-add carry conflicts that a pure SAT solver
   wouldn't see until deep search)
3. Feed CAS-derived inferences back to SAT via IPASIR-UP propagator
   callbacks

## IPASIR-UP API Survey

IPASIR-UP (User Propagator) is the standard external-propagator
interface for modern CDCL solvers. Implemented in CaDiCaL 1.5+ and
MapleSAT. NOT in vanilla kissat (kissat doesn't support external
propagators).

### IPASIR-UP API surface

The propagator implements callbacks invoked by the solver during
CDCL search:

```cpp
class ExternalPropagator {
public:
    // Called when a literal becomes assigned (true)
    virtual void notify_assignment(int lit, bool is_fixed) = 0;
    
    // Called when CDCL backtracks; propagator must undo state
    virtual void notify_new_decision_level() = 0;
    virtual void notify_backtrack(size_t new_level) = 0;
    
    // Called to ask if propagator wants to add learned clauses
    virtual int cb_decide() = 0;
    
    // Called to ask for unit propagation that solver missed
    virtual int cb_propagate() = 0;
    
    // Called to provide a reason clause for a propagation
    virtual int cb_add_reason_clause_lit(int propagated_lit) = 0;
    
    // Called when SAT/UNSAT determined; propagator can override
    virtual bool cb_check_found_model(const std::vector<int>& model) = 0;
};
```

The solver registers the propagator and calls `notify_assignment`
on every variable assignment. The propagator maintains its own
internal state (e.g., current modular adder carry chains) and can:
- **Force literals**: via cb_propagate()
- **Force decisions**: via cb_decide()
- **Add learned clauses**: via cb_add_external_clause()
- **Reject a model**: via cb_check_found_model() returning false

### Performance considerations

- **Backtracking cost**: every notify_backtrack must restore
  propagator state in O(level_diff). For SHA-256 with ~10k vars,
  this can be O(10^4) per backtrack call. Implementations use
  trail-based reconstruction.
- **Propagation cost**: cb_propagate is called frequently. Must be
  O(log N) or better per call to avoid >10x slowdown.
- **Reason clauses**: must be valid (entailed by current trail).
  Each reason clause is added as a learned clause; bloated reasons
  blow up the clause database.

## Connection to project's programmatic_sat_propagator bet

The closed bet (status: closed, BET.yaml records ENGINEERING-COMPLETE
state) implemented a SHA-256/cascade-aware external propagator on
CaDiCaL 3.0.0. Empirical findings from that work:

1. **Rule 4@r=62 fires SAME number of times at 50k and 500k conflicts**
   (e.g., bit-19: 209/209, bit-25: 249/249). Propagator fires are
   FRONT-LOADED in the first ~50k conflicts.

2. **Mode B cascade_aux preprocessing achieves ~80% of the
   propagator's effect with 10% of the complexity**. So the
   propagator's value-add is marginal vs cleaner CNF encoding.

3. **1.9x wall-time overhead** at all measured budgets. Net negative
   on solve time.

The bet was correctly closed as "marginal value vs Mode B," with
Rule 6 (modular Theorem 4 with two varying inputs) identified as
the only remaining differentiator.

## Connection to Alamgir et al.'s likely contribution

Without direct access to the paper, the inferable contribution is:

1. **More aggressive CAS-side reasoning**: instead of just propagating
   carry constraints (our project's approach), use Maple/SageMath to
   detect higher-order algebraic infeasibilities in the residual
   structure.

2. **Finite-field representations**: SHA-256 register state as
   GF(2)^32 vectors; CAS computes Gröbner basis or similar to detect
   infeasible bit-patterns.

3. **Hybrid restart strategy**: SAT-CDCL runs for N conflicts → CAS
   analyzes failed branches → returns infeasibility certificates →
   SAT continues with new clauses. The CAS phase prunes branches
   that pure CDCL would re-explore.

These approaches likely require LARGER per-call overhead than our
"per-assignment" propagator, but the reasoning is DEEPER (algebraic
vs bit-level).

## Why this matters for our paper

For paper Section 5 (or 6), the SAT/CAS approach is the natural
extension of our SAT-only work. The project closed
programmatic_sat_propagator with a marginal-value verdict; Alamgir
et al. likely reports more substantive gains via deeper algebraic
reasoning.

If the paper's contribution is "structural sr=60 result without
algebraic propagation," we should explicitly note that Alamgir et al.
represents a parallel and possibly faster track on the SAT/CAS side.

## What to verify in the actual paper

1. **Identifier**: arXiv:2406.20072 or ePrint 2024/2017?
2. **CAS used**: Maple, SageMath, or custom?
3. **Quantitative speedup**: how many bits / hours saved on round-N
   SHA-256?
4. **N range tested**: do they reach round 56? 60? 63?
5. **Cascade-aware encoding**: do they use cascade-1/cascade-2 or
   plain CNF?
6. **Compatibility with our F-series**: would their CAS detect the
   42% kernel-invariance from our project's carry_automaton work?

## Action items for paper integration

1. **Section 2 (Background)**: cite as the SAT+CAS analog. Note our
   project's parallel programmatic_sat_propagator work and its
   marginal-value verdict.

2. **Section 6 (Discussion)**: position this as future work — if
   their paper claims sub-conflict gains on round-N SHA-256, our
   sr=60 result is independently obtained and might cross-validate.

## Action items for the project (concrete)

1. **Locate the actual paper**. Try arXiv:2406.20072 first; if 404,
   try ePrint 2024/2017. Update literature.yaml with verified ID.

2. **If they report round-60+ SAT-based collision findings**: this
   is HEADLINE-COMPETITION territory. The project's ~10 hours of
   sr=60 cascade_aux Mode A wall + LM analysis must be compared.

3. **If they DON'T report sr=60**: our cascade_aux + sr=60 framework
   is more advanced than their SAT/CAS approach (since we already
   reached sr=60 SAT). Differentiator: schedule-relaxed model is
   strictly stronger than round-reduced model at N=64.

## Status

- Read status: STRUCTURAL_SUMMARY based on training-cutoff knowledge
  of SAT+CAS systems. PDF read STILL PENDING (identifier ambiguous).
- This note unblocks the "alamgir_nejati_bright_sat_cas_sha256"
  literature entry for current programmatic_sat_propagator
  cross-reference work.

EVIDENCE-level: HYPOTHESIS — based on indirect references to SAT+CAS
methodology in the field. Direct PDF read needed to harden specific
quantitative claims.

# RETRACTION: SPEC bug claim was wrong — cert satisfies XOR-equality trivially

The previous writeup `20260425_theorem4_pinpoint.md` flagged a "POSSIBLE BUG" in cascade_aux Mode-B SPEC: the encoder enforces `dA[61][i] = dE[61][i]` (XOR-equality) but Theorem 4 is genuinely modular-equality, and only 0.04% of cascade-held random samples satisfy XOR-equality at r=61.

I claimed this might explain why all Mode B kissat runs TIMEOUT'd.

**That claim is incorrect.** Empirical verification:

## Cert run (verified sr=60 collision: M[0]=0x17149975, W1[57..60] from certificate)

| round | da_xor | da_mod | de_xor | de_mod | XOR-eq | MOD-eq |
|---:|---|---|---|---|---|---|
| r=57 | 0x00000000 | 0x00000000 | 0x10114230 | 0xefef3e30 | no | no |
| r=58 | 0x00000000 | 0x00000000 | 0x0e34accc | 0x0e2ca4bc | no | no |
| r=59 | 0x00000000 | 0x00000000 | 0x8b57c367 | 0x754fbd5d | no | no |
| **r=60** | **0** | **0** | **0** | **0** | **YES** | **YES** |
| r=61 | 0 | 0 | 0 | 0 | YES | YES |
| r=62 | 0 | 0 | 0 | 0 | YES | YES |
| r=63 | 0 | 0 | 0 | 0 | YES | YES |

At the cert, BOTH da and de become zero at round 60 (cascade-2 forces de60=0; cascade-1 already had da57..60=0). From r=60 onward, da=de=0 — making XOR-equality and MOD-equality both trivially hold.

## Why the previous claim was wrong

Theorem 4 says da_61 = de_61 *modular*. For RANDOM cascade-held residuals, this means random nonzero modular value with random XOR pattern → XOR-equality very rare (0.04%).

But for the COLLISION-finding context (the actual goal of Mode B), the combined constraints `dE[61] = 0` (Theorem 3) and `dA[61] = dE[61]` (Theorem 4) force `dA[61] = dE[61] = 0`. At zero, XOR-equality and modular-equality coincide trivially. The cert is admitted.

So **Mode B's XOR-equality encoding is NOT a bug** for collision-finding. The 99.96% of cascade-held random samples that don't satisfy XOR-equality at r=61 are NOT collision solutions — they have non-zero da, de that diverge in XOR pattern but happen to match modularly.

## Why Mode B kissat still TIMEOUT'd

Some other reason. The 90-min budget (5400s) was insufficient regardless of the encoding choice, given the 12-hour solve time of the standard encoding. The "≥10x speedup" claim of the SPEC remains empirically refuted at 90-min budget — but NOT because of the XOR-vs-modular issue.

## Lesson

Always verify a claimed bug against the verified-correct cert before flagging it. The 5-minute empirical check would have caught this.

## Status

- 20260425_theorem4_pinpoint.md: contains a "POSSIBLE BUG FLAGGED" section that is now SUPERSEDED by this retraction. The Theorem 4 boundary-pinpoint observation (r=61 modular = 100%, r=62 = 0%) STANDS — that's an independent empirical finding still valid.
- The cascade_aux SPEC's Mode B encoding is correct for collision-finding.
- The Mode B "≥10x SAT speedup" claim remains separately refuted at 90-min budget; needs a longer-budget test for definitive answer.

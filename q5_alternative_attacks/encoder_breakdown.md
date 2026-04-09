# sr=60 CNF Encoder Breakdown

For 0x17149975 fill=0xff sr=60 (the verified SAT instance):

| Gate type | Count | Clauses each | Subtotal | % of total |
|---|---|---|---|---|
| XOR | 6902 | 4 | 27608 | 60% |
| MAJ | 2109 | 6 | 12654 | 27% |
| FA (xor+maj) | 2125 | (already counted) | — | — |
| MUX (Ch) | 320 | 4 | 1280 | 3% |
| AND | 703 | 3 | 2109 | 5% |
| Constant folds | 4694 | 0 | (saved) | — |

**Total: 10988 vars, 46255 clauses**

## Where the XOR cost comes from

Each `Sigma0` and `Sigma1` invocation does 3 rotations XORed together
(via `xor_word` which is 32 xor2 gates per call).
- Sigma0 / Sigma1: 64 xor2 gates each = ~256 clauses each
- Per round: 1 Sigma0 + 1 Sigma1 = ~512 clauses
- 7 rounds × 2 messages = 14 invocations × 512 = ~7168 clauses
- Plus sigma0/sigma1 in schedule: similar
- Plus XOR2 chains in adders (full adders use XOR3 which is 2 XOR2)

## Potential optimizations (per Issue #10)

1. **Direct XOR3 encoding**: A XOR B XOR C = R can be encoded in 4
   "parity check" clauses (size 4 each = 16 literals) instead of
   2 XOR2 chained = 8 clauses (size 3 each = 24 literals). Net: similar
   clause count but fewer literals and one fewer auxiliary variable per
   XOR3. ~4000 vars saved across the encoding.

2. **CSE for Sigma**: Sigma0(a) and Sigma0(a') don't share, but
   ROTR(a, k1) and ROTR(a, k2) for different k could potentially share
   bit-position groups. Probably not enough commonality.

3. **Differential encoding**: Encode (value, diff) pairs directly per
   Li et al. EUROCRYPT 2024 signed-difference approach. The constraint
   tables in `q5_alternative_attacks/signed_diff_encoder.py` partially
   implement this.

4. **Boolean function models per eprint 2026/232**: Improved Ch/Maj
   encodings that "accurately capture bit conditions". Without access
   to the paper, would need to derive from first principles.

5. **Use IPASIR-UP propagator** (CaDiCaL-SHA256): Carry constraint
   propagation. Already built at /tmp/cadical-sha256/build/cadical
   with CUSTOM_PROP=true. May or may not activate on our CNF
   (depends on whether variable naming matches Nejati's convention).

## Action items

- Try direct XOR3 encoding (low risk, possible 5-10% size reduction)
- Verify whether CaDiCaL-SHA256 propagator activates on our CNF
- Read eprint 2026/232 if accessible

## Evidence level

**EVIDENCE**: counts derived from running encoder on verified SAT CNF.
Not benchmarked against alternative encodings yet.

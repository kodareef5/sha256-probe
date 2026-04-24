# Certificates

One YAML per verified collision/near-collision. Schema (informal):

```yaml
id: <result-id>
sr_level: 60 | 61 | ...
n: 32
m0: "0x..."
fill: "0x..."
kernel: { word_pair: [a, b], bit: N, diff_hex: "0x..." }
W1: ["0x...", ...]            # round-by-round W difference
hash: "<output sha256 hex>"
mechanism: "<short prose>"
solver: { name, version, seed }
solve_time_seconds: <float>
verified_by_machines: [<list>]
verification_log: <path>
notes: <free text>
```

Each certificate must be re-verifiable from this YAML alone.

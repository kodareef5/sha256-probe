#!/usr/bin/env python3
"""Run de58 image-size measurement across ALL 36 registered candidates.
Outputs JSONL records sorted by entropy ascending (most-concentrated first).
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from de58_histogram import candidate_de58_histogram

import yaml
import math


def main(n_samples=1<<18):  # 262k samples ≈ 2.5s/candidate
    with open(os.path.join(HERE, '..', '..', 'registry', 'candidates.yaml')) as f:
        cands = yaml.safe_load(f)

    results = []
    print(f"# de58 image-size sweep across {len(cands)} registered candidates", file=sys.stderr)
    print(f"# n_samples per candidate: {n_samples}", file=sys.stderr)

    for c in cands:
        m0 = int(c['m0'], 16)
        fill = int(c['fill'], 16)
        bit = c['kernel']['bit']
        t0 = time.time()
        result = candidate_de58_histogram(m0, fill, bit, n_samples=n_samples, seed=42)
        elapsed = time.time() - t0
        if result is None:
            results.append({"id": c['id'], "error": "not cascade-eligible", "elapsed_s": elapsed})
            continue
        counts, n_held = result
        n = sum(counts.values())
        distinct = len(counts)
        entropy = -sum((cnt/n) * math.log2(cnt/n) for cnt in counts.values() if cnt > 0)
        rec = {
            "id": c['id'], "m0": c['m0'], "fill": c['fill'], "bit": bit,
            "distinct": distinct,
            "n_samples": n_held,
            "entropy_bits": round(entropy, 2),
            "log2_image": round(math.log2(distinct) if distinct > 0 else 0, 2),
            "compression_bits": round(32 - math.log2(distinct) if distinct > 0 else 0, 2),
            "elapsed_s": round(elapsed, 2),
        }
        results.append(rec)
        print(json.dumps(rec))
        sys.stdout.flush()

    # Sort and report
    results.sort(key=lambda r: r.get('log2_image', 99))
    print("\n# === RANKED BY COMPRESSION (smallest de58 image first) ===", file=sys.stderr)
    for r in results:
        if 'error' in r:
            print(f"# {r['id']}: ERROR {r['error']}", file=sys.stderr)
        else:
            print(f"# {r['compression_bits']:5.1f} bits compress | "
                  f"image=2^{r['log2_image']:5.2f} = {r['distinct']:>7} | {r['id']}", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
audit_kernel_preservation.py — scan search-result JSONs for cascade-1 kernel
drift artifacts. Catches the F322/F333 class of bug before it propagates.

SCOPE: this tool is for **block-1 cascade-1 pair search** results, where
(M1, M2) should satisfy the cascade-1 kernel structure. Examples of bets
in scope:
  - block2_wang search_seeded_atlas / search_kernel_preserving / atlas-loss
    runs (F315-F322, F328+, F315/F316/F317/F318/F319/F320/F321/F322/F328+).
    These use atlas_evaluate which treats (M1, M2) as a block-1 cascade-1 pair.
  - math_principles atlas-loss / Pareto-front / repair probes (F344-F368).
    Same atlas_evaluate semantics.

OUT OF SCOPE: block-2 absorber search results (block2_wang F101-F200 chunked-
scan and basin search). Those store BLOCK-2 (M1, M2) where the absorber search
is exactly trying to find a block-2 pair that propagates the block-1 cascade-1
diff to a small chain output diff. Block-2 (M1, M2) are NOT supposed to follow
the cascade-1 kernel structure — they're supposed to ABSORB it.

Use the `--block-context block1|block2` flag to label the audit explicitly.
For block2 context, only PASS / NO_DIFF / DRIFT counts are reported with the
note that DRIFT is expected and acceptable for block-2 absorber search.

Cascade-1 kernel for word_pair (0, 9) at bit b (block-1 idx=0..n cands):
  M1[0] ^ M2[0] = 1 << b
  M1[9] ^ M2[9] = 1 << b
  M1[i] ^ M2[i] = 0 for all i ∈ {1..8, 10..15}

For each (M1, M2) pair found in a JSON, this tool reports:
  - PASS: pair satisfies cascade-1 kernel for SOME registered candidate
  - DRIFT: pair has nonzero diff outside the kernel positions
  - NO_DIFF: M1 == M2 (degenerate)

Recursively walks the JSON looking for any object with "M1"/"M2",
"best_M1"/"best_M2", or "M2_kernel" pairing keys.

Usage:
  python3 audit_kernel_preservation.py path/to/search_result.json
  python3 audit_kernel_preservation.py --dir path/to/results/
  python3 audit_kernel_preservation.py --block-context block1   # default
  python3 audit_kernel_preservation.py --block-context block2   # informational

Output: JSON summary to stdout + human-readable verdict.
"""
import argparse
import json
import os
import sys
from typing import Any, Optional


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# Cascade-1 kernels in registry: word_pair=[0,9], bit ∈ [0,31] depending on cand
# We accept ANY (word_pair=[0,9], bit) combination as cascade-1-valid.
ACCEPTED_KERNELS = [
    ((0, 9), b) for b in range(32)
]
# Plus exotic kernels (registry has 0_14, 0_1)
ACCEPTED_KERNELS += [
    ((0, 14), b) for b in range(32)
]
ACCEPTED_KERNELS += [
    ((0, 1), b) for b in range(32)
]


def parse_pair(M1_field: Any, M2_field: Any) -> Optional[tuple]:
    """Try to coerce M1 and M2 to tuples of 16 ints. Returns None if invalid."""
    def coerce(field):
        if not isinstance(field, list) or len(field) != 16:
            return None
        out = []
        for v in field:
            if isinstance(v, int):
                out.append(v & 0xFFFFFFFF)
            elif isinstance(v, str):
                try:
                    out.append(int(v, 16) & 0xFFFFFFFF)
                except ValueError:
                    return None
            else:
                return None
        return tuple(out)
    M1 = coerce(M1_field)
    M2 = coerce(M2_field)
    if M1 is None or M2 is None:
        return None
    return (M1, M2)


def classify(M1: tuple, M2: tuple) -> dict:
    """Classify a (M1, M2) pair against cascade-1 kernels."""
    diff = tuple((m1 ^ m2) for m1, m2 in zip(M1, M2))
    nonzero_words = [(i, d) for i, d in enumerate(diff) if d != 0]
    if not nonzero_words:
        return {"verdict": "NO_DIFF", "diff": diff, "matched_kernel": None}

    # Try to match any accepted kernel
    for word_pair, bit in ACCEPTED_KERNELS:
        expected = 1 << bit
        wpair_set = set(word_pair)
        # All nonzero diffs must be at exactly word_pair, with value = 1 << bit
        if (set(i for i, _ in nonzero_words) == wpair_set
                and all(diff[i] == expected for i in word_pair)):
            return {
                "verdict": "PASS",
                "diff": diff,
                "matched_kernel": {"word_pair": word_pair, "bit": bit},
            }
    return {
        "verdict": "DRIFT",
        "diff": diff,
        "matched_kernel": None,
        "nonzero_words": [(i, f"0x{d:08x}") for i, d in nonzero_words],
        "total_diff_hw": sum(bin(d).count("1") for _, d in nonzero_words),
    }


def find_pairs(obj: Any, path: str = "") -> list:
    """Recursively find dicts with (M1,M2)-like or (best_M1,best_M2)-like keys."""
    found = []
    if isinstance(obj, dict):
        # Standard M1/M2 keys (yale style + most encoders)
        if "M1" in obj and "M2" in obj:
            pair = parse_pair(obj["M1"], obj["M2"])
            if pair:
                found.append((path, pair))
        # best_M1/best_M2 (macbook search_seeded_atlas / search_kernel_preserving)
        if "best_M1" in obj and "best_M2" in obj:
            pair = parse_pair(obj["best_M1"], obj["best_M2"])
            if pair:
                found.append((f"{path}.best" if path else "best", pair))
        # M2_kernel sometimes paired with M1 (yale chamber-seed)
        if "M1" in obj and "M2_kernel" in obj:
            pair = parse_pair(obj["M1"], obj["M2_kernel"])
            if pair:
                found.append((f"{path}.M2_kernel" if path else "M2_kernel", pair))
        # M1 + best_M2 (macbook search_seeded_atlas: M1 fixed, M2 mutated)
        if "M1" in obj and "best_M2" in obj:
            pair = parse_pair(obj["M1"], obj["best_M2"])
            if pair:
                found.append((f"{path}.best_M2_vs_M1" if path else "best_M2_vs_M1", pair))
        for k, v in obj.items():
            found.extend(find_pairs(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(find_pairs(v, f"{path}[{i}]"))
    return found


def audit_file(path: str) -> dict:
    """Audit one JSON file. Returns {pairs, summary}."""
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        return {"error": f"load failed: {e}"}
    pairs = find_pairs(data)
    results = []
    pass_count = 0
    drift_count = 0
    nodiff_count = 0
    for path_str, (M1, M2) in pairs:
        cls = classify(M1, M2)
        results.append({"path": path_str, **cls})
        if cls["verdict"] == "PASS":
            pass_count += 1
        elif cls["verdict"] == "DRIFT":
            drift_count += 1
        else:
            nodiff_count += 1
    return {
        "file": path,
        "n_pairs": len(pairs),
        "pass_count": pass_count,
        "drift_count": drift_count,
        "nodiff_count": nodiff_count,
        "results": results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="JSON files or directories to audit")
    ap.add_argument("--dir", help="audit all JSONs under this directory")
    ap.add_argument("--summary-only", action="store_true",
                    help="print only summary counts, not per-pair details")
    ap.add_argument("--show-drift-detail", action="store_true",
                    help="for DRIFT verdicts, print per-word nonzero diff")
    ap.add_argument("--block-context", choices=["block1", "block2"], default="block1",
                    help="block1 (default): DRIFT means cascade-1 kernel violated, "
                         "indicating bug for block-1 cascade-1 pair search. "
                         "block2: DRIFT is expected (block-2 absorber freely mutates).")
    ap.add_argument("--json", action="store_true", help="emit JSON output to stdout")
    args = ap.parse_args()

    files = list(args.paths)
    if args.dir:
        for root, _, names in os.walk(args.dir):
            for name in names:
                if name.endswith(".json"):
                    files.append(os.path.join(root, name))
    if not files:
        print("usage: audit_kernel_preservation.py <file.json> [...]  OR  --dir <path>",
              file=sys.stderr)
        sys.exit(1)

    summaries = []
    grand_pass = 0
    grand_drift = 0
    grand_nodiff = 0
    files_with_drift = []

    for f in files:
        s = audit_file(f)
        if "error" in s:
            print(f"  ERROR {f}: {s['error']}", file=sys.stderr)
            continue
        summaries.append(s)
        grand_pass += s["pass_count"]
        grand_drift += s["drift_count"]
        grand_nodiff += s["nodiff_count"]
        if s["drift_count"] > 0:
            files_with_drift.append((f, s["drift_count"], s["n_pairs"]))

    if args.json:
        print(json.dumps(summaries, indent=2))
        return

    # Human-readable
    print(f"=== Kernel-preservation audit (block-context: {args.block_context}) ===")
    if args.block_context == "block2":
        print(f"NOTE: block2 context — DRIFT is EXPECTED for block-2 absorber search.")
        print(f"      DRIFT count below is informational, not a bug indicator.")
    print(f"Files scanned: {len(summaries)}")
    print(f"Total (M1, M2) pairs: {grand_pass + grand_drift + grand_nodiff}")
    print(f"  PASS (kernel-preserving):    {grand_pass}")
    print(f"  DRIFT (NOT cascade-1 valid): {grand_drift}")
    print(f"  NO_DIFF (degenerate):        {grand_nodiff}")
    print()
    if files_with_drift:
        if args.block_context == "block1":
            print(f"Files with drift ({len(files_with_drift)}) — BUG INDICATOR:")
        else:
            print(f"Files with drift ({len(files_with_drift)}) — informational only:")
        for f, drift_n, total_n in sorted(files_with_drift,
                                            key=lambda x: -x[1])[:20]:
            print(f"  {drift_n:>4d}/{total_n:<4d} drift  {f}")
        if len(files_with_drift) > 20:
            print(f"  ... and {len(files_with_drift)-20} more")
    else:
        print("No drift artifacts found. All scanned pairs are cascade-1-kernel-valid.")

    if args.show_drift_detail and grand_drift > 0:
        print()
        print("=== DRIFT detail (first 5 per file) ===")
        for s in summaries:
            drift_pairs = [r for r in s["results"] if r["verdict"] == "DRIFT"]
            if not drift_pairs:
                continue
            print(f"\n{s['file']}:")
            for r in drift_pairs[:5]:
                print(f"  [{r['path']}]: HW={r['total_diff_hw']}, "
                      f"nonzero_words={[(i, h) for i, h in r['nonzero_words'][:5]]}")


if __name__ == "__main__":
    main()

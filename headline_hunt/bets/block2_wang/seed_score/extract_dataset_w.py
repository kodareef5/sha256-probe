#!/usr/bin/env python3
"""F836 follow-up — extract W-pair-beam dataset for block-1 HW prediction.

Input files: headline_hunt/bets/block2_wang/results/search_artifacts/*pair_beam*.json
that contain init_W (i.e., the W-cube residual search runs).

Each row predicts best_seen.hw_total from the initial (W57..W60, init_hw63,
slots, candidate) configuration. Output is an .npz with X, y, feature_names,
candidates, paths.
"""
import argparse, json, sys
from pathlib import Path
from collections import Counter
import numpy as np


def popcount32(x):
    return bin(x & 0xFFFFFFFF).count("1")


def parse_words(seq):
    return [int(str(w), 16) if not isinstance(w, int) else w for w in seq]


# fixed vocabulary for penalty_regs one-hot (covers historical values)
PENALTY_REGS_VOCAB = ["c,g", "c", "g", "a,b,c,d,e,f,g,h", "a,b,c,e,f,g", ""]


def feats_from_path(path: Path):
    try:
        d = json.loads(path.read_text())
    except Exception:
        return None
    if "init_W" not in d or "best_seen" not in d:
        return None
    bs = d["best_seen"]
    if not isinstance(bs, dict) or bs.get("hw_total") is None:
        return None
    try:
        Wv = parse_words(d["init_W"])
    except Exception:
        return None
    if len(Wv) != 4:
        return None

    feats = {}
    # 4 per-word HW
    for i, w in enumerate(Wv):
        feats[f"W_word{i}_hw"] = popcount32(w)
    # 32 bit-position popcount across 4 words
    for b in range(32):
        feats[f"W_bit{b:02d}"] = sum(1 for w in Wv if (w >> b) & 1)
    # total HW
    feats["W_total_hw"] = sum(popcount32(w) for w in Wv)

    # scalars
    for k in ("init_hw", "init_score", "pair_pool", "max_pairs", "beam_width", "max_radius", "penalty_weight"):
        v = d.get(k)
        if v is None:
            feats[k] = 0.0
            feats[k + "_isnull"] = 1.0
        else:
            try:
                feats[k] = float(v)
                feats[k + "_isnull"] = 0.0
            except Exception:
                feats[k] = 0.0
                feats[k + "_isnull"] = 1.0

    # init_hw63: list of 8 lane HWs at round 63
    lh = d.get("init_hw63") or [0] * 8
    if len(lh) != 8:
        lh = (list(lh) + [0] * 8)[:8]
    for i, v in enumerate(lh):
        feats[f"init_hw63_{i}"] = float(v)

    # slots: which 4 W-positions are being modified (e.g., [57,58,59,60])
    slots = d.get("slots") or [0] * 4
    if len(slots) != 4:
        slots = (list(slots) + [0] * 4)[:4]
    for i, s in enumerate(slots):
        feats[f"slot_{i}"] = float(s)
    # also: span = max-min, encodes "wide vs tight" cube basis
    feats["slot_span"] = float(max(slots) - min(slots))

    # penalty_regs one-hot
    pr = d.get("penalty_regs", "")
    for v in PENALTY_REGS_VOCAB:
        feats[f"penalty_regs_{v.replace(',', '_') or 'empty'}"] = 1.0 if pr == v else 0.0

    # pair_rank vocab (new flag in F520+)
    PR_VOCAB = ["hw", "cg", "weighted", "sparse", "target", "target_sparse", "cg_target"]
    pair_rank = d.get("pair_rank", "")
    for v in PR_VOCAB:
        feats[f"pair_rank_{v}"] = 1.0 if pair_rank == v else 0.0

    cand = d.get("candidate", "") or ""
    y = float(bs["hw_total"])
    return feats, y, cand, str(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        default="headline_hunt/bets/block2_wang/results/search_artifacts",
    )
    ap.add_argument("--pattern", default="*pair_beam*.json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    files = sorted(Path(args.root).glob(args.pattern))
    print(f"[extract-w] {len(files)} candidate files", file=sys.stderr)

    rows, ys, cands, paths = [], [], [], []
    for p in files:
        r = feats_from_path(p)
        if r is None:
            continue
        feats, y, cand, fp = r
        rows.append(feats)
        ys.append(y)
        cands.append(cand)
        paths.append(fp)

    print(f"[extract-w] {len(rows)} usable rows", file=sys.stderr)
    if not rows:
        print("no rows extracted", file=sys.stderr)
        sys.exit(1)

    keys = sorted({k for r in rows for k in r.keys()})
    X = np.zeros((len(rows), len(keys)), dtype=np.float64)
    for i, r in enumerate(rows):
        for j, k in enumerate(keys):
            X[i, j] = r.get(k, 0.0)
    y = np.array(ys, dtype=np.float64)

    cnt = Counter(cands)
    print(f"[extract-w] {len(cnt)} distinct candidates; top:", file=sys.stderr)
    for c, n in cnt.most_common(20):
        print(f"  {c or '(blank)'}: {n}", file=sys.stderr)

    print(f"[extract-w] y stats: min={y.min():.1f} max={y.max():.1f} "
          f"mean={y.mean():.2f} std={y.std():.2f}", file=sys.stderr)
    print(f"[extract-w] feature count: {len(keys)}", file=sys.stderr)

    np.savez(
        args.out,
        X=X,
        y=y,
        feature_names=np.array(keys),
        candidates=np.array(cands),
        paths=np.array(paths),
    )
    print(f"[extract-w] wrote {args.out}: X={X.shape}, y={y.shape}", file=sys.stderr)


if __name__ == "__main__":
    main()

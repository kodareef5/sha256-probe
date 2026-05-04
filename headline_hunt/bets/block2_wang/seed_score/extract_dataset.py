#!/usr/bin/env python3
"""F835 Angle C — extract (features, best_seen_hw) dataset from pair_beam result JSONs.

Walks headline_hunt/bets/block2_wang/results/search_artifacts/ for
*_pair_beam*.json files and joins each result to its seed jsonl entry to
recover the candidate identity and rich seed-level features (bridge_score,
cg_*, lane HWs, etc.).

Output: a numpy .npz at <out> with arrays X, y, feature_names, candidates,
file_paths.
"""
import argparse, json, re, sys
from pathlib import Path
from collections import Counter
import numpy as np


def popcount32(x: int) -> int:
    return bin(x & 0xFFFFFFFF).count("1")


def per_lane_hw_8(words):
    """16 32-bit words → 8 lane buckets (lane i = words {i, i+8})."""
    lh = [0] * 8
    for i, w in enumerate(words):
        lh[i % 8] += popcount32(w)
    return lh


def parse_words(seq):
    out = []
    for w in seq:
        if isinstance(w, int):
            out.append(w)
        else:
            out.append(int(str(w), 16))
    return out


CAND_RX = re.compile(r"bit(\d+)_m([0-9a-fA-F]+)")
RANK_RX = re.compile(r"_?rank(\d+)")


def find_candidate_in_strings(*strings):
    for s in strings:
        if not s:
            continue
        m = CAND_RX.search(str(s))
        if m:
            return f"bit{m.group(1)}_m{m.group(2)}"
    return ""


def find_rank_in_strings(*strings):
    for s in strings:
        if not s:
            continue
        m = RANK_RX.search(str(s))
        if m:
            return int(m.group(1))
    return None


# ───── seed jsonl join layer ─────


def load_seed_jsonl(path: Path):
    """Return list of seed records (dicts) keyed by ['rank'] or list index.

    Returns the list (rank lookup uses each record's 'rank' field if present;
    else positional index)."""
    if not path.exists():
        return None
    out = []
    for ln in path.read_text().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out


def lookup_seed(seed_records, seed_rank):
    """Find seed record matching seed_rank (which might be the 'rank' field
    inside the record, or the positional index)."""
    if seed_records is None:
        return None
    if seed_rank is None:
        return None
    # match by 'rank' field if present
    for r in seed_records:
        if r.get("rank") == seed_rank:
            return r
    # fall back to positional
    if 0 <= seed_rank < len(seed_records):
        return seed_records[seed_rank]
    return None


# ───── feature extraction ─────


def feats_from_m2(m2):
    feats = {}
    for i, w in enumerate(m2):
        feats[f"m2_word{i:02d}_hw"] = popcount32(w)
    for i, lh in enumerate(per_lane_hw_8(m2)):
        feats[f"m2_lane{i}_hw"] = lh
    for b in range(32):
        c = sum(1 for w in m2 if (w >> b) & 1)
        feats[f"m2_bit{b:02d}"] = c
    return feats


def feats_from_seed(seed):
    """Pull the seed-level features that were already computed during seed
    generation."""
    feats = {}
    if seed is None:
        feats["seed_isnull"] = 1.0
        return feats
    feats["seed_isnull"] = 0.0
    for k in (
        "absorber_best_hw",
        "absorber_improvement",
        "absorber_start_hw",
        "block1_hw",
        "bridge_score",
        "cg_best_hw",
        "cg_cleared_hw",
        "cg_new_hw",
        "cleared_total",
        "new_total",
        "overlap_total",
        "rank",
    ):
        v = seed.get(k)
        if v is None:
            feats[f"seed_{k}"] = 0.0
            feats[f"seed_{k}_isnull"] = 1.0
        else:
            try:
                feats[f"seed_{k}"] = float(v)
                feats[f"seed_{k}_isnull"] = 0.0
            except Exception:
                feats[f"seed_{k}"] = 0.0
                feats[f"seed_{k}_isnull"] = 1.0
    # vectorial: lane HWs
    for prefix in (
        "absorber_lane_hw",
        "cleared_lane_hw",
        "input_lane_hw",
        "lane_delta",
        "new_lane_hw",
        "overlap_lane_hw",
    ):
        lh = seed.get(prefix) or [0] * 8
        if len(lh) != 8:
            lh = (list(lh) + [0] * 8)[:8]
        for i, v in enumerate(lh):
            try:
                feats[f"seed_{prefix}_{i}"] = float(v)
            except Exception:
                feats[f"seed_{prefix}_{i}"] = 0.0
    return feats


def extract_one(path: Path, seed_cache):
    try:
        d = json.loads(path.read_text())
    except Exception:
        return None
    if "best_seen_hw" not in d or d["best_seen_hw"] is None:
        return None
    if "init_M2" not in d:
        return None
    try:
        m2 = parse_words(d["init_M2"])
    except Exception:
        return None
    if len(m2) != 16:
        return None

    feats = {}
    feats.update(feats_from_m2(m2))

    # init scalars
    for k in (
        "init_hw",
        "init_m2_weight",
        "init_m2_added_bits",
        "init_m2_removed_bits",
        "init_m2_net_added_bits",
        "rounds",
        "pair_pool",
        "pair_pool_hw_min",
        "pair_pool_hw_max",
        "beam_width",
        "max_pairs",
        "max_radius",
        "cg_weight",
        "target_weight",
        "m2_weight_penalty",
        "shape_net_add_penalty",
        "shape_removed_bonus",
        "seed_rank",
    ):
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

    for k in ("min_m2_weight", "max_m2_weight", "max_target_l1"):
        v = d.get(k)
        feats[k + "_isnull"] = 1.0 if v is None else 0.0
        feats[k] = 0.0 if v is None else float(v)

    OBJ_VOCAB = ["hw", "cg", "weighted", "sparse", "target", "target_sparse", "cg_target"]
    for o in OBJ_VOCAB:
        feats[f"obj_{o}"] = 1.0 if d.get("objective") == o else 0.0
    PR_VOCAB = OBJ_VOCAB
    for o in PR_VOCAB:
        feats[f"pair_rank_{o}"] = 1.0 if d.get("pair_rank") == o else 0.0

    lw = d.get("lane_weights") or [0.0] * 8
    if len(lw) != 8:
        lw = (list(lw) + [0.0] * 8)[:8]
    for i, v in enumerate(lw):
        feats[f"lane_weight_{i}"] = float(v)

    # join seed jsonl → cand + rich seed features
    label = d.get("label", "") or ""
    src = d.get("seed_jsonl", "") or ""
    seed_rank = d.get("seed_rank")
    if seed_rank is not None:
        try:
            seed_rank = int(seed_rank)
        except Exception:
            seed_rank = None

    seed = None
    if src:
        sp = Path(src)
        if not sp.is_absolute():
            sp = Path.cwd() / sp
        if str(sp) not in seed_cache:
            seed_cache[str(sp)] = load_seed_jsonl(sp)
        seed_records = seed_cache[str(sp)]
        seed = lookup_seed(seed_records, seed_rank)

    feats.update(feats_from_seed(seed))

    # candidate: try regex on label/src/path, then seed.candidate
    cand = find_candidate_in_strings(label, src, path.name)
    if not cand and seed and "candidate" in seed:
        cand = str(seed["candidate"])
    # also recover seed_rank from path/label if missing
    if seed_rank is None:
        seed_rank = find_rank_in_strings(label, path.name) or 0
    feats["seed_rank_resolved"] = float(seed_rank or 0)

    y = float(d["best_seen_hw"])
    return feats, y, cand, str(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        default="headline_hunt/bets/block2_wang/results/search_artifacts",
        help="search_artifacts root",
    )
    ap.add_argument("--pattern", default="*pair_beam*.json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    root = Path(args.root)
    files = sorted(root.glob(args.pattern))
    print(f"[extract] {len(files)} candidate files", file=sys.stderr)

    seed_cache = {}
    rows, ys, cands, paths = [], [], [], []
    for p in files:
        r = extract_one(p, seed_cache)
        if r is None:
            continue
        feats, y, cand, fp = r
        rows.append(feats)
        ys.append(y)
        cands.append(cand)
        paths.append(fp)

    print(f"[extract] {len(rows)} usable rows", file=sys.stderr)
    if not rows:
        print("no rows extracted", file=sys.stderr)
        sys.exit(1)

    keys = sorted({k for r in rows for k in r.keys()})
    X = np.zeros((len(rows), len(keys)), dtype=np.float32)
    for i, r in enumerate(rows):
        for j, k in enumerate(keys):
            X[i, j] = r.get(k, 0.0)
    y = np.array(ys, dtype=np.float32)

    cand_counts = Counter(cands)
    print(f"[extract] {len(cand_counts)} distinct candidates; top:", file=sys.stderr)
    for c, n in cand_counts.most_common(15):
        print(f"  {c or '(blank)'}: {n}", file=sys.stderr)

    print(f"[extract] y stats: min={y.min():.1f} max={y.max():.1f} "
          f"mean={y.mean():.2f} std={y.std():.2f}", file=sys.stderr)
    print(f"[extract] feature count: {len(keys)}", file=sys.stderr)

    np.savez(
        args.out,
        X=X,
        y=y,
        feature_names=np.array(keys),
        candidates=np.array(cands),
        paths=np.array(paths),
    )
    print(f"[extract] wrote {args.out}: X={X.shape}, y={y.shape}", file=sys.stderr)


if __name__ == "__main__":
    main()

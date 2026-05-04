#!/usr/bin/env python3
"""F836/F837 prefilter eval: how good is the model as a prefilter?

We don't actually need MAE — we need: when we keep the top-K predicted, do
we retain the rows with the lowest true HW (the ones we want to cert-pin)?

Reports recall@K under grouped-by-candidate CV (the realistic deployment
scenario where the model has not seen the held-out candidate before).
"""
import argparse, sys
import numpy as np


def standardize(X, mean=None, std=None):
    X = X.astype(np.float64)
    if mean is None:
        mean = X.mean(axis=0)
        std = X.std(axis=0)
        std[std < 1e-9] = 1.0
    return (X - mean) / std, mean, std


def ridge_fit(X, y, lam):
    n, d = X.shape
    A = X.T @ X + lam * np.eye(d)
    return np.linalg.solve(A, X.T @ y)


def grouped_kfold(groups, k, seed):
    rng = np.random.default_rng(seed)
    uniq = list({g for g in groups})
    rng.shuffle(uniq)
    grp_fold = {g: i % k for i, g in enumerate(uniq)}
    folds = [[] for _ in range(k)]
    for i, g in enumerate(groups):
        folds[grp_fold[g]].append(i)
    return [np.array(f) for f in folds]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--lam", type=float, default=10.0)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--keep", type=float, nargs="+", default=[0.30, 0.50, 0.70],
                    help="prefilter-keep fractions to evaluate")
    ap.add_argument("--top-frac", type=float, default=0.30,
                    help="ground-truth 'good' = lowest-HW top fraction")
    args = ap.parse_args()

    data = np.load(args.npz, allow_pickle=True)
    X = data["X"].astype(np.float64)
    y = data["y"].astype(np.float64)
    cands = data["candidates"]
    n = len(y)

    folds = grouped_kfold(cands, args.folds, args.seed)
    pred = np.zeros_like(y)
    have = np.zeros(n, dtype=bool)
    for fi, val in enumerate(folds):
        if len(val) == 0:
            continue
        train = np.concatenate([f for j, f in enumerate(folds) if j != fi])
        Xtr, Xva = X[train], X[val]
        ytr, yva = y[train], y[val]
        Xtr_s, mu, sd = standardize(Xtr)
        Xva_s, _, _ = standardize(Xva, mu, sd)
        ymean = ytr.mean()
        w = ridge_fit(Xtr_s, ytr - ymean, args.lam)
        pred[val] = Xva_s @ w + ymean
        have[val] = True

    yhat = pred[have]
    ytrue = y[have]

    # ground-truth: rows with the lowest HW (best refinement) are "good"
    n_good = max(1, int(round(len(ytrue) * args.top_frac)))
    true_good_idx = np.argsort(ytrue)[:n_good]  # lowest HW = best
    true_good_mask = np.zeros(len(ytrue), dtype=bool)
    true_good_mask[true_good_idx] = True

    print(f"\n=== prefilter eval (grouped CV, n={len(ytrue)}, "
          f"true-good = bottom-{int(args.top_frac*100)}% by HW, count={n_good}) ===")
    print(f"  HW range: [{ytrue.min():.0f}, {ytrue.max():.0f}], mean={ytrue.mean():.2f}")
    print(f"  HW threshold for 'good': <={ytrue[true_good_idx].max():.0f}")
    print()
    print(f"  {'keep':>7} | {'kept_n':>7} | {'recall':>8} | {'precision':>10} | {'random_recall':>13}")
    print(f"  {'-'*7} | {'-'*7} | {'-'*8} | {'-'*10} | {'-'*13}")
    for keep_frac in args.keep:
        n_keep = max(1, int(round(len(ytrue) * keep_frac)))
        keep_idx = np.argsort(yhat)[:n_keep]  # lowest predicted HW = top picks
        keep_mask = np.zeros(len(ytrue), dtype=bool)
        keep_mask[keep_idx] = True
        recall = (keep_mask & true_good_mask).sum() / max(1, true_good_mask.sum())
        precision = (keep_mask & true_good_mask).sum() / max(1, keep_mask.sum())
        random_recall = keep_frac  # under independence
        print(f"  {keep_frac:>7.2f} | {n_keep:>7d} | {recall:>8.3f} | {precision:>10.3f} | {random_recall:>13.3f}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""F837 follow-up — sklearn GBT to test the ceiling above ridge.

Compares HistGradientBoostingRegressor against the F837 ridge baseline
under the same three CV settings: random, grouped-by-candidate,
within-candidate, plus time-split.

If GBT lifts substantially over ridge, it's the better deployment
artifact. If not, the linear model has exhausted the signal in this
feature set and we should focus on adding features instead.
"""
import argparse, re, sys
from pathlib import Path
from collections import Counter
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor


DATE_RX = re.compile(r"(\d{8})")


def metrics(yt, yp, label):
    err = yp - yt
    mae = np.abs(err).mean()
    rmse = np.sqrt((err ** 2).mean())
    sst = ((yt - yt.mean()) ** 2).sum()
    r2 = 1 - (err ** 2).sum() / sst if sst > 1e-9 else 0.0
    print(f"  {label:42s} MAE={mae:.3f}  RMSE={rmse:.3f}  R^2={r2:+.3f}")
    return mae, r2


def kfold_indices(n, k, seed):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    return np.array_split(idx, k)


def grouped_kfold(groups, k, seed):
    rng = np.random.default_rng(seed)
    uniq = list({g for g in groups})
    rng.shuffle(uniq)
    grp_fold = {g: i % k for i, g in enumerate(uniq)}
    folds = [[] for _ in range(k)]
    for i, g in enumerate(groups):
        folds[grp_fold[g]].append(i)
    return [np.array(f) for f in folds]


def cv_eval(X, y, folds, name, **gbt_kwargs):
    pred = np.zeros_like(y, dtype=np.float64)
    have = np.zeros(len(y), dtype=bool)
    for fi, val in enumerate(folds):
        if len(val) == 0:
            continue
        train = np.concatenate([f for j, f in enumerate(folds) if j != fi])
        m = HistGradientBoostingRegressor(**gbt_kwargs)
        m.fit(X[train], y[train])
        pred[val] = m.predict(X[val])
        have[val] = True
    return metrics(y[have], pred[have], name)


def prefilter_recall(yt, yp, top_frac=0.30, keeps=(0.30, 0.50, 0.70)):
    n_good = max(1, int(round(len(yt) * top_frac)))
    true_idx = np.argsort(yt)[:n_good]
    true_mask = np.zeros(len(yt), dtype=bool)
    true_mask[true_idx] = True
    print(f"  prefilter recall (top-{int(top_frac*100)}% threshold, n_good={n_good}):")
    for keep in keeps:
        n_keep = max(1, int(round(len(yt) * keep)))
        keep_idx = np.argsort(yp)[:n_keep]
        keep_mask = np.zeros(len(yt), dtype=bool)
        keep_mask[keep_idx] = True
        rec = (keep_mask & true_mask).sum() / max(1, true_mask.sum())
        print(f"    keep={keep:.2f}  kept={n_keep:3d}  recall={rec:.3f}  random={keep:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-iter", type=int, default=200)
    ap.add_argument("--max-depth", type=int, default=4)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--l2", type=float, default=1.0)
    ap.add_argument("--min-samples-leaf", type=int, default=8)
    args = ap.parse_args()

    data = np.load(args.npz, allow_pickle=True)
    X = data["X"].astype(np.float64)
    y = data["y"].astype(np.float64)
    cands = data["candidates"]
    feat_names = data["feature_names"]
    paths = data["paths"]
    n = len(y)
    print(f"loaded X={X.shape} y range [{y.min():.0f},{y.max():.0f}] mean={y.mean():.2f}")

    gbt_kwargs = dict(
        max_iter=args.max_iter,
        max_depth=args.max_depth,
        learning_rate=args.lr,
        l2_regularization=args.l2,
        min_samples_leaf=args.min_samples_leaf,
        random_state=args.seed,
    )
    print(f"GBT params: {gbt_kwargs}\n")

    print("=== random 5-fold CV ===")
    rfolds = kfold_indices(n, args.folds, args.seed)
    cv_eval(X, y, rfolds, "GBT random", **gbt_kwargs)

    print("\n=== grouped-by-candidate 5-fold CV ===")
    gfolds = grouped_kfold(cands, args.folds, args.seed)
    pred = np.zeros_like(y)
    have = np.zeros(n, dtype=bool)
    for fi, val in enumerate(gfolds):
        if len(val) == 0:
            continue
        train = np.concatenate([f for j, f in enumerate(gfolds) if j != fi])
        m = HistGradientBoostingRegressor(**gbt_kwargs)
        m.fit(X[train], y[train])
        pred[val] = m.predict(X[val])
        have[val] = True
    metrics(y[have], pred[have], "GBT grouped")
    prefilter_recall(y[have], pred[have], top_frac=0.30)

    # within-candidate (largest)
    cnt = Counter(cands.tolist())
    top_c, top_n = cnt.most_common(1)[0]
    if top_n >= 20:
        cmask = (cands == top_c)
        Xc = X[cmask]
        yc = y[cmask]
        cfolds = kfold_indices(len(yc), args.folds, args.seed)
        print(f"\n=== within-candidate CV ({top_c}, n={top_n}) ===")
        cv_eval(Xc, yc, cfolds, f"GBT within-{top_c}", **gbt_kwargs)

    # time-split
    dates = []
    for p in paths:
        m = DATE_RX.search(Path(str(p)).name)
        dates.append(m.group(1) if m else "00000000")
    order = np.argsort(dates)
    Xs, ys, dates_s = X[order], y[order], [dates[i] for i in order]
    n_train = int(round(0.80 * n))
    print(f"\n=== time-split (train {dates_s[0]}..{dates_s[n_train-1]}, eval {dates_s[n_train]}..{dates_s[-1]}) ===")
    m = HistGradientBoostingRegressor(**gbt_kwargs)
    m.fit(Xs[:n_train], ys[:n_train])
    pred = m.predict(Xs[n_train:])
    metrics(ys[n_train:], pred, "GBT time-split")
    prefilter_recall(ys[n_train:], pred, top_frac=0.30)

    # feature importance
    print("\n=== top features (permutation-free GBT importance via fit on full data) ===")
    full = HistGradientBoostingRegressor(**gbt_kwargs)
    full.fit(X, y)
    # HistGradientBoosting doesn't expose feature_importances_ in older sklearn,
    # so use permutation
    from sklearn.inspection import permutation_importance
    pi = permutation_importance(full, X, y, n_repeats=5, random_state=args.seed, n_jobs=1)
    order_imp = np.argsort(-pi.importances_mean)
    for i in order_imp[:20]:
        print(f"  {str(feat_names[i]):32s} importance={pi.importances_mean[i]:+.4f} (std={pi.importances_std[i]:.4f})")


if __name__ == "__main__":
    main()

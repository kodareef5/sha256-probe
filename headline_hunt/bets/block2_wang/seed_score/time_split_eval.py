#!/usr/bin/env python3
"""F837 follow-up — time-split eval to check for manifold drift.

Sorts rows by date (YYYYMMDD prefix in path), trains on the first 80%, evals
on the most recent 20%. If the model decays vs grouped-CV performance, the
deployment plan needs online retraining.
"""
import argparse, re, sys
from pathlib import Path
import numpy as np


DATE_RX = re.compile(r"(\d{8})")


def standardize(X, mean=None, std=None):
    X = X.astype(np.float64)
    if mean is None:
        mean = X.mean(axis=0)
        std = X.std(axis=0)
        std[std < 1e-9] = 1.0
    return (X - mean) / std, mean, std


def ridge_fit(X, y, lam):
    n, d = X.shape
    return np.linalg.solve(X.T @ X + lam * np.eye(d), X.T @ y)


def metrics(yt, yp, label):
    err = yp - yt
    mae = np.abs(err).mean()
    rmse = np.sqrt((err ** 2).mean())
    sst = ((yt - yt.mean()) ** 2).sum()
    r2 = 1 - (err ** 2).sum() / sst if sst > 1e-9 else 0.0
    print(f"  {label:36s} MAE={mae:.3f}  RMSE={rmse:.3f}  R^2={r2:+.3f}  n={len(yt)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--lam", type=float, default=10.0)
    ap.add_argument("--train-frac", type=float, default=0.80)
    args = ap.parse_args()

    data = np.load(args.npz, allow_pickle=True)
    X = data["X"].astype(np.float64)
    y = data["y"].astype(np.float64)
    paths = data["paths"]
    n = len(y)

    # extract date from each path
    dates = []
    bad = 0
    for p in paths:
        m = DATE_RX.search(Path(str(p)).name)
        if m:
            dates.append(m.group(1))
        else:
            dates.append("00000000")
            bad += 1
    if bad:
        print(f"[time-split] {bad} paths without parseable date → sorted as oldest", file=sys.stderr)

    order = np.argsort(dates)
    X = X[order]
    y = y[order]
    dates_sorted = [dates[i] for i in order]

    n_train = int(round(args.train_frac * n))
    Xtr, Xva = X[:n_train], X[n_train:]
    ytr, yva = y[:n_train], y[n_train:]

    print(f"[time-split] train: {dates_sorted[0]}..{dates_sorted[n_train-1]} (n={len(ytr)})")
    print(f"[time-split] val:   {dates_sorted[n_train]}..{dates_sorted[-1]} (n={len(yva)})")
    print(f"[time-split] y train: mean={ytr.mean():.2f} std={ytr.std():.2f}")
    print(f"[time-split] y val:   mean={yva.mean():.2f} std={yva.std():.2f}")

    print("\n=== naive baselines ===")
    metrics(yva, np.full_like(yva, ytr.mean()), "always-train-mean")

    print(f"\n=== ridge (lam={args.lam}) ===")
    Xtr_s, mu, sd = standardize(Xtr)
    Xva_s, _, _ = standardize(Xva, mu, sd)
    ymean = ytr.mean()
    w = ridge_fit(Xtr_s, ytr - ymean, args.lam)
    pred = Xva_s @ w + ymean
    metrics(yva, pred, "ridge time-split")

    # rank-only prefilter eval at top-30%
    n_good = max(1, int(round(len(yva) * 0.30)))
    true_good = np.argsort(yva)[:n_good]
    true_mask = np.zeros(len(yva), dtype=bool)
    true_mask[true_good] = True
    print(f"\n=== prefilter recall (val set, top-30% threshold) ===")
    for keep in (0.3, 0.5, 0.7):
        n_keep = max(1, int(round(len(yva) * keep)))
        keep_idx = np.argsort(pred)[:n_keep]
        keep_mask = np.zeros(len(yva), dtype=bool)
        keep_mask[keep_idx] = True
        recall = (keep_mask & true_mask).sum() / max(1, true_mask.sum())
        print(f"  keep={keep:.2f}  kept={n_keep:3d}  recall={recall:.3f}  random={keep:.3f}")


if __name__ == "__main__":
    main()

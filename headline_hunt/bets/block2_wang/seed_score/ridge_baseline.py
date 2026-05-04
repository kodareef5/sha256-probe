#!/usr/bin/env python3
"""F835 Angle C — ridge baseline for predicting M2-pair-beam best_seen_hw.

Trains numpy-only ridge regression with 5-fold CV. Compares against three
naive baselines:
  - Mean predictor
  - init_hw alone (1-feature linear)
  - init_m2_weight alone (1-feature linear)

Reports MAE, RMSE, R^2 on holdout. Also runs grouped CV by candidate so we
test out-of-candidate generalisation (the harder, more useful question).
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
    """Closed-form ridge: w = (X^T X + lam I)^-1 X^T y. X assumed centered+scaled."""
    n, d = X.shape
    A = X.T @ X + lam * np.eye(d)
    b = X.T @ y
    w = np.linalg.solve(A, b)
    return w


def metrics(y_true, y_pred, label=""):
    err = y_pred - y_true
    mae = np.abs(err).mean()
    rmse = np.sqrt((err ** 2).mean())
    sst = ((y_true - y_true.mean()) ** 2).sum()
    sse = (err ** 2).sum()
    r2 = 1 - sse / sst if sst > 1e-9 else 0.0
    print(f"  {label:36s} MAE={mae:.3f}  RMSE={rmse:.3f}  R^2={r2:+.3f}")
    return mae, rmse, r2


def kfold_indices(n, k, seed):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    folds = np.array_split(idx, k)
    return folds


def grouped_kfold_indices(groups, k, seed):
    """Folds split so each group ends up entirely in one fold (when possible).

    groups: 1d str array of length n. We round-robin assign distinct groups
    into folds, then collect each row by its group's fold."""
    rng = np.random.default_rng(seed)
    uniq = list({g for g in groups})
    rng.shuffle(uniq)
    grp_fold = {g: i % k for i, g in enumerate(uniq)}
    folds = [[] for _ in range(k)]
    for i, g in enumerate(groups):
        folds[grp_fold[g]].append(i)
    return [np.array(f) for f in folds]


def cv_eval(X, y, lam, folds, name):
    print(f"\n[{name}] lam={lam}")
    all_pred = np.zeros_like(y)
    all_mask = np.zeros(len(y), dtype=bool)
    for fi, val_idx in enumerate(folds):
        if len(val_idx) == 0:
            continue
        train_idx = np.concatenate([f for j, f in enumerate(folds) if j != fi])
        Xtr, Xva = X[train_idx], X[val_idx]
        ytr, yva = y[train_idx], y[val_idx]
        Xtr_s, mu, sd = standardize(Xtr)
        Xva_s, _, _ = standardize(Xva, mu, sd)
        ytr_mean = ytr.mean()
        w = ridge_fit(Xtr_s, ytr - ytr_mean, lam)
        pred = Xva_s @ w + ytr_mean
        all_pred[val_idx] = pred
        all_mask[val_idx] = True
    return metrics(y[all_mask], all_pred[all_mask], name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--lam", type=float, default=10.0, help="ridge L2")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--feature-subset",
        choices=["all", "m2only", "seedonly", "no_m2bits"],
        default="all",
    )
    ap.add_argument(
        "--within-candidate",
        action="store_true",
        help="Run within-candidate k-fold for the largest candidate (>=20 rows)",
    )
    args = ap.parse_args()

    data = np.load(args.npz, allow_pickle=True)
    X = data["X"].astype(np.float64)
    y = data["y"].astype(np.float64)
    feat_names = data["feature_names"]
    cands = data["candidates"]
    # apply feature subset
    fnames = list(feat_names)
    if args.feature_subset != "all":
        mask = np.zeros(X.shape[1], dtype=bool)
        for j, f in enumerate(fnames):
            keep = False
            if args.feature_subset == "m2only":
                keep = f.startswith("m2_") or f.startswith("init_") or f.startswith("lane_weight") \
                    or f.startswith("obj_") or f.startswith("pair_rank_")
            elif args.feature_subset == "seedonly":
                keep = f.startswith("seed_")
            elif args.feature_subset == "no_m2bits":
                keep = not f.startswith("m2_bit")
            mask[j] = keep
        X = X[:, mask]
        feat_names = np.array(fnames)[mask]
        print(f"[subset={args.feature_subset}] kept {X.shape[1]}/{len(fnames)} features", file=sys.stderr)

    n, d = X.shape
    print(f"loaded X={X.shape} y={y.shape}", file=sys.stderr)
    print(f"y: min={y.min():.1f} max={y.max():.1f} mean={y.mean():.2f} std={y.std():.2f}", file=sys.stderr)

    # ── naive baselines ──
    print("\n=== naive baselines (no learning) ===")
    mean_pred = np.full_like(y, y.mean())
    metrics(y, mean_pred, "always-mean")

    # 1-feature: init_hw
    if "init_hw" in list(feat_names):
        idx = list(feat_names).index("init_hw")
        x1 = X[:, idx]
        # least-squares y = a + b*x
        A = np.stack([np.ones_like(x1), x1], axis=1)
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        pred = A @ coef
        metrics(y, pred, "linreg(init_hw) [in-sample]")

    if "init_m2_weight" in list(feat_names):
        idx = list(feat_names).index("init_m2_weight")
        x1 = X[:, idx]
        A = np.stack([np.ones_like(x1), x1], axis=1)
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        pred = A @ coef
        metrics(y, pred, "linreg(init_m2_weight) [in-sample]")

    # ── ridge: random k-fold ──
    folds = kfold_indices(n, args.folds, args.seed)
    print(f"\n=== ridge {args.folds}-fold CV (random) ===")
    cv_eval(X, y, args.lam, folds, "ridge-random-kfold")

    # ── ridge: candidate-grouped k-fold (harder) ──
    # only meaningful if multiple candidates
    uniq_cands = sorted(set(cands.tolist()))
    print(f"\n=== ridge {args.folds}-fold CV (grouped by candidate, n_groups={len(uniq_cands)}) ===")
    if len(uniq_cands) >= args.folds:
        gfolds = grouped_kfold_indices(cands, args.folds, args.seed)
        cv_eval(X, y, args.lam, gfolds, "ridge-grouped-kfold")
    else:
        print("  skipped: too few distinct candidates")

    # ── within-candidate CV (largest cand) ──
    if args.within_candidate:
        from collections import Counter
        cnt = Counter(cands.tolist())
        top_cand, top_n = cnt.most_common(1)[0]
        if top_n >= 20:
            cmask = (cands == top_cand)
            Xc = X[cmask]
            yc = y[cmask]
            print(f"\n=== within-candidate CV: {top_cand} (n={top_n}) ===")
            cfolds = kfold_indices(top_n, args.folds, args.seed)
            cv_eval(Xc, yc, args.lam, cfolds, f"ridge-within-{top_cand}")
        else:
            print(f"\n[skip within-candidate] largest cand {top_cand} has only {top_n} rows")

    # ── feature importance from full-data fit ──
    Xs, mu, sd = standardize(X)
    ymean = y.mean()
    w = ridge_fit(Xs, y - ymean, args.lam)
    print("\n=== top features by |weight| (standardized, full-data fit) ===")
    order = np.argsort(-np.abs(w))
    for i in order[:25]:
        print(f"  {feat_names[i]:32s} w={w[i]:+7.3f}")


if __name__ == "__main__":
    main()

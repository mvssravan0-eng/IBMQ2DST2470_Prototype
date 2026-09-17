"""
train_anomaly.py
-----------------
PART 2 -- Unsupervised anomaly detection for ZERO-DAY simulation.

Key idea: train ONLY on Normal traffic from KDDTrain+ (67,343 rows), so the
models never see ANY attack signature -- known or unknown -- during
training. This is the honest way to simulate "zero-day": the model learns
what normal looks like and flags deviations, rather than learning attack
patterns directly.

Models used:
  - Isolation Forest   (tree-based, fast, scales well)
  - Local Outlier Factor (density-based, novelty=True mode)
  - Autoencoder (Keras/TF if available, else a PCA-reconstruction-error
    fallback so the script never hard-fails on environments without TF)

Evaluated as BINARY anomaly detection (Normal=0 / Attack=1) on the full
KDDTest+ set, AND specifically on the subset of KDDTest+ whose attack_type
never appeared in KDDTrain+ at all (the TRUE zero-day subset) -- this is
the number that actually matters for the assignment's stated goal.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score, roc_curve, precision_recall_curve, average_precision_score

from data_loading import load_nslkdd, ATTACK_CATEGORY_MAP
from preprocessing import fit_transform_train_test

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "..", "data")
OUT_PLOTS = os.path.join(HERE, "..", "outputs", "plots")
OUT_TABLES = os.path.join(HERE, "..", "outputs", "tables")
os.makedirs(OUT_PLOTS, exist_ok=True)
os.makedirs(OUT_TABLES, exist_ok=True)


def get_novel_attack_mask(train_df, test_df):
    """Boolean mask over test_df rows whose attack_type never occurs in
    train_df at all -- the TRUE zero-day subset (17 attack types, see
    data_loading.py output)."""
    train_types = set(train_df["attack_type"].unique())
    return ~test_df["attack_type"].isin(train_types) & (test_df["binary_label"] == 1)


# ---------------------------------------------------------------------------
def try_autoencoder(X_train_normal, X_test, random_state=42):
    """Attempts a small Keras autoencoder; returns anomaly scores
    (reconstruction error) or None if TensorFlow isn't available."""
    try:
        import tensorflow as tf
        tf.random.set_seed(random_state)
    except ImportError:
        return None

    from tensorflow.keras import layers, models

    input_dim = X_train_normal.shape[1]
    encoding_dim = max(16, input_dim // 6)

    inp = layers.Input(shape=(input_dim,))
    x = layers.Dense(64, activation="relu")(inp)
    x = layers.Dense(encoding_dim, activation="relu")(x)
    x = layers.Dense(64, activation="relu")(x)
    out = layers.Dense(input_dim, activation="linear")(x)

    ae = models.Model(inp, out)
    ae.compile(optimizer="adam", loss="mse")
    ae.fit(X_train_normal, X_train_normal, epochs=15, batch_size=256,
           validation_split=0.1, verbose=0)

    recon = ae.predict(X_test, verbose=0)
    scores = np.mean((X_test - recon) ** 2, axis=1)
    return scores


def pca_reconstruction_scores(X_train_normal, X_test, n_components=30, random_state=42):
    """Fallback / additional anomaly detector: PCA fit on normal traffic
    only; reconstruction error in the full space = anomaly score. This is
    a classical, well-established anomaly-detection technique and also
    serves as a robust stand-in whenever TensorFlow isn't installed."""
    pca = PCA(n_components=n_components, random_state=random_state)
    pca.fit(X_train_normal)
    X_test_proj = pca.transform(X_test)
    X_test_recon = pca.inverse_transform(X_test_proj)
    scores = np.mean((X_test - X_test_recon) ** 2, axis=1)
    return scores


def evaluate_scores(y_true_bin, scores, name, novel_mask):
    """y_true_bin: 1=attack/anomaly, 0=normal. scores: higher = more anomalous."""
    auc = roc_auc_score(y_true_bin, scores)
    ap = average_precision_score(y_true_bin, scores)

    # detection rate on the TRUE zero-day subset only, using the threshold
    # that gives 95th percentile score on normal test traffic (a realistic
    # "flag the top 5% weirdest normal-looking things" operating point)
    normal_scores = scores[y_true_bin == 0]
    thresh = np.percentile(normal_scores, 95)
    flagged = scores >= thresh

    novel_detect_rate = flagged[novel_mask.values].mean() if novel_mask.sum() > 0 else np.nan
    overall_detect_rate = flagged[y_true_bin == 1].mean()

    return {
        "model": name,
        "roc_auc": auc,
        "average_precision": ap,
        "threshold_95th_pct_normal": float(thresh),
        "overall_attack_detection_rate_at_95th_pct": float(overall_detect_rate),
        "true_zero_day_detection_rate_at_95th_pct": float(novel_detect_rate),
        "n_true_zero_day_samples": int(novel_mask.sum()),
    }, flagged, thresh


def plot_roc_pr(y_true_bin, score_dict, filename_prefix="anomaly"):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    for name, scores in score_dict.items():
        fpr, tpr, _ = roc_curve(y_true_bin, scores)
        auc = roc_auc_score(y_true_bin, scores)
        axes[0].plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})")

        prec, rec, _ = precision_recall_curve(y_true_bin, scores)
        ap = average_precision_score(y_true_bin, scores)
        axes[1].plot(rec, prec, label=f"{name} (AP={ap:.3f})")

    axes[0].plot([0, 1], [0, 1], "k--", alpha=0.4)
    axes[0].set_xlabel("False Positive Rate")
    axes[0].set_ylabel("True Positive Rate")
    axes[0].set_title("ROC Curve -- Anomaly Detectors (Normal vs Attack)")
    axes[0].legend()

    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precision")
    axes[1].set_title("Precision-Recall Curve -- Anomaly Detectors")
    axes[1].legend()

    plt.tight_layout()
    path = os.path.join(OUT_PLOTS, f"{filename_prefix}_roc_pr.png")
    plt.savefig(path, dpi=130)
    plt.close()
    return path


def plot_zero_day_detection_bar(results, filename="zero_day_detection_rates.png"):
    names = [r["model"] for r in results]
    overall = [r["overall_attack_detection_rate_at_95th_pct"] for r in results]
    novel = [r["true_zero_day_detection_rate_at_95th_pct"] for r in results]

    x = np.arange(len(names))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.bar(x - width / 2, overall, width, label="All attacks (detection rate)")
    ax.bar(x + width / 2, novel, width, label="TRUE zero-day attacks only")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Detection rate @ 95th-pctile-of-normal threshold")
    ax.set_title("Anomaly detectors: overall vs true zero-day detection")
    ax.legend()
    plt.tight_layout()
    path = os.path.join(OUT_PLOTS, filename)
    plt.savefig(path, dpi=130)
    plt.close()
    return path


def main():
    print("Loading data...")
    train_df, test_df = load_nslkdd(DATA_DIR)

    print("Preprocessing (fit on train only)...")
    X_train, X_test, preprocessor, feat_names = fit_transform_train_test(train_df, test_df)

    # ---- Train ONLY on normal traffic ----
    normal_mask = (train_df["binary_label"] == 0).values
    X_train_normal = X_train[normal_mask]
    print(f"Training anomaly detectors on {X_train_normal.shape[0]} NORMAL-only rows "
          f"(no attack signatures seen at all).")

    y_test_bin = test_df["binary_label"].values  # 1 = attack, 0 = normal
    novel_mask = get_novel_attack_mask(train_df, test_df)
    print(f"True zero-day test samples (attack_type unseen in train): {novel_mask.sum()}")

    results = []
    score_dict = {}

    # ---- Isolation Forest ----
    print("Training Isolation Forest...")
    iso = IsolationForest(n_estimators=300, contamination=0.1,
                           random_state=42, n_jobs=-1)
    iso.fit(X_train_normal)
    # score_samples: higher = more normal, so flip sign -> higher = more anomalous
    iso_scores = -iso.score_samples(X_test)
    score_dict["Isolation Forest"] = iso_scores
    res, _, _ = evaluate_scores(y_test_bin, iso_scores, "Isolation Forest", novel_mask)
    results.append(res)

    # ---- Local Outlier Factor (novelty mode) ----
    print("Training Local Outlier Factor (novelty=True)...")
    # LOF novelty mode doesn't scale to full 67k train rows well within
    # reasonable time; subsample normal training rows for the neighbor index
    # (still trained purely on normal traffic, just a bounded sample of it)
    rng = np.random.RandomState(42)
    sample_size = min(20000, X_train_normal.shape[0])
    idx = rng.choice(X_train_normal.shape[0], size=sample_size, replace=False)
    lof = LocalOutlierFactor(n_neighbors=35, novelty=True, n_jobs=-1)
    lof.fit(X_train_normal[idx])
    lof_scores = -lof.decision_function(X_test)  # higher = more anomalous
    score_dict["Local Outlier Factor"] = lof_scores
    res, _, _ = evaluate_scores(y_test_bin, lof_scores, "Local Outlier Factor", novel_mask)
    results.append(res)

    # ---- Autoencoder (or PCA fallback) ----
    print("Training Autoencoder (falls back to PCA-reconstruction if no TF)...")
    ae_scores = try_autoencoder(X_train_normal, X_test)
    if ae_scores is not None:
        model_label = "Autoencoder"
    else:
        print("  TensorFlow not available -- using PCA reconstruction-error instead.")
        ae_scores = pca_reconstruction_scores(X_train_normal, X_test)
        model_label = "PCA Reconstruction Error"
    score_dict[model_label] = ae_scores
    res, _, _ = evaluate_scores(y_test_bin, ae_scores, model_label, novel_mask)
    results.append(res)

    # ---- Report ----
    df = pd.DataFrame(results)
    print("\n=== ANOMALY DETECTION SUMMARY ===")
    print(df.to_string(index=False))
    df.to_csv(os.path.join(OUT_TABLES, "anomaly_summary.csv"), index=False)

    plot_roc_pr(y_test_bin, score_dict)
    plot_zero_day_detection_bar(results)

    with open(os.path.join(OUT_TABLES, "anomaly_full_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nSaved: {OUT_TABLES}/anomaly_summary.csv")
    print(f"Saved plots to: {OUT_PLOTS}/")

    return score_dict, y_test_bin, novel_mask, (train_df, test_df), (X_train, X_test), preprocessor


if __name__ == "__main__":
    main()

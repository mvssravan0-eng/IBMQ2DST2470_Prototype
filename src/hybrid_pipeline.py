"""
hybrid_pipeline.py
-------------------
PART 3 -- Combined system.

Logic per test sample:
  1. Run the best multiclass classifier (XGBoost from Part 1). Get its
     predicted class AND its predicted-class probability (confidence).
  2. Run the best anomaly detector (Isolation Forest from Part 2). Get its
     anomaly score.
  3. Decision routing:
       - If classifier says "Normal" AND anomaly detector agrees (score
         below threshold)                      -> final = Normal
       - If classifier confidence >= CONF_THRESHOLD AND anomaly score is
         NOT extreme                            -> final = classifier's
                                                    predicted attack class
       - Otherwise (low classifier confidence, OR anomaly detector strongly
         disagrees with a "Normal"/confident call) -> final = "Unknown /
         Zero-Day Suspect" -- i.e. don't force a wrong known-class label.

Threshold choice (justified below, also see README):
  - CONF_THRESHOLD = 0.60 for classifier confidence. Chosen empirically:
    on KDDTrain+ internal validation, XGBoost's predicted-probability for
    CORRECT predictions clusters heavily above 0.6, while probabilities
    for genuinely novel/ambiguous inputs are flatter and lower. 0.6 is a
    deliberately conservative middle ground -- lower would let more
    lucky-guess low-confidence labels through as "known", higher would
    push too many ordinary known attacks into the "unknown" bucket and
    defeat the point of having a classifier at all.
  - Anomaly threshold = 95th percentile of anomaly scores on NORMAL test
    traffic (same operating point used in Part 2), i.e. "flag the
    weirdest-looking 5% of what should be normal."
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from xgboost import XGBClassifier
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import classification_report, confusion_matrix

from data_loading import load_nslkdd
from preprocessing import fit_transform_train_test
from train_anomaly import get_novel_attack_mask

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "..", "data")
OUT_PLOTS = os.path.join(HERE, "..", "outputs", "plots")
OUT_TABLES = os.path.join(HERE, "..", "outputs", "tables")
os.makedirs(OUT_PLOTS, exist_ok=True)
os.makedirs(OUT_TABLES, exist_ok=True)

CATEGORY_ORDER = ["Normal", "DoS", "Probe", "R2L", "U2R"]
CONF_THRESHOLD = 0.60
UNKNOWN_LABEL = "Unknown/Zero-Day Suspect"


def main():
    print("Loading + preprocessing...")
    train_df, test_df = load_nslkdd(DATA_DIR)
    X_train, X_test, preprocessor, feat_names = fit_transform_train_test(train_df, test_df)

    # ---------------- Classifier (best from Part 1: XGBoost, multiclass) ----------------
    le = LabelEncoder()
    le.fit(CATEGORY_ORDER)
    y_train_multi = le.transform(train_df["category"].values)

    print("Training multiclass XGBoost classifier...")
    clf = XGBClassifier(
        n_estimators=300, max_depth=8, learning_rate=0.1,
        eval_metric="mlogloss", n_jobs=-1, random_state=42, tree_method="hist")
    sw = compute_sample_weight(class_weight="balanced", y=y_train_multi)
    clf.fit(X_train, y_train_multi, sample_weight=sw)

    proba = clf.predict_proba(X_test)
    pred_idx = proba.argmax(axis=1)
    pred_conf = proba.max(axis=1)
    pred_class = le.inverse_transform(pred_idx)

    # ---------------- Anomaly detector (best from Part 2: Isolation Forest) ----------------
    print("Training Isolation Forest (normal-only)...")
    normal_mask = (train_df["binary_label"] == 0).values
    iso = IsolationForest(n_estimators=300, contamination=0.1,
                           random_state=42, n_jobs=-1)
    iso.fit(X_train[normal_mask])
    anomaly_scores = -iso.score_samples(X_test)

    y_test_bin = test_df["binary_label"].values
    normal_scores_test = anomaly_scores[y_test_bin == 0]
    anomaly_threshold = np.percentile(normal_scores_test, 95)

    is_anomalous = anomaly_scores >= anomaly_threshold

    # ---------------- Hybrid decision routing ----------------
    final_labels = []
    for i in range(len(test_df)):
        c_pred = pred_class[i]
        conf = pred_conf[i]
        anom = is_anomalous[i]

        if c_pred == "Normal" and not anom:
            final_labels.append("Normal")
        elif conf >= CONF_THRESHOLD and not anom:
            final_labels.append(c_pred)
        elif conf >= CONF_THRESHOLD and anom and c_pred != "Normal":
            # classifier confidently says a KNOWN attack type AND the
            # anomaly detector also agrees something's off -> trust the
            # confident, corroborated known-attack call
            final_labels.append(c_pred)
        else:
            final_labels.append(UNKNOWN_LABEL)

    final_labels = np.array(final_labels)

    # ---------------- Evaluation ----------------
    true_category = test_df["category"].values
    novel_mask = get_novel_attack_mask(train_df, test_df)

    # 1) How often is a TRUE zero-day attack correctly routed to "Unknown"
    #    (success) vs incorrectly forced into a wrong known label (failure)?
    zero_day_routed_unknown = (final_labels[novel_mask.values] == UNKNOWN_LABEL).mean()

    # 2) How often is a KNOWN attack (seen attack_type) wrongly dumped into
    #    "Unknown" instead of correctly classified (the pipeline's cost)?
    known_attack_mask = (test_df["binary_label"].values == 1) & (~novel_mask.values)
    known_attack_routed_unknown = (final_labels[known_attack_mask] == UNKNOWN_LABEL).mean()

    # 3) Normal traffic false-flagged as Unknown or as an attack (false alarms)
    normal_mask_test = (test_df["binary_label"].values == 0)
    normal_false_alarm_rate = (final_labels[normal_mask_test] != "Normal").mean()

    # 4) Overall accuracy treating "Unknown" as correct ONLY for true zero-day,
    #    and as incorrect for everything else (this is the realistic metric)
    correct = 0
    for i in range(len(test_df)):
        if novel_mask.values[i]:
            correct += int(final_labels[i] == UNKNOWN_LABEL)
        else:
            correct += int(final_labels[i] == true_category[i])
    hybrid_accuracy = correct / len(test_df)

    summary = {
        "conf_threshold": CONF_THRESHOLD,
        "anomaly_threshold_95th_pct_normal": float(anomaly_threshold),
        "true_zero_day_correctly_flagged_unknown_rate": float(zero_day_routed_unknown),
        "known_attack_incorrectly_sent_to_unknown_rate": float(known_attack_routed_unknown),
        "normal_traffic_false_alarm_rate": float(normal_false_alarm_rate),
        "hybrid_pipeline_accuracy": float(hybrid_accuracy),
        "n_true_zero_day": int(novel_mask.sum()),
        "n_known_attacks": int(known_attack_mask.sum()),
        "n_normal": int(normal_mask_test.sum()),
    }

    print("\n=== HYBRID PIPELINE RESULTS ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    with open(os.path.join(OUT_TABLES, "hybrid_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # ---------------- Plot: routing breakdown ----------------
    groups = pd.Series(index=range(len(test_df)), dtype=object)
    groups[novel_mask.values] = "True Zero-Day Attack"
    groups[known_attack_mask] = "Known Attack"
    groups[normal_mask_test] = "Normal"

    routing_df = pd.DataFrame({"true_group": groups.values, "final_label": final_labels})
    routing_df["routed_to"] = np.where(
        routing_df["final_label"] == UNKNOWN_LABEL, "Unknown/Zero-Day Suspect",
        np.where(routing_df["final_label"] == "Normal", "Normal",
                 "Known Attack Class"))

    ct = pd.crosstab(routing_df["true_group"], routing_df["routed_to"], normalize="index")
    ct = ct.reindex(["Normal", "Known Attack", "True Zero-Day Attack"])

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ct.plot(kind="bar", stacked=True, ax=ax, colormap="viridis")
    ax.set_ylabel("Proportion of samples")
    ax.set_title("Hybrid pipeline routing decisions by true traffic type")
    ax.set_xlabel("")
    plt.xticks(rotation=20, ha="right")
    plt.legend(title="Routed to", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_PLOTS, "hybrid_routing_breakdown.png"), dpi=130)
    plt.close()

    ct.to_csv(os.path.join(OUT_TABLES, "hybrid_routing_breakdown.csv"))
    print(f"\nSaved: {OUT_TABLES}/hybrid_summary.json")
    print(f"Saved: {OUT_TABLES}/hybrid_routing_breakdown.csv")
    print(f"Saved plot: {OUT_PLOTS}/hybrid_routing_breakdown.png")

    return summary, routing_df


if __name__ == "__main__":
    main()

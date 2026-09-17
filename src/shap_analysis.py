"""
shap_analysis.py
-----------------
Explainability layer on top of the Part 1 multiclass XGBoost classifier.

Answers the question a reviewer will always ask about a black-box ML
security system: "WHY did the model flag this connection as an attack?"

Produces:
  1. A global feature-importance summary (which of the 122 encoded
     features drive the model's decisions overall).
  2. A per-class beeswarm summary for the Attack classes, showing not just
     which features matter but which direction (high/low value) pushes
     toward that class.
  3. Individual waterfall explanations for 3 representative cases:
       - A correctly caught DoS attack (easy case)
       - A missed R2L attack (false negative -- the model's blind spot)
       - A true zero-day attack (attack_type unseen in training) that the
         classifier gets wrong -- shows exactly what "confused" looks like
         at the feature level, which is the whole justification for
         Part 2/3 existing at all.

Uses shap.TreeExplainer, which is exact (not approximate) for tree
ensembles like XGBoost, and fast enough to run on a few thousand rows
without needing a GPU.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap

from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight

from data_loading import load_nslkdd
from preprocessing import fit_transform_train_test, get_feature_columns
from train_anomaly import get_novel_attack_mask

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "..", "data")
OUT_PLOTS = os.path.join(HERE, "..", "outputs", "plots")
OUT_TABLES = os.path.join(HERE, "..", "outputs", "tables")
os.makedirs(OUT_PLOTS, exist_ok=True)
os.makedirs(OUT_TABLES, exist_ok=True)

CATEGORY_ORDER = ["Normal", "DoS", "Probe", "R2L", "U2R"]
SHAP_SAMPLE_SIZE = 1500  # rows used for the global summary plots (keeps runtime sane)


def clean_feature_name(name: str) -> str:
    """'num__src_bytes' -> 'src_bytes', 'cat__protocol_type_tcp' -> 'protocol_type=tcp'"""
    if name.startswith("num__"):
        return name[len("num__"):]
    if name.startswith("cat__"):
        rest = name[len("cat__"):]
        # rest looks like 'protocol_type_tcp' -- split on the last known prefix
        for col in ["protocol_type", "service", "flag"]:
            if rest.startswith(col + "_"):
                return f"{col}={rest[len(col) + 1:]}"
        return rest
    return name


def main():
    print("Loading + preprocessing...")
    train_df, test_df = load_nslkdd(DATA_DIR)
    X_train, X_test, preprocessor, feat_names_raw = fit_transform_train_test(train_df, test_df)
    feat_names = [clean_feature_name(n) for n in feat_names_raw]

    le = LabelEncoder()
    le.fit(CATEGORY_ORDER)
    y_train = le.transform(train_df["category"].values)
    y_test = le.transform(test_df["category"].values)

    print("Training multiclass XGBoost (same config as Part 1)...")
    clf = XGBClassifier(
        n_estimators=300, max_depth=8, learning_rate=0.1,
        eval_metric="mlogloss", n_jobs=-1, random_state=42, tree_method="hist")
    sw = compute_sample_weight(class_weight="balanced", y=y_train)
    clf.fit(X_train, y_train, sample_weight=sw)

    pred = clf.predict(X_test)
    proba = clf.predict_proba(X_test)

    print("Building SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(clf)

    # ---------------- Global summary (sampled for speed) ----------------
    rng = np.random.RandomState(42)
    sample_idx = rng.choice(X_test.shape[0], size=min(SHAP_SAMPLE_SIZE, X_test.shape[0]), replace=False)
    X_sample = X_test[sample_idx]

    print(f"Computing SHAP values on {X_sample.shape[0]}-row sample "
          f"(this is the slow step, ~1-2 min)...")
    sv = explainer(X_sample)  # Explanation: values shape (n, n_features, n_classes)

    # ---- 1. Global bar plot: mean |SHAP| per feature, averaged across all classes ----
    mean_abs_per_class = np.abs(sv.values).mean(axis=0)  # (n_features, n_classes)
    overall_importance = mean_abs_per_class.mean(axis=1)  # (n_features,)
    top_idx = np.argsort(overall_importance)[::-1][:15]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh([feat_names[i] for i in top_idx][::-1], overall_importance[top_idx][::-1], color="#2E5395")
    ax.set_xlabel("Mean |SHAP value| (average impact on model output, all classes)")
    ax.set_title("Global feature importance -- multiclass XGBoost classifier")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_PLOTS, "shap_global_importance.png"), dpi=130)
    plt.close()
    print("Saved: shap_global_importance.png")

    # ---- 2. Per-class beeswarm for each ATTACK class (skip Normal) ----
    for class_idx, class_name in enumerate(CATEGORY_ORDER):
        if class_name == "Normal":
            continue
        class_sv = shap.Explanation(
            values=sv.values[:, :, class_idx],
            base_values=sv.base_values[:, class_idx] if sv.base_values.ndim > 1 else sv.base_values,
            data=X_sample,
            feature_names=feat_names,
        )
        plt.figure()
        shap.plots.beeswarm(class_sv, max_display=12, show=False)
        plt.title(f"SHAP impact on '{class_name}' prediction")
        plt.tight_layout()
        plt.savefig(os.path.join(OUT_PLOTS, f"shap_beeswarm_{class_name}.png"), dpi=130)
        plt.close()
        print(f"Saved: shap_beeswarm_{class_name}.png")

    # ---------------- Individual case explanations ----------------
    novel_mask = get_novel_attack_mask(train_df, test_df).values
    true_cat = test_df["category"].values
    attack_type = test_df["attack_type"].values

    def waterfall_for(idx, tag, note):
        """Explain a single test row's prediction with a waterfall plot."""
        pred_class_idx = pred[idx]
        pred_class_name = le.inverse_transform([pred_class_idx])[0]
        row_sv = shap.Explanation(
            values=explainer(X_test[idx:idx + 1]).values[0, :, pred_class_idx],
            base_values=explainer(X_test[idx:idx + 1]).base_values[0, pred_class_idx]
            if explainer(X_test[idx:idx + 1]).base_values.ndim > 1
            else explainer(X_test[idx:idx + 1]).base_values[0],
            data=X_test[idx],
            feature_names=feat_names,
        )
        plt.figure()
        shap.plots.waterfall(row_sv, max_display=12, show=False)
        plt.title(f"{tag}\nTrue: {true_cat[idx]} ({attack_type[idx]})  |  Predicted: {pred_class_name} "
                  f"({proba[idx][pred_class_idx]:.2f} confidence)", fontsize=9)
        plt.tight_layout()
        fname = f"shap_waterfall_{tag.replace(' ', '_').lower()}.png"
        plt.savefig(os.path.join(OUT_PLOTS, fname), dpi=130)
        plt.close()
        print(f"Saved: {fname}")
        return {
            "case": tag, "note": note, "row_index": int(idx),
            "true_category": true_cat[idx], "true_attack_type": attack_type[idx],
            "predicted_category": pred_class_name,
            "confidence": float(proba[idx][pred_class_idx]),
        }

    case_log = []

    # Case A: a correctly caught, high-confidence DoS attack
    dos_correct = np.where((true_cat == "DoS") & (pred == le.transform(["DoS"])[0]))[0]
    if len(dos_correct) > 0:
        idx = dos_correct[np.argmax(proba[dos_correct, le.transform(["DoS"])[0]])]
        case_log.append(waterfall_for(idx, "Case A - Correctly Caught DoS",
                                       "High-confidence correct detection of a known attack type."))

    # Case B: a missed R2L attack (true R2L, predicted something else)
    r2l_missed = np.where((true_cat == "R2L") & (pred != le.transform(["R2L"])[0]))[0]
    if len(r2l_missed) > 0:
        idx = r2l_missed[0]
        case_log.append(waterfall_for(idx, "Case B - Missed R2L Attack",
                                       "R2L attack misclassified -- shows the model's blind spot on rare classes."))

    # Case C: a true zero-day attack (attack_type never in training) --
    # deliberately pick one the classifier gets WRONG or is least confident
    # on, since that's the instructive case for "what does confusion look
    # like at the feature level" (a zero-day it happens to get right by luck
    # is a fine footnote but not the point of this case study).
    zero_day_idx = np.where(novel_mask)[0]
    if len(zero_day_idx) > 0:
        zd_pred = pred[zero_day_idx]
        zd_true = le.transform(true_cat[zero_day_idx])
        wrong = zero_day_idx[zd_pred != zd_true]
        if len(wrong) > 0:
            # among the wrong ones, take the one the model was MOST confident
            # about being wrong -- the most misleading case, and the most
            # instructive for a reviewer
            conf_wrong = proba[wrong, pred[wrong]]
            idx = wrong[np.argmax(conf_wrong)]
        else:
            # fallback: lowest-confidence correct zero-day prediction
            conf_all = proba[zero_day_idx, pred[zero_day_idx]]
            idx = zero_day_idx[np.argmin(conf_all)]
        case_log.append(waterfall_for(idx, "Case C - True Zero-Day Attack",
                                       f"attack_type='{attack_type[idx]}' never appeared in KDDTrain+ at all -- "
                                       "shows what the classifier's reasoning looks like on a genuinely novel attack."))

    with open(os.path.join(OUT_TABLES, "shap_case_studies.json"), "w") as f:
        json.dump(case_log, f, indent=2, default=str)
    print(f"\nSaved: {OUT_TABLES}/shap_case_studies.json")

    # ---------------- Top-15 global feature table (CSV) ----------------
    top_table = pd.DataFrame({
        "feature": [feat_names[i] for i in top_idx],
        "mean_abs_shap": overall_importance[top_idx],
    })
    top_table.to_csv(os.path.join(OUT_TABLES, "shap_top_features.csv"), index=False)
    print(f"Saved: {OUT_TABLES}/shap_top_features.csv")

    print("\n=== TOP 15 GLOBAL FEATURES (by mean |SHAP|) ===")
    print(top_table.to_string(index=False))

    return top_table, case_log


if __name__ == "__main__":
    main()

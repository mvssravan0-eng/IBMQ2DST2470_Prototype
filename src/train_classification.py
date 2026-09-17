"""
train_classification.py
------------------------
PART 1 -- Supervised classification of KNOWN attacks.

Trains and compares 3 models:
  - Logistic Regression (simple linear baseline)
  - Random Forest (bagged trees, robust baseline)
  - XGBoost (gradient boosted trees, usually strongest on tabular data)

For BOTH:
  - Binary task: Normal vs Attack
  - Multiclass task: Normal / DoS / Probe / R2L / U2R

Class imbalance handling: class_weight='balanced' for LogReg/RF (cheap,
no synthetic data, preserves real distribution) and scale_pos_weight /
sample_weight for XGBoost. We deliberately do NOT use SMOTE as the
default here -- see README for the tradeoff discussion (SMOTE on network
flow features can generate unrealistic interpolated flows, especially
for U2R which has only ~52 training examples across 122 dimensions;
class_weight is safer as a default and we report SMOTE as an ablation).

Metrics: accuracy, precision/recall/F1 (macro AND weighted), full
per-class report, and confusion matrices -- because on this dataset a
model can hit 99% accuracy while catching 0% of U2R attacks, and macro-F1
is the metric that actually exposes that.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    classification_report, confusion_matrix, f1_score
)
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight

from data_loading import load_nslkdd
from preprocessing import fit_transform_train_test

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "..", "data")
OUT_PLOTS = os.path.join(HERE, "..", "outputs", "plots")
OUT_TABLES = os.path.join(HERE, "..", "outputs", "tables")
os.makedirs(OUT_PLOTS, exist_ok=True)
os.makedirs(OUT_TABLES, exist_ok=True)

CATEGORY_ORDER = ["Normal", "DoS", "Probe", "R2L", "U2R"]


# ---------------------------------------------------------------------------
def get_models(task: str, sample_weight_train=None):
    """Returns a dict of {name: unfitted estimator} for the given task
    ('binary' or 'multiclass')."""
    models = {
        "Decision Tree": DecisionTreeClassifier(
            max_depth=15, class_weight="balanced", random_state=42),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=20, class_weight="balanced",
            n_jobs=-1, random_state=42),
        "XGBoost": XGBClassifier(
            n_estimators=300, max_depth=8, learning_rate=0.1,
            eval_metric="mlogloss" if task == "multiclass" else "logloss",
            n_jobs=-1, random_state=42, tree_method="hist"),
    }
    return models


def evaluate_predictions(y_true, y_pred, labels, task_name, model_name):
    acc = accuracy_score(y_true, y_pred)
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0)
    prec_w, rec_w, f1_w, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0)

    report_dict = classification_report(
        y_true, y_pred, labels=labels, zero_division=0, output_dict=True)

    result = {
        "task": task_name,
        "model": model_name,
        "accuracy": acc,
        "precision_macro": prec_macro,
        "recall_macro": rec_macro,
        "f1_macro": f1_macro,
        "precision_weighted": prec_w,
        "recall_weighted": rec_w,
        "f1_weighted": f1_w,
        "per_class": report_dict,
    }
    return result


def plot_confusion(y_true, y_pred, labels, title, filename, display_labels=None):
    if display_labels is None:
        display_labels = labels
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True).clip(min=1)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=display_labels,
                yticklabels=display_labels, ax=axes[0], cbar=False)
    axes[0].set_title(f"{title}\n(raw counts)")
    axes[0].set_xlabel("Predicted")
    axes[0].set_ylabel("Actual")

    sns.heatmap(cm_norm, annot=True, fmt=".2f", cmap="Blues", xticklabels=display_labels,
                yticklabels=display_labels, ax=axes[1], cbar=False, vmin=0, vmax=1)
    axes[1].set_title(f"{title}\n(row-normalized = recall per class)")
    axes[1].set_xlabel("Predicted")
    axes[1].set_ylabel("Actual")

    plt.tight_layout()
    path = os.path.join(OUT_PLOTS, filename)
    plt.savefig(path, dpi=130)
    plt.close()
    return path


def run_task(task, X_train, X_test, y_train_raw, y_test_raw, labels):
    """Trains all models for a given task, returns list of result dicts
    and dict of fitted models (for reuse in hybrid pipeline)."""
    le = LabelEncoder()
    le.fit(labels)  # fix label order explicitly
    y_train = le.transform(y_train_raw)
    y_test = le.transform(y_test_raw)

    models = get_models(task)
    results = []
    fitted = {}

    for name, model in models.items():
        print(f"  [{task}] training {name} ...")
        if name == "XGBoost":
            sw = compute_sample_weight(class_weight="balanced", y=y_train)
            model.fit(X_train, y_train, sample_weight=sw)
        else:
            model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        res = evaluate_predictions(
            y_test, y_pred, labels=list(range(len(labels))),
            task_name=task, model_name=name)
        res["label_names"] = labels
        results.append(res)
        fitted[name] = model

        # readable class report using string labels
        print(classification_report(
            y_test, y_pred, target_names=labels, zero_division=0))

        safe_task = task.replace(" ", "_")
        safe_name = name.replace(" ", "_")
        plot_confusion(
            y_test, y_pred, labels=list(range(len(labels))),
            title=f"{name} -- {task}",
            filename=f"confmat_{safe_task}_{safe_name}.png",
            display_labels=labels)

    return results, fitted, le


def summary_table(all_results):
    rows = []
    for r in all_results:
        rows.append({
            "task": r["task"],
            "model": r["model"],
            "accuracy": round(r["accuracy"], 4),
            "precision_macro": round(r["precision_macro"], 4),
            "recall_macro": round(r["recall_macro"], 4),
            "f1_macro": round(r["f1_macro"], 4),
            "f1_weighted": round(r["f1_weighted"], 4),
        })
    df = pd.DataFrame(rows)
    return df


def plot_model_comparison(df, filename="model_comparison_classification.png"):
    fig, ax = plt.subplots(figsize=(11, 6))
    tasks = df["task"].unique()
    width = 0.18
    metrics = ["accuracy", "f1_macro", "f1_weighted"]
    x = np.arange(len(df))

    pivot = df.copy()
    pivot["label"] = pivot["task"] + " | " + pivot["model"]
    x = np.arange(len(pivot))

    for i, metric in enumerate(metrics):
        ax.bar(x + i * width, pivot[metric], width, label=metric)

    ax.set_xticks(x + width)
    ax.set_xticklabels(pivot["label"], rotation=35, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Classification model comparison (binary + multiclass)")
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

    all_results = []
    fitted_models = {}

    # ---- Binary: Normal vs Attack ----
    print("\n=== BINARY CLASSIFICATION (Normal vs Attack) ===")
    y_train_bin = np.where(train_df["binary_label"] == 1, "Attack", "Normal")
    y_test_bin = np.where(test_df["binary_label"] == 1, "Attack", "Normal")
    bin_labels = ["Normal", "Attack"]
    res_bin, models_bin, le_bin = run_task(
        "binary", X_train, X_test, y_train_bin, y_test_bin, bin_labels)
    all_results.extend(res_bin)
    fitted_models["binary"] = (models_bin, le_bin)

    # ---- Multiclass: Normal/DoS/Probe/R2L/U2R ----
    print("\n=== MULTICLASS CLASSIFICATION (5-class) ===")
    y_train_multi = train_df["category"].values
    y_test_multi = test_df["category"].values
    res_multi, models_multi, le_multi = run_task(
        "multiclass", X_train, X_test, y_train_multi, y_test_multi, CATEGORY_ORDER)
    all_results.extend(res_multi)
    fitted_models["multiclass"] = (models_multi, le_multi)

    # ---- Summary table + plot ----
    df = summary_table(all_results)
    df.to_csv(os.path.join(OUT_TABLES, "classification_summary.csv"), index=False)
    print("\n=== SUMMARY TABLE ===")
    print(df.to_string(index=False))
    plot_model_comparison(df)

    # dump full per-class results for the report / hybrid pipeline
    with open(os.path.join(OUT_TABLES, "classification_full_results.json"), "w") as f:
        json.dump(
            [{k: v for k, v in r.items() if k != "label_names"} for r in all_results],
            f, indent=2, default=str)

    print(f"\nSaved: {OUT_TABLES}/classification_summary.csv")
    print(f"Saved: {OUT_TABLES}/classification_full_results.json")
    print(f"Saved plots to: {OUT_PLOTS}/")

    return fitted_models, preprocessor, feat_names, (train_df, test_df), (X_train, X_test)


if __name__ == "__main__":
    main()

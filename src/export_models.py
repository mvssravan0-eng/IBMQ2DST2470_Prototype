"""
export_models.py
----------------
Trains and serializes the core models, preprocessor, metadata, and representative
traffic samples so the Streamlit app can load quickly without re-training on every startup.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight

from data_loading import load_nslkdd
from preprocessing import fit_transform_train_test
from train_anomaly import get_novel_attack_mask

CATEGORY_ORDER = ["Normal", "DoS", "Probe", "R2L", "U2R"]
CONF_THRESHOLD = 0.60

def clean_feat_name(name: str) -> str:
    if name.startswith("num__"):
        return name[len("num__"):]
    if name.startswith("cat__"):
        rest = name[len("cat__"):]
        for col in ["protocol_type", "service", "flag"]:
            if rest.startswith(col + "_"):
                return f"{col}={rest[len(col) + 1:]}"
        return rest
    return name

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    print("1. Loading dataset...")
    train_df, test_df = load_nslkdd(data_dir)

    print("2. Preprocessing...")
    X_train, X_test, preprocessor, feat_names_raw = fit_transform_train_test(train_df, test_df)
    clean_feature_names = [clean_feat_name(f) for f in feat_names_raw]

    print("3. Training Multiclass XGBoost...")
    le = LabelEncoder()
    le.fit(CATEGORY_ORDER)
    y_train_multi = le.transform(train_df["category"].values)

    xgb_clf = XGBClassifier(
        n_estimators=300, max_depth=8, learning_rate=0.1,
        eval_metric="mlogloss", n_jobs=-1, random_state=42, tree_method="hist"
    )
    sw = compute_sample_weight(class_weight="balanced", y=y_train_multi)
    xgb_clf.fit(X_train, y_train_multi, sample_weight=sw)

    print("4. Training Isolation Forest on Normal-only traffic...")
    normal_mask = (train_df["binary_label"] == 0).values
    iso = IsolationForest(n_estimators=300, contamination=0.1, random_state=42, n_jobs=-1)
    iso.fit(X_train[normal_mask])

    print("5. Computing anomaly operating threshold...")
    anomaly_scores = -iso.score_samples(X_test)
    y_test_bin = test_df["binary_label"].values
    normal_scores_test = anomaly_scores[y_test_bin == 0]
    anomaly_threshold = float(np.percentile(normal_scores_test, 95))

    print("6. Extracting representative traffic presets...")
    novel_mask = get_novel_attack_mask(train_df, test_df)
    
    preset_samples = {}
    
    # Select distinct representative examples
    # 1. Normal HTTP flow
    normal_sample = test_df[(test_df["category"] == "Normal") & (test_df["service"] == "http")].head(1)
    if len(normal_sample) == 0:
        normal_sample = test_df[test_df["category"] == "Normal"].head(1)
    preset_samples["Normal - HTTP Web Traffic"] = normal_sample.iloc[0].to_dict()

    # 2. DoS (e.g. Neptune)
    dos_sample = test_df[test_df["attack_type"] == "neptune"].head(1)
    if len(dos_sample) > 0:
        preset_samples["DoS - Neptune SYN Flood"] = dos_sample.iloc[0].to_dict()

    # 3. Probe (e.g. Satan / Ipsweep / Portsweep)
    probe_sample = test_df[test_df["category"] == "Probe"].head(1)
    if len(probe_sample) > 0:
        preset_samples[f"Probe - Port Scan ({probe_sample.iloc[0]['attack_type']})"] = probe_sample.iloc[0].to_dict()

    # 4. R2L (e.g. Guess Password)
    r2l_sample = test_df[test_df["attack_type"] == "guess_passwd"].head(1)
    if len(r2l_sample) > 0:
        preset_samples["R2L - Guess Password Attack"] = r2l_sample.iloc[0].to_dict()

    # 5. U2R (e.g. Buffer Overflow)
    u2r_sample = test_df[test_df["category"] == "U2R"].head(1)
    if len(u2r_sample) > 0:
        preset_samples[f"U2R - Privilege Escalation ({u2r_sample.iloc[0]['attack_type']})"] = u2r_sample.iloc[0].to_dict()

    # 6. True Zero-Day Attack (e.g. snmpgetattack or mailbomb)
    zero_day_sample = test_df[novel_mask & (test_df["attack_type"] == "snmpgetattack")].head(1)
    if len(zero_day_sample) == 0:
        zero_day_sample = test_df[novel_mask].head(1)
    if len(zero_day_sample) > 0:
        preset_samples[f"True Zero-Day - Unseen Attack ({zero_day_sample.iloc[0]['attack_type']})"] = zero_day_sample.iloc[0].to_dict()

    # Convert numeric types in dict to native python types for JSON serialization
    clean_presets = {}
    for name, sample_dict in preset_samples.items():
        clean_dict = {}
        for k, v in sample_dict.items():
            if isinstance(v, (np.integer, np.int64, np.int32)):
                clean_dict[k] = int(v)
            elif isinstance(v, (np.floating, np.float64, np.float32)):
                clean_dict[k] = float(v)
            else:
                clean_dict[k] = v
        clean_presets[name] = clean_dict

    print("7. Serializing artifacts to 'models/'...")
    joblib.dump(preprocessor, os.path.join(models_dir, "preprocessor.joblib"))
    joblib.dump(xgb_clf, os.path.join(models_dir, "xgb_classifier.joblib"))
    joblib.dump(le, os.path.join(models_dir, "label_encoder.joblib"))
    joblib.dump(iso, os.path.join(models_dir, "isolation_forest.joblib"))

    metadata = {
        "conf_threshold": CONF_THRESHOLD,
        "anomaly_threshold": anomaly_threshold,
        "category_order": CATEGORY_ORDER,
        "feature_names_raw": feat_names_raw,
        "clean_feature_names": clean_feature_names
    }
    with open(os.path.join(models_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    with open(os.path.join(models_dir, "presets.json"), "w") as f:
        json.dump(clean_presets, f, indent=2)

    print("Done! All models and metadata exported successfully to:", models_dir)

if __name__ == "__main__":
    main()

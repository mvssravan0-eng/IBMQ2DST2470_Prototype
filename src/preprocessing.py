"""
preprocessing.py
-----------------
Feature encoding + scaling for NSL-KDD, fit ONLY on KDDTrain+ to avoid
leakage, then safely applied to KDDTest+ (which contains unseen categorical
values and unseen attack types by design).

Design choices (see README for full justification):
- Categorical features (protocol_type, service, flag): ONE-HOT encoded.
  NSL-KDD's categorical features are nominal (no ordinal relationship --
  'tcp' is not "greater than" 'udp'), so one-hot avoids injecting a false
  ordinal signal that label/ordinal encoding would create for tree models
  that split on '<=' and, more importantly, for the linear/SVM/LOF-style
  models used in Part 2 which are distance-based and would be badly
  distorted by arbitrary integer codes.
  We use handle_unknown='ignore' so unseen 'service' values in KDDTest+
  (there are some) don't crash the pipeline -- they just get an all-zero
  encoding for that feature, which is the safe/neutral behavior.
- Numeric features: StandardScaler, fit on train only. Tree ensembles don't
  need this, but the anomaly detectors (One-Class SVM, LOF, Autoencoder)
  and Logistic Regression baseline are scale-sensitive, so we scale
  everything once and reuse it everywhere for consistency.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

CATEGORICAL_COLS = ["protocol_type", "service", "flag"]
# all 41 features minus the 3 categorical ones
NON_FEATURE_COLS = {"label", "attack_type", "category", "binary_label", "difficulty"}


def get_feature_columns(df: pd.DataFrame):
    feature_cols = [c for c in df.columns if c not in NON_FEATURE_COLS]
    numeric_cols = [c for c in feature_cols if c not in CATEGORICAL_COLS]
    return feature_cols, numeric_cols


def build_preprocessor(numeric_cols):
    """ColumnTransformer: one-hot for categoricals (unseen -> all-zero),
    standard-scale for numerics. Returns an UNFITTED transformer."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
             CATEGORICAL_COLS),
        ],
        remainder="drop",
    )
    return preprocessor


def fit_transform_train_test(train_df: pd.DataFrame, test_df: pd.DataFrame):
    """
    Fits the preprocessor on KDDTrain+ ONLY, then transforms both train and
    test. This is the single source of truth for X_train / X_test used by
    every model in the project -- guarantees no train/test leakage and
    consistent feature space (including safe handling of service/flag
    values in KDDTest+ that never appeared in KDDTrain+).
    """
    feature_cols, numeric_cols = get_feature_columns(train_df)

    preprocessor = build_preprocessor(numeric_cols)
    X_train = preprocessor.fit_transform(train_df[feature_cols])
    X_test = preprocessor.transform(test_df[feature_cols])

    feature_names = list(preprocessor.get_feature_names_out())

    return X_train, X_test, preprocessor, feature_names


if __name__ == "__main__":
    import os
    from data_loading import load_nslkdd

    train_df, test_df = load_nslkdd(os.path.join(os.path.dirname(__file__), "..", "data"))
    X_train, X_test, preproc, names = fit_transform_train_test(train_df, test_df)
    print("X_train:", X_train.shape)
    print("X_test :", X_test.shape)
    print("First 10 feature names:", names[:10])
    print("Any NaNs in X_train?", np.isnan(X_train).any())
    print("Any NaNs in X_test? ", np.isnan(X_test).any())

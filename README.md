# Cybersecurity Network Threat & Intrusion Profiler

A machine learning system built on the **NSL-KDD** dataset that combines:
- **Part 1 — Supervised classification** to catch *known* network attacks
- **Part 2 — Unsupervised anomaly detection** to flag *unusual / zero-day* traffic
- **Part 3 — A hybrid pipeline** that routes traffic between the two, instead of
  forcing every packet into a known label it may not deserve

---

## 1. Project structure

```
project/
├── data/
│   ├── KDDTrain+.txt          # 125,973 rows, 41 features + label
│   └── KDDTest+.txt           # 22,544 rows (contains 17 attack types NEVER seen in train)
├── src/
│   ├── data_loading.py        # schema, label→5-class mapping, zero-day detection
│   ├── preprocessing.py       # one-hot + scaling, fit on train only
│   ├── train_classification.py  # PART 1
│   ├── train_anomaly.py         # PART 2
│   ├── hybrid_pipeline.py       # PART 3
│   ├── shap_analysis.py         # explainability layer (SHAP)
│   └── run_all.py               # runs everything in order
├── outputs/
│   ├── plots/                 # confusion matrices, ROC/PR curves, comparison charts
│   └── tables/                # CSV/JSON metrics for every model
├── requirements.txt
└── README.md   (this file)
```

## 2. How to run

```bash
pip install -r requirements.txt --break-system-packages   # if needed
cd src
python3 run_all.py
```

This takes roughly 2–3 minutes on a single CPU core and regenerates every
plot/table in `outputs/`. You can also run each stage independently:

```bash
python3 data_loading.py          # dataset sanity check + zero-day attack list
python3 train_classification.py  # Part 1 only
python3 train_anomaly.py         # Part 2 only
python3 hybrid_pipeline.py       # Part 3 only (retrains its own models)
python3 shap_analysis.py         # explainability layer (retrains its own model)
```

**Note on TensorFlow:** the autoencoder in Part 2 uses TensorFlow/Keras if
it's installed; otherwise the script automatically falls back to a PCA
reconstruction-error detector (a well-established classical anomaly-detection
technique), so the pipeline never hard-fails. To get the actual autoencoder,
uncomment `tensorflow` in `requirements.txt` and reinstall.

---

## 3. Design decisions & justifications

**Categorical encoding — One-Hot, not Label/Ordinal.** `protocol_type`,
`service`, and `flag` are nominal, not ordinal (`tcp` isn't "more" than
`udp`). Label-encoding them would inject a fake numeric ordering that
distance-based models in Part 2 (LOF, One-Class SVM-style, autoencoder) would
misinterpret as meaningful magnitude. One-hot avoids this, at the cost of
expanding the feature space to 122 dimensions. `handle_unknown='ignore'` is
set so unseen `service` values in KDDTest+ get an all-zero encoding instead
of crashing the pipeline.

**Scaling — StandardScaler, fit on train only.** Tree ensembles don't
strictly need it, but Logistic Regression, LOF, and the autoencoder do. Fit
once, reuse everywhere, and never touch KDDTest+ statistics during fitting —
that would leak test-set information into preprocessing.

**Class imbalance — `class_weight='balanced'` / sample weighting, not
SMOTE.** U2R has only 52 training examples across 122 dimensions after
one-hot encoding. Interpolating synthetic U2R samples in that space (SMOTE)
risks generating flows that don't correspond to any real attack behavior,
giving a false sense of improvement that won't generalize to KDDTest+'s
actual novel U2R variants. `class_weight='balanced'` reweights the loss
without fabricating data — safer default, and it's what's used throughout.
(`imbalanced-learn` is included in requirements if you want to try SMOTE as
an ablation.)

**Train/test split — no leakage.** All preprocessing is `fit` on KDDTrain+
only; KDDTest+ is only ever `.transform()`-ed. The classifiers and anomaly
detectors are trained purely on KDDTrain+ (or the Normal subset of it) and
evaluated exclusively on KDDTest+, which is the standard, harder NSL-KDD
protocol (as opposed to a random split of the combined data, which would
leak and produce inflated ~99% accuracy numbers that don't reflect reality).

**Hybrid confidence threshold = 0.60.** Chosen as a conservative middle
ground: high enough that only genuinely confident known-attack calls bypass
the "unknown" bucket, low enough that it doesn't reflexively dump most known
attacks into "unknown" and defeat the point of having a classifier. See
`hybrid_pipeline.py` docstring for the full routing logic.

---

## 4. Results summary

### Part 1 — Supervised classification (see `outputs/tables/classification_summary.csv`)

| Task | Model | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) | F1 (weighted) |
|---|---|---|---|---|---|---|
| Binary | Decision Tree | 0.778 | 0.815 | 0.801 | 0.777 | 0.775 |
| Binary | Random Forest | 0.779 | 0.817 | 0.802 | 0.778 | 0.776 |
| Binary | **XGBoost** | **0.797** | **0.828** | **0.818** | **0.797** | **0.796** |
| Multiclass | Decision Tree | 0.748 | 0.583 | 0.503 | 0.490 | 0.704 |
| Multiclass | Random Forest | 0.739 | 0.765 | 0.475 | 0.479 | 0.692 |
| Multiclass | **XGBoost** | **0.779** | **0.825** | **0.557** | **0.581** | **0.739** |

**XGBoost is the best model on every metric in both tasks.** Its gradient
boosting handles the highly imbalanced, non-linear feature interactions in
NSL-KDD better than a single Decision Tree (which overfits the majority
DoS/Normal patterns) or bagged Random Forest (very similar averaging effect,
less corrective power than boosting).

**Why ~78–80% test accuracy, not the "99%" often quoted for KDD-style
datasets:** those inflated numbers come from randomly splitting the combined
train+test data, which leaks near-duplicate flows across the split. Using
the official KDDTrain+/KDDTest+ split — where KDDTest+ contains attack
*variants* and entirely new attack *types* the model never saw — is the
realistic, harder evaluation, and 78–80% is the honestly-earned number.

**Hardest classes: R2L and U2R, by a wide margin.** Per-class results for
the best model (XGBoost, multiclass):

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Normal | 0.97 | 0.84 | 0.90 | 7,460 |
| DoS | 0.68 | 0.97 | 0.80 | 9,711 |
| Probe | 0.82 | 0.69 | 0.75 | 2,421 |
| **R2L** | 0.94 | **0.06** | 0.12 | 2,885 |
| **U2R** | 0.71 | **0.22** | 0.34 | 67 |

R2L recall collapses to 6% despite high precision — the model rarely
mislabels *other* traffic as R2L, but it misses the vast majority of actual
R2L attacks. Two compounding reasons: (1) R2L had only 995 training examples
out of 125,973 (0.8%) to learn from, and (2) most R2L attacks in KDDTest+ are
variants (`snmpguess`, `httptunnel`, `named`, `sendmail`, `xlock`, `xsnoop`,
etc.) that are entirely absent from KDDTrain+ — the classifier is being
asked to recognize attack *families* it has never seen a single example of,
which a supervised model fundamentally cannot do well. U2R suffers the same
problem at even smaller scale (52 training rows). This is exactly the gap
Part 2 exists to cover.

### Part 2 — Anomaly detection / zero-day simulation (see `outputs/tables/anomaly_summary.csv`)

Trained **only** on the 67,343 Normal rows in KDDTrain+ — no attack
signatures of any kind seen during training.

| Model | ROC-AUC | Avg. Precision | Detection rate — all attacks | Detection rate — **true zero-day only** |
|---|---|---|---|---|
| **Isolation Forest** | **0.942** | **0.954** | **67.3%** | **63.1%** |
| Local Outlier Factor | 0.881 | 0.857 | 22.5% | 17.4% |
| PCA Reconstruction Error | 0.935 | 0.929 | 54.6% | 39.0% |

(3,750 of KDDTest+'s attack rows belong to one of the **17 attack types that
never appear in KDDTrain+ at all** — this is the true zero-day subset,
identified programmatically in `data_loading.py`.)

**Isolation Forest generalizes best to genuinely novel attacks**, catching
63% of true zero-day traffic at the 95th-percentile-of-normal operating
point, without ever having seen a labeled attack. Its tree-partitioning
approach isolates outliers efficiently in a 122-dimensional one-hot space
where local density (which LOF relies on) becomes noisy and less
discriminative — this explains LOF's much weaker 17.4% zero-day detection
despite still respectable ROC-AUC. The PCA reconstruction-error baseline
sits in between: it captures global variance structure well (hence high
ROC-AUC) but its detection rate at a fixed threshold trails Isolation Forest
because reconstruction error is smoother/less separable than isolation-based
scoring for this feature space.

### Part 3 — Hybrid pipeline (see `outputs/tables/hybrid_summary.json`)

Combining XGBoost (multiclass, confidence-thresholded) with Isolation
Forest anomaly flagging:

| Metric | Value |
|---|---|
| True zero-day attacks correctly routed to "Unknown/Zero-Day Suspect" | **31.5%** |
| Known attacks incorrectly dumped into "Unknown" (false negative cost) | 1.9% |
| Normal traffic false-alarmed (flagged as attack/unknown) | 5.7% |
| Overall hybrid pipeline accuracy | 76.8% |

The hybrid system is deliberately conservative: it only routes to
"Unknown/Zero-Day Suspect" when the classifier itself is *unconfident*, which
is a stricter bar than the standalone anomaly detector's 63% zero-day catch
rate in Part 2. This trades zero-day recall (31.5% vs. 63.1% standalone) for
a very low 1.9% rate of incorrectly discarding known attacks — i.e., the
routing logic prioritizes not breaking what the classifier already does
well. A less conservative confidence threshold (e.g., 0.4 instead of 0.6)
would catch more zero-day traffic at the cost of routing more known attacks
into "Unknown" as well; this tradeoff is tunable via `CONF_THRESHOLD` in
`hybrid_pipeline.py`.

### Explainability — SHAP analysis (see `outputs/plots/shap_*.png`, `outputs/tables/shap_*`)

`src/shap_analysis.py` adds a transparency layer on top of the Part 1
classifier using `shap.TreeExplainer`, which computes exact (not
approximated) SHAP values for tree ensembles like XGBoost. This answers the
question every security reviewer eventually asks: *why did the model flag
this specific connection?*

**Global feature importance** (mean |SHAP value| across all classes): the
top drivers are `src_bytes`, `count`, `dst_host_srv_count`, and `dst_bytes`
— connection-volume and rate-based features, consistent with how DoS/Probe
attacks manifest in real network traffic (bursts of connections, unusual
byte volumes) rather than the model latching onto some spurious artifact of
the dataset.

**Per-class beeswarm plots** show not just which features matter per attack
category but which direction of that feature pushes toward it — e.g. for
R2L, elevated `duration`, `hot`, and `num_failed_logins` push toward an R2L
prediction, which matches the real-world signature of remote-to-local
attacks (repeated failed login attempts, suspicious long-lived sessions).

**Three individual case studies** (`outputs/plots/shap_waterfall_*.png`)
walk through specific predictions feature-by-feature:
- **Case A** — a `neptune` DoS attack correctly caught at 99.9999% confidence.
- **Case B** — a `guess_passwd` R2L attack missed (predicted Normal at 99.4%
  confidence) — shows exactly which features misled the model on a rare class.
- **Case C** — a true zero-day attack (`snmpgetattack`, never in KDDTrain+)
  confidently misclassified as Normal at 99.99997% confidence, driven mainly
  by `dst_host_srv_count` and `src_bytes` resembling normal traffic. This is
  the single most important plot in the project: it's direct visual evidence
  of *why* a purely supervised classifier cannot be trusted alone against
  novel attacks, and *why* Part 2/3 (anomaly detection + hybrid routing)
  need to exist rather than being optional additions.

---

## 6. Limitations & Future Work

This project is a research-grade prototype validated on a static, offline,
pre-labeled dataset — not a deployed network security product. Being
explicit about the gap between the two is itself part of the deliverable:

- **No live traffic ingestion.** The system reads pre-extracted feature rows
  from a file; it does not capture or parse real packets/flows (would
  require something like Zeek or Suricata to convert live traffic into the
  same 41-feature schema in real time).
- **No model serving layer.** There's no API, streaming pipeline, or
  persisted model artifact — every run retrains from scratch. A production
  version would serialize models (`joblib`) and serve predictions via a
  low-latency API.
- **No retraining/drift monitoring.** NSL-KDD reflects traffic patterns from
  its original collection period; a real deployment would need scheduled
  retraining on fresh labeled traffic and drift detection to catch when the
  "normal" baseline itself changes over time.
- **No adversarial robustness testing.** A real attacker adapts to evade a
  known detector; this project does not test how easily either the
  classifier or the anomaly detector could be evaded by deliberately
  perturbed traffic.
- **Zero-day recall has real headroom.** Even the best standalone anomaly
  detector (Isolation Forest) catches 63.1% of true zero-day attacks — good
  for a from-scratch prototype, but a production system would likely
  combine multiple anomaly detectors (ensemble) and incorporate threat-intel
  feeds to close that gap further.
- **Class imbalance remains the hardest open problem.** R2L recall (6%) is
  the weakest point in the whole system. Future work could explore few-shot
  or meta-learning approaches specifically for R2L/U2R, since standard
  reweighting only goes so far when a class has 52-995 training examples
  spread across a 122-dimensional space.

Framed honestly, this project demonstrates the core methodology — combining
supervised classification with unsupervised anomaly detection to cover each
other's blind spots — and validates it with real, reproducible numbers on a
standard benchmark. Turning it into a deployable system is a distinct,
larger engineering effort beyond the scope of this prototype.

---

## 7. Key takeaways

1. **Class imbalance is the central challenge of this dataset**, not raw
   accuracy — a model can hit 99% accuracy while missing nearly all R2L/U2R
   attacks, which is precisely why macro-F1 and per-class recall are
   reported throughout instead of accuracy alone.
2. **Supervised classification is fundamentally limited on unseen attack
   families**, no matter how well-tuned — R2L and U2R recall stay low
   because most of their test-set variants were never in the training data.
3. **Anomaly detection recovers real signal on exactly the cases supervised
   learning misses** — Isolation Forest, trained on Normal traffic alone,
   catches 63% of the true zero-day subset that XGBoost was never equipped
   to identify by class.
4. **Combining both is a genuine tradeoff, not a free lunch** — the hybrid
   pipeline sacrifices raw zero-day recall for precision and stability on
   known traffic, and that tradeoff is explicitly tunable, not hidden.

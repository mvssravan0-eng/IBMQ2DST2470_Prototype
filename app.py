import os
import json
import joblib
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Cybersecurity Network Threat & Intrusion Profiler",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
PLOTS_DIR = os.path.join(OUTPUTS_DIR, "plots")
TABLES_DIR = os.path.join(OUTPUTS_DIR, "tables")

# -----------------------------------------------------------------------------
# Custom Styling (Cybersecurity Command Center Theme)
# -----------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace;
    }

    /* Main Container background */
    .main {
        background-color: #0F172A;
    }

    /* Hero Header */
    .cyber-header {
        background: linear-gradient(135deg, rgba(15, 98, 254, 0.12) 0%, rgba(30, 41, 59, 0.3) 100%);
        border: 1px solid rgba(15, 98, 254, 0.25);
        border-radius: 14px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .cyber-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #60A5FA 0%, #38BDF8 50%, #A78BFA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .cyber-header p {
        color: #94A3B8;
        font-size: 1.05rem;
        margin: 0;
    }

    /* Glassmorphism Metric Cards */
    .stat-card {
        background: rgba(18, 24, 36, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .stat-card:hover {
        border-color: rgba(96, 165, 250, 0.4);
        transform: translateY(-2px);
    }
    .stat-title {
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stat-value {
        color: #F8FAFC;
        font-size: 1.6rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .stat-caption {
        font-size: 0.8rem;
        margin-top: 2px;
    }

    /* Decision Banners */
    .decision-banner {
        border-radius: 12px;
        padding: 20px 24px;
        margin: 18px 0;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .decision-banner.success {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 78, 59, 0.25) 100%);
        border: 1px solid #10B981;
    }
    .decision-banner.danger {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(127, 29, 29, 0.25) 100%);
        border: 1px solid #EF4444;
    }
    .decision-banner.warning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(120, 53, 15, 0.25) 100%);
        border: 1px solid #F59E0B;
    }
    .decision-title {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .decision-banner.success .decision-title { color: #34D399; }
    .decision-banner.danger .decision-title { color: #F87171; }
    .decision-banner.warning .decision-title { color: #FBBF24; }

    .decision-action {
        color: #E2E8F0;
        font-size: 0.95rem;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(18, 24, 36, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-weight: 500;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(15, 98, 254, 0.2) !important;
        border-color: #0F62FE !important;
        color: #60A5FA !important;
    }

    /* Sidebar polish */
    [data-testid="stSidebar"] {
        background-color: #0B0F17;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
</style>
"""

# -----------------------------------------------------------------------------
# Caching Model and Metadata Loading
# -----------------------------------------------------------------------------
@st.cache_resource
def load_artifacts():
    if not os.path.exists(os.path.join(MODELS_DIR, "xgb_classifier.joblib")):
        return None, None, None, None, None, None

    preprocessor = joblib.load(os.path.join(MODELS_DIR, "preprocessor.joblib"))
    xgb_clf = joblib.load(os.path.join(MODELS_DIR, "xgb_classifier.joblib"))
    label_encoder = joblib.load(os.path.join(MODELS_DIR, "label_encoder.joblib"))
    iso_forest = joblib.load(os.path.join(MODELS_DIR, "isolation_forest.joblib"))

    with open(os.path.join(MODELS_DIR, "metadata.json"), "r") as f:
        metadata = json.load(f)

    with open(os.path.join(MODELS_DIR, "presets.json"), "r") as f:
        presets = json.load(f)

    return preprocessor, xgb_clf, label_encoder, iso_forest, metadata, presets

# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------
def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    preprocessor, xgb_clf, label_encoder, iso_forest, metadata, presets = load_artifacts()

    # Sidebar
    st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 15px;">
        <img src="https://img.icons8.com/fluency/96/shield.png" width="65"/>
        <h2 style="margin: 6px 0 0 0; color: #F8FAFC; font-size: 1.3rem;">SOC Threat Profiler</h2>
        <span style="background: rgba(15, 98, 254, 0.2); color: #60A5FA; font-size: 0.75rem; padding: 2px 8px; border-radius: 12px; border: 1px solid rgba(15, 98, 254, 0.4);">
            IBM Project #18 • UG Level 2
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("""
    ---
    """)

    st.sidebar.subheader("System Architecture")
    st.sidebar.markdown("""
    - 🌲 **Part 1 (Supervised):**  
      XGBoost Multiclass (Normal/DoS/Probe/R2L/U2R)
    - 🔍 **Part 2 (Unsupervised):**  
      Isolation Forest (Normal-Only Baseline for Zero-Day)
    - ⚡ **Part 3 (Hybrid Engine):**  
      Calibrated Decision Gate & SOC Escalation
    """)

    if preprocessor is None:
        st.error("⚠️ Pretrained models not found in `models/`. Please run `python src/export_models.py` first.")
        st.stop()

    conf_thresh = metadata["conf_threshold"]
    anom_thresh = metadata["anomaly_threshold"]

    # Hero Banner
    st.markdown("""
    <div class="cyber-header">
        <h1>🛡️ Cybersecurity Network Threat & Intrusion Profiler</h1>
        <p>A hybrid AI defense architecture combining supervised multi-attack profiling with unsupervised zero-day anomaly triage on the NSL-KDD benchmark.</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "🔍 Live Traffic Profiler & Inspector",
        "📊 Benchmark Results & Performance",
        "📑 Case Study & Methodology"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: Live Traffic Profiler
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("Simulate & Profile Network Connections")
        st.write("Select a pre-captured network connection preset from the test dataset or adjust parameters manually:")

        col_preset, col_mode = st.columns([2, 1])
        with col_preset:
            selected_preset_name = st.selectbox("Choose a Traffic Preset:", list(presets.keys()))
        with col_mode:
            st.markdown(f"""
            <div class="stat-card" style="margin-top: 5px;">
                <div class="stat-title">Classifier Confidence Gate</div>
                <div class="stat-value" style="color: #60A5FA;">{conf_thresh * 100:.0f}%</div>
                <div class="stat-caption" style="color: #94A3B8;">Calibrated routing threshold</div>
            </div>
            """, unsafe_allow_html=True)

        sample_data = presets[selected_preset_name]

        with st.expander("🛠️ View / Modify Flow Parameters", expanded=False):
            st.write("Modify key network features to simulate perturbations:")
            p_cols = st.columns(4)
            editable_sample = dict(sample_data)
            
            with p_cols[0]:
                editable_sample["duration"] = st.number_input("Duration (s)", value=float(sample_data.get("duration", 0.0)))
                editable_sample["protocol_type"] = st.selectbox("Protocol", ["tcp", "udp", "icmp"], index=["tcp", "udp", "icmp"].index(sample_data.get("protocol_type", "tcp")))
                editable_sample["service"] = st.text_input("Service", value=str(sample_data.get("service", "http")))
                editable_sample["flag"] = st.text_input("Flag", value=str(sample_data.get("flag", "SF")))

            with p_cols[1]:
                editable_sample["src_bytes"] = st.number_input("Source Bytes", value=int(sample_data.get("src_bytes", 0)))
                editable_sample["dst_bytes"] = st.number_input("Dest Bytes", value=int(sample_data.get("dst_bytes", 0)))
                editable_sample["count"] = st.number_input("Count (connections to same host)", value=int(sample_data.get("count", 1)))
                editable_sample["srv_count"] = st.number_input("Srv Count", value=int(sample_data.get("srv_count", 1)))

            with p_cols[2]:
                editable_sample["logged_in"] = st.selectbox("Logged In", [0, 1], index=int(sample_data.get("logged_in", 0)))
                editable_sample["num_failed_logins"] = st.number_input("Failed Logins", value=int(sample_data.get("num_failed_logins", 0)))
                editable_sample["hot"] = st.number_input("Hot Indicators", value=int(sample_data.get("hot", 0)))
                editable_sample["num_compromised"] = st.number_input("Compromised Conditions", value=int(sample_data.get("num_compromised", 0)))

            with p_cols[3]:
                editable_sample["dst_host_count"] = st.number_input("Dst Host Count", value=int(sample_data.get("dst_host_count", 1)))
                editable_sample["dst_host_srv_count"] = st.number_input("Dst Host Srv Count", value=int(sample_data.get("dst_host_srv_count", 1)))
                editable_sample["dst_host_same_srv_rate"] = st.number_input("Dst Host Same Srv Rate", value=float(sample_data.get("dst_host_same_srv_rate", 1.0)))
                editable_sample["dst_host_serror_rate"] = st.number_input("Dst Host Serror Rate", value=float(sample_data.get("dst_host_serror_rate", 0.0)))

        if st.button("🚀 Analyze Traffic Flow", type="primary", use_container_width=True):
            # Prepare single-row DataFrame
            row_df = pd.DataFrame([editable_sample])
            
            # Preprocess
            X_encoded = preprocessor.transform(row_df)

            # 1. Classifier prediction
            probs = xgb_clf.predict_proba(X_encoded)[0]
            pred_idx = np.argmax(probs)
            pred_class = label_encoder.inverse_transform([pred_idx])[0]
            pred_conf = probs[pred_idx]

            # 2. Anomaly score
            anom_score = -iso_forest.score_samples(X_encoded)[0]
            is_anomalous = bool(anom_score >= anom_thresh)

            # 3. Decision Routing Logic
            UNKNOWN_LABEL = "Unknown / Zero-Day Suspect"
            if pred_class == "Normal" and not is_anomalous:
                final_decision = "Normal Traffic"
                badge_type = "success"
                action_text = "Traffic allowed. Routine background telemetry logged."
                icon = "🟢"
            elif pred_conf >= conf_thresh and not is_anomalous:
                final_decision = f"Known Attack: {pred_class}"
                badge_type = "danger"
                action_text = f"Automated Mitigation Triggered: Flow auto-blocked as signature matches known {pred_class} profile."
                icon = "🔴"
            elif pred_conf >= conf_thresh and is_anomalous and pred_class != "Normal":
                final_decision = f"Corroborated Attack: {pred_class}"
                badge_type = "danger"
                action_text = f"Automated Mitigation Triggered: Classifier confidence ({pred_conf*100:.1f}%) and Anomaly Detector corroboration confirmed malicious activity."
                icon = "🔴"
            else:
                final_decision = UNKNOWN_LABEL
                badge_type = "warning"
                action_text = "Escalated to SOC Tier-2 Human Analyst: Classifier lacks confidence or statistical deviation detected (potential Zero-Day threat)."
                icon = "⚠️"

            # Display Styled Decision Banner
            st.markdown(f"""
            <div class="decision-banner {badge_type}">
                <div class="decision-title">{icon} Decision: {final_decision}</div>
                <div class="decision-action"><strong>SOC Action Directive:</strong> {action_text}</div>
            </div>
            """, unsafe_allow_html=True)

            # Styled Metrics Grid
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-title">Ground Truth</div>
                    <div class="stat-value" style="font-size: 1.3rem;">{sample_data.get('category', 'Unknown')}</div>
                    <div class="stat-caption" style="color: #94A3B8;">Type: {sample_data.get('attack_type', '-')}</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-title">XGBoost Classification</div>
                    <div class="stat-value" style="font-size: 1.3rem; color: #60A5FA;">{pred_class}</div>
                    <div class="stat-caption" style="color: #94A3B8;">Top class prediction</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-title">Prediction Confidence</div>
                    <div class="stat-value" style="font-size: 1.3rem; color: {'#34D399' if pred_conf >= conf_thresh else '#FBBF24'};">{pred_conf * 100:.1f}%</div>
                    <div class="stat-caption" style="color: #94A3B8;">{'Meets threshold' if pred_conf >= conf_thresh else 'Below threshold (uncertain)'}</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-title">Anomaly Rating</div>
                    <div class="stat-value" style="font-size: 1.3rem; color: {'#F87171' if is_anomalous else '#34D399'};">{anom_score:.4f}</div>
                    <div class="stat-caption" style="color: {'#F87171' if is_anomalous else '#34D399'};">{'Statistically Anomalous' if is_anomalous else 'Within Normal Limits'}</div>
                </div>
                """, unsafe_allow_html=True)

            # Probability Distribution Chart with Dark Theme
            st.write("#### Multiclass Classifier Probability Distribution")
            chart_df = pd.DataFrame({
                "Category": label_encoder.classes_,
                "Probability": probs
            })
            
            # Dark styled chart
            fig, ax = plt.subplots(figsize=(8, 2.6))
            fig.patch.set_facecolor('#0B0F17')
            ax.set_facecolor('#121824')
            
            bars = ax.barh(chart_df["Category"], chart_df["Probability"], color="#3B82F6", alpha=0.85, height=0.55)
            ax.set_xlim(0, 1.0)
            ax.axvline(conf_thresh, color="#EF4444", linestyle="--", linewidth=1.5, label=f"Confidence Gate ({conf_thresh*100:.0f}%)")
            
            ax.tick_params(colors="#94A3B8")
            ax.xaxis.label.set_color("#94A3B8")
            ax.yaxis.label.set_color("#94A3B8")
            for spine in ax.spines.values():
                spine.set_color("#334155")
            
            ax.legend(facecolor="#121824", edgecolor="#334155", labelcolor="#F8FAFC", loc="lower right")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    # -------------------------------------------------------------------------
    # TAB 2: Benchmarks & Visualizations
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("Model Evaluation & Experimental Benchmarks")
        st.markdown("""
        All metrics are evaluated on the official **KDDTest+** split (22,544 rows), containing 17 novel attack types absent in training.
        """)

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### 1. Supervised Classification (Part 1)")
            cls_summary_file = os.path.join(TABLES_DIR, "classification_summary.csv")
            if os.path.exists(cls_summary_file):
                df_cls = pd.read_csv(cls_summary_file)
                st.dataframe(df_cls, use_container_width=True)

            comp_plot = os.path.join(PLOTS_DIR, "model_comparison_classification.png")
            if os.path.exists(comp_plot):
                st.image(comp_plot, caption="Model Comparison (Accuracy / Macro-F1 / Weighted-F1)", use_container_width=True)

        with col_right:
            st.markdown("#### 2. Anomaly Detection & Zero-Day Catch Rate (Part 2)")
            anom_summary_file = os.path.join(TABLES_DIR, "anomaly_summary.csv")
            if os.path.exists(anom_summary_file):
                df_anom = pd.read_csv(anom_summary_file)
                st.dataframe(df_anom, use_container_width=True)

            zero_day_plot = os.path.join(PLOTS_DIR, "zero_day_detection_rates.png")
            if os.path.exists(zero_day_plot):
                st.image(zero_day_plot, caption="Detection Rate on All Attacks vs. True Zero-Day Subset", use_container_width=True)

        st.divider()
        st.markdown("#### 3. Hybrid Routing Breakdown & Confusion Matrices")
        c1, c2 = st.columns(2)
        with c1:
            hybrid_plot = os.path.join(PLOTS_DIR, "hybrid_routing_breakdown.png")
            if os.path.exists(hybrid_plot):
                st.image(hybrid_plot, caption="Hybrid Pipeline Decision Distribution", use_container_width=True)
        with c2:
            conf_plot = os.path.join(PLOTS_DIR, "confmat_multiclass_XGBoost.png")
            if os.path.exists(conf_plot):
                st.image(conf_plot, caption="Multiclass XGBoost Confusion Matrix", use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 3: Case Study Report & Architecture
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("Case Study Documentation & Technical Highlights")
        st.markdown("""
        ### Executive Summary
        Security Operations Centers (SOCs) face two critical pitfalls with conventional ML:
        1. **Supervised Blind Spots:** Classifiers mislabel entirely novel attack techniques as normal traffic with high confidence.
        2. **Alert Fatigue:** Naive anomaly detectors flood analysts with false alarms without contextual categorization.

        **The Solution:**
        This prototype combines **XGBoost** (for known attacks) with **Isolation Forest** (trained strictly on normal traffic) through a calibrated routing logic:
        - Trusted known attacks are automatically blocked.
        - Statistically deviant or low-confidence traffic is escalated to a **Zero-Day Suspect triage queue**.
        - Standard benign traffic flows smoothly with minimal false alarms (5.7%).
        """)

        st.markdown("""
        ### Key Technical Decisions
        - **Categorical Encoding:** One-Hot Encoding (`handle_unknown='ignore'`) rather than Label Encoding to avoid imposing false numeric ordering on nominal network protocols.
        - **Class Imbalance:** Handled via loss sample weighting (`class_weight='balanced'`) rather than synthetic SMOTE interpolation, preserving realistic network traffic physics.
        - **Leakage-Free Validation:** Preprocessing is fit strictly on `KDDTrain+` only. KDDTest+ includes 3,750 true zero-day attack samples across 17 distinct unseen types.
        """)

        st.info("Complete Case Study PDF available in workspace: `IBMQ2DST2470_CaseStudy.pdf`")

if __name__ == "__main__":
    main()

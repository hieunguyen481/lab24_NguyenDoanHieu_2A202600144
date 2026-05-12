import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="RAG Evaluation Dashboard", layout="wide")

st.title("📊 Production RAG Evaluation Dashboard")
st.markdown("Dashboard for monitoring RAGAS Evaluation, LLM-Judge metrics, and Guardrail latency/accuracy.")

# CSS for styling
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0px;
    text-align: center;
}
.metric-value {
    font-size: 24px;
    font-weight: bold;
    color: #0f52ba;
}
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Phase A: RAGAS", "Phase B: LLM Judge", "Phase C: Guardrails"])

# --- Phase A: RAGAS ---
with tab1:
    st.header("RAGAS Evaluation Summary")
    ragas_summary_path = "phase-a/ragas_summary.json"
    if os.path.exists(ragas_summary_path):
        with open(ragas_summary_path, 'r', encoding='utf-8') as f:
            ragas_summary = json.load(f)
        
        cols = st.columns(4)
        for i, (metric, val) in enumerate(ragas_summary.items()):
            color = "green" if val >= 0.75 else "orange" if val >= 0.5 else "red"
            with cols[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{metric.replace('_', ' ').title()}</h4>
                    <div class="metric-value" style="color: {color};">{val:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
        ragas_results_path = "phase-a/ragas_results.csv"
        if os.path.exists(ragas_results_path):
            df_ragas = pd.read_csv(ragas_results_path)
            st.subheader("Detailed Results")
            st.dataframe(df_ragas)
    else:
        st.warning("Run pipeline to generate phase-a/ragas_summary.json")

# --- Phase B: LLM Judge ---
with tab2:
    st.header("LLM-as-a-Judge Evaluation")
    judge_report_path = "reports/judge_report.json"
    if os.path.exists(judge_report_path):
        with open(judge_report_path, 'r', encoding='utf-8') as f:
            judge_report = json.load(f)
            
        st.subheader("Pairwise Results")
        pw = judge_report.get("pairwise", {})
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Production Wins (B)", pw.get("b_wins", 0))
        col2.metric("Baseline Wins (A)", pw.get("a_wins", 0))
        col3.metric("Ties", pw.get("ties", 0))
        col4.metric("Win Rate", f"{pw.get('b_win_rate', 0)*100:.1f}%")

        st.subheader("Absolute Scores (Average)")
        abs_scores = judge_report.get("absolute", {})
        baseline = abs_scores.get("baseline_avg", {})
        production = abs_scores.get("production_avg", {})
        
        if baseline and production:
            df_abs = pd.DataFrame([baseline, production], index=["Baseline", "Production"])
            st.bar_chart(df_abs.T)

        st.subheader("Cohen's Kappa (Agreement with Humans)")
        kappa = judge_report.get("cohen_kappa", {})
        st.metric("Kappa Score", f"{kappa.get('kappa', 0):.3f}", kappa.get("agreement", ""))

        pairwise_csv = "phase-b/pairwise_results.csv"
        if os.path.exists(pairwise_csv):
            df_pw = pd.read_csv(pairwise_csv)
            with st.expander("View Pairwise Detail"):
                st.dataframe(df_pw)
    else:
        st.warning("Run pipeline to generate judge reports")

# --- Phase C: Guardrails ---
with tab3:
    st.header("Guardrails Performance")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Adversarial Tests")
        adv_path = "phase-c/adversarial_test_results.csv"
        if os.path.exists(adv_path):
            df_adv = pd.read_csv(adv_path)
            correct = len(df_adv[df_adv['correct'] == True])
            total = len(df_adv)
            st.metric("Detection Accuracy", f"{correct/total*100:.1f}%", f"{correct}/{total} blocked")
            st.dataframe(df_adv)
        else:
            st.warning("No adversarial_test_results.csv found.")
            
    with col2:
        st.subheader("Latency Benchmarks")
        lat_path = "phase-c/latency_benchmark.csv"
        if os.path.exists(lat_path):
            df_lat = pd.read_csv(lat_path)
            st.dataframe(df_lat)
            st.bar_chart(df_lat.set_index("layer")["P95_ms"])
        else:
            st.warning("No latency_benchmark.csv found.")

st.sidebar.markdown("### Lab 24 Production Eval")
st.sidebar.info("This dashboard reads the generated artifacts to present the end-to-end evaluation metrics.")

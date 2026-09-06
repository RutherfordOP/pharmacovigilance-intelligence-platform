import streamlit as st
from snowflake.snowpark.context import get_active_session

st.title("Pharmacovigilance Signal Dashboard")
session = get_active_session()

# ------------------------------------------------------------------
# KPI summary row
# ------------------------------------------------------------------
kpi = session.sql("""
    SELECT
        (SELECT COUNT(*) FROM PV_PLATFORM.CURATED.FACT_ADVERSE_EVENT) AS total_reports,
        (SELECT COUNT(*) FROM PV_PLATFORM.CURATED.AE_SIGNAL_FLAGS WHERE is_anomaly = TRUE) AS anomaly_count,
        (SELECT COUNT(DISTINCT country) FROM PV_PLATFORM.CURATED.DIM_GEOGRAPHY) AS country_count,
        (SELECT country FROM PV_PLATFORM.CURATED.VW_SERIOUS_RATE_BY_COUNTRY
            GROUP BY country ORDER BY AVG(serious_rate_pct) DESC LIMIT 1) AS top_serious_country
""").to_pandas()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Reports", int(kpi["TOTAL_REPORTS"][0]))
col2.metric("Anomalies Flagged", int(kpi["ANOMALY_COUNT"][0]))
col3.metric("Countries Covered", int(kpi["COUNTRY_COUNT"][0]))
col4.metric("Highest Serious Rate", kpi["TOP_SERIOUS_COUNTRY"][0])

st.divider()

# ------------------------------------------------------------------
# AE Trend Over Time
# ------------------------------------------------------------------
st.header("AE Trend Over Time")
trend = session.sql("""
    SELECT dt.full_date AS report_date, COUNT(*) AS ae_count
    FROM PV_PLATFORM.CURATED.FACT_ADVERSE_EVENT f
    JOIN PV_PLATFORM.CURATED.DIM_DATE dt ON f.report_date_key = dt.date_key
    GROUP BY dt.full_date ORDER BY dt.full_date
""").to_pandas()
st.line_chart(trend.set_index("REPORT_DATE"))
st.caption("Daily adverse event report volume across the full observed period.")

# ------------------------------------------------------------------
# Top Drugs by Report Volume
# ------------------------------------------------------------------
st.header("Top Drugs by Report Volume")
top_drugs = session.sql("""
    SELECT d.drug_name, COUNT(*) AS report_count
    FROM PV_PLATFORM.CURATED.FACT_ADVERSE_EVENT f
    JOIN PV_PLATFORM.CURATED.DIM_DRUG d ON f.drug_key = d.drug_key
    GROUP BY d.drug_name ORDER BY report_count DESC
""").to_pandas()
st.bar_chart(top_drugs.set_index("DRUG_NAME"))
st.caption("Report volume varies roughly 2x across drugs (Vasculin highest, Immunova/Rheumatrix lowest)  useful context before reading the anomaly panel below.")

# ------------------------------------------------------------------
# Serious Event Rate by Country
# ------------------------------------------------------------------
st.header("Serious Event Rate by Country")
serious = session.sql("""
    SELECT country, ROUND(AVG(serious_rate_pct), 1) AS avg_serious_rate
    FROM PV_PLATFORM.CURATED.VW_SERIOUS_RATE_BY_COUNTRY
    GROUP BY country ORDER BY avg_serious_rate DESC
""").to_pandas()
st.bar_chart(serious.set_index("COUNTRY"))
st.caption("Japan's rate is markedly elevated relative to other countries a geography-level pattern worth investigating independently of the drug-level anomaly signal below. Rates on months with very few total reports should be read cautiously given small sample size.")

# ------------------------------------------------------------------
# Anomaly Signals
# ------------------------------------------------------------------
st.header("Anomaly Signals")
signals = session.sql("""
    SELECT d.drug_name, s.series AS drug_ndc_code, s.ts AS period,
           s.y AS actual_reports, s.forecast, s.is_anomaly
    FROM PV_PLATFORM.CURATED.AE_SIGNAL_FLAGS s
    JOIN PV_PLATFORM.CURATED.DIM_DRUG d ON s.series = d.drug_ndc_code
    ORDER BY s.is_anomaly DESC
""").to_pandas()

def highlight_anomaly(row):
    return ['background-color: #7D3C98; color: white' if row["IS_ANOMALY"] else '' for _ in row]

st.dataframe(signals.style.apply(highlight_anomaly, axis=1))
st.caption("Anomaly flag indicates statistically unusual report volume for that drug/month. This is a triage signal for reviewer follow-up, not a determination of clinical causality see the Documentation Package, Section 6.4, for the Oncozel case demonstrating this distinction with real data.")
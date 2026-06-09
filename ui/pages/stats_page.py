"""
ui/pages/stats_page.py
Auto-Dashboard — matches original layout: KPIs + Distribution + Categorical Split
+ adds correlation heatmap, outlier summary, descriptive stats table.
"""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics.stats_engine import (
    compute_all_descriptive_stats,
    compute_correlation,
    compute_kpis,
    detect_all_outliers,
)


def render() -> None:
    st.title("📈 Instant Insights Dashboard")

    load_result = st.session_state.load_result
    profile = st.session_state.profile
    clean_result = st.session_state.clean_result

    if profile is None:
        st.warning("Please upload a file first.")
        return

    df = clean_result.df if clean_result else load_result.df
    num_cols = profile.numeric_columns
    cat_cols = profile.categorical_columns

    if not num_cols:
        st.warning("No numeric columns found to generate dashboards.")
        return

    st.caption(
        "📊 Using **cleaned** data"
        if clean_result
        else "⚠️ Using **raw** data — go to Home tab and enable cleaning first"
    )

    # ── KPI Cards (same as original) ─────────────────────────────
    st.subheader("Key Performance Indicators")
    metric_col = st.selectbox("Select Key Metric for KPIs:", num_cols, index=0)

    kpi = compute_kpis(df, metric_col)
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Sum", f"{kpi.total:,.2f}")
    kpi2.metric("Average", f"{kpi.mean:,.2f}")
    kpi3.metric("Max Value", f"{kpi.max_val:,.2f}")

    # Extra KPIs (new — below original 3)
    with st.expander("📊 Full KPI Details"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Median", f"{kpi.median:,.2f}")
        c2.metric("Std Dev", f"{kpi.std:,.2f}")
        c3.metric("Min Value", f"{kpi.min_val:,.2f}")
        c4.metric(
            "CV %",
            f"{kpi.cv_pct:.1f}%",
            help="Coefficient of Variation — lower = more consistent",
        )
        if kpi.mom_change_pct is not None:
            sign = "+" if kpi.mom_change_pct >= 0 else ""
            color = "green" if kpi.mom_change_pct >= 0 else "red"
            st.markdown(
                f"**Month-over-Month:** :{color}[{sign}{kpi.mom_change_pct:.1f}%]"
            )

    st.markdown("---")

    # ── Distribution + Categorical (same layout as original) ─────
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Distribution")
        fig_hist = px.histogram(
            df,
            x=metric_col,
            title=f"Distribution of {metric_col}",
            color_discrete_sequence=["#0D9488"],
            nbins=40,
        )
        st.plotly_chart(fig_hist, width='stretch')

    with col_chart2:
        if cat_cols:
            st.subheader("Categorical Split")
            cat_col = st.selectbox("Select Category:", cat_cols, key="dash_cat")
            df_grouped = df.groupby(cat_col)[metric_col].sum().reset_index()
            fig_pie = px.pie(
                df_grouped,
                names=cat_col,
                values=metric_col,
                title=f"{metric_col} by {cat_col}",
            )
            st.plotly_chart(fig_pie, width='stretch')
        else:
            st.info("No categorical columns found for categorical analysis.")

    st.markdown("---")

    # ── Descriptive Statistics (new — bonus below original) ──────
    with st.expander("📋 Full Descriptive Statistics Table"):
        desc_stats = compute_all_descriptive_stats(df, profile)
        if desc_stats:
            table = []
            for col_name, ds in desc_stats.items():
                table.append(
                    {
                        "Column": col_name,
                        "Count": ds.count,
                        "Mean": ds.mean,
                        "Median": ds.median,
                        "Std Dev": ds.std,
                        "Min": ds.min_val,
                        "Max": ds.max_val,
                        "Skewness": ds.skewness,
                        "Normal?": "✅" if ds.is_normal else "❌",
                    }
                )
            st.dataframe(table, width='stretch')

    # ── Correlation Heatmap (new) ────────────────────────────────
    if len(num_cols) >= 2:
        with st.expander("🔗 Correlation Matrix"):
            corr_result = compute_correlation(df, profile)
            if corr_result:
                fig_hm = go.Figure(
                    data=go.Heatmap(
                        z=corr_result.matrix.values,
                        x=corr_result.matrix.columns.tolist(),
                        y=corr_result.matrix.columns.tolist(),
                        colorscale="RdBu",
                        zmid=0,
                        text=[
                            [f"{v:.2f}" for v in row]
                            for row in corr_result.matrix.values
                        ],
                        texttemplate="%{text}",
                    )
                )
                fig_hm.update_layout(title="Pearson Correlation Heatmap")
                st.plotly_chart(fig_hm, width='stretch')
                if corr_result.strong_pairs:
                    st.markdown("**Strong correlations (|r| ≥ 0.5):**")
                    for col_a, col_b, val in corr_result.strong_pairs[:5]:
                        icon = "🔴" if abs(val) > 0.8 else "🟡"
                        st.write(f"{icon} **{col_a}** ↔ **{col_b}**: {val:.3f}")

    # ── Outlier Summary (new) ────────────────────────────────────
    with st.expander("🔍 Outlier Summary"):
        outliers = detect_all_outliers(df, profile)
        if outliers:
            summary = [
                {
                    "Column": col,
                    "Outliers": r.outlier_count,
                    "Outlier %": f"{r.outlier_pct:.1f}%",
                    "Severity": "🔴 High"
                    if r.outlier_pct > 5
                    else "🟡 Medium"
                    if r.outlier_pct > 1
                    else "🟢 Low",
                }
                for col, r in outliers.items()
            ]
            st.dataframe(summary, width='stretch')

"""
ui/pages/outliers_page.py
Outlier detection page — IQR and Z-Score visualisations.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from analytics.stats_engine import (
    detect_outliers_iqr,
    detect_outliers_zscore,
)


def render() -> None:
    st.header("🔍 Outlier Analysis")

    load_result = st.session_state.load_result
    profile = st.session_state.profile
    clean_result = st.session_state.clean_result

    if profile is None:
        st.warning("Upload a file first.")
        return

    df = clean_result.df if clean_result else load_result.df

    if not profile.has_numeric:
        st.warning("No numeric columns found for outlier detection.")
        return

    st.caption(
        "Outliers are flagged — not automatically removed. "
        "You decide what to do with them based on context."
    )

    # ── Method selection ──────────────────────────────────────────
    method = st.radio(
        "Detection method",
        ["IQR (recommended)", "Z-Score"],
        horizontal=True,
        help=(
            "**IQR**: robust, works with skewed data\n\n"
            "**Z-Score**: assumes normal distribution"
        ),
    )

    col1, _ = st.columns(2)
    if "IQR" in method:
        multiplier = col1.slider("IQR multiplier (k)", 1.0, 3.0, 1.5, 0.1)
    else:
        z_thresh = col1.slider("Z-Score threshold", 2.0, 4.0, 3.0, 0.1)

    # ── Run detection ─────────────────────────────────────────────
    with st.spinner("Detecting outliers..."):
        all_outliers: dict = {}
        for col in profile.numeric_columns:
            if col not in df.columns:
                continue
            try:
                if "IQR" in method:
                    all_outliers[col] = detect_outliers_iqr(
                        df[col], multiplier=multiplier
                    )
                else:
                    all_outliers[col] = detect_outliers_zscore(
                        df[col], threshold=z_thresh
                    )
            except Exception:  # noqa: S110 # nosec B110
                pass

    # ── Summary table ─────────────────────────────────────────────
    st.subheader("Outlier Summary")
    summary = [
        {
            "Column": col,
            "Outliers Found": r.outlier_count,
            "Outlier %": f"{r.outlier_pct:.1f}%",
            "Method": r.method,
            "Lower Bound": r.lower_bound,
            "Upper Bound": r.upper_bound,
            "Severity": (
                "🔴 High"
                if r.outlier_pct > 5
                else "🟡 Medium"
                if r.outlier_pct > 1
                else "🟢 Low"
            ),
        }
        for col, r in all_outliers.items()
    ]
    st.dataframe(summary, width='stretch')

    # ── Visual inspection ─────────────────────────────────────────
    st.subheader("Visual Inspection")
    inspect_col = st.selectbox(
        "Select column to inspect",
        options=profile.numeric_columns,
        key="outlier_inspect_col",
    )

    if inspect_col and inspect_col in all_outliers:
        result = all_outliers[inspect_col]
        fig = px.box(
            df,
            y=inspect_col,
            title=f"Box Plot — {inspect_col} "
            f"({result.outlier_count} outliers detected)",
            color_discrete_sequence=["#0D9488"],
        )
        if result.lower_bound is not None:
            fig.add_hline(
                y=result.lower_bound,
                line_dash="dash",
                line_color="red",
                annotation_text="Lower fence",
            )
            fig.add_hline(
                y=result.upper_bound,
                line_dash="dash",
                line_color="red",
                annotation_text="Upper fence",
            )
        fig.update_layout(
            plot_bgcolor="#0F172A", paper_bgcolor="#0F172A", font_color="#F8FAFC"
        )
        st.plotly_chart(fig, width='stretch')

        if result.outlier_count > 0:
            with st.expander(f"Show {result.outlier_count} outlier rows"):
                outlier_rows = df.loc[result.outlier_indices]
                st.dataframe(outlier_rows, width='stretch')

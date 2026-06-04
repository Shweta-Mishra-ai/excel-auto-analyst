"""
ui/pages/upload_page.py
Home & Data Cleaning — matches original layout exactly.
Improvements: smart imputation, audit trail, quality score.
"""

from __future__ import annotations

import streamlit as st

from core.cleaner import clean_dataframe
from core.validator import profile_dataframe


def render() -> None:
    load_result = st.session_state.load_result
    profile = st.session_state.profile

    if load_result is None:
        _render_welcome()
        return

    df = load_result.df

    st.title("🏠 Data Overview & Cleaning")

    # ── 1. Raw Data Preview (same as original) ────────────────────
    st.markdown("### 1. Raw Data Preview")
    st.dataframe(df.head(), use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rows", f"{df.shape[0]:,}")
    col2.metric("Total Columns", df.shape[1])
    col3.metric("Missing Values", int(df.isnull().sum().sum()))

    # Quality score (new — bonus info)
    if profile:
        qs = profile.quality_score
        qcol = "green" if qs >= 75 else "orange" if qs >= 50 else "red"
        st.markdown(f"**Data Quality Score:** :{qcol}[{qs}/100]")
        if profile.high_missing_columns:
            st.warning(
                f"⚠️ High missing data in: `{'`, `'.join(profile.high_missing_columns)}`"
            )
        if profile.constant_columns:
            st.info(
                f"📌 Constant columns (single value): `{'`, `'.join(profile.constant_columns)}`"
            )

    st.markdown("---")

    # ── 2. Auto-Cleaning Options (same as original + strategy choice) ──
    st.markdown("### 2. Auto-Cleaning Options")

    clean_mode = st.checkbox("✅ Enable Auto-Cleaning Mode")

    if clean_mode:
        # Strategy selectors (new — original only did fillna(0))
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            num_strategy = st.selectbox(
                "Numeric missing values strategy",
                ["median", "mean", "ffill", "zero"],
                help="**Median** is recommended — robust to outliers. Original used 'zero' which corrupts averages.",
            )
        with col_s2:
            cat_strategy = st.selectbox(
                "Categorical missing values strategy",
                ["mode", "unknown"],
            )

        if profile is None:
            profile = profile_dataframe(df)

        try:
            clean_result = clean_dataframe(
                df=df,
                profile=profile,
                numeric_strategy=num_strategy,
                categorical_strategy=cat_strategy,
            )
            st.session_state.clean_result = clean_result
            # Keep old session key for any legacy code
            st.session_state["df_cleaned"] = clean_result.df

            st.success(
                f"Data Cleaned! {clean_result.duplicates_removed} duplicates removed "
                f"and missing values filled ({num_strategy} strategy)."
            )
            st.dataframe(clean_result.df.head(), use_container_width=True)

            # Audit trail (new)
            if clean_result.audit_trail:
                with st.expander("📋 View Audit Trail"):
                    audit_data = [
                        {
                            "Operation": s.operation,
                            "Column": s.column or "—",
                            "Before": s.before,
                            "After": s.after,
                            "Rows Affected": s.rows_affected,
                        }
                        for s in clean_result.audit_trail
                    ]
                    st.dataframe(audit_data, use_container_width=True)

            # Warnings
            for w in clean_result.warnings:
                st.warning(w)

            # Download button (same as original)
            csv = clean_result.df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Cleaned Data",
                data=csv,
                file_name="cleaned_data.csv",
                mime="text/csv",
            )

        except Exception as e:
            st.error(f"Cleaning failed: {type(e).__name__}: {e}")

    else:
        # Not cleaning — use original data
        st.session_state["df_cleaned"] = df
        st.session_state.clean_result = None

    st.markdown("---")
    st.info("👈 Navigate using the sidebar to explore your data.")


def _render_welcome() -> None:
    st.info("👈 Please upload a CSV or Excel file from the sidebar to begin.")
    st.markdown("""
### Welcome to Excel Auto-Analyst!
This app helps you:
1. **Clean Data** automatically (remove duplicates, fill missing values).
2. **Visualize** trends with instant dashboards.
3. **Analyze** custom relationships with AI-powered summaries.
4. **Chat** with your data in plain English.
5. **Generate PPT Report** — one-click executive presentation *(new!)*
    """)

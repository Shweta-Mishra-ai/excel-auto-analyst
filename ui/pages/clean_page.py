"""
ui/pages/clean_page.py
Data cleaning page — user selects strategies, sees audit trail.
"""

from __future__ import annotations

import streamlit as st

from core.cleaner import clean_dataframe


def render() -> None:
    st.header("🧹 Clean & Validate")

    load_result = st.session_state.load_result
    profile = st.session_state.profile

    if load_result is None or profile is None:
        st.warning("Upload a file first.")
        return

    df = load_result.df

    # ── Strategy selection ────────────────────────────────────────
    st.subheader("Cleaning Strategy")
    st.caption(
        "Choose how missing values are handled. "
        "**Median is recommended** for numeric columns — it's robust to outliers."
    )

    col1, col2 = st.columns(2)

    with col1:
        num_strategy = st.selectbox(
            "Numeric columns — missing value strategy",
            options=["median", "mean", "ffill", "drop"],
            index=0,
            help=(
                "**Median** (recommended): robust to outliers\n\n"
                "**Mean**: only for symmetric distributions\n\n"
                "**Forward-fill**: good for time-series\n\n"
                "**Drop**: removes rows with any null"
            ),
        )

    with col2:
        cat_strategy = st.selectbox(
            "Categorical columns — missing value strategy",
            options=["mode", "unknown", "drop"],
            index=0,
            help=(
                "**Mode**: fill with most frequent value\n\n"
                "**Unknown**: fill with 'Unknown'\n\n"
                "**Drop**: removes rows with any null"
            ),
        )

    col3, col4 = st.columns(2)
    with col3:
        drop_constant = st.checkbox(
            "Drop constant columns",
            value=False,
            help="Columns with only one unique value add no analytical value.",
        )
    with col4:
        drop_ids = st.checkbox(
            "Drop ID-like columns",
            value=False,
            help="High-cardinality columns that look like row identifiers.",
        )

    # ── Missing value summary before cleaning ─────────────────────
    if profile.total_missing > 0:
        st.subheader("Missing Values — Before Cleaning")
        missing_data = [
            {
                "Column": col,
                "Missing Count": profile.columns[col].null_count,
                "Missing %": f"{profile.columns[col].null_pct:.1f}%",
                "Type": profile.columns[col].semantic_type.value,
                "Will use strategy": (
                    num_strategy
                    if col in profile.numeric_columns
                    else cat_strategy
                    if col in profile.categorical_columns
                    else "N/A"
                ),
            }
            for col in df.columns
            if profile.columns[col].null_count > 0
        ]
        st.dataframe(missing_data, width='stretch')
    else:
        st.success("✅ No missing values found in this dataset.")

    st.divider()

    # ── Run cleaning ──────────────────────────────────────────────
    if st.button("🧹 Clean Data", type="primary", width='stretch'):
        with st.spinner("Cleaning data..."):
            try:
                clean_result = clean_dataframe(
                    df=df,
                    profile=profile,
                    numeric_strategy=num_strategy,
                    categorical_strategy=cat_strategy,
                    drop_constant_columns=drop_constant,
                    drop_id_columns=drop_ids,
                )
                st.session_state.clean_result = clean_result
            except Exception as e:
                st.error(f"Cleaning failed: {type(e).__name__}: {e}")
                return

        st.success("✅ Data cleaned successfully!")

        # ── Results summary ───────────────────────────────────────
        c1, c2, c3 = st.columns(3)
        c1.metric("Duplicates Removed", clean_result.duplicates_removed)
        c2.metric("Columns Imputed", len(clean_result.columns_imputed))
        c3.metric("Rows After", f"{len(clean_result.df):,}")

        # ── Warnings ──────────────────────────────────────────────
        for warn in clean_result.warnings:
            st.warning(warn)

        # ── Audit trail ───────────────────────────────────────────
        if clean_result.audit_trail:
            with st.expander(
                "📋 Audit Trail (every transformation logged)", expanded=True
            ):
                audit_data = [
                    {
                        "Operation": step.operation,
                        "Column": step.column or "—",
                        "Before": step.before,
                        "After": step.after,
                        "Rows Affected": step.rows_affected,
                    }
                    for step in clean_result.audit_trail
                ]
                st.dataframe(audit_data, width='stretch')

        # ── Download cleaned data ─────────────────────────────────
        st.subheader("Download Cleaned Data")
        csv_bytes = clean_result.df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️  Download Cleaned CSV",
            data=csv_bytes,
            file_name=f"cleaned_{load_result.file_name.replace('.xlsx', '.csv')}",
            mime="text/csv",
        )

    # ── Show current state ────────────────────────────────────────
    elif st.session_state.clean_result is not None:
        clean_result = st.session_state.clean_result
        st.info(
            f"Data already cleaned. "
            f"{clean_result.duplicates_removed} duplicates removed, "
            f"{len(clean_result.columns_imputed)} columns imputed."
        )
        if st.button("Re-run with new settings"):
            st.session_state.clean_result = None
            st.rerun()

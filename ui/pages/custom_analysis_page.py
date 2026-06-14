"""
ui/pages/custom_analysis_page.py
Custom Report Builder - with advanced features:
- Sort (ascending/descending, by Y axis value)
- Top N filter
- Aggregation method (sum, mean, count, max, min, median)
- Category filter (multi-select)
- Export chart data as CSV
- AI insights (Groq, with rule-based fallback)
"""

from __future__ import annotations

import logging

import plotly.express as px
import streamlit as st

from config.settings import CONFIG, get_groq_api_key

logger = logging.getLogger(__name__)


def _get_ai_insight(x_col: str, y_col: str, chart_type: str, df) -> str:
    """Generate AI insight text for the selected chart. Falls back to rule-based."""
    max_val = df[y_col].max()
    min_val = df[y_col].min()
    mean_val = df[y_col].mean()

    trend = "stable"
    try:
        df_sorted = df[[x_col, y_col]].dropna().sort_values(by=x_col)
        if len(df_sorted) >= 2:
            start_val = float(df_sorted[y_col].iloc[0])
            end_val = float(df_sorted[y_col].iloc[-1])
            if end_val > start_val * 1.05:
                trend = "increasing"
            elif end_val < start_val * 0.95:
                trend = "decreasing"
    except Exception:
        logger.debug("Trend detection failed for %s vs %s", x_col, y_col)

    api_key = get_groq_api_key()
    if api_key:
        try:
            from groq import Groq

            client = Groq(api_key=api_key)
            prompt_parts = [
                "You are a data analyst. Give 3 bullet point insights for a ",
                f"{chart_type} showing '{y_col}' vs '{x_col}'. ",
                f"Stats: min={min_val:.2f}, max={max_val:.2f}, ",
                f"mean={mean_val:.2f}, trend={trend}. ",
                "Keep it brief, plain English, no code.",
            ]
            prompt = "".join(prompt_parts)
            resp = client.chat.completions.create(
                model=CONFIG.ai.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            return resp.choices[0].message.content
        except Exception:
            logger.warning("AI insight generation failed, using fallback")

    fallback_parts = [
        f"* **Observation:** The values for **{y_col}** range from ",
        f"**{min_val:,.2f}** to **{max_val:,.2f}** (mean: {mean_val:,.2f}).\n",
        f"* **Trend:** Over the course of **{x_col}**, the data appears to ",
        f"be **{trend}**.\n",
        "* **Peak:** The highest point helps identify the most performing ",
        "category or time period.",
    ]
    return "".join(fallback_parts)


_AGG_FUNCS = {
    "Sum": "sum",
    "Average": "mean",
    "Count": "count",
    "Maximum": "max",
    "Minimum": "min",
    "Median": "median",
}


def _apply_sort_and_top_n(plot_df, y_axis, sort_order, top_n):
    """Apply sort order and top-N limit to a dataframe. Returns new df."""
    if sort_order != "None":
        ascending = sort_order.startswith("Ascending")
        plot_df = plot_df.sort_values(by=y_axis, ascending=ascending)

    if top_n > 0:
        if sort_order == "None":
            plot_df = plot_df.nlargest(top_n, y_axis)
        else:
            plot_df = plot_df.head(top_n)

    return plot_df


def render() -> None:
    st.title("🎨 Custom Report Builder")

    load_result = st.session_state.load_result
    profile = st.session_state.profile
    clean_result = st.session_state.clean_result

    if load_result is None or profile is None:
        st.warning("Please upload a file first.")
        return

    df = clean_result.df if clean_result else load_result.df
    num_cols = profile.numeric_columns
    cat_cols = profile.categorical_columns

    if not num_cols:
        st.warning(
            "No numeric columns found. Custom analysis requires at "
            "least one numeric column."
        )
        return

    st.caption(
        "📊 Using **cleaned** data"
        if clean_result
        else "⚠️ Using **raw** data - go to Clean & Validate for better accuracy"
    )

    # ── Chart configuration ─────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        x_axis = st.selectbox(
            "X-Axis (Category/Time)", df.columns.tolist(), key="ca_x"
        )
    with col2:
        y_axis = st.selectbox("Y-Axis (Values)", num_cols, key="ca_y")
    with col3:
        chart_type = st.selectbox(
            "Chart Type",
            ["Bar Chart", "Line Chart", "Scatter Plot", "Box Plot", "Area Chart"],
            key="ca_chart",
        )

    if st.button("🔍 Generate Analysis", type="primary", width='stretch'):
        st.markdown("---")

        # ── Apply category filter ───────────────────────────────
        work_df = df.copy()
        if filter_col and filter_col != "None" and filter_vals:
            work_df = work_df[work_df[filter_col].astype(str).isin(filter_vals)]

        if work_df.empty:
            st.warning("No data left after applying filters.")
            return

        # ── Build chart ──────────────────────────────────────────
        try:
            if chart_type == "Bar Chart":
                plot_df = (
                    work_df.groupby(x_axis)[y_axis].agg(agg_method).reset_index()
                )
                plot_df = _apply_sort_and_top_n(plot_df, y_axis, sort_order, top_n)
                fig = px.bar(
                    plot_df,
                    x=x_axis,
                    y=y_axis,
                    color=y_axis,
                    title=f"{agg_method_label} of {y_axis} by {x_axis}",
                    color_continuous_scale="Teal",
                )

            elif chart_type == "Box Plot":
                plot_df = work_df[[x_axis, y_axis]].dropna()
                fig = px.box(
                    plot_df,
                    x=x_axis,
                    y=y_axis,
                    title=f"{y_axis} distribution by {x_axis}",
                    color_discrete_sequence=["#0D9488"],
                )

            elif chart_type == "Line Chart":
                plot_df = work_df[[x_axis, y_axis]].dropna().sort_values(by=x_axis)
                plot_df = _apply_sort_and_top_n(plot_df, y_axis, sort_order, top_n)
                fig = px.line(
                    plot_df,
                    x=x_axis,
                    y=y_axis,
                    title=f"{y_axis} trend over {x_axis}",
                    color_discrete_sequence=["#0D9488"],
                )

            elif chart_type == "Scatter Plot":
                plot_df = work_df[[x_axis, y_axis]].dropna()
                plot_df = _apply_sort_and_top_n(plot_df, y_axis, sort_order, top_n)
                fig = px.scatter(
                    plot_df,
                    x=x_axis,
                    y=y_axis,
                    title=f"{y_axis} vs {x_axis}",
                    color_discrete_sequence=["#0D9488"],
                )

            else:  # Area Chart
                plot_df = work_df[[x_axis, y_axis]].dropna().sort_values(by=x_axis)
                plot_df = _apply_sort_and_top_n(plot_df, y_axis, sort_order, top_n)
                fig = px.area(
                    plot_df,
                    x=x_axis,
                    y=y_axis,
                    title=f"{y_axis} area over {x_axis}",
                    color_discrete_sequence=["#0D9488"],
                )

            st.plotly_chart(fig, width='stretch')

        except Exception as e:
            st.error(f"Chart generation failed: {e}")
            return

        # ── Export chart data ────────────────────────────────────
        csv_bytes = plot_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Chart Data (CSV)",
            data=csv_bytes,
            file_name=f"chart_data_{x_axis}_{y_axis}.csv",
            mime="text/csv",
        )

        # ── AI Insights ───────────────────────────────────────────
        st.subheader("🤖 AI Insights")
        with st.spinner("Generating insights..."):
            insight_text = _get_ai_insight(x_axis, y_axis, chart_type, work_df)
        st.info(insight_text)

        # ── Quick stats ───────────────────────────────────────────
        with st.expander("📊 Quick Statistics"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mean", f"{work_df[y_axis].mean():,.2f}")
            c2.metric("Median", f"{work_df[y_axis].median():,.2f}")
            c3.metric("Max", f"{work_df[y_axis].max():,.2f}")
            c4.metric("Min", f"{work_df[y_axis].min():,.2f}")

            c5, c6 = st.columns(2)
            c5.metric("Rows shown", f"{len(plot_df):,}")
            c6.metric("Total rows", f"{len(df):,}")

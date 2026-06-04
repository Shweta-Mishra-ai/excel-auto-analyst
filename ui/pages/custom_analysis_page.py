"""
ui/pages/custom_analysis_page.py
Custom Report Builder — original feature restored + improved.
X-axis / Y-axis / chart type selector + AI insights.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from config.settings import CONFIG, get_groq_api_key


def _get_ai_insight(x_col: str, y_col: str, chart_type: str, df) -> str:
    """Generate AI insight text for the selected chart. Falls back to rule-based."""
    max_val = df[y_col].max()
    min_val = df[y_col].min()
    mean_val = df[y_col].mean()

    # Safe trend: only sort if x is numeric or datetime
    trend = "stable ➖"  # noqa: RUF001
    try:
        df_sorted = df[[x_col, y_col]].dropna().sort_values(by=x_col)
        if len(df_sorted) >= 2:
            start_val = float(df_sorted[y_col].iloc[0])
            end_val = float(df_sorted[y_col].iloc[-1])
            if end_val > start_val * 1.05:
                trend = "increasing 📈"
            elif end_val < start_val * 0.95:
                trend = "decreasing 📉"
    except Exception:  # noqa: S110
        pass

    # Try Groq for richer insight
    api_key = get_groq_api_key()
    if api_key:
        try:
            from groq import Groq

            client = Groq(api_key=api_key)
            prompt = (
                f"You are a data analyst. Give 3 bullet point insights for a {chart_type} "
                f"showing '{y_col}' vs '{x_col}'. Stats: min={min_val:.2f}, max={max_val:.2f}, "
                f"mean={mean_val:.2f}, trend={trend}. "
                f"Keep it brief, plain English, no code."
            )
            resp = client.chat.completions.create(
                model=CONFIG.ai.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            return resp.choices[0].message.content
        except Exception:  # noqa: S110
            pass  # fall through to rule-based

    # Rule-based fallback (always works, no API needed)
    return (
        f"* **Observation:** The values for **{y_col}** range from "
        f"**{min_val:,.2f}** to **{max_val:,.2f}** (mean: {mean_val:,.2f}).\n"
        f"* **Trend:** Over the course of **{x_col}**, the data appears to be **{trend}**.\n"
        f"* **Peak:** The highest point helps identify the most performing category or time period."
    )


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

    if not num_cols:
        st.warning(
            "No numeric columns found. Custom analysis requires at least one numeric column."
        )
        return

    st.caption(
        "📊 Using **cleaned** data"
        if clean_result
        else "⚠️ Using **raw** data — go to Clean & Validate for better accuracy"
    )

    # ── Controls ─────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        x_axis = st.selectbox("X-Axis (Category/Time)", df.columns.tolist(), key="ca_x")
    with col2:
        y_axis = st.selectbox("Y-Axis (Values)", num_cols, key="ca_y")
    with col3:
        chart_type = st.selectbox(
            "Chart Type",
            ["Bar Chart", "Line Chart", "Scatter Plot", "Box Plot", "Area Chart"],
            key="ca_chart",
        )

    if st.button("🔍 Generate Analysis", type="primary", use_container_width=True):
        st.markdown("---")

        # ── Chart ─────────────────────────────────────────────────
        try:
            if chart_type == "Bar Chart":
                df_grouped = df.groupby(x_axis)[y_axis].sum().reset_index()
                fig = px.bar(
                    df_grouped,
                    x=x_axis,
                    y=y_axis,
                    color=y_axis,
                    title=f"{y_axis} by {x_axis}",
                    color_continuous_scale="Teal",
                )
            elif chart_type == "Line Chart":
                df_sorted = df[[x_axis, y_axis]].dropna().sort_values(by=x_axis)
                fig = px.line(
                    df_sorted,
                    x=x_axis,
                    y=y_axis,
                    title=f"{y_axis} trend over {x_axis}",
                    color_discrete_sequence=["#0D9488"],
                )
            elif chart_type == "Scatter Plot":
                fig = px.scatter(
                    df,
                    x=x_axis,
                    y=y_axis,
                    title=f"{y_axis} vs {x_axis}",
                    color_discrete_sequence=["#0D9488"],
                )
            elif chart_type == "Box Plot":
                fig = px.box(
                    df,
                    x=x_axis,
                    y=y_axis,
                    title=f"{y_axis} distribution by {x_axis}",
                    color_discrete_sequence=["#0D9488"],
                )
            else:  # Area Chart
                df_sorted = df[[x_axis, y_axis]].dropna().sort_values(by=x_axis)
                fig = px.area(
                    df_sorted,
                    x=x_axis,
                    y=y_axis,
                    title=f"{y_axis} area over {x_axis}",
                    color_discrete_sequence=["#0D9488"],
                )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Chart generation failed: {e}")
            return

        # ── AI Insights ───────────────────────────────────────────
        st.subheader("🤖 AI Insights")
        with st.spinner("Generating insights..."):
            insight_text = _get_ai_insight(x_axis, y_axis, chart_type, df)
        st.info(insight_text)

        # ── Quick stats ───────────────────────────────────────────
        with st.expander("📊 Quick Statistics"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mean", f"{df[y_axis].mean():,.2f}")
            c2.metric("Median", f"{df[y_axis].median():,.2f}")
            c3.metric("Max", f"{df[y_axis].max():,.2f}")
            c4.metric("Min", f"{df[y_axis].min():,.2f}")

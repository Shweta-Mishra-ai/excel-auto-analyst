"""
ai/prompt_builder.py
Builds structured, context-rich prompts for the LLM.
Centralised here so prompts are version-controlled and testable.
"""

from __future__ import annotations

import json

import pandas as pd

from config.settings import CONFIG
from core.validator import DataProfile


def build_chat_system_prompt(df: pd.DataFrame, profile: DataProfile) -> str:
    """
    System prompt for the Chat with Data feature.
    Gives the LLM precise schema knowledge and strict output rules.
    """
    columns_info = []
    for col_name, col_profile in profile.columns.items():
        info = {
            "name": col_name,
            "type": col_profile.semantic_type.value,
            "dtype": col_profile.dtype,
            "null_pct": col_profile.null_pct,
            "unique_count": col_profile.unique_count,
        }
        if col_profile.mean is not None:
            info["mean"] = col_profile.mean
            info["min"] = col_profile.min_val
            info["max"] = col_profile.max_val
        if col_profile.top_values:
            info["top_values"] = [v[0] for v in col_profile.top_values[:3]]
        columns_info.append(info)

    sample_rows = df.head(CONFIG.ai.max_tokens // 200).to_string(max_cols=10)

    allowed = sorted(CONFIG.ai.allowed_modules)

    return f"""You are a senior Python data analyst. Your job is to analyse the DataFrame `df`.

SCHEMA:
{json.dumps(columns_info, indent=2)}

SAMPLE DATA (first rows):
{sample_rows}

DATASET SUMMARY:
- {profile.total_rows:,} rows, {profile.total_columns} columns
- Data quality score: {profile.quality_score}/100
- Numeric columns: {profile.numeric_columns}
- Categorical columns: {profile.categorical_columns}

STRICT RULES — violating these will break the app:
1. Output ONLY valid Python code inside ```python``` fences.
2. Use print() for text answers — the user cannot see variables.
3. Create charts as `fig` (Plotly). Do NOT call fig.show().
4. Only use these modules (pre-imported): {allowed} + pandas (pd), plotly.express (px), numpy (np).
5. Do NOT import anything. Do NOT use os, sys, exec, eval, open.
6. Keep output human-readable plain English — no raw DataFrames.
7. If the question cannot be answered from the data, print a clear explanation.
8. For aggregations, always handle potential NaN values.
"""


def build_insight_prompt(
    df: pd.DataFrame, profile: DataProfile, metric_col: str
) -> str:
    """
    Prompt to generate a plain-English narrative about the dataset.
    Returns a structured JSON with 3-5 key insights.
    """
    stats_summary = []
    for col in profile.numeric_columns[:5]:
        cp = profile.columns.get(col)
        if cp and cp.mean is not None:
            stats_summary.append(
                f"{col}: mean={cp.mean}, min={cp.min_val}, max={cp.max_val}"
            )

    return f"""Analyse this dataset and return ONLY a JSON object with this exact structure:
{{
  "headline": "One sentence that captures the most important finding",
  "insights": [
    {{"title": "Insight 1 title", "detail": "2-3 sentence explanation with numbers"}},
    {{"title": "Insight 2 title", "detail": "2-3 sentence explanation with numbers"}},
    {{"title": "Insight 3 title", "detail": "2-3 sentence explanation with numbers"}}
  ],
  "recommendation": "One actionable recommendation based on the data"
}}

Dataset stats:
- Primary metric: {metric_col}
- Rows: {profile.total_rows:,}
- Quality score: {profile.quality_score}/100
- Stats: {chr(10).join(stats_summary)}
- Sample values: {df[metric_col].dropna().head(10).tolist()}

Return ONLY the JSON. No preamble, no markdown, no explanation.
"""

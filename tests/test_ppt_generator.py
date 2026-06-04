"""
tests/test_ppt_generator.py
Tests PowerPoint report generation logic.
"""

from __future__ import annotations

import pandas as pd

from analytics.stats_engine import (
    compute_correlation,
    compute_kpis,
    detect_all_outliers,
)
from core.validator import profile_dataframe
from reports.ppt_generator import ReportInput, generate_ppt_report


class TestPPTGenerator:
    def test_generate_report_successful(self, clean_df):
        profile = profile_dataframe(clean_df)
        kpi = compute_kpis(clean_df, "sales")
        outliers = detect_all_outliers(clean_df, profile)
        correlation = compute_correlation(clean_df, profile)

        ai_insights = {
            "headline": "Revenue is growing steadily across all key regions.",
            "insights": [
                {"title": "Strong Sales Correlation", "detail": "Sales are strongly correlated with profits (r = 0.85)."},
                {"title": "Low Outliers", "detail": "Less than 2% of transaction records are categorized as outliers."},
                {"title": "Growth", "detail": "Units sold show a 5% month-over-month growth trend."}
            ],
            "recommendation": "Expand operations in the North and West regions to capture peak demand."
        }

        ri = ReportInput(
            df=clean_df,
            profile=profile,
            kpi=kpi,
            outliers=outliers,
            correlation=correlation,
            ai_insights=ai_insights,
            file_name="clean_dataset.csv",
            metric_col="sales",
        )

        ppt_bytes = generate_ppt_report(ri)

        # Verify pptx output matches basic zip file signature (all pptx files are zip files)
        assert isinstance(ppt_bytes, bytes)
        assert len(ppt_bytes) > 0
        assert ppt_bytes.startswith(b"PK\x03\x04")

    def test_generate_report_no_numeric_columns(self):
        # Create a dataframe with only categorical columns
        df = pd.DataFrame({
            "region": ["North", "South", "East"],
            "product": ["Widget", "Gadget", "Doohickey"]
        })
        profile = profile_dataframe(df)

        ri = ReportInput(
            df=df,
            profile=profile,
            kpi=None,
            outliers={},
            correlation=None,
            ai_insights=None,
            file_name="categorical_only.csv",
            metric_col="N/A",
        )

        ppt_bytes = generate_ppt_report(ri)
        assert isinstance(ppt_bytes, bytes)
        assert len(ppt_bytes) > 0
        assert ppt_bytes.startswith(b"PK\x03\x04")

    def test_generate_report_no_correlations(self):
        # Only 1 numeric column, so correlation will be None
        df = pd.DataFrame({
            "sales": [10.0, 20.0, 30.0],
            "product": ["Widget", "Gadget", "Doohickey"]
        })
        profile = profile_dataframe(df)
        kpi = compute_kpis(df, "sales")
        outliers = detect_all_outliers(df, profile)
        correlation = compute_correlation(df, profile)

        assert correlation is None

        ri = ReportInput(
            df=df,
            profile=profile,
            kpi=kpi,
            outliers=outliers,
            correlation=None,
            ai_insights=None,
            file_name="one_numeric.csv",
            metric_col="sales",
        )

        ppt_bytes = generate_ppt_report(ri)
        assert isinstance(ppt_bytes, bytes)
        assert len(ppt_bytes) > 0
        assert ppt_bytes.startswith(b"PK\x03\x04")

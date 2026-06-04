"""
reports/ppt_generator.py
Auto-generates a branded PowerPoint report from analysis results.
This is the key advanced feature: one-click executive PPT from any dataset.

Uses python-pptx — installable via pip, no Node.js required.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

import pandas as pd

from analytics.stats_engine import (
    CorrelationResult,
    KPIResult,
    OutlierResult,
    compute_all_descriptive_stats,
)
from core.validator import DataProfile

logger = logging.getLogger(__name__)


@dataclass
class ReportInput:
    """Everything needed to generate the PPT report."""

    df: pd.DataFrame
    profile: DataProfile
    kpi: KPIResult | None
    outliers: dict[str, OutlierResult]
    correlation: CorrelationResult | None
    ai_insights: dict | None  # JSON from build_insight_prompt
    file_name: str
    metric_col: str


def generate_ppt_report(report_input: ReportInput) -> bytes:
    """
    Generate a PowerPoint report and return raw bytes.
    The caller (Streamlit) handles the download button.

    Returns
    -------
    bytes — the .pptx file content
    """
    try:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.util import Inches, Pt
    except ImportError as e:
        raise ImportError(
            "python-pptx is required for report generation. "
            "Run: pip install python-pptx"
        ) from e

    ri = report_input
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]  # completely blank

    # ── Color palette ─────────────────────────────────────────────
    BG_DARK = RGBColor(0x0B, 0x0F, 0x19)  # noqa: N806
    CARD_BG = RGBColor(0x1E, 0x29, 0x3B)  # noqa: N806
    TEAL = RGBColor(0x0D, 0x94, 0x88)  # noqa: N806
    WHITE = RGBColor(0xF8, 0xFA, 0xFC)  # noqa: N806
    SLATE = RGBColor(0x94, 0xA3, 0xB8)  # noqa: N806
    RED = RGBColor(0xDC, 0x26, 0x26)  # noqa: N806
    AMBER = RGBColor(0xD9, 0x77, 0x06)  # noqa: N806
    GREEN = RGBColor(0x16, 0xA3, 0x4A)  # noqa: N806

    def add_text_box(
        slide,
        text,
        left,
        top,
        width,
        height,
        font_size=14,
        bold=False,
        color=None,
        align="left",
    ):
        from pptx.enum.text import PP_ALIGN

        tx_box = slide.shapes.add_textbox(
            Inches(left), Inches(top), Inches(width), Inches(height)
        )
        tf = tx_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = str(text)
        p.alignment = PP_ALIGN.CENTER if align == "center" else PP_ALIGN.LEFT
        run = p.runs[0]
        run.font.size = Pt(font_size)
        run.font.bold = bold
        if color:
            run.font.color.rgb = color
        return tx_box

    def add_rect(slide, left, top, width, height, fill_color):
        from pptx.util import Inches as I  # noqa: N817

        shape = slide.shapes.add_shape(
            1,  # MSO_SHAPE_TYPE.RECTANGLE
            I(left),
            I(top),
            I(width),
            I(height),
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
        shape.line.fill.background()
        return shape

    # ─── Slide 1: Title ──────────────────────────────────────────
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, BG_DARK)
    add_rect(slide, 0, 0, 0.15, 7.5, TEAL)

    add_text_box(
        slide,
        "DATA ANALYSIS REPORT",
        0.4,
        0.5,
        12,
        0.7,
        font_size=13,
        bold=True,
        color=TEAL,
        align="left",
    )
    add_text_box(
        slide, ri.file_name, 0.4, 1.3, 12, 1.2, font_size=42, bold=True, color=WHITE
    )
    add_text_box(
        slide,
        f"Rows: {ri.profile.total_rows:,}  ·  "
        f"Columns: {ri.profile.total_columns}  ·  "
        f"Quality Score: {ri.profile.quality_score}/100",
        0.4,
        2.7,
        12,
        0.5,
        font_size=14,
        color=SLATE,
    )

    # Quality score pill
    qs = ri.profile.quality_score
    qs_color = GREEN if qs >= 75 else AMBER if qs >= 50 else RED
    add_rect(slide, 0.4, 3.4, 2.0, 0.7, qs_color)
    add_text_box(
        slide,
        f"Quality: {qs}/100",
        0.4,
        3.4,
        2.0,
        0.7,
        font_size=14,
        bold=True,
        color=WHITE,
        align="center",
    )

    # ─── Slide 2: Data Overview ───────────────────────────────────
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, BG_DARK)
    add_rect(slide, 0, 0, 13.33, 1.0, CARD_BG)
    add_rect(slide, 0, 0.95, 13.33, 0.05, TEAL)
    add_text_box(
        slide, "DATA OVERVIEW", 0.3, 0.15, 12, 0.7, font_size=22, bold=True, color=WHITE
    )

    metrics = [
        ("Total Rows", f"{ri.profile.total_rows:,}", TEAL),
        ("Total Columns", str(ri.profile.total_columns), TEAL),
        (
            "Missing Values",
            f"{ri.profile.total_missing:,}",
            RED if ri.profile.total_missing > 0 else GREEN,
        ),
        (
            "Missing %",
            f"{ri.profile.total_missing_pct:.1f}%",
            AMBER if ri.profile.total_missing_pct > 10 else GREEN,
        ),
        (
            "Duplicates",
            str(ri.profile.duplicate_row_count),
            RED if ri.profile.duplicate_row_count > 0 else GREEN,
        ),
        ("Memory (MB)", str(ri.profile.memory_mb), TEAL),
    ]
    for i, (label, val, col) in enumerate(metrics):
        bx = 0.3 + (i % 3) * 4.3
        by = 1.4 + (i // 3) * 1.8
        add_rect(slide, bx, by, 3.8, 1.5, CARD_BG)
        add_rect(slide, bx, by, 3.8, 0.06, TEAL)
        add_text_box(
            slide,
            val,
            bx,
            by + 0.15,
            3.8,
            0.8,
            font_size=28,
            bold=True,
            color=col,
            align="center",
        )
        add_text_box(
            slide,
            label,
            bx,
            by + 0.95,
            3.8,
            0.45,
            font_size=12,
            color=SLATE,
            align="center",
        )

    # Column type breakdown
    add_text_box(
        slide,
        f"Numeric: {len(ri.profile.numeric_columns)}  ·  "
        f"Categorical: {len(ri.profile.categorical_columns)}  ·  "
        f"Datetime: {len(ri.profile.datetime_columns)}  ·  "
        f"ID-like: {len(ri.profile.id_columns)}",
        0.3,
        5.8,
        12,
        0.5,
        font_size=13,
        color=SLATE,
    )

    # ─── Slide 3: KPI Summary ─────────────────────────────────────
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, BG_DARK)
    add_rect(slide, 0, 0, 13.33, 1.0, CARD_BG)
    add_rect(slide, 0, 0.95, 13.33, 0.05, TEAL)
    add_text_box(
        slide,
        f"KPI SUMMARY — {ri.metric_col.upper()}",
        0.3,
        0.15,
        12,
        0.7,
        font_size=22,
        bold=True,
        color=WHITE,
    )

    if ri.kpi:
        kpi_items = [
            ("Total", f"{ri.kpi.total:,.2f}"),
            ("Mean", f"{ri.kpi.mean:,.2f}"),
            ("Median", f"{ri.kpi.median:,.2f}"),
            ("Std Dev", f"{ri.kpi.std:,.2f}"),
            ("Max", f"{ri.kpi.max_val:,.2f}"),
            ("Min", f"{ri.kpi.min_val:,.2f}"),
            ("Range", f"{ri.kpi.range_val:,.2f}"),
            ("CV %", f"{ri.kpi.cv_pct:.1f}%"),
        ]
        for i, (label, val) in enumerate(kpi_items):
            bx = 0.3 + (i % 4) * 3.2
            by = 1.4 + (i // 4) * 1.8
            add_rect(slide, bx, by, 2.9, 1.5, CARD_BG)
            add_rect(slide, bx, by, 2.9, 0.06, TEAL)
            add_text_box(
                slide,
                val,
                bx,
                by + 0.15,
                2.9,
                0.8,
                font_size=24,
                bold=True,
                color=TEAL,
                align="center",
            )
            add_text_box(
                slide,
                label,
                bx,
                by + 0.95,
                2.9,
                0.45,
                font_size=12,
                color=SLATE,
                align="center",
            )

        if ri.kpi.mom_change_pct is not None:
            mom_col = GREEN if ri.kpi.mom_change_pct >= 0 else RED
            sign = "+" if ri.kpi.mom_change_pct >= 0 else ""
            add_rect(slide, 0.3, 5.2, 4.0, 0.7, CARD_BG)
            add_rect(slide, 0.3, 5.2, 0.08, 0.7, mom_col)
            add_text_box(
                slide,
                f"Month-over-Month: {sign}{ri.kpi.mom_change_pct:.1f}%",
                0.5,
                5.2,
                3.8,
                0.7,
                font_size=14,
                bold=True,
                color=mom_col,
                align="center",
            )

    # ─── Slide 4: Statistical Summary ─────────────────────────────
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, BG_DARK)
    add_rect(slide, 0, 0, 13.33, 1.0, CARD_BG)
    add_rect(slide, 0, 0.95, 13.33, 0.05, TEAL)
    add_text_box(
        slide,
        "STATISTICAL SUMMARY",
        0.3,
        0.15,
        12,
        0.7,
        font_size=22,
        bold=True,
        color=WHITE,
    )

    desc_stats = compute_all_descriptive_stats(ri.df, ri.profile)
    y_pos = 1.35
    headers = ["Column", "Mean", "Median", "Std Dev", "Skewness", "Normal?", "Outliers"]
    widths = [3.2, 1.7, 1.7, 1.7, 1.6, 1.3, 1.5]
    x_positions = [0.2]
    for w in widths[:-1]:
        x_positions.append(x_positions[-1] + w)

    # Header row
    add_rect(slide, 0.2, y_pos, 12.9, 0.45, CARD_BG)
    add_rect(slide, 0.2, y_pos + 0.43, 12.9, 0.02, TEAL)
    for hdr, xp, wd in zip(headers, x_positions, widths, strict=False):
        add_text_box(
            slide, hdr, xp, y_pos, wd, 0.45, font_size=10, bold=True, color=WHITE
        )

    y_pos += 0.5
    for col_name, ds in list(desc_stats.items())[:8]:
        outlier_count = ri.outliers.get(col_name)
        out_str = str(outlier_count.outlier_count) if outlier_count else "—"
        bg = CARD_BG
        add_rect(slide, 0.2, y_pos, 12.9, 0.48, bg)
        add_rect(slide, 0.2, y_pos + 0.46, 12.9, 0.02, BG_DARK)
        row_vals = [
            col_name,
            f"{ds.mean:.2f}",
            f"{ds.median:.2f}",
            f"{ds.std:.2f}",
            f"{ds.skewness:.2f}",
            "Yes" if ds.is_normal else "No",
            out_str,
        ]
        for val, xp, wd, hdr in zip(
            row_vals, x_positions, widths, headers, strict=False
        ):
            col_color = SLATE
            if val in ("Yes",):
                col_color = GREEN
            elif val in ("No",) and hdr == "Normal?":
                col_color = AMBER
            elif hdr == "Column":
                col_color = WHITE
            add_text_box(slide, val, xp, y_pos, wd, 0.45, font_size=10, color=col_color)
        y_pos += 0.5

    # ─── Slide 5: Outlier Analysis ────────────────────────────────
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, BG_DARK)
    add_rect(slide, 0, 0, 13.33, 1.0, CARD_BG)
    add_rect(slide, 0, 0.95, 13.33, 0.05, TEAL)
    add_text_box(
        slide,
        "OUTLIER ANALYSIS",
        0.3,
        0.15,
        12,
        0.7,
        font_size=22,
        bold=True,
        color=WHITE,
    )

    if ri.outliers:
        for i, (col, out) in enumerate(list(ri.outliers.items())[:9]):
            bx = 0.3 + (i % 3) * 4.35
            by = 1.4 + (i // 3) * 1.85
            sev_color = (
                RED if out.outlier_pct > 5 else AMBER if out.outlier_pct > 1 else GREEN
            )
            add_rect(slide, bx, by, 4.0, 1.65, CARD_BG)
            add_rect(slide, bx, by, 4.0, 0.08, sev_color)
            add_text_box(
                slide,
                col,
                bx + 0.1,
                by + 0.15,
                3.8,
                0.4,
                font_size=12,
                bold=True,
                color=WHITE,
            )
            add_text_box(
                slide,
                f"Outliers: {out.outlier_count} ({out.outlier_pct:.1f}%)\n"
                f"Method: {out.method}",
                bx + 0.1,
                by + 0.6,
                3.8,
                0.9,
                font_size=10,
                color=SLATE,
            )
    else:
        add_text_box(
            slide,
            "No numeric columns available for outlier analysis.",
            0.3,
            2.0,
            12,
            0.5,
            font_size=14,
            color=SLATE,
        )

    # ─── Slide 6: Key Data Correlations ───────────────────────────
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, BG_DARK)
    add_rect(slide, 0, 0, 13.33, 1.0, CARD_BG)
    add_rect(slide, 0, 0.95, 13.33, 0.05, TEAL)
    add_text_box(
        slide,
        "KEY DATA CORRELATIONS",
        0.3,
        0.15,
        12,
        0.7,
        font_size=22,
        bold=True,
        color=WHITE,
    )

    if ri.correlation and ri.correlation.strong_pairs:
        for i, (col_a, col_b, val) in enumerate(ri.correlation.strong_pairs[:6]):
            bx = 0.3 + (i % 3) * 4.35
            by = 1.4 + (i // 3) * 1.85
            corr_color = TEAL if val >= 0 else AMBER
            strength_desc = "Strong" if abs(val) >= 0.7 else "Moderate"
            dir_desc = "Positive" if val >= 0 else "Negative"

            add_rect(slide, bx, by, 4.0, 1.65, CARD_BG)
            add_rect(slide, bx, by, 4.0, 0.08, corr_color)

            add_text_box(
                slide,
                f"{col_a}\nvs\n{col_b}",
                bx + 0.1,
                by + 0.12,
                3.8,
                0.75,
                font_size=11,
                bold=True,
                color=WHITE,
            )
            add_text_box(
                slide,
                f"r = {val:+.2f}",
                bx + 0.1,
                by + 0.92,
                3.8,
                0.35,
                font_size=16,
                bold=True,
                color=corr_color,
            )
            add_text_box(
                slide,
                f"{strength_desc} {dir_desc} Correlation",
                bx + 0.1,
                by + 1.25,
                3.8,
                0.3,
                font_size=9,
                color=SLATE,
            )
    else:
        add_text_box(
            slide,
            "No strong linear relationships (r >= 0.5) detected between numeric columns.",
            0.3,
            2.0,
            12,
            0.5,
            font_size=14,
            color=SLATE,
        )

    # ─── Slide 7: AI Insights ─────────────────────────────────────
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, BG_DARK)
    add_rect(slide, 0, 0, 13.33, 1.0, CARD_BG)
    add_rect(slide, 0, 0.95, 13.33, 0.05, TEAL)
    add_text_box(
        slide,
        "AI-GENERATED INSIGHTS",
        0.3,
        0.15,
        12,
        0.7,
        font_size=22,
        bold=True,
        color=WHITE,
    )

    if ri.ai_insights:
        headline = ri.ai_insights.get("headline", "")
        add_rect(slide, 0.3, 1.2, 12.7, 0.7, CARD_BG)
        add_rect(slide, 0.3, 1.2, 0.08, 0.7, TEAL)
        add_text_box(
            slide, headline, 0.5, 1.25, 12.5, 0.6, font_size=14, bold=True, color=WHITE
        )

        for i, insight in enumerate(ri.ai_insights.get("insights", [])[:3]):
            bx = 0.3 + i * 4.35
            by = 2.1
            add_rect(slide, bx, by, 4.0, 2.8, CARD_BG)
            add_rect(slide, bx, by, 4.0, 0.08, TEAL)
            add_text_box(
                slide,
                insight.get("title", ""),
                bx + 0.1,
                by + 0.15,
                3.8,
                0.5,
                font_size=12,
                bold=True,
                color=TEAL,
            )
            add_text_box(
                slide,
                insight.get("detail", ""),
                bx + 0.1,
                by + 0.72,
                3.8,
                2.0,
                font_size=10,
                color=WHITE,
            )

        rec = ri.ai_insights.get("recommendation", "")
        if rec:
            add_rect(slide, 0.3, 5.1, 12.7, 0.7, CARD_BG)
            add_rect(slide, 0.3, 5.1, 0.08, 0.7, GREEN)
            add_text_box(
                slide,
                f"Recommendation: {rec}",
                0.5,
                5.15,
                12.5,
                0.6,
                font_size=12,
                bold=True,
                color=WHITE,
            )
    else:
        add_text_box(
            slide,
            "AI insights not available (configure GROQ_API_KEY).",
            0.3,
            2.0,
            12,
            0.5,
            font_size=14,
            color=SLATE,
        )

    # ─── Slide 8: Closing ─────────────────────────────────────────
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, BG_DARK)
    add_rect(slide, 0, 0, 0.15, 7.5, TEAL)
    add_text_box(
        slide,
        "REPORT GENERATED BY",
        0.4,
        1.5,
        12,
        0.6,
        font_size=12,
        color=SLATE,
        align="center",
    )
    add_text_box(
        slide,
        "Excel Auto-Analyst",
        0.4,
        2.2,
        12,
        1.0,
        font_size=42,
        bold=True,
        color=WHITE,
        align="center",
    )
    add_text_box(
        slide,
        f"Dataset: {ri.file_name}  ·  "
        f"Rows: {ri.profile.total_rows:,}  ·  "
        f"Quality: {ri.profile.quality_score}/100",
        0.4,
        3.4,
        12,
        0.5,
        font_size=13,
        color=SLATE,
        align="center",
    )

    # ─── Save to bytes ─────────────────────────────────────────────
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    logger.info("PPT report generated: %d bytes", buffer.getbuffer().nbytes)
    return buffer.read()

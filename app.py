"""
app.py — Excel Auto-Analyst v2.0
─────────────────────────────────────────────────────────────────
Thin router only. Zero business logic here.
Matches original navigation: Home | Dashboard | Custom | Chat + PPT Report (new)
"""

from __future__ import annotations

import logging

import streamlit as st

from config.settings import CONFIG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

st.set_page_config(
    page_title=CONFIG.title,
    page_icon=CONFIG.page_icon,
    layout=CONFIG.layout,
    initial_sidebar_state="expanded",
)


def _init_session_state() -> None:
    defaults = {
        "load_result": None,
        "profile": None,
        "clean_result": None,
        "chat_history": [],
        "current_page": "🏠 Home & Data Cleaning",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _render_error(error: Exception) -> None:
    st.error(
        f"**Something went wrong:** {type(error).__name__}: {error}\n\n"
        "Try refreshing the page or uploading a different file."
    )
    if st.button("Clear error & restart"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def _render_sidebar() -> str:
    with st.sidebar:
        st.title("📊 Auto-Analyst")
        st.write("Upload your data and navigate through the tabs below.")

        # ── File upload ───────────────────────────────────────────
        st.markdown("**Upload Excel/CSV**")
        uploaded = st.file_uploader(
            "Drag and drop file here",
            type=["csv", "xlsx", "xls", "xlsm"],
            label_visibility="collapsed",
            help=f"Limit {CONFIG.data.max_file_size_mb}MB per file · CSV, XLSX",
        )

        if uploaded is not None:
            _handle_upload(uploaded)

        st.markdown("---")
        st.markdown("**Navigate to:**")

        # Same pages as original + PPT Report (new)
        pages = [
            "🏠 Home & Data Cleaning",
            "📈 Auto-Dashboard",
            "🎨 Custom Analysis",
            "🗣️ Chat with Data",
            "📋 PPT Report",  # NEW feature
        ]

        has_data = st.session_state.load_result is not None

        for p in pages:
            disabled = (not has_data) and (p != "🏠 Home & Data Cleaning")
            if st.button(
                p, use_container_width=True, disabled=disabled, key=f"nav_{p}"
            ):
                st.session_state.current_page = p

        # Quality badge
        if st.session_state.profile:
            qs = st.session_state.profile.quality_score
            color = "green" if qs >= 75 else "orange" if qs >= 50 else "red"
            st.markdown(f"\n**Data Quality:** :{color}[{qs}/100]")

        st.markdown("---")
        st.info("Built with Streamlit & Python")

    return st.session_state.current_page


def _handle_upload(uploaded) -> None:
    """Load, validate, profile — only re-runs when file changes."""
    from core.data_loader import LoadError, load_dataframe
    from core.validator import profile_dataframe

    # Only re-process if new file
    current_name = (
        st.session_state.load_result.file_name if st.session_state.load_result else None
    )
    if current_name == uploaded.name:
        return

    file_bytes = uploaded.read()
    max_bytes = CONFIG.data.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        st.error(
            f"File too large ({len(file_bytes) / 1e6:.1f} MB). Limit: {CONFIG.data.max_file_size_mb} MB."
        )
        return

    with st.spinner("Loading data..."):
        try:
            load_result = load_dataframe(file_bytes, uploaded.name)
            profile = profile_dataframe(load_result.df)
            st.session_state.load_result = load_result
            st.session_state.profile = profile
            st.session_state.clean_result = None
            st.session_state.chat_history = []
            # Also store in old-style session key for compatibility
            st.session_state["df_cleaned"] = load_result.df
        except LoadError as e:
            st.error(f"Could not load file: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {type(e).__name__}: {e}")


# ── Page renderers ────────────────────────────────────────────────


def _page_home():
    from ui.pages.upload_page import render

    render()


def _page_dashboard():
    from ui.pages.stats_page import render

    render()


def _page_custom():
    from ui.pages.custom_analysis_page import render

    render()


def _page_chat():
    from ui.pages.chat_page import render

    render()


def _page_report():
    from ui.pages.report_page import render

    render()


def _inject_custom_css() -> None:
    st.markdown(
        """
<style>
    /* Google Fonts import */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Style sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid rgba(13, 148, 136, 0.2);
    }

    /* Styled navigation buttons */
    div[data-testid="stVerticalBlock"] button {
        background-color: rgba(30, 41, 59, 0.5) !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(226, 232, 240, 0.1) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stVerticalBlock"] button:hover {
        background-color: rgba(13, 148, 136, 0.15) !important;
        border-color: #0D9488 !important;
        color: #0D9488 !important;
    }

    /* Style metric cards */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.4);
        padding: 15px 20px;
        border-radius: 12px;
        border: 1px solid rgba(226, 232, 240, 0.08);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(13, 148, 136, 0.4);
    }

    /* Header fonts */
    h1, h2, h3 {
        font-weight: 600 !important;
    }

    /* Links and highlight styling */
    a {
        color: #0D9488 !important;
    }

    /* Success message custom styling */
    div.stAlert {
        border-radius: 10px !important;
        border: 1px solid rgba(13, 148, 136, 0.2) !important;
        background-color: rgba(13, 148, 136, 0.05) !important;
    }
</style>
    """,
        unsafe_allow_html=True,
    )


def main() -> None:
    _init_session_state()
    _inject_custom_css()
    page = _render_sidebar()

    # No file uploaded yet
    if st.session_state.load_result is None and page != "🏠 Home & Data Cleaning":
        st.info("👈 Please upload a CSV or Excel file from the sidebar to begin.")
        st.markdown("""
### Welcome to Excel Auto-Analyst!
This app helps you:
1. **Clean Data** — remove duplicates, smart imputation (not just fill with 0)
2. **Visualize** — instant dashboards with KPIs, distributions, correlations
3. **Analyse** — custom charts with AI-powered insights
4. **Chat** — ask questions in plain English, AI generates charts & answers
5. **Report** — one-click executive PowerPoint report generation *(new!)*
        """)
        return

    page_map = {
        "🏠 Home & Data Cleaning": _page_home,
        "📈 Auto-Dashboard": _page_dashboard,
        "🎨 Custom Analysis": _page_custom,
        "🗣️ Chat with Data": _page_chat,
        "📋 PPT Report": _page_report,
    }

    renderer = page_map.get(page, _page_home)
    try:
        renderer()
    except Exception as e:
        _render_error(e)


if __name__ == "__main__":
    main()

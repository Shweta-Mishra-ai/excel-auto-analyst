"""
app.py - Excel Auto-Analyst v2.0
Thin router only. Zero business logic here.
"""

from __future__ import annotations

import logging

import streamlit as st

from config.settings import CONFIG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

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
        "last_upload_error": None,
        "last_upload_name": None,
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


def _process_upload(uploaded) -> None:
    """
    Process uploaded file - called from main body, not sidebar.
    Every failure path sets st.session_state.last_upload_error so the
    main body can show a visible, persistent error/warning to the user.
    """
    from core.data_loader import LoadError, load_dataframe
    from core.validator import profile_dataframe

    # Skip if this exact file was already successfully loaded
    current_name = (
        st.session_state.load_result.file_name
        if st.session_state.load_result
        else None
    )
    if current_name == uploaded.name:
        return

    st.session_state.last_upload_name = uploaded.name
    st.session_state.last_upload_error = None

    # Read bytes immediately - before any rerun can clear them
    try:
        file_bytes = uploaded.read()
    except Exception as e:
        msg = f"Could not read '{uploaded.name}': {type(e).__name__}: {e}"
        logger.exception(msg)
        st.session_state.last_upload_error = msg
        return

    if len(file_bytes) == 0:
        msg = f"'{uploaded.name}' is empty (0 bytes). Please choose a valid file."
        st.session_state.last_upload_error = msg
        return

    max_bytes = CONFIG.data.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        size_mb = len(file_bytes) / 1e6
        msg = (
            f"'{uploaded.name}' is {size_mb:.1f} MB, which exceeds the "
            f"{CONFIG.data.max_file_size_mb} MB limit. Please upload a "
            f"smaller file or split it into parts."
        )
        st.session_state.last_upload_error = msg
        return

    try:
        load_result = load_dataframe(file_bytes, uploaded.name)
    except LoadError as e:
        msg = f"Could not load '{uploaded.name}': {e}"
        logger.warning(msg)
        st.session_state.last_upload_error = msg
        return
    except Exception as e:
        msg = f"Unexpected error loading '{uploaded.name}': {type(e).__name__}: {e}"
        logger.exception(msg)
        st.session_state.last_upload_error = msg
        return

    if load_result.df is None or load_result.df.empty:
        msg = (
            f"'{uploaded.name}' loaded but contains no data rows. "
            "Please check the file and try again."
        )
        st.session_state.last_upload_error = msg
        return

    try:
        profile = profile_dataframe(load_result.df)
    except Exception as e:
        msg = (
            f"'{uploaded.name}' loaded, but data profiling failed: "
            f"{type(e).__name__}: {e}"
        )
        logger.exception(msg)
        st.session_state.last_upload_error = msg
        return

    # Success
    st.session_state.load_result = load_result
    st.session_state.profile = profile
    st.session_state.clean_result = None
    st.session_state.chat_history = []
    st.session_state["df_cleaned"] = load_result.df
    st.session_state.current_page = "🏠 Home & Data Cleaning"
    st.session_state.last_upload_error = None
    logger.info(
        "Loaded '%s': %d rows x %d cols",
        uploaded.name,
        load_result.original_rows,
        len(load_result.df.columns),
    )


def _render_sidebar() -> tuple[str, object]:
    """Render sidebar. Returns (current_page, uploaded_file_or_None)."""
    uploaded = None
    with st.sidebar:
        st.title("📊 Auto-Analyst")
        st.write("Upload your data and navigate through the tabs below.")

        st.markdown("**Upload Excel/CSV**")
        uploaded = st.file_uploader(
            "Drag and drop file here",
            type=["csv", "xlsx", "xls", "xlsm"],
            label_visibility="collapsed",
            help=f"Limit {CONFIG.data.max_file_size_mb}MB per file - CSV, XLSX",
            key="file_uploader",
        )

        # Show filename if loaded
        if st.session_state.load_result:
            st.success(
                f"Loaded: {st.session_state.load_result.file_name} "
                f"({st.session_state.load_result.original_rows:,} rows)"
            )

        # Persistent upload error/warning in sidebar too
        if st.session_state.get("last_upload_error"):
            st.error(st.session_state.last_upload_error)

        st.markdown("---")
        st.markdown("**Navigate to:**")

        pages = [
            "🏠 Home & Data Cleaning",
            "📈 Auto-Dashboard",
            "🎨 Custom Analysis",
            "🗣️ Chat with Data",
            "📋 PPT Report",
        ]

        has_data = st.session_state.load_result is not None

        for p in pages:
            disabled = (not has_data) and (p != "🏠 Home & Data Cleaning")
            if st.button(
                p,
                width="stretch",
                disabled=disabled,
                key=f"nav_{p}",
            ):
                st.session_state.current_page = p

        if st.session_state.profile:
            qs = st.session_state.profile.quality_score
            color = "green" if qs >= 75 else "orange" if qs >= 50 else "red"
            st.markdown(f"\n**Data Quality:** :{color}[{qs}/100]")

        st.markdown("---")
        st.info("Built with Streamlit & Python")

    return st.session_state.current_page, uploaded


def _inject_custom_css() -> None:
    st.markdown(
        """
<style>
    html, body, [class*="css"] {
        font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid rgba(13,148,136,0.2);
    }
    div[data-testid="stMetric"] {
        background: rgba(30,41,59,0.4);
        padding: 15px 20px;
        border-radius: 12px;
        border: 1px solid rgba(226,232,240,0.08);
    }
    h1, h2, h3 { font-weight: 600 !important; }
    a { color: #0D9488 !important; }
</style>
    """,
        unsafe_allow_html=True,
    )


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


def main() -> None:
    _init_session_state()
    _inject_custom_css()

    page, uploaded = _render_sidebar()

    # Process upload in main body - fixes Streamlit Cloud file bytes bug
    if uploaded is not None:
        _process_upload(uploaded)

    # No file yet - show error/warning prominently, then welcome screen
    if st.session_state.load_result is None:
        if st.session_state.get("last_upload_error"):
            st.error(
                f"### ⚠️ Upload failed\n\n{st.session_state.last_upload_error}"
            )
            st.info(
                "Please check the file format and size, then upload again "
                "using the sidebar."
            )
        else:
            st.info("👈 Upload a CSV or Excel file from the sidebar to begin.")

        st.markdown("""
### Welcome to Excel Auto-Analyst!

| Step | What it does |
|------|-------------|
| 🏠 **Upload & Clean** | Smart cleaning - median imputation, duplicate removal |
| 📈 **Auto-Dashboard** | KPIs, distributions, correlation heatmap |
| 🎨 **Custom Analysis** | Bar, line, scatter charts with AI insights |
| 🗣️ **Chat with Data** | Ask questions in plain English |
| 📋 **PPT Report** | One-click 9-slide executive presentation |
        """)
        return

    # Have data, but show a warning banner if the LAST upload attempt
    # (e.g. a re-upload of a different file) failed, while keeping the
    # previously loaded data usable.
    if st.session_state.get("last_upload_error"):
        st.warning(
            f"⚠️ Your last upload attempt failed: "
            f"{st.session_state.last_upload_error}\n\n"
            f"Still showing results for "
            f"**{st.session_state.load_result.file_name}**."
        )

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

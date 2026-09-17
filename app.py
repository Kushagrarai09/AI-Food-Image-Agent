import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from agent.controller import run_agent
from config.settings import AI_THRESHOLD, CANDIDATES, DRIVE_FOLDER_ID, ROOT


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Food Image Agent",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    /* ---------- App ---------- */
    .stApp {
        background: #f6f7fb;
    }

    .main .block-container {
        max-width: 1180px;
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }

    /* ---------- Hide unnecessary Streamlit chrome ---------- */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e8eaf0;
    }

    [data-testid="stSidebar"] .block-container {
        padding: 1.8rem 1.25rem;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 1.8rem;
    }

    .sidebar-logo {
        width: 38px;
        height: 38px;
        border-radius: 11px;
        background: #111827;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 19px;
    }

    .sidebar-title {
        font-size: 15px;
        font-weight: 700;
        color: #111827;
    }

    .sidebar-subtitle {
        font-size: 11px;
        color: #8a91a1;
        margin-top: 1px;
    }

    .sidebar-section {
        font-size: 11px;
        font-weight: 700;
        color: #8a91a1;
        text-transform: uppercase;
        letter-spacing: .08em;
        margin: 1.5rem 0 .65rem 0;
    }

    .sidebar-note {
        background: #f8f9fc;
        border: 1px solid #eceef3;
        border-radius: 10px;
        padding: 10px 11px;
        font-size: 11px;
        line-height: 1.5;
        color: #6b7280;
        margin-top: 8px;
    }

    /* ---------- Header ---------- */
    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.7rem;
    }

    .brand-wrap {
        display: flex;
        align-items: center;
        gap: 13px;
    }

    .brand-icon {
        width: 48px;
        height: 48px;
        border-radius: 13px;
        background: #111827;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 4px 12px rgba(17, 24, 39, .10);
    }

    .brand-title {
        font-size: 29px;
        line-height: 1.1;
        font-weight: 750;
        color: #111827;
        letter-spacing: -.5px;
    }

    .brand-subtitle {
        color: #7a8190;
        font-size: 13px;
        margin-top: 4px;
    }

  


    /* ---------- Cards ---------- */
    .card {
        background: #ffffff;
        border: 1px solid #e8eaf0;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(17, 24, 39, .025);
    }

    .card + .card {
        margin-top: 16px;
    }

    .card-title {
        color: #171b26;
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .card-description {
        color: #7b8190;
        font-size: 12px;
        margin-bottom: 14px;
    }

    /* ---------- Upload area ---------- */
    [data-testid="stFileUploader"] {
        background: #fafbfc;
        border: 1px dashed #d8dce5;
        border-radius: 12px;
        padding: 4px;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: transparent;
    }

    /* ---------- File loaded ---------- */
    .file-card {
        display: flex;
        align-items: center;
        gap: 12px;
        background: #f8fafc;
        border: 1px solid #e7eaf0;
        border-radius: 11px;
        padding: 12px 14px;
        margin-top: 12px;
    }

    .file-icon {
        width: 38px;
        height: 38px;
        border-radius: 9px;
        background: #eef2ff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }

    .file-name {
        font-size: 13px;
        font-weight: 650;
        color: #252a35;
        word-break: break-word;
    }

    .file-meta {
        font-size: 11px;
        color: #8a91a1;
        margin-top: 2px;
    }

    .file-ready {
        margin-left: auto;
        color: #15803d;
        font-size: 11px;
        font-weight: 700;
        white-space: nowrap;
    }

    /* ---------- Buttons ---------- */
    .stButton > button,
    .stDownloadButton > button,
    .stLinkButton > a {
        border-radius: 10px !important;
        min-height: 42px !important;
        font-weight: 650 !important;
    }

    /* ---------- Metrics ---------- */
    .metric {
        background: #ffffff;
        border: 1px solid #e8eaf0;
        border-radius: 13px;
        padding: 16px 17px;
        min-height: 88px;
    }

    .metric-label {
        color: #8a91a1;
        font-size: 11px;
        font-weight: 600;
        margin-bottom: 5px;
    }

    .metric-value {
        color: #171b26;
        font-size: 25px;
        line-height: 1;
        font-weight: 750;
    }

    /* ---------- Processing ---------- */
    .processing-title {
        color: #171b26;
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 3px;
    }

    .processing-subtitle {
        color: #7b8190;
        font-size: 12px;
        margin-bottom: 12px;
    }

    .status-box {
        background: #f8fafc;
        border: 1px solid #e7eaf0;
        border-radius: 10px;
        padding: 10px 13px;
        color: #4b5563;
        font-size: 12px;
        margin-top: 8px;
    }

    /* ---------- Results ---------- */
    .results-heading {
        margin-top: 1.5rem;
        margin-bottom: .75rem;
    }

    .results-title {
        color: #171b26;
        font-size: 17px;
        font-weight: 700;
    }

    .results-subtitle {
        color: #8a91a1;
        font-size: 12px;
        margin-top: 2px;
    }

    /* ---------- Small footer ---------- */
    .footer-note {
        text-align: center;
        color: #a0a6b2;
        font-size: 11px;
        padding-top: 20px;
    }

    /* ---------- Responsive ---------- */
    @media (max-width: 800px) {
        .brand-title {
            font-size: 24px;
        }

        .ready-pill {
            display: none;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo">🍽️</div>
            <div>
                <div class="sidebar-title">AI Food Image Agent</div>
                <div class="sidebar-subtitle">Automation Console</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-section">Agent settings</div>', unsafe_allow_html=True)

    candidate_count = st.slider(
        "Candidates per item",
        min_value=1,
        max_value=10,
        value=CANDIDATES,
    )

    threshold = st.slider(
        "AI acceptance threshold",
        min_value=50,
        max_value=95,
        value=AI_THRESHOLD,
    )

    st.markdown('<div class="sidebar-section">Google Drive</div>', unsafe_allow_html=True)

    drive_folder = st.text_input(
        "Folder ID",
        value=DRIVE_FOLDER_ID,
        placeholder="Enter Drive folder ID",
        help="Enter only the Google Drive folder ID, not the complete URL.",
        label_visibility="visible",
    )

    st.markdown(
        """
        <div class="sidebar-note">
            Processed food images and the final Excel report are uploaded
            automatically to this Google Drive folder.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-section">AI source</div>', unsafe_allow_html=True)

    st.caption("Image search: Wikimedia Commons")
    st.caption("Vision scoring: Gemini when configured")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="topbar">
        <div class="brand-wrap">
            <div class="brand-icon">🍽️</div>
            <div>
                <div class="brand-title">AI Food Image Agent</div>
                <div class="brand-subtitle">
                    Automated food image collection, quality checking and delivery
                </div>
            </div>
        </div>

    
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# INPUT CARD
# ============================================================

st.markdown(
    """
    <div class="card">
        <div class="card-title">Menu Input</div>
        <div class="card-description">
            Upload an Excel file containing the restaurant food item names.
        </div>
    """,
    unsafe_allow_html=True,
)

uploaded = st.file_uploader(
    "Upload Excel file",
    type=["xlsx", "xls"],
    label_visibility="visible",
)

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# FILE LOADED
# ============================================================

if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(uploaded.getbuffer())
        input_path = Path(tmp.name)

    item_count = None

    try:
        df_preview = pd.read_excel(input_path)
        item_count = len(df_preview)
    except Exception:
        pass

    file_info = (
        f"{item_count} food item{'s' if item_count != 1 else ''}"
        if item_count is not None
        else "Menu file loaded"
    )

    st.markdown(
        f"""
        <div class="file-card">
            <div class="file-icon">📄</div>
            <div>
                <div class="file-name">{uploaded.name}</div>
                <div class="file-meta">{file_info}</div>
            </div>
            <div class="file-ready">✓ Ready</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # ========================================================
    # START
    # ========================================================

    start = st.button(
        "🚀  Start Processing",
        type="primary",
        use_container_width=True,
    )

    if start:
        if not drive_folder.strip():
            st.error("Please enter your Google Drive folder ID.")
            st.stop()

        # ----------------------------------------------------
        # PROCESSING CARD
        # ----------------------------------------------------

        st.markdown(
            """
            <div class="card">
                <div class="processing-title">Processing menu</div>
                <div class="processing-subtitle">
                    The agent is searching, evaluating, processing and uploading images.
                </div>
            """,
            unsafe_allow_html=True,
        )

        progress_bar = st.progress(0)
        status_box = st.empty()
        rows = []

        def callback(index, total, food, message):
            if total:
                progress_bar.progress(min(index / total, 1.0))

            status_box.markdown(
                f"""
                <div class="status-box">
                    <strong>{food}</strong>
                    <span> — {message}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        try:
            rows, report_path = run_agent(
                input_path,
                candidates_per_item=candidate_count,
                threshold=threshold,
                drive_folder_id=drive_folder.strip(),
                progress_callback=callback,
            )

            progress_bar.progress(1.0)
            status_box.empty()

            st.markdown("</div>", unsafe_allow_html=True)

            # ------------------------------------------------
            # STATS
            # ------------------------------------------------

            total_items = len(rows)
            uploaded_count = 0
            failed_count = 0

            for row in rows:
                status = str(row.get("Status", "")).lower()
                uploaded_value = str(row.get("Uploaded", "")).lower()

                if (
                    "uploaded" in status
                    or uploaded_value in ["yes", "true", "1"]
                ):
                    uploaded_count += 1

                if "fail" in status or "error" in status:
                    failed_count += 1

            processed_count = max(
                uploaded_count,
                total_items - failed_count,
            )

            st.success("Processing completed.")

            m1, m2, m3, m4 = st.columns(4)

            with m1:
                st.markdown(
                    f"""
                    <div class="metric">
                        <div class="metric-label">TOTAL ITEMS</div>
                        <div class="metric-value">{total_items}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with m2:
                st.markdown(
                    f"""
                    <div class="metric">
                        <div class="metric-label">PROCESSED</div>
                        <div class="metric-value">{processed_count}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with m3:
                st.markdown(
                    f"""
                    <div class="metric">
                        <div class="metric-label">UPLOADED</div>
                        <div class="metric-value">{uploaded_count}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with m4:
                st.markdown(
                    f"""
                    <div class="metric">
                        <div class="metric-label">FAILED</div>
                        <div class="metric-value">{failed_count}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # ------------------------------------------------
            # RESULTS
            # ------------------------------------------------

            st.markdown(
                """
                <div class="results-heading">
                    <div class="results-title">Processing Results</div>
                    <div class="results-subtitle">
                        Image status and processing details for each food item
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
            )

            # ------------------------------------------------
            # ACTIONS
            # ------------------------------------------------

            st.write("")

            action1, action2 = st.columns(2)

            with action1:
                st.download_button(
                    "⬇️  Download Processing Report",
                    data=report_path.read_bytes(),
                    file_name="processing_report.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    use_container_width=True,
                )

            with action2:
                drive_url = (
                    "https://drive.google.com/drive/folders/"
                    + drive_folder.strip()
                )

                st.link_button(
                    "☁️  Open Google Drive Folder",
                    drive_url,
                    use_container_width=True,
                )

            # ------------------------------------------------
            # LOCAL OUTPUT
            # ------------------------------------------------

            with st.expander("Technical details"):
                st.write("Local processed images:")
                st.code(
                    str(ROOT / "output" / "images"),
                    language="text",
                )

        except Exception as exc:
            st.markdown("</div>", unsafe_allow_html=True)
            st.error(f"Agent error: {exc}")


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer-note">
        AI Food Image Agent • Automated image collection and processing
    </div>
    """,
    unsafe_allow_html=True,
)

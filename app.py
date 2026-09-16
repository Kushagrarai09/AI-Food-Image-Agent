import tempfile
from pathlib import Path
import streamlit as st

from agent.controller import run_agent
from config.settings import AI_THRESHOLD, CANDIDATES, DRIVE_FOLDER_ID, ROOT

st.set_page_config(page_title="AI Menu Image Agent", page_icon="🍽️", layout="wide")

st.title("🍽️ AI Menu Image Automation Agent")
st.caption("Excel → Image Search → AI Selection → Quality Check → 1800×1200 → Rename → Google Drive → Report")

with st.sidebar:
    st.header("Agent Settings")
    candidate_count = st.slider("Candidates per food item", 1, 10, CANDIDATES)
    threshold = st.slider("AI acceptance threshold", 50, 95, AI_THRESHOLD)
    drive_folder = st.text_input("Google Drive folder ID", value=DRIVE_FOLDER_ID)
    st.markdown("**Free MVP source:** Wikimedia Commons")
    st.markdown("**AI:** Gemini Vision when `GEMINI_API_KEY` is configured")

uploaded = st.file_uploader("Upload restaurant menu Excel", type=["xlsx", "xls"])

if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(uploaded.getbuffer())
        input_path = Path(tmp.name)
    st.success(f"Loaded: {uploaded.name}")

    if st.button("🚀 START AGENT", type="primary", use_container_width=True):
        status_box = st.empty()
        progress_bar = st.progress(0)
        rows = []

        def callback(index, total, food, message):
            progress_bar.progress(index / total)
            status_box.info(f"**{food}** — {message}")

        try:
            rows, report_path = run_agent(
                input_path,
                candidates_per_item=candidate_count,
                threshold=threshold,
                drive_folder_id=drive_folder.strip(),
                progress_callback=callback,
            )
            progress_bar.progress(1.0)
            st.success("Agent run completed. One failed food item does not stop the remaining items.")
            st.dataframe(rows, use_container_width=True)
            st.download_button(
                "⬇️ Download Processing Report",
                data=report_path.read_bytes(),
                file_name="processing_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            st.info(f"Local processed images: {ROOT / 'output' / 'images'}")
        except Exception as exc:
            st.error(str(exc))
else:
    st.info("Upload the supplied menu Excel (or sample_input.xlsx) to start.")
    st.markdown("### What this agent does")
    st.markdown("""
1. Reads each `item_name` from Excel.
2. Searches Wikimedia Commons automatically.
3. Runs basic blur/resolution checks.
4. Uses Gemini Vision to score food match, clarity, centering and framing.
5. Rejects poor candidates and tries another candidate.
6. Center-crops/resizes to exactly **1800×1200 JPG** and keeps the file below 10 MB.
7. Renames using the food item name.
8. Uploads to the configured Google Drive folder.
9. Creates `processing_report.xlsx` with status and image provenance.
""")

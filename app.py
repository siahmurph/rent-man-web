import streamlit as st
import pandas as pd
from google.cloud import storage
from io import BytesIO, StringIO
import csv
from openpyxl.styles import PatternFill, Border, Side
from openpyxl.worksheet.pagebreak import Break

# --- CONFIGURATION (Keep your existing PROPERTY_NAMES and OUTPUT_ORDER) ---
# ... (Configuration code here) ...

# --- GCS INITIALIZATION ---
client = storage.Client.from_service_account_info(st.secrets["gcp"])
BUCKET_NAME = "rent-man-reports-01"

# --- MAIN UI SETUP ---
st.set_page_config(page_title="RentManager Pro Dashboard", layout="wide")
st.title("📊 RentManager Pro Dashboard")

# --- TOP ROW: CONTROLS ---
# Using a container with a border helps separate the tools from the data table
with st.container(border=True):
    col1, col2 = st.columns([1, 2])

    with col1:
        # Move GCS Polling here to fill the top-left space
        try:
            bucket = client.get_bucket(BUCKET_NAME)
            available_files = [
                b.name for b in bucket.list_blobs() if b.name.endswith(".csv")
            ]
            selected_file = st.selectbox(
                "📂 1. Choose GCS File",
                ["Select..."] + sorted(available_files, reverse=True),
            )
        except Exception as e:
            st.error(f"GCS Error: {e}")
            selected_file = None

    with col2:
        if selected_file and selected_file != "Select...":
            # Form prevents "jitter" while clicking multiple properties
            with st.form("processing_controls"):
                selected_props = st.multiselect(
                    "🏗️ 2. Select Properties:", OUTPUT_ORDER, default=OUTPUT_ORDER
                )
                submit_btn = st.form_submit_button(
                    "Generate Report", use_container_width=True
                )
        else:
            st.info("Please select a file to begin.")
            submit_btn = False

# --- DATA PROCESSING & RESULTS ---
if selected_file and selected_file != "Select..." and submit_btn:
    blob = bucket.blob(selected_file)
    header_indices, lines = parse_csv_sections(blob.download_as_text())

    # ... (Rest of your data processing and table rendering logic) ...

    # Result area with Metrics and Download
    st.divider()
    res_col1, res_col2 = st.columns([3, 1])

    with res_col1:
        st.subheader("Report Preview")
        st.dataframe(final_df, use_container_width=True, height=600)

    with res_col2:
        st.metric("Properties Processed", len(selected_props))
        xlsx_data = convert_df_to_excel(final_df)
        st.download_button(
            "📥 Download Excel Report",
            xlsx_data,
            f"Report_{selected_file}.xlsx",
            use_container_width=True,
        )

# --- SIDEBAR (Optional Clean-up) ---
with st.sidebar:
    st.image(
        "https://www.gstatic.com/images/branding/product/2x/cloud_storage_64dp.png",
        width=50,
    )
    st.markdown("### System Status")
    st.success("Connected to GCS")
    st.caption(f"Bucket: {BUCKET_NAME}")

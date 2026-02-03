import streamlit as st
import pandas as pd
from google.cloud import storage
from datetime import datetime
from io import BytesIO, StringIO
import csv
from openpyxl.styles import PatternFill, Border, Side
from openpyxl.worksheet.pagebreak import Break

# --- CONFIGURATION (From your Local Code) ---
PROPERTY_NAMES = [
    "12241 Londonderry Lane",
    "1410 W. Irving Park",
    "1745 N. Clybourn Residential",
    "2949 Halsted",
    "3349 Willowcreek",
    "6854 Highland Pines Circle",
    "995 Second Ave.",
    "Eastgate Plaza",
    "Foxmoor Plaza",
    "Grand Trunk Warehouse",
    "Morton Grove 09",
    "Morton Grove 10",
    "Morton Grove 11",
    "Morton Grove 37",
    "Patriot Square",
    "Riverdale Shopping Center",
    "San Carlos Plaza",
    "Shoppes on Clybourn",
    "Willowcreek Plaza",
]
OUTPUT_ORDER = [
    "Shoppes on Clybourn",
    "Eastgate Plaza",
    "Grand Trunk Warehouse",
    "Willowcreek Plaza",
    "3349 Willowcreek",
    "995 Second Ave.",
    "Foxmoor Plaza",
    "Patriot Square",
    "Riverdale Shopping Center",
    "San Carlos Plaza",
    "1410 W. Irving Park",
    "2949 Halsted",
    "1745 N. Clybourn Residential",
    "Morton Grove 09",
    "Morton Grove 10",
    "Morton Grove 11",
    "Morton Grove 37",
    "12241 Londonderry Lane",
    "6854 Highland Pines Circle",
]
HEADER_ROW = "Account Type,Parent,Account,Amount"

# --- GCS SETUP ---
client = storage.Client.from_service_account_info(st.secrets["gcp"])
BUCKET_NAME = "rent-man-reports-01"


# --- CORE LOGIC (Imported from your Local Version) ---
def parse_csv_sections(content):
    lines = content.strip().split("\n")
    header_indices = []
    for i, line in enumerate(lines):
        normalized_line = line.strip().replace('"', "").replace("\r", "")
        if normalized_line == HEADER_ROW:
            header_indices.append(i)
    return header_indices, lines


def transform_property_section(lines, start_idx, end_idx, property_name):
    # ... [Same logic as your local transform_property_section function] ...
    # (Keeps expenses, groups by parent, adds totals)
    pass


# --- STREAMLIT UI ---
st.set_page_config(page_title="RentManager Pro Dashboard", layout="wide")

with st.sidebar:
    st.header("1. Select Report")
    bucket = client.get_bucket(BUCKET_NAME)
    blobs = bucket.list_blobs()
    available_files = [b.name for b in blobs if b.name.endswith(".csv")]
    selected_file = st.selectbox("Choose GCS File", available_files)

if selected_file:
    # 1. Fetch from GCS
    blob = bucket.blob(selected_file)
    content = blob.download_as_text()

    # 2. Parse and Validate
    header_indices, lines = parse_csv_sections(content)

    if len(header_indices) != 19:
        st.error(
            f"Validation Error: Found {len(header_indices)} properties, expected 19."
        )
    else:
        st.success(f"Successfully loaded {selected_file}")

        # 3. Property Selection
        st.subheader("2. Filter & Export")
        selected_props = st.multiselect(
            "Include Properties:", OUTPUT_ORDER, default=OUTPUT_ORDER
        )

        # 4. Processing (The actual stitching)
        all_rows = []
        for i, (start_idx, prop_name) in enumerate(zip(header_indices, PROPERTY_NAMES)):
            if prop_name in selected_props:
                end_idx = (
                    header_indices[i + 1] if i + 1 < len(header_indices) else len(lines)
                )
                all_rows.extend(
                    transform_property_section(lines, start_idx, end_idx, prop_name)
                )
                all_rows.append(["", "", "", ""])  # Spacer

        final_df = pd.DataFrame(
            all_rows, columns=["Account Type", "Parent", "Account", "Amount"]
        )

        # 5. UI Tabs for Preview
        tab1, tab2 = st.tabs(["📊 Summary View", "📥 Export"])

        with tab1:
            st.dataframe(final_df, use_container_width=True, height=600)

        with tab2:
            # Excel Download (Using your openpyxl logic)
            excel_data = convert_df_to_excel(
                final_df
            )  # This uses your local formatting function
            st.download_button(
                "📥 Download Stitched XLSX", excel_data, f"{selected_file}.xlsx"
            )

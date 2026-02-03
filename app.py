import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- UI SETUP ---
st.set_page_config(page_title="RentManager Debug", page_icon="📊", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    try:
        # Access the Spreadsheet ID directly from your Secrets
        spreadsheet_id = st.secrets["connections"]["gsheets"]["spreadsheet"]
        client = conn.client

        # Open by URL since that is what you have in your secrets
        sh = client.open_by_url(spreadsheet_id)
        metadata = sh.fetch_sheet_metadata()
        weeks = [s["properties"]["title"] for s in metadata["sheets"]]

        st.success("✅ Connection Successful")
        selected_week = st.selectbox(
            "📅 Select Reporting Period", ["Select..."] + weeks
        )

    except Exception as e:
        st.error("⚠️ Metadata Fetch Failed")
        st.code(str(e))
        st.stop()

# --- MAIN CONTENT ---
if selected_week != "Select...":
    try:
        # Pull data from Cell A1
        df = conn.read(worksheet=selected_week, header=None)
        st.write(f"### Previewing: {selected_week}")
        # 2026 Syntax for dataframes
        st.dataframe(df, width="stretch")
    except Exception as e:
        st.error(f"Error reading tab '{selected_week}': {e}")
else:
    st.info("Select a week in the sidebar to test the data connection.")

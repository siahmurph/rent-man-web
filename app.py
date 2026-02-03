import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- UI SETUP ---
st.set_page_config(page_title="RentManager Debug", page_icon="📊", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    # 2026 Syntax: width='stretch' replaces use_container_width
    st.markdown("### **System Status**")
    
    try:
        # Step 1: Attempt to verify connection and fetch metadata
        sheet_metadata = conn.client._spreadsheets.get(conn._spreadsheet_id)
        weeks = [s['properties']['title'] for s in sheet_metadata['sheets']]
        
        st.success("✅ Connection Successful")
        selected_week = st.selectbox("📅 Select Reporting Period", ["Select..."] + weeks)
        
    except Exception as e:
        # Step 2: Print the REAL error message to the screen
        st.error("⚠️ Connection Failed")
        st.write("### Technical Error Details:")
        st.code(str(e))
        
        st.info("""
        **Common Fixes:**
        1. **Enable APIs:** Ensure 'Google Drive API' is enabled in Cloud Console.
        2. **Check Quotes:** Ensure `private_key` in Secrets is wrapped in "double quotes".
        3. **Sharing:** Re-verify the Sheet is shared with the service account email.
        """)
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
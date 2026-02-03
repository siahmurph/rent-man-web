import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io

# --- INITIALIZE VARIABLES ---
# This prevents the NameError if the sidebar fails to load
selected_week = "Select..."

# --- UI SETUP ---
st.set_page_config(page_title="RentManager Summarizer", page_icon="📊", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    try:
        # Reaches through to the actual gspread tool
        sh = conn._instance._open_spreadsheet()
        worksheets = sh.worksheets()
        weeks = [w.title for w in worksheets]

        st.success("✅ Connection Successful")
        selected_week = st.selectbox(
            "📅 Select Reporting Period", ["Select..."] + weeks
        )

    except Exception as e:
        st.error("⚠️ Connection Failed")
        st.code(str(e))
        st.stop()

# --- MAIN CONTENT ---
if selected_week != "Select...":
    try:
        # 1. Pull the raw CSV text from Cell A1
        raw_df = conn.read(worksheet=selected_week, header=None)
        raw_text = str(raw_df.iloc[0, 0]).strip()

        # 2. Parse the CSV text
        # quotechar handles the double quotes seen in your screenshot
        df = pd.read_csv(io.StringIO(raw_text), quotechar='"')

        # 3. Clean Column Names and Data
        df.columns = df.columns.str.strip()
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

        # 4. Filter for Expenses only
        expenses = df[df["Account Type"].str.contains("Expense", na=False)].copy()

        st.header(f"Summary for {selected_week}")

        if not expenses.empty:
            # Display the processed data
            st.dataframe(expenses, width="stretch", height=500)

            # 5. Summary Metric
            total_val = expenses["Amount"].sum()
            st.divider()
            st.metric(label="Grand Total Expenses", value=f"${total_val:,.2f}")
        else:
            st.warning("⚠️ No 'Expense' rows found in the data.")

    except Exception as e:
        st.error(f"Error processing data: {e}")
else:
    st.info("👈 Please select a reporting period in the sidebar.")

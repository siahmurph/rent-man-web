import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io

# --- UI SETUP ---
st.set_page_config(page_title="RentManager Summarizer", page_icon="📊", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    try:
        # Working connection logic from our debug phase
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
        # 1. Pull the raw CSV text from Cell A1 of the selected tab
        raw_df = conn.read(worksheet=selected_week, header=None)
        raw_text = raw_df.iloc[0, 0]

        # 2. Parse the text into a real table
        # We use io.StringIO to treat the text like a file
        df = pd.read_csv(io.StringIO(raw_text))

        # 3. Clean and Filter
        # Ensure 'Amount' is numeric and filter for Expenses only
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        expenses = df[df["Account Type"].str.contains("Expense", na=False)].copy()

        st.header(f"Summary for {selected_week}")

        # 4. Display the Cleaned Data
        # 2026 syntax: width="stretch"
        st.subheader("Detail View")
        st.dataframe(expenses, width="stretch", height=400)

        # 5. Summary Metrics
        total_val = expenses["Amount"].sum()
        st.divider()
        st.metric(label="Grand Total Expenses", value=f"${total_val:,.2f}")

    except Exception as e:
        st.error(f"Error processing data: {e}")
        st.info("Check that Cell A1 in your Google Sheet contains the raw CSV export.")
else:
    st.info("👈 Please select a reporting period in the sidebar to view the summary.")

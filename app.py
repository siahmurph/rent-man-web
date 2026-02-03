import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io

# --- INITIALIZE VARIABLES ---
# Prevents NameError if the sidebar fails
selected_week = "Select..."

# --- UI SETUP ---
st.set_page_config(page_title="RentManager Summarizer", page_icon="📊", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    try:
        # Reaches through the Streamlit wrapper to the actual gspread instance
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
        # 1. Pull the raw data. It comes in with each row as a CSV string in Column 0
        df_raw = conn.read(worksheet=selected_week, header=None)

        # 2. Transform the single column into a full table
        # We clean the quotes and split by the comma into separate columns
        df = df_raw[0].str.replace('"', "").str.split(",", expand=True)

        # 3. Set the first row (headers) as the actual column names
        df.columns = df.iloc[0].str.strip()
        df = df[1:].reset_index(drop=True)

        # 4. Convert 'Amount' to a number so we can do math
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

        # 5. Filter for Expenses
        # Using case-insensitive search to be safe
        expenses = df[
            df["Account Type"].str.contains("Expense", case=False, na=False)
        ].copy()

        st.header(f"Summary for {selected_week}")

        if not expenses.empty:
            # Display the processed data table
            st.dataframe(expenses, width="stretch", height=500)

            # 6. Show the Grand Total
            # Using .item() or float() converts the numpy int64 to a standard float
            total_val = float(expenses["Amount"].sum())

            st.divider()
            st.metric(label="Grand Total Expenses", value=f"${total_val:,.2f}")
        else:
            st.warning("⚠️ No 'Expense' rows found in the data.")
            st.write("Columns detected:", df.columns.tolist())

    except Exception as e:
        st.error(f"Error processing data: {e}")
else:
    st.info("👈 Please select a reporting period in the sidebar.")

import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io
import re

# --- UI SETUP ---
st.set_page_config(page_title="RentManager Summarizer", page_icon="📊", layout="wide")

# Initialize connection
conn = st.connection("gsheets", type=GSheetsConnection)

# --- SIDEBAR ---
selected_week = "Select..."
with st.sidebar:
    try:
        # Reaches through to the actual gspread tool to get sheet names
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
        # We read without a header first to ensure we get the full string from A1
        raw_df = conn.read(worksheet=selected_week, header=None)

        if raw_df.empty:
            st.error("The selected sheet appears to be empty.")
            st.stop()

        raw_text = str(raw_df.iloc[0, 0]).strip()

        # 2. Parse the CSV text with explicit quote handling
        # skipinitialspace=True helps if there's a space after the comma
        df = pd.read_csv(io.StringIO(raw_text), quotechar='"', skipinitialspace=True)

        # 3. Aggressive Cleaning
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()

        # Strip whitespace from all string columns to fix matching issues
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # 4. Handle the "Amount" column
        # Removes $, commas, and parentheses (often used for negative numbers in accounting)
        def clean_currency(value):
            if pd.isna(value) or value == "":
                return 0.0
            val_str = str(value).replace("$", "").replace(",", "").strip()
            # Handle accounting negative numbers: "(100.00)" -> "-100.00"
            if val_str.startswith("(") and val_str.endswith(")"):
                val_str = "-" + val_str[1:-1]
            try:
                return float(val_str)
            except ValueError:
                return 0.0

        if "Amount" in df.columns:
            df["Amount"] = df["Amount"].apply(clean_currency)
        else:
            st.error(f"Could not find 'Amount' column. Found: {list(df.columns)}")
            st.stop()

        # 5. Filter for Expenses
        # Using a regex to catch both 'Expense' and 'Non Operating Expense'
        mask = df["Account Type"].str.contains("Expense", case=False, na=False)
        expenses = df[mask].copy()

        st.header(f"Summary for {selected_week}")

        if not expenses.empty:
            # Display the processed data
            st.subheader("Expense Breakdown")
            st.dataframe(expenses, use_container_width=True, height=400)

            # 6. Summary Metric
            total_val = expenses["Amount"].sum()
            st.divider()
            st.metric(label="Grand Total Expenses", value=f"${total_val:,.2f}")
        else:
            st.warning("⚠️ No 'Expense' rows found in the data.")
            with st.expander("Debug: View Raw Data Structure"):
                st.write("Columns found:", list(df.columns))
                st.write(
                    "Unique Account Types:",
                    (
                        df["Account Type"].unique()
                        if "Account Type" in df.columns
                        else "N/A"
                    ),
                )
                st.dataframe(df.head())

    except Exception as e:
        st.error(f"Error processing data: {e}")
else:
    st.info("👈 Please select a reporting period in the sidebar.")

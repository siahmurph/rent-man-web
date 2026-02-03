import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io
import csv

# --- UI SETUP ---
st.set_page_config(page_title="RentManager Summarizer", page_icon="📊", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    try:
        sh = conn._instance._open_spreadsheet()
        worksheets = sh.worksheets()
        weeks = [w.title for w in worksheets]
        st.success("✅ Connection Successful")
        selected_week = st.selectbox(
            "📅 Select Reporting Period", ["Select..."] + weeks
        )
    except Exception as e:
        st.error("⚠️ Connection Failed")
        st.stop()

# --- MAIN CONTENT ---
if selected_week != "Select...":
    try:
        # 1. Pull the raw string from Cell A1
        raw_df = conn.read(worksheet=selected_week, header=None)
        if raw_df.empty:
            st.warning("Selected sheet is empty.")
            st.stop()

        raw_content = str(raw_df.iloc[0, 0]).strip()

        # 2. Manual CSV Parsing
        # We split the string into lines and use csv.reader to handle the quotes
        lines = raw_content.splitlines()
        reader = csv.reader(lines, quotechar='"', skipinitialspace=True)
        all_rows = list(reader)

        if not all_rows:
            st.error("No data found in Cell A1.")
            st.stop()

        # 3. Build DataFrame and Clean
        # Use the first row of the CSV text as headers
        df = pd.DataFrame(all_rows[1:], columns=all_rows[0])

        # Strip whitespace from column names and all cells
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

        # Remove repeating header rows that appear in the middle of the data
        df = df[df["Account Type"].str.lower() != "account type"]

        # 4. Convert Amount to Numeric
        def to_numeric_clean(val):
            if not val or pd.isna(val):
                return 0.0
            # Remove symbols and handle accounting parens (100.00)
            s = str(val).replace("$", "").replace(",", "").strip()
            if s.startswith("(") and s.endswith(")"):
                s = "-" + s[1:-1]
            try:
                return float(s)
            except:
                return 0.0

        if "Amount" in df.columns:
            df["Amount"] = df["Amount"].apply(to_numeric_clean)
        else:
            st.error(f"Missing 'Amount' column. Found: {df.columns.tolist()}")
            st.stop()

        # 5. Filter for BOTH Expense types
        # This regex catches "Expense" and "Non Operating Expense"
        expenses = df[
            df["Account Type"].str.contains("Expense", case=False, na=False)
        ].copy()

        st.header(f"Summary for {selected_week}")

        if not expenses.empty:
            # Display a clean summary table
            st.subheader("Expense Details")
            st.dataframe(
                expenses[["Account Type", "Parent", "Account", "Amount"]],
                use_container_width=True,
                height=500,
            )

            # Metrics Calculation
            total_val = expenses["Amount"].sum()
            st.divider()

            # Layout metrics for better visibility
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="Total Expenses Identified", value=f"{len(expenses)} rows"
                )
            with col2:
                st.metric(label="Grand Total Cost", value=f"${total_val:,.2f}")

        else:
            st.warning("⚠️ No 'Expense' or 'Non Operating Expense' rows found.")
            with st.expander("Debug: Raw Data Check"):
                st.write(
                    "Unique values in 'Account Type':",
                    df["Account Type"].unique().tolist(),
                )
                st.dataframe(df.head(20))

    except Exception as e:
        st.error(f"Error processing data: {e}")
else:
    st.info("👈 Please select a reporting period in the sidebar.")

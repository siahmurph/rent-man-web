import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io

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
        # header=None ensures we treat the first row of the sheet as data
        raw_df = conn.read(worksheet=selected_week, header=None)

        # Grab the content of A1 (row 0, col 0)
        raw_content = str(raw_df.iloc[0, 0]).strip()

        # 2. Parse the CSV text
        # RentManager often puts quotes around everything.
        # skipinitialspace handles spaces after commas.
        df = pd.read_csv(
            io.StringIO(raw_content),
            quotechar='"',
            skipinitialspace=True,
            on_bad_lines="skip",  # Useful if there are footer/total rows that break the 4-column format
        )

        # 3. Clean Columns & Data
        df.columns = df.columns.str.strip().str.replace('"', "")

        # Remove any repeating header rows that might have been sucked in from the A1 text
        df = df[df["Account Type"] != "Account Type"]

        # 4. Convert Amount to Numeric
        # Handles strings like "$1,234.56" or "(100.00)"
        def to_numeric_clean(val):
            if pd.isna(val):
                return 0.0
            s = str(val).replace("$", "").replace(",", "").replace('"', "").strip()
            if s.startswith("(") and s.endswith(")"):
                s = "-" + s[1:-1]
            try:
                return float(s)
            except:
                return 0.0

        if "Amount" in df.columns:
            df["Amount"] = df["Amount"].apply(to_numeric_clean)

        # 5. Filter Logic
        # This catches both "Expense" and "Non Operating Expense"
        expense_mask = df["Account Type"].str.contains("Expense", case=False, na=False)
        expenses = df[expense_mask].copy()

        st.header(f"Summary for {selected_week}")

        if not expenses.empty:
            st.dataframe(expenses, use_container_width=True)

            total_val = expenses["Amount"].sum()
            st.divider()
            st.metric(label="Grand Total Expenses", value=f"${total_val:,.2f}")
        else:
            st.warning("⚠️ No 'Expense' rows found.")
            # Critical Debug: Show what we actually parsed
            with st.expander("Debug: Data Structure in Cell A1"):
                st.write("Columns Detected:", list(df.columns))
                st.write(
                    "First 5 rows of Account Type column:",
                    df["Account Type"].head().tolist(),
                )
                st.dataframe(df.head())

    except Exception as e:
        st.error(f"Error processing data: {e}")

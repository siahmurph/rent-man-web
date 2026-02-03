import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import csv

# --- UI SETUP ---
st.set_page_config(page_title="RentManager Summarizer", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    try:
        # Dynamically get all tab names
        sh = conn._instance._open_spreadsheet()
        worksheets = sh.worksheets()
        # Filter out any internal sheets if necessary
        tab_names = [w.title for w in worksheets if "Sheet" not in w.title]

        st.success("✅ Connection Successful")
        selected_tab = st.selectbox(
            "📅 Select Reporting Period", ["Select..."] + tab_names
        )
    except Exception as e:
        st.error(f"⚠️ Connection Failed: {e}")
        st.stop()

# --- MAIN CONTENT ---
if selected_tab != "Select...":
    try:
        # 1. Read the selected tab (Single column of rows)
        raw_df = conn.read(worksheet=selected_tab, header=None)

        # 2. Parse the rows. Since each row in Column A is a CSV string:
        raw_strings = raw_df[0].astype(str).tolist()
        reader = csv.reader(
            raw_strings, quotechar='"', delimiter=",", skipinitialspace=True
        )
        parsed_data = [row for row in reader if row]

        if parsed_data:
            # 3. Create DataFrame
            # Headers are: "Account Type", "Parent", "Account", "Amount"
            df = pd.DataFrame(parsed_data[1:], columns=parsed_data[0])
            df.columns = df.columns.str.strip()

            # Remove repeating header rows from the middle of the paste
            df = df[df["Account Type"] != "Account Type"]

            # 4. Clean numeric data for your calculations
            def clean_val(v):
                s = str(v).replace("$", "").replace(",", "").replace('"', "").strip()
                if s.startswith("(") and s.endswith(")"):
                    s = "-" + s[1:-1]
                try:
                    return float(s)
                except:
                    return 0.0

            df["Amount"] = df["Amount"].apply(clean_val)

            # 5. Filter for 'Expense' and 'Non Operating Expense'
            expenses = df[
                df["Account Type"].str.contains("Expense", case=False, na=False)
            ].copy()

            st.header(f"Summary for {selected_tab}")

            if not expenses.empty:
                total_val = expenses["Amount"].sum()
                st.metric("Grand Total Expenses", f"${total_val:,.2f}")
                st.dataframe(expenses, use_container_width=True, height=500)
            else:
                st.warning("No expense data found in this tab.")
        else:
            st.error("The selected tab contains no data.")

    except Exception as e:
        st.error(f"Error processing tab '{selected_tab}': {e}")
else:
    st.info("👈 Please select a date tab from the sidebar.")

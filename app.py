import streamlit as st
import pandas as pd
from google.cloud import storage
import io

# --- INITIALIZE APP ---
st.set_page_config(
    page_title="RentManager GCS Dashboard", page_icon="📊", layout="wide"
)

# Initialize connection client using secrets
# Note: Ensure your Secrets header is exactly [gcp]
client = storage.Client.from_service_account_info(st.secrets["gcp"])
BUCKET_NAME = "rent-man-reports-01"


# --- HELPER FUNCTIONS ---
@st.cache_data
def get_gcs_data(file_name):
    """Downloads a CSV from GCS and returns a cleaned DataFrame."""
    try:
        bucket = client.get_bucket(BUCKET_NAME)
        blob = bucket.blob(file_name)
        data = blob.download_as_text()

        # Read the raw single-column data
        df_raw = pd.read_csv(io.StringIO(data), header=None)

        # Parse the single column (Column 0) into separate columns
        # This handles the "quoted csv string per row" format
        df = df_raw[0].str.replace('"', "").str.split(",", expand=True)

        # Promote the first row to be the header
        df.columns = df.iloc[0].str.strip()
        df = df[1:].reset_index(drop=True)

        # Ensure 'Amount' is numeric for math operations
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        return df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return None


# --- SIDEBAR: NAVIGATION ---
with st.sidebar:
    st.title("Navigation")
    try:
        # Dynamically list all CSV files in the bucket
        bucket = client.get_bucket(BUCKET_NAME)
        blobs = list(bucket.list_blobs())
        file_list = [blob.name for blob in blobs if blob.name.endswith(".csv")]

        if file_list:
            selected_file = st.selectbox(
                "📂 Select a Report", sorted(file_list, reverse=True)
            )
        else:
            st.warning("No CSV files found in the bucket.")
            selected_file = None
    except Exception as e:
        st.error(f"Permission Error: {e}")
        selected_file = None

# --- MAIN CONTENT ---
if selected_file:
    df = get_gcs_data(selected_file)

    if df is not None:
        # Filter for Expenses
        # Searching for 'Exp' catches 'Expense' and 'Non Operating Expense'
        expenses = df[
            df["Account Type"].str.contains("Exp", case=False, na=False)
        ].copy()

        st.header(f"Summary: {selected_file}")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("Detail View")
            if not expenses.empty:
                st.dataframe(expenses, use_container_width=True, height=500)
            else:
                st.warning("No expense rows found in this file.")

        with col2:
            st.subheader("Financials")
            if not expenses.empty:
                # float() conversion prevents JSON serialization errors
                total_val = float(expenses["Amount"].sum())
                st.metric(label="Total Expenses", value=f"${total_val:,.2f}")

                # Bonus: Simple breakdown by Parent category
                st.write("Breakdown by Category:")
                summary = (
                    expenses.groupby("Parent")["Amount"]
                    .sum()
                    .sort_values(ascending=False)
                )
                st.table(summary.map("${:,.2f}".format))

        # Optional: Show raw data for debugging
        with st.expander("View Raw Data (All Rows)"):
            st.write(df)
else:
    st.info("👈 Please select a report from the sidebar to view the data.")

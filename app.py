import streamlit as st
import pandas as pd
from google.cloud import storage
import io

# --- INITIALIZE APP ---
st.set_page_config(page_title="RentManager Report Viewer", layout="wide")

# Setup GCS Client
client = storage.Client.from_service_account_info(st.secrets["gcp"])
BUCKET_NAME = "rent-man-reports-01"


# --- AUTO-POLLING LOGIC ---
def list_csv_files(bucket_name):
    """Scans the bucket and returns a list of CSV filenames."""
    try:
        bucket = client.get_bucket(bucket_name)
        blobs = bucket.list_blobs()
        # Returns a list of strings for the sidebar
        return [blob.name for blob in blobs if blob.name.endswith(".csv")]
    except Exception as e:
        st.error(f"Error polling bucket: {e}")
        return []


@st.cache_data
def load_csv_from_gcs(file_name):
    """Reads a standard CSV file directly from the bucket."""
    bucket = client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)
    content = blob.download_as_text()
    # No more manual string splitting needed!
    return pd.read_csv(io.StringIO(content))


# --- SIDEBAR ---
with st.sidebar:
    st.header("Report Selection")
    # This automatically polls the bucket for you
    available_files = list_csv_files(BUCKET_NAME)

    if available_files:
        selected_file = st.selectbox(
            "Select a file to view:", sorted(available_files, reverse=True)
        )
    else:
        st.warning("No CSV files found.")
        selected_file = None

# --- MAIN CONTENT ---
if selected_file:
    df = load_csv_from_gcs(selected_file)

    # Clean up column names and amounts
    df.columns = df.columns.str.strip()
    if "Amount" in df.columns:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

        # Filter for Expenses
        expenses = df[
            df["Account Type"].str.contains("Exp", case=False, na=False)
        ].copy()

        st.header(f"Report: {selected_file}")

        if not expenses.empty:
            st.metric("Total Expenses", f"${float(expenses['Amount'].sum()):,.2f}")
            st.dataframe(expenses, use_container_width=True)
        else:
            st.info("No expense rows found. Showing raw data below:")
            st.dataframe(df)
    else:
        st.error(
            f"Error: Column 'Amount' not found. Columns available: {df.columns.tolist()}"
        )
else:
    st.info("👈 Select a report from the sidebar to begin.")

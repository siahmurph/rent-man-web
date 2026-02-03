import streamlit as st
import pandas as pd
from google.cloud import storage
import io

# --- INITIALIZE UI ---
st.set_page_config(
    page_title="RentManager GCS Dashboard", page_icon="📊", layout="wide"
)


# --- GCS CONNECTION FUNCTION ---
def get_gcs_data(file_name):
    # Authenticates using the JSON key data you pasted into Streamlit Secrets
    client = storage.Client.from_service_account_info(st.secrets["gcp"])
    bucket = client.get_bucket("rent-man-reports-01")  # Matches your screenshot
    blob = bucket.blob(file_name)

    # Download as text and convert to a clean DataFrame
    data = blob.download_as_text()
    return pd.read_csv(io.StringIO(data))


# --- SIDEBAR: FILE SELECTION ---
with st.sidebar:
    st.success("✅ Connection Successful")  # Confirmed by your screenshot

    try:
        # Automatically list all CSVs so you don't have to type them
        client = storage.Client.from_service_account_info(st.secrets["gcp"])
        bucket = client.get_bucket("rent-man-reports-01")
        file_list = [
            blob.name for blob in bucket.list_blobs() if blob.name.endswith(".csv")
        ]

        if file_list:
            selected_file = st.selectbox("📅 Select Reporting Period", file_list)
        else:
            st.warning("No .csv files found in bucket.")
            selected_file = None
    except Exception as e:
        st.error(f"GCS Error: {e}")
        selected_file = None

# --- MAIN CONTENT ---
if selected_file:
    try:
        # 1. Load the data
        df = get_gcs_data(selected_file)

        # 2. Basic Cleanup
        # This ensures 'Amount' is a number even if it has quotes or commas
        df.columns = df.columns.str.strip()
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

        # 3. Flexible Filter
        # This looks for "Exp" to catch both "Expense" and "Expenses"
        expenses = df[
            df["Account Type"].str.contains("Exp", case=False, na=False)
        ].copy()

        st.header(f"Summary for {selected_file}")

        if not expenses.empty:
            # Display the processed data table
            st.subheader("Detail View")
            st.dataframe(expenses, width="stretch", height=500)

            # 4. The Grand Total
            # float() prevents the 'int64 is not JSON serializable' error
            total_val = float(expenses["Amount"].sum())
            st.divider()
            st.metric(label="Grand Total Expenses", value=f"${total_val:,.2f}")
        else:
            st.warning("⚠️ File loaded, but no 'Expense' rows were found.")
            st.write("Column names found in your file:", df.columns.tolist())
            st.write("First few rows of raw data:", df.head())

    except Exception as e:
        st.error(f"Error processing data: {e}")
else:
    st.info("👈 Please select a report from the sidebar to begin.")

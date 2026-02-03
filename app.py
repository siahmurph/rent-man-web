import streamlit as st
import pandas as pd
from google.cloud import (
    storage,
)  # You'll need 'google-cloud-storage' in requirements.txt
import io


# 1. Connect to GCS
def get_gcs_data(file_name):
    # Uses the secrets we set up in Step 3
    client = storage.Client.from_service_account_info(st.secrets["gcp"])
    bucket = client.get_bucket("rent-man-reports-01")
    blob = bucket.blob(file_name)

    # Read the actual CSV file directly
    data = blob.download_as_text()
    return pd.read_csv(io.StringIO(data))


# 2. Main App Logic
st.title("RentManager Reports (GCS Edition)")

# You can name your files in GCS by date: "2026-02-02.csv"
file_to_load = st.sidebar.text_input("Enter Date (YYYY-MM-DD)", value="2026-02-02")

if st.sidebar.button("Load Report"):
    try:
        df = get_gcs_data(f"{file_to_load}.csv")

        # Now 'Amount' is likely already a column, no split() needed!
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        expenses = df[df["Account Type"].str.contains("Expense", case=False)]

        st.metric("Total Expenses", f"${float(expenses['Amount'].sum()):,.2f}")
        st.dataframe(expenses)

    except Exception as e:
        st.error(f"Could not find file: {file_to_load}.csv")

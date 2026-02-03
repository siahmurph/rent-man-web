# --- MAIN CONTENT ---
if selected_week != "Select...":
    try:
        # 1. Pull the data. It comes in as one column (Column 0)
        df_raw = conn.read(worksheet=selected_week, header=None)

        # 2. Split the single column into multiple columns
        # We take Column 0, strip quotes, and split by the comma
        df = df_raw[0].str.replace('"', "").str.split(",", expand=True)

        # 3. Set the first row as the header
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)

        # 4. Clean up Column Names and 'Amount'
        df.columns = df.columns.str.strip()
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

        # 5. Filter for Expenses
        expenses = df[
            df["Account Type"].str.contains("Expense", case=False, na=False)
        ].copy()

        st.header(f"Summary for {selected_week}")

        if not expenses.empty:
            st.dataframe(expenses, width="stretch", height=500)

            # Summary Metric
            total_val = expenses["Amount"].sum()
            st.divider()
            st.metric(label="Grand Total Expenses", value=f"${total_val:,.2f}")
        else:
            st.warning("⚠️ No 'Expense' rows found. Is Column A empty?")
            # Useful for debugging what the columns actually look like
            st.write("Detected Columns:", df.columns.tolist())

    except Exception as e:
        st.error(f"Error processing data: {e}")

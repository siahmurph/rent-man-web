# --- MAIN CONTENT ---
if selected_week != "Select...":
    try:
        # 1. Pull the raw text
        raw_df = conn.read(worksheet=selected_week, header=None)
        raw_text = str(raw_df.iloc[0, 0]).strip()

        # 2. Parse the CSV text
        # quotechar='"' ensures pandas handles those double quotes correctly
        df = pd.read_csv(io.StringIO(raw_text), quotechar='"', skipinitialspace=True)

        # 3. Clean Column Names
        # Sometimes hidden spaces in the CSV header break the filter
        df.columns = df.columns.str.strip()

        # 4. Filter for Expenses
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        expenses = df[df["Account Type"].str.contains("Expense", na=False)].copy()

        st.header(f"Summary for {selected_week}")

        if not expenses.empty:
            # Display the processed data
            st.dataframe(expenses, width="stretch", height=500)

            # Summary Metric
            total_val = expenses["Amount"].sum()
            st.divider()
            st.metric(label="Grand Total Expenses", value=f"${total_val:,.2f}")
        else:
            st.warning("⚠️ Data found, but no 'Expense' rows were identified.")
            st.write("Current Columns found:", df.columns.tolist())

    except Exception as e:
        st.error(f"Error processing data: {e}")

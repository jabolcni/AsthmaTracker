import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# App Title & Icon
st.set_page_config(page_title="LungLog", page_icon="🫁")

st.title("🫁 LungLog: Asthma Tracker")

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
# Load existing data
existing_data = conn.read(worksheet="Sheet1")

# --- TWO TAB LAYOUT ---
tab1, tab2 = st.tabs(["📝 Log Entry", "📈 Trends"])

with tab1:
    st.header("New Reading")
    
    with st.form("input_form", clear_on_submit=True):
        date = st.date_input("Date", datetime.date.today())
        volume = st.number_input("Volume (L/min)", min_value=0, max_value=1000, step=10)
        feeling = st.select_slider("How do you feel?", options=["😫", "😕", "😐", "🙂", "😄"])
        
        submit = st.form_submit_button("Save to Cloud")
        
        if submit:
            # Append new row to the dataframe
            new_entry = pd.DataFrame([{"Date": str(date), "Volume": volume, "Feeling": feeling}])
            updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
            
            # Update Google Sheet
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success("Data logged successfully!")

with tab2:
    st.header("Volume Over Time")
    
    if not existing_data.empty:
        # Convert Date column to actual datetime for plotting
        existing_data['Date'] = pd.to_datetime(existing_data['Date'])
        
        # Simple Line Chart
        st.line_chart(data=existing_data, x="Date", y="Volume")
        
        # Data Table (Optional)
        with st.expander("View Raw Data"):
            st.dataframe(existing_data.sort_values(by="Date", ascending=False))
    else:
        st.info("No data yet. Log your first reading in the first tab!")

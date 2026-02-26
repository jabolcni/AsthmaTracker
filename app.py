import streamlit as st
import pandas as pd
import datetime
import sqlite3

# App Title & Icon
st.set_page_config(page_title="LungLog", page_icon="🫁")

st.title("🫁 LungLog: Asthma Tracker")

# ----------
# local storage
# ----------
# use a lightweight SQLite database in the workspace directory so that
# data persists between Streamlit sessions without any cloud setup.
DB_PATH = "data.db"
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)

# create table if it doesn't exist
with _conn:
    _conn.execute(
        """
        CREATE TABLE IF NOT EXISTS readings (
            Date TEXT,
            Volume REAL,
            Feeling TEXT
        )
        """
    )


def _load_data():
    try:
        df = pd.read_sql_query("SELECT * FROM readings ORDER BY Date", _conn)
    except Exception:
        df = pd.DataFrame(columns=["Date", "Volume", "Feeling"])
    return df


def _save_data(df: pd.DataFrame):
    # overwrite entire table for simplicity
    df.to_sql("readings", _conn, index=False, if_exists="replace")

existing_data = _load_data()

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
            
            # Save into local SQLite database
            _save_data(updated_df)
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

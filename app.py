import streamlit as st
import pandas as pd
import datetime
from datetime import timezone
from zoneinfo import ZoneInfo
import sqlite3

# App Title & Icon
st.set_page_config(page_title="LungLog", page_icon="🫁")

# remove extra top padding/spacing so mobile users don't have to scroll
st.markdown(
    """
    <style>
    /* generic rules; streamlit class names may change, so keep selectors broad */
    .css-1d391kg, .css-18e3th9, .reportview-container .main > div {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    header {
        margin-top: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🫁 LungLog")

# ----------
# local storage
# ----------
# use a lightweight SQLite database in the workspace directory so that
# data persists between Streamlit sessions without any cloud setup.
DB_PATH = "data.db"
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)

# create table if it doesn't exist and migrate columns
with _conn:
    _conn.execute(
        """
        CREATE TABLE IF NOT EXISTS readings (
            Date TEXT,
            Time TEXT,
            Volume1 REAL,
            Volume2 REAL,
            Volume3 REAL,
            FeelingNum INTEGER
        )
        """
    )
    # make sure any missing columns are added (simple PRAGMA introspection)
    existing_cols = {row[1] for row in _conn.execute("PRAGMA table_info(readings)")}
    for col_def in [
        ("Volume1", "REAL"),
        ("Volume2", "REAL"),
        ("Volume3", "REAL"),
        ("FeelingNum", "INTEGER"),
    ]:
        if col_def[0] not in existing_cols:
            try:
                _conn.execute(f"ALTER TABLE readings ADD COLUMN {col_def[0]} {col_def[1]}")
            except Exception:
                pass



def _load_data():
    try:
        df = pd.read_sql_query("SELECT * FROM readings ORDER BY Date, Time", _conn)
    except Exception:
        df = pd.DataFrame(columns=["Date", "Time", "Volume1", "Volume2", "Volume3", "FeelingNum"])
    return df


def _save_data(df: pd.DataFrame):
    # overwrite entire table for simplicity
    df.to_sql("readings", _conn, index=False, if_exists="replace")

existing_data = _load_data()

# --- TWO TAB LAYOUT ---
tab1, tab2 = st.tabs(["📝 Log Entry", "📈 Trends"])

with tab1:
    #st.header("New Reading")
    
    with st.form("input_form", clear_on_submit=True):
        # date and time on same row to save vertical space
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.date.today())
        with col2:
            # default time to current CET (Europe/Prague) regardless of server tz
            cet_now = datetime.datetime.now(ZoneInfo("Europe/Prague"))
            time = st.time_input("Time", cet_now.time())

        volume1 = st.number_input("Volume 1 (L/min)", min_value=0, max_value=1000, step=1)
        volume2 = st.number_input("Volume 2 (L/min)", min_value=0, max_value=1000, step=1)
        volume3 = st.number_input("Volume 3 (L/min)", min_value=0, max_value=1000, step=1)
        feeling = st.select_slider("How do you feel?", options=["😫", "😕", "😐", "🙂", "😄"])
        
        submit = st.form_submit_button("Save to Cloud")
        
        if submit:
            # Append new row to the dataframe
            # map emoji to numeric scale 1..5
            feeling_map = {"😫": 1, "😕": 2, "😐": 3, "🙂": 4, "😄": 5}
            num = feeling_map.get(feeling, None)
            new_entry = pd.DataFrame([{"Date": str(date), "Time": str(time),
                                      "Volume1": volume1, "Volume2": volume2,
                                      "Volume3": volume3, "FeelingNum": num}])
            updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
            
            # Save into local SQLite database
            _save_data(updated_df)
            st.success("Data logged successfully!")

with tab2:
    st.header("Volume Over Time")
    
    if not existing_data.empty:
        # combine Date and Time into a datetimestamp for plotting
        existing_data['Timestamp'] = pd.to_datetime(existing_data['Date'] + ' ' + existing_data['Time'])
        # compute mean volume across three trials for convenience
        existing_data['Volume'] = existing_data[["Volume1", "Volume2", "Volume3"]].mean(axis=1)
        
        # Simple Line Chart
        st.line_chart(data=existing_data, x="Timestamp", y="Volume")
        
        # Data Table (Optional)
        with st.expander("View Raw Data"):
            st.dataframe(existing_data.sort_values(by=["Date", "Time"], ascending=False))
    else:
        st.info("No data yet. Log your first reading in the first tab!")

    # download button
    if not existing_data.empty:
        csv = existing_data.to_csv(index=False)
        st.download_button(
            label="Download all data",
            data=csv,
            file_name="asthma_readings.csv",
            mime="text/csv",
        )

import streamlit as st
import pandas as pd
import datetime
from datetime import timezone
from zoneinfo import ZoneInfo
import sqlite3
import os
from pathlib import Path

# App Title & Icon
st.set_page_config(page_title="LungLog", page_icon="🫁")

# remove extra top padding/spacing so mobile users don't have to scroll
# also force date/time inputs to sit side-by-side even on narrow screens
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

    /* ensure columns don't wrap on mobile and shrink inputs if necessary */
    @media only screen and (max-width: 600px) {
        .stColumns {
            flex-wrap: nowrap !important;
        }
        /* force date/time pickers to half-width */
        div[data-testid="stDateInput"],
        div[data-testid="stTimeInput"] {
            display: inline-block !important;
            width: 33% !important;
            vertical-align: top;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🫁 LungLog")

# ----------
# local storage
# ----------
# allow database to live outside of the repository itself so it is not
# accidentally deleted when the repo is synced/cleaned.  user can override
# with the ASTHMA_DB_PATH environment variable.  otherwise use a hidden file
# in the home directory which is normally persistent.
def _get_db_path():
    env = os.environ.get("ASTHMA_DB_PATH")
    if env:
        return env
    return str(Path.home() / ".asthma_tracker.db")

# if an old data.db exists in the repo root (perhaps from earlier versions),
# move it to the new location on first run so users don't lose entries.
new_db = _get_db_path()
if os.path.exists("data.db") and os.path.abspath("data.db") != os.path.abspath(new_db):
    try:
        os.replace("data.db", new_db)
    except Exception:
        pass

DB_PATH = new_db
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
    # events table for comments/illness/exercise
    _conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            Date TEXT,
            Time TEXT,
            Type TEXT,
            Notes TEXT
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


def _load_events():
    try:
        ev = pd.read_sql_query("SELECT * FROM events ORDER BY Date, Time", _conn)
    except Exception:
        ev = pd.DataFrame(columns=["Date", "Time", "Type", "Notes"])
    return ev


def _save_events(df: pd.DataFrame):
    df.to_sql("events", _conn, index=False, if_exists="replace")


def _append_event(row: dict):
    ev = _load_events()
    ev = pd.concat([ev, pd.DataFrame([row])], ignore_index=True)
    _save_events(ev)


def _save_data(df: pd.DataFrame):
    # overwrite entire table for simplicity
    df.to_sql("readings", _conn, index=False, if_exists="replace")

existing_data = _load_data()

# --- TWO TAB LAYOUT ---
tab1, tab2 = st.tabs(["📝 Log Entry", "📈 Trends"])

with tab1:
    #st.header("New Reading")
    
    with st.form("input_form", clear_on_submit=True):
        # single datetime picker (CET) to keep date+time on one line
        cet_now = datetime.datetime.now(ZoneInfo("Europe/Prague"))
        dt = st.datetime_input("Date & time", value=cet_now)

        # use slider with 5-unit steps between 100 and 700 to mimic dial
        volume1 = st.slider("Volume 1 (L/min)", 100, 700, step=5)
        volume2 = st.slider("Volume 2 (L/min)", 100, 700, step=5)
        volume3 = st.slider("Volume 3 (L/min)", 100, 700, step=5)
        feeling = st.select_slider("How do you feel?", options=["😫", "😕", "😐", "🙂", "😄"])
        
        submit = st.form_submit_button("Save to Cloud")
        
        if submit:
                # Append new row to the dataframe
            # map emoji to numeric scale 1..5
            feeling_map = {"😫": 1, "😕": 2, "😐": 3, "🙂": 4, "😄": 5}
            num = feeling_map.get(feeling, None)
            # split datetime into date/time strings
            date = dt.date()
            time = dt.time()
            new_entry = pd.DataFrame([{"Date": str(date), "Time": str(time),
                                      "Volume1": volume1, "Volume2": volume2,
                                      "Volume3": volume3, "FeelingNum": num}])
            updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
            
            # Save into local SQLite database
            _save_data(updated_df)
            st.success("Data logged successfully!")

    # event logging area
    with st.expander("Log event (illness, exercise, notes)"):
        with st.form("event_form", clear_on_submit=True):
            ev_dt = st.datetime_input("Event date & time", value=cet_now)
            ev_type = st.selectbox("Type", ["Illness", "Exercise", "Medication", "Note"])
            ev_notes = st.text_area("Details", "")
            submit_ev = st.form_submit_button("Add event")
            if submit_ev:
                edate = ev_dt.date()
                etime = ev_dt.time()
                _append_event({"Date": str(edate), "Time": str(etime),
                               "Type": ev_type, "Notes": ev_notes})
                st.success("Event saved!")

with tab2:
    st.header("Volume Over Time")
    
    if not existing_data.empty:
        # combine Date and Time into a datetimestamp for plotting
        existing_data['Timestamp'] = pd.to_datetime(existing_data['Date'] + ' ' + existing_data['Time'])
        # compute mean, max, min volumes across three trials
        existing_data['Volume'] = existing_data[["Volume1", "Volume2", "Volume3"]].mean(axis=1)
        existing_data['Vol_max'] = existing_data[["Volume1", "Volume2", "Volume3"]].max(axis=1)
        existing_data['Vol_min'] = existing_data[["Volume1", "Volume2", "Volume3"]].min(axis=1)

        # time-range selector
        range_option = st.selectbox("Date range", ["All time", "Last 30 days", "Last 7 days"])
        now = pd.Timestamp.now()
        if range_option == "Last 30 days":
            cutoff = now - pd.Timedelta(days=30)
        elif range_option == "Last 7 days":
            cutoff = now - pd.Timedelta(days=7)
        else:
            cutoff = None
        if cutoff is not None:
            plot_data = existing_data[existing_data['Timestamp'] >= cutoff]
        else:
            plot_data = existing_data

        # compute summary statistics
        mean7 = plot_data['Volume'].tail(7*1).mean() if not plot_data.empty else float('nan')
        mean30 = plot_data['Volume'].tail(30*1).mean() if not plot_data.empty else float('nan')
        # variability: average standard deviation of three trials
        variability = plot_data[["Volume1","Volume2","Volume3"]].std(axis=1).mean() if not plot_data.empty else float('nan')
        col1, col2, col3 = st.columns(3)
        col1.metric("Avg (7d)", f"{mean7:.1f}" if not pd.isna(mean7) else "-")
        col2.metric("Avg (30d)", f"{mean30:.1f}" if not pd.isna(mean30) else "-")
        col3.metric("Variability", f"{variability:.1f}" if not pd.isna(variability) else "-")

        # build Altair multi-line chart with colored lines and events
        import altair as alt
        base = alt.Chart(plot_data).encode(x='Timestamp:T')
        line_mean = base.mark_line(color='blue').encode(y='Volume:Q')
        line_max = base.mark_line(color='green').encode(y='Vol_max:Q')
        line_min = base.mark_line(color='red').encode(y='Vol_min:Q')
        layers = [line_max, line_min, line_mean]
        # load events and add points/rules
        events = _load_events()
        if not events.empty:
            events['Timestamp'] = pd.to_datetime(events['Date'] + ' ' + events['Time'])
            if cutoff is not None:
                ev_plot = events[events['Timestamp'] >= cutoff]
            else:
                ev_plot = events
            if not ev_plot.empty:
                evt = alt.Chart(ev_plot).mark_point(shape='triangle', size=100).encode(
                    x='Timestamp:T',
                    tooltip=['Type', 'Notes'],
                    color=alt.Color('Type:N', legend=alt.Legend(title='Event'))
                )
                layers.append(evt)
        chart = alt.layer(*layers).interactive()
        st.altair_chart(chart, use_container_width=True)

        # download excel report
        if not existing_data.empty:
            output = pd.ExcelWriter("report.xlsx", engine="openpyxl")
            existing_data.to_excel(output, sheet_name="readings", index=False)
            ev = _load_events()
            ev.to_excel(output, sheet_name="events", index=False)
            output.save()
            with open("report.xlsx", "rb") as f:
                btn = st.download_button(
                    label="Download Excel report",
                    data=f,
                    file_name="asthma_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        
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

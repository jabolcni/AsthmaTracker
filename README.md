# AsthmaTracker

This Streamlit application logs asthma readings to a SQLite database
stored locally in the workspace.  No external cloud service is required;
your data lives in `data.db` beside the app files.

## Local storage (no cloud)

To keep things simple and free, the app uses Python's built-in `sqlite3`
module.  When the app starts it will create a `readings` table if one does not
already exist, and every new entry is saved into that table.  You can view or
edit the database with any SQLite client (e.g. `sqlite3`, `DB Browser for
SQLite`, etc.).

There are no additional setup steps – just install the requirements and run
`streamlit run app.py`.

## Requirements

Dependencies are listed in `requirements.txt` and include only Streamlit and
Pandas, which remain necessary for the UI and data handling.

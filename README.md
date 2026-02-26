# AsthmaTracker

This Streamlit application logs asthma readings (date, time, three volume trials, and a
numeric feeling score) to a SQLite database stored locally in the
workspace.  No external cloud service is required; your data lives in
`data.db` beside the app files.

## Local storage (no cloud)

To keep things simple and free, the app uses Python's built-in `sqlite3`
module.  When the app starts it will create a `readings` table if one does not
already exist, and every new entry is saved into that table.  You can view or
edit the database with any SQLite client (e.g. `sqlite3`, `DB Browser for
SQLite`, etc.).

There are no additional setup steps – just install the requirements and
run `streamlit run app.py`.  The log form now asks for three separate
volume measurements and a feeling slider; feelings are stored as numbers
(1‑5) while the UI still shows emojis.  The volume fields use a slider
that moves in 5‑unit increments from 100 to 700 (emulating the dial used in
similar apps). The date and time are entered via a single "Date & time"
picker (set to CET) so the fields occupy one row on mobile. A "Timestamp"
and mean volume are generated for plotting, and the CSV export includes all
raw columns.

## Requirements

Dependencies are listed in `requirements.txt` and include only Streamlit and
Pandas, which remain necessary for the UI and data handling.

> **Privacy**: the SQLite database file `data.db` resides in the workspace
> and is **not committed** to the public repository. It is added to
> `.gitignore` to prevent your personal entries from being exposed.  If
> you've already run the app and see `data.db` in `git status`, run
> ``git rm --cached data.db`` to untrack it.

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
picker (set to CET) so the fields occupy one row on mobile. 

In the *Trends* tab you can choose between "All time", "Last 30 days", and
"Last 7 days" ranges.  The chart plots three lines: green represents the
maximum (highest) of the three trials, red the minimum (lowest), and blue
is the mean volume.  This gives you a quick visual of your best, worst and
average performance.  Summary metrics above the chart show the 7‑day and
30‑day mean volume and the variability score (standard deviation of the
three trials).

The app now supports *event logging* – use the Expander on the Log Entry
tab to record illness, exercise, medication, or general notes.  Events
appear as colored triangles on the trend chart; hover over them to see
details.

A new "Download Excel report" button generates an `.xlsx` file with two
sheets (`readings` and `events`) containing all your stored data, making it
easy to share or archive your logs.

## Requirements

Dependencies are listed in `requirements.txt` and include only Streamlit and
Pandas, which remain necessary for the UI and data handling.

> **Privacy**: the SQLite database file `data.db` resides in the workspace
> and is **not committed** to the public repository. It is added to
> `.gitignore` to prevent your personal entries from being exposed.  If
> you've already run the app and see `data.db` in `git status`, run
> ``git rm --cached data.db`` to untrack it.
>
> **Persistence**: repository synchronisation (e.g. pulling new commits or
> rebuilding a Codespace) may delete untracked files. To avoid losing your
> readings, the app now stores the database outside of the repo by default.
> It uses `~/.asthma_tracker.db` (home directory) or any path you specify
> with the `ASTHMA_DB_PATH` environment variable.  If an old `data.db` file
> exists in the repository root it will automatically be moved on first run.

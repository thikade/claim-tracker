# Insurance Claim Tracker

A self-contained, local-first tool to track medical insurance claims through
their lifecycle. Runs entirely on your own machine: a NiceGUI web frontend and
a SQLite database, in a single Python process. No separate backend service, no
cloud, no account.

## The workflow

Each claim is a small state machine moving through four stages:

```
Bill scanned ──┬──> Public claim pending ──> Private claim pending ──> Archived
               └────────────────────────────^
```

1. **Bill scanned** — you scanned a medical bill after a doctor's visit.
2. **Public claim pending** — *(optional)* submitted to the public health
   service portal. This can take weeks.
3. **Private claim pending** — submitted to private health insurance. If you
   went through the public service first, you attach its confirmation document
   at this transition; otherwise you jump here directly from step 1.
4. **Archived** — the private insurer processed the claim; you attach its
   confirmation and all documents are archived.

Only legal transitions are offered in the UI, and the data layer rejects
illegal ones.

## Features

- Claims grouped by stage on a single board
- Attach the actual scanned files (bills, confirmations, other documents) —
  stored on disk under `data/attachments/`, referenced from the database
- Per-claim history log — every creation, move, edit, and attachment is
  timestamped
- Staleness reminders — a claim pending longer than its threshold is flagged
  (35 days for public, 21 for private; change in `db.py` → `STALE_DAYS`)
- Dashboard — active claims, outstanding money not yet archived, count needing
  attention, archived total
- Search across title / provider / notes, plus a stage filter
- Portal reference-number fields for the public and private claims
- One-click backup of the database + all attachments to a timestamped folder

## Requirements

- Python 3.10 or newer
- NiceGUI (`pip install nicegui`)

SQLite needs nothing installed — it ships with Python.

## Setup

```bash
cd claim-tracker
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py
```

The app opens at <http://localhost:8080/> and should launch your browser
automatically. Stop it with Ctrl+C.

## Where your data lives

Everything is under the `data/` folder next to the code:

```
claim-tracker/
├── main.py                  launcher
├── requirements.txt
├── claim_tracker/
│   ├── db.py                SQLite schema + all data access
│   └── app.py               NiceGUI frontend
└── data/                    created on first run
    ├── claims.db            the SQLite database
    ├── attachments/         your scanned files
    └── backups/             backup snapshots (when you click "Backup")
```

To move the tool to another machine, copy the whole `claim-tracker/` folder —
the `data/` directory comes with it. To back up, click **Backup** in the UI or
just copy `data/`.

## Notes

- This is a single-user local tool. NiceGUI runs one worker; page state is
  kept in a plain dict, which is fine here.
- The database uses WAL mode, so you may also see `claims.db-wal` and
  `claims.db-shm` files — that is normal; include them if you copy the DB
  while the app is running, or just stop the app first.
- Changing the stale-day thresholds: edit `STALE_DAYS` in `claim_tracker/db.py`.

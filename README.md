# Insurance Claim Tracker

A self-contained, local-first tool to track medical insurance claims through
their lifecycle. Runs entirely on your own machine: a NiceGUI web frontend and
a SQLite database, in a single Python process. No separate backend service, no
cloud, no account.

## The workflow

Each claim is a small state machine moving through four stages:

```
Claim created ──┬──> Public claim pending ──> Private claim pending ──> Archived
                └────────────────────────────^
```

1. **Claim created** — you scanned a medical bill after a doctor's visit.
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
- Multiple claimants with colored badges; managed via the Settings page
- Provider / doctor dropdown, also managed via Settings
- Attach scanned files (bills, prescriptions, bank statements, confirmations)
  — stored on disk under `data/attachments/`, referenced from the database
- Per-claim history log — every creation, move, edit, and attachment is
  timestamped
- Staleness reminders — a claim pending longer than its threshold is flagged
  (35 days for public, 21 for private; change `STALE_DAYS` in `db.py`)
- Dashboard — active claims, outstanding money not yet archived, count needing
  attention, archived total with per-claimant breakdown
- Search across title / provider / claimant / notes, plus a stage filter
- Public and private insurer reference-number fields
- One-click backup of the database + all attachments to a timestamped folder

## Requirements

- Python 3.10 or newer
- NiceGUI 3.x (`pip install nicegui`)

SQLite needs nothing installed — it ships with Python.

## Setup (local)

```bash
cd claims-tracker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run (local)

```bash
source venv/bin/activate
CLAIMS_DEV=1 python main.py
```

The app opens at <http://localhost:8080/> and launches your browser
automatically. Stop it with Ctrl+C.

## Run with Docker

See [docker.md](docker.md) for full instructions. Quick start:

```bash
docker compose up -d
```

The app will be available at <http://localhost:8080/>. Data is persisted in a
named Docker volume.

## Where your data lives

Everything is under the `data/` folder next to the code (or in the Docker
volume when running via Docker Compose):

```
claims-tracker/
├── main.py                  launcher
├── requirements.txt
├── Dockerfile
├── compose.yaml
├── claim_tracker/
│   ├── db.py                SQLite schema + all data access
│   └── app.py               NiceGUI frontend
└── data/                    created on first run
    ├── claims.db            the SQLite database
    ├── attachments/         your scanned files
    └── backups/             backup snapshots (Backup button)
```

To move the tool to another machine, copy the whole folder — the `data/`
directory comes with it. To back up, click **Backup** in the UI or copy `data/`.

## Notes

- Single-user local tool. NiceGUI runs one worker; page state is kept in a
  plain dict, which is fine here.
- The database uses WAL mode, so you may also see `claims.db-wal` and
  `claims.db-shm` files — normal. Include them if copying the DB while the
  app is running, or stop the app first.
- Stale-day thresholds: edit `STALE_DAYS` in `claim_tracker/db.py`.
- `CLAIMS_DEV=1` enables hot-reload and auto-opens the browser (local dev
  only; not needed or useful inside a container).

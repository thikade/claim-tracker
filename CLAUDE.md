# CLAUDE.md

Guidance for Claude (and Claude Code) when working in this repository.

## What this project is

A self-contained, local-first tool to track medical insurance claims through
their lifecycle. It runs entirely on the user's own machine — no cloud, no
account, no separate backend service.

- **Frontend:** NiceGUI (Python web UI framework), built against the 3.x API.
- **Storage:** SQLite via the Python stdlib `sqlite3` module. No ORM.
- **Process model:** a single Python process. NiceGUI serves the web UI and
  talks directly to the SQLite file. There is intentionally no separate
  backend tier.

The user (Tom) is an experienced platform/infrastructure engineer, so code
should be clean, explicit, and not over-explained in comments.

## Project layout

```
claim-tracker/
├── main.py                  launcher — `python main.py`
├── requirements.txt         nicegui>=2.0
├── CLAUDE.md                this file
├── README.md                end-user setup + usage
├── claim_tracker/
│   ├── __init__.py
│   ├── db.py                SQLite schema + ALL data access
│   └── app.py               NiceGUI frontend
└── data/                    created on first run, NOT in version control
    ├── claims.db            the SQLite database (WAL mode)
    ├── attachments/         uploaded scan files, stored as real files
    └── backups/             timestamped snapshots (Backup button)
```

## How to run

```bash
source venv/bin/activate  # activate the Python venv
pip install -r requirements.txt
python main.py            # opens http://localhost:8080/
```

Always activate the venv with `source venv/bin/activate` before running Python commands.

## Architecture notes / conventions

- **Separation of concerns:** `db.py` owns every SQL statement and all
  filesystem writes for attachments. `app.py` never touches SQLite or the
  filesystem directly — it only calls `db.*` functions. Keep this boundary.
- **State machine:** claims move through four stages —
  `scanned → public_pending → private_pending → archived`. The public stage
  is optional (a claim may go `scanned → private_pending` directly). Legal
  moves are defined in `db.TRANSITIONS`; `db.move_claim()` validates them and
  raises `ValueError` on an illegal transition. Never bypass `move_claim()`.
- **Claim IDs:** human-readable, sequential — `CLM-0001`, `CLM-0002`, etc.
  The sequence is stored in a `meta` table (`key='claim_seq'`). These IDs are
  displayed in the UI on each claim card.
- **Attachments:** file bytes are written into `data/attachments/` as real
  files; only the path + metadata go into the `attachments` table. This keeps
  the DB small and documents recoverable from the filesystem. Filenames are
  `{claim_id}_{uuid12}{ext}` (e.g. `CLM-0001_3f8a2c1d4e9b.pdf`). Each
  attachment has a `kind`: `bill`, `prescription`, `bank_statement`,
  `confirmation`, or `other`.
- **History:** every meaningful action appends a row to the `history` table
  via `db.add_history()`. Any new mutating operation should also log history.
- **Staleness:** `db.STALE_DAYS` sets per-stage thresholds (public 35d,
  private 21d). `db.is_stale()` / `db.dashboard_stats()` use them.
- **UI refresh:** `app.py` uses two `@ui.refreshable` regions — `metrics_row`
  and `claim_board`. After any data change, call `refresh_page()` which
  refreshes both. Page state (search, stage filter, open card) is a plus a
  module-level `state` dict — fine because NiceGUI runs single-worker and this
  is a single-user tool.
- **Timestamps:** stored as ISO-8601 UTC strings (`db._now()`). Format for
  display only in `app.py` (`fmt_date`, `fmt_datetime`).
- **No new dependencies** without a good reason. SQLite is stdlib; NiceGUI is
  the only third-party package. Do not add an ORM or a web framework.

## Testing

- `db.py` is pure stdlib and fully testable without a network. The data layer
  has been exercised through a complete lifecycle test (create, walk all
  stages, illegal-move rejection, attachments, history, dashboard, search,
  backup, delete) — all passing.
- The NiceGUI UI has been run live and several runtime bugs fixed (see progress
  log). The app is functional.
- When adding `db.py` logic, prefer a quick throwaway-temp-dir test like the
  one used during the initial build (point `db.DATA_DIR` / `db.DB_PATH` /
  `db.FILES_DIR` at a `tempfile.mkdtemp()` directory).

## Progress log

### 2026-05-25 — Initial build
- Created project structure: `db.py`, `app.py`, `main.py`, `requirements.txt`,
  `README.md`.
- `db.py`: schema (claims / attachments / history), four-stage state machine,
  transition validation, attachment storage on disk, history logging,
  dashboard aggregates, search/filter, backup-to-folder.
- `app.py`: NiceGUI frontend — stage-grouped claim board, collapsible claim
  cards, create/edit/move/delete dialogs, file-upload dialogs, attachment
  download route, dashboard metric cards, search + stage filter, Backup button.
- Added public/private portal reference-number fields.
- Set staleness thresholds: public 35 days, private 21 days.
- **Verified:** full `db.py` lifecycle test passes; all modules compile.
- **Not verified:** live NiceGUI run (no network in build environment).
- Added this `CLAUDE.md`.

### 2026-05-25 — Runtime fixes and UI polish (session 2)
- Fixed `create_claim()` missing `public_ref`/`private_ref` params (TypeError on save).
- Fixed file upload handler for NiceGUI 3.x API (`e.file.read()` async, not `e.content`).
- Switched claim IDs to human-readable `CLM-NNNN` sequence via `meta` table.
- Claim ID now displayed in card summary row (left of stage badge).
- Visit date defaults to yesterday in create dialog.
- Removed currency selector; amount fixed to EUR (€).
- Enabled `reload=True` for hot-reload during development.

### 2026-05-25 — Feature additions (session 3)
- Added claimants with colored badges; click badge to edit color.
- Provider / doctor field converted to managed dropdown (like claimants).
- Settings page (`/settings`) with full add/edit/delete for claimants and providers.
- Archive-from-any-stage transitions added (`scanned` and `public_pending`).
- Outstanding dashboard card now shows per-claimant breakdown (no total).
- Search extended to match claimant name.
- Title field autocompletes from existing claim titles.
- Upload dialog consolidated into single "Add document" with type selector
  (Medical bill, Prescription, Bank statement, Other).
- Renamed: "Bill scanned" → "Claim created", "Public portal reference" → "Public insurer reference".

## Open items / planned enhancements

- [x] First live run of the NiceGUI app — runtime bugs fixed (see 2026-05-25 session 2).
- [x] **Duplicate claim button:** on each claim card, quickly create a new claim
      with all fields pre-filled (title, provider, claimant, amount, notes, refs)
      but visit date reset to yesterday and stage reset to `scanned`.
- [x] Consider a `.gitignore` (exclude `data/`, `__pycache__/`, `*.pyc`,
      `claims.db*`) if the project goes under version control.
- [ ] Possible enhancement: CSV/JSON export of all claims for tax records.
- [ ] Possible enhancement: a desktop-window mode via `ui.run(native=True)`
      instead of serving on a browser port.
- [ ] Possible enhancement: per-attachment size guard / large-file handling.
- [ ] No automated test suite yet — `db.py` would be straightforward to cover
      with pytest if desired.

### 2026-05-26 — Duplicate claim button (session 4)
- Added "Duplicate" button to the claim detail panel footer (alongside "Edit details").
- Reuses `claim_form_dialog` with a `dupe_mode=True` flag: pre-fills title, provider,
  claimant, amount, notes, public_ref, private_ref from the source claim; resets
  visit_date and bill_date to yesterday; stage starts at `scanned`.
- History and attachments are not copied.
- After save the new claim is opened/focused.
- Added DE translations for "Duplicate claim", "Duplicate", "Claim duplicated".
- `days_in_stage` now compares calendar dates (not raw timedelta) so a claim
  created yesterday always shows ≥ 1d even if < 24h have elapsed.

## Conventions for updating this file

When making changes, append a dated entry to the **Progress log** and update
**Open items** (check off or add). Keep the log factual and brief.

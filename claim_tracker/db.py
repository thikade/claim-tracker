"""SQLite data layer for the insurance claim tracker.

Uses only the Python standard library (sqlite3). No ORM, no external
dependency. The database file and an attachments directory live side by
side under a single data directory so the whole thing is portable: copy
the folder, copy your data.
"""
from __future__ import annotations

import sqlite3
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "claims.db"
FILES_DIR = DATA_DIR / "attachments"


# --------------------------------------------------------------------------
# Stage model
#
# The workflow is a small state machine. Each claim sits in exactly one
# stage. TRANSITIONS defines which moves are legal from a given stage and
# what each move means in plain language.
# --------------------------------------------------------------------------

STAGES = {
    "scanned":         "Bill scanned",
    "public_pending":  "Public claim pending",
    "private_pending": "Private claim pending",
    "archived":        "Archived",
}

STAGE_ORDER = ["scanned", "public_pending", "private_pending", "archived"]

STAGE_COLORS = {
    "scanned":         "#7c8a9c",
    "public_pending":  "#b8893b",
    "private_pending": "#3a6f9c",
    "archived":        "#2c5f4f",
}

# Each transition: target stage, button label, and whether confirmation
# document upload should be offered as part of the move.
TRANSITIONS = {
    "scanned": [
        {"to": "public_pending",
         "label": "Submit to public health portal",
         "needs_doc": False},
        {"to": "private_pending",
         "label": "Submit directly to private insurer",
         "needs_doc": False},
    ],
    "public_pending": [
        {"to": "private_pending",
         "label": "Public claim processed - file private claim",
         "needs_doc": True,
         "doc_hint": "Attach the public health service confirmation"},
    ],
    "private_pending": [
        {"to": "archived",
         "label": "Private claim processed - archive",
         "needs_doc": True,
         "doc_hint": "Attach the private insurer confirmation"},
    ],
    "archived": [],
}

# Days a claim may sit in a pending stage before it is flagged as stale.
STALE_DAYS = {
    "public_pending": 35,   # public health processing genuinely runs long
    "private_pending": 21,
}


# --------------------------------------------------------------------------
# Connection / schema
# --------------------------------------------------------------------------

def _now() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    """Open a connection with sensible pragmas and row access by name."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    """Create the schema if it does not yet exist."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS claims (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                provider    TEXT,
                amount      REAL,
                currency    TEXT NOT NULL DEFAULT '€',
                visit_date  TEXT,
                notes       TEXT,
                stage       TEXT NOT NULL DEFAULT 'scanned',
                created_at  TEXT NOT NULL,
                staged_at   TEXT NOT NULL,
                public_ref  TEXT,
                private_ref TEXT
            );

            CREATE TABLE IF NOT EXISTS attachments (
                id          TEXT PRIMARY KEY,
                claim_id    TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
                kind        TEXT NOT NULL DEFAULT 'other',
                name        TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                size        INTEGER,
                added_at    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id  TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
                ts        TEXT NOT NULL,
                text      TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_att_claim  ON attachments(claim_id);
            CREATE INDEX IF NOT EXISTS idx_hist_claim ON history(claim_id);
            CREATE INDEX IF NOT EXISTS idx_claim_stage ON claims(stage);
            """
        )


# --------------------------------------------------------------------------
# History helper
# --------------------------------------------------------------------------

def add_history(conn: sqlite3.Connection, claim_id: str, text: str) -> None:
    """Append one line to a claim's history log."""
    conn.execute(
        "INSERT INTO history (claim_id, ts, text) VALUES (?, ?, ?)",
        (claim_id, _now(), text),
    )


# --------------------------------------------------------------------------
# Claim CRUD
# --------------------------------------------------------------------------

def create_claim(title: str, provider: str = "", amount: Optional[float] = None,
                  currency: str = "€", visit_date: str = "",
                  notes: str = "") -> str:
    """Insert a new claim in the 'scanned' stage. Returns its id."""
    claim_id = uuid.uuid4().hex[:12]
    ts = _now()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO claims
               (id, title, provider, amount, currency, visit_date, notes,
                stage, created_at, staged_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'scanned', ?, ?)""",
            (claim_id, title, provider, amount, currency, visit_date,
             notes, ts, ts),
        )
        add_history(conn, claim_id, "Claim created - medical bill scanned.")
    return claim_id


def update_claim(claim_id: str, **fields) -> None:
    """Update editable claim fields. Unknown keys are ignored."""
    allowed = {"title", "provider", "amount", "currency", "visit_date",
               "notes", "public_ref", "private_ref"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return
    assignments = ", ".join(f"{k} = ?" for k in sets)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE claims SET {assignments} WHERE id = ?",
            (*sets.values(), claim_id),
        )
        add_history(conn, claim_id, "Claim details edited.")


def move_claim(claim_id: str, to_stage: str) -> None:
    """Move a claim to a new stage, validating the transition is legal."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT stage FROM claims WHERE id = ?", (claim_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"No claim with id {claim_id}")
        current = row["stage"]
        legal = {t["to"] for t in TRANSITIONS.get(current, [])}
        if to_stage not in legal:
            raise ValueError(
                f"Illegal transition {current} -> {to_stage}"
            )
        conn.execute(
            "UPDATE claims SET stage = ?, staged_at = ? WHERE id = ?",
            (to_stage, _now(), claim_id),
        )
        add_history(
            conn, claim_id,
            f"Moved: {STAGES[current]} -> {STAGES[to_stage]}.",
        )


def delete_claim(claim_id: str) -> None:
    """Delete a claim, its history, and its attachment files from disk."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT stored_path FROM attachments WHERE claim_id = ?",
            (claim_id,),
        ).fetchall()
        for r in rows:
            p = Path(r["stored_path"])
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
        # ON DELETE CASCADE removes attachments + history rows.
        conn.execute("DELETE FROM claims WHERE id = ?", (claim_id,))


def get_claim(claim_id: str) -> Optional[dict]:
    """Return one claim as a dict, or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM claims WHERE id = ?", (claim_id,)
        ).fetchone()
        return dict(row) if row else None


def list_claims(search: str = "", stage: str = "all") -> list[dict]:
    """Return all claims, optionally filtered by search text and stage."""
    query = "SELECT * FROM claims"
    clauses, params = [], []
    if stage != "all":
        clauses.append("stage = ?")
        params.append(stage)
    if search:
        clauses.append(
            "(LOWER(title) LIKE ? OR LOWER(COALESCE(provider,'')) LIKE ? "
            "OR LOWER(COALESCE(notes,'')) LIKE ?)"
        )
        like = f"%{search.lower()}%"
        params += [like, like, like]
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


# --------------------------------------------------------------------------
# Attachments
#
# The file's bytes are copied into data/attachments/ under a unique name;
# only the path and metadata go into SQLite. This keeps the database small
# and the documents directly recoverable from the filesystem.
# --------------------------------------------------------------------------

def add_attachment(claim_id: str, original_name: str, content: bytes,
                   kind: str = "other") -> str:
    """Store an uploaded file on disk and record it. Returns attachment id."""
    att_id = uuid.uuid4().hex[:12]
    suffix = Path(original_name).suffix
    stored = FILES_DIR / f"{claim_id}_{att_id}{suffix}"
    stored.write_bytes(content)
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO attachments
               (id, claim_id, kind, name, stored_path, size, added_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (att_id, claim_id, kind, original_name, str(stored),
             len(content), _now()),
        )
        verb = {"bill": "Bill", "confirmation": "Confirmation"}.get(
            kind, "Document")
        add_history(conn, claim_id,
                    f'{verb} "{original_name}" attached.')
    return att_id


def list_attachments(claim_id: str) -> list[dict]:
    """Return all attachments for a claim, oldest first."""
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM attachments WHERE claim_id = ? ORDER BY added_at",
            (claim_id,),
        ).fetchall()]


def delete_attachment(att_id: str) -> None:
    """Delete one attachment row and its file on disk."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT claim_id, name, stored_path FROM attachments WHERE id = ?",
            (att_id,),
        ).fetchone()
        if row is None:
            return
        p = Path(row["stored_path"])
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
        conn.execute("DELETE FROM attachments WHERE id = ?", (att_id,))
        add_history(conn, row["claim_id"],
                    f'Document "{row["name"]}" removed.')


# --------------------------------------------------------------------------
# History
# --------------------------------------------------------------------------

def list_history(claim_id: str) -> list[dict]:
    """Return a claim's history log, newest first."""
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM history WHERE claim_id = ? ORDER BY ts DESC, id DESC",
            (claim_id,),
        ).fetchall()]


# --------------------------------------------------------------------------
# Dashboard aggregates
# --------------------------------------------------------------------------

def dashboard_stats() -> dict:
    """Compute summary numbers for the dashboard cards."""
    with get_connection() as conn:
        claims = [dict(r) for r in conn.execute(
            "SELECT stage, amount, staged_at FROM claims").fetchall()]

    total = len(claims)
    active = sum(1 for c in claims if c["stage"] != "archived")
    archived = sum(1 for c in claims if c["stage"] == "archived")
    outstanding = sum((c["amount"] or 0.0)
                      for c in claims if c["stage"] != "archived")

    stale = 0
    now = datetime.now(timezone.utc)
    for c in claims:
        limit = STALE_DAYS.get(c["stage"])
        if limit is None:
            continue
        try:
            staged = datetime.fromisoformat(c["staged_at"])
        except (ValueError, TypeError):
            continue
        if (now - staged).days >= limit:
            stale += 1

    return {
        "total": total,
        "active": active,
        "archived": archived,
        "outstanding": outstanding,
        "stale": stale,
    }


def is_stale(claim: dict) -> bool:
    """Return True if a claim has been pending longer than its threshold."""
    limit = STALE_DAYS.get(claim["stage"])
    if limit is None:
        return False
    try:
        staged = datetime.fromisoformat(claim["staged_at"])
    except (ValueError, TypeError):
        return False
    return (datetime.now(timezone.utc) - staged).days >= limit


def days_in_stage(claim: dict) -> int:
    """Return how many whole days the claim has been in its current stage."""
    try:
        staged = datetime.fromisoformat(claim["staged_at"])
    except (ValueError, TypeError):
        return 0
    return (datetime.now(timezone.utc) - staged).days


# --------------------------------------------------------------------------
# Backup / export
# --------------------------------------------------------------------------

def backup_to(dest_dir: Path) -> Path:
    """Copy the database and all attachments into a timestamped folder."""
    dest_dir = Path(dest_dir)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = dest_dir / f"claim_tracker_backup_{stamp}"
    target.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, target / "claims.db")
    if FILES_DIR.exists():
        shutil.copytree(FILES_DIR, target / "attachments",
                        dirs_exist_ok=True)
    return target

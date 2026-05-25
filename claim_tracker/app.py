"""NiceGUI frontend for the insurance claim tracker.

Run with:  python -m claim_tracker.app   (or python app.py from this folder)

The whole application is a single Python process: NiceGUI serves the web
UI and the SQLite database lives on disk next to the code. There is no
separate backend service.
"""
from __future__ import annotations

import base64
from datetime import datetime, timedelta
from pathlib import Path

from nicegui import ui, app

from . import db


# --------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------

def fmt_date(iso: str) -> str:
    """Render an ISO timestamp as a short local date."""
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y")
    except ValueError:
        return iso


def fmt_datetime(iso: str) -> str:
    """Render an ISO timestamp as a short local date + time."""
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y, %H:%M")
    except ValueError:
        return iso


def fmt_size(n: int | None) -> str:
    """Human-readable file size."""
    if not n:
        return ""
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / 1024 / 1024:.1f} MB"


# --------------------------------------------------------------------------
# Page state
#
# Kept in a plain dict so the refreshable functions can read it. NiceGUI
# runs single-worker, so this is safe for a local single-user tool.
# --------------------------------------------------------------------------

state = {"search": "", "stage": "active", "open_id": None}


# --------------------------------------------------------------------------
# Dialogs
# --------------------------------------------------------------------------

def add_claimant_dialog(on_created) -> None:
    """Open a dialog to add a new claimant with a badge color."""
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label("New claimant").classes("text-lg font-medium")
        name_input = ui.input("Full name").classes("w-full")
        color_input = ui.color_input("Badge color", value="#6366f1", preview=True).classes("w-full")
        color_input.picker.q_color.props('default-view="palette"')

        def save() -> None:
            name = (name_input.value or "").strip()
            if not name:
                ui.notify("Please enter a name", type="warning")
                return
            try:
                new_id = db.add_claimant(name, color=color_input.value or "#6366f1")
            except Exception:
                ui.notify("Claimant already exists", type="warning")
                return
            dialog.close()
            on_created(new_id, name, color_input.value or "#6366f1")

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Add", on_click=save).props("color=primary")
    dialog.open()


def delete_claimant_dialog(on_deleted=None) -> None:
    """Open a dialog listing unassigned claimants with a delete button each."""
    unassigned = db.list_unassigned_claimants()
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label("Delete claimant").classes("text-lg font-medium")
        if not unassigned:
            ui.label("No unassigned claimants.").classes("text-gray-500 text-sm")
        else:
            for c in unassigned:
                def make_delete(cid: int, cname: str):
                    def do_delete():
                        try:
                            db.delete_claimant(cid)
                            ui.notify(f"{cname} deleted", type="positive")
                            dialog.close()
                            if on_deleted:
                                on_deleted(cid)
                        except ValueError as exc:
                            ui.notify(str(exc), type="warning")
                    return do_delete

                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(c["name"])
                    ui.button(icon="remove", on_click=make_delete(c["id"], c["name"])) \
                        .props("flat round dense color=negative")

        with ui.row().classes("w-full justify-end"):
            ui.button("Close", on_click=dialog.close).props("flat")
    dialog.open()


def add_provider_dialog(on_created) -> None:
    """Open a dialog to add a new provider."""
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label("New provider").classes("text-lg font-medium")
        name_input = ui.input("Name").classes("w-full")

        def save() -> None:
            name = (name_input.value or "").strip()
            if not name:
                ui.notify("Please enter a name", type="warning")
                return
            try:
                new_id = db.add_provider(name)
            except Exception:
                ui.notify("Provider already exists", type="warning")
                return
            dialog.close()
            on_created(new_id, name)

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Add", on_click=save).props("color=primary")
    dialog.open()


def delete_provider_dialog(on_deleted=None) -> None:
    """Open a dialog listing unassigned providers with a delete button each."""
    unassigned = db.list_unassigned_providers()
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label("Delete provider").classes("text-lg font-medium")
        if not unassigned:
            ui.label("No unassigned providers.").classes("text-gray-500 text-sm")
        else:
            for p in unassigned:
                def make_delete(pid: int, pname: str):
                    def do_delete():
                        try:
                            db.delete_provider(pid)
                            ui.notify(f"{pname} deleted", type="positive")
                            dialog.close()
                            if on_deleted:
                                on_deleted(pid)
                        except ValueError as exc:
                            ui.notify(str(exc), type="warning")
                    return do_delete

                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(p["name"])
                    ui.button(icon="remove", on_click=make_delete(p["id"], p["name"])) \
                        .props("flat round dense color=negative")

        with ui.row().classes("w-full justify-end"):
            ui.button("Close", on_click=dialog.close).props("flat")
    dialog.open()


def edit_claimant_color_dialog(claimant_id: int, name: str, current_color: str) -> None:
    """Open a dialog to change a claimant's badge color."""
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label(f"Badge color — {name}").classes("text-lg font-medium")
        color_input = ui.color_input("Badge color", value=current_color, preview=True).classes("w-full")
        color_input.picker.q_color.props('default-view="palette"')

        def save() -> None:
            db.update_claimant_color(claimant_id, color_input.value or current_color)
            dialog.close()
            refresh_page()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Save", on_click=save).props("color=primary")
    dialog.open()


def claim_form_dialog(existing: dict | None = None) -> None:
    """Open a dialog to create a new claim or edit an existing one."""
    editing = existing is not None
    with ui.dialog() as dialog, ui.card().classes("w-96 gap-2"):
        ui.label("Edit claim" if editing else "New claim") \
            .classes("text-xl font-medium")

        title = ui.input(
            "Title",
            placeholder="e.g. Dr. Müller - physiotherapy",
            value=existing["title"] if editing else "",
            autocomplete=db.list_titles(),
        ).classes("w-full")

        providers = db.list_providers()
        provider_options = {p["id"]: p["name"] for p in providers}
        current_provider = existing.get("provider_id") if editing else None

        with ui.row().classes("w-full items-end gap-2"):
            provider_sel = ui.select(
                provider_options,
                label="Provider / doctor",
                value=current_provider,
            ).classes("flex-1")

            def on_provider_created(new_id: int, name: str) -> None:
                provider_sel.options[new_id] = name
                provider_sel.value = new_id
                provider_sel.update()

            def on_provider_deleted(deleted_id: int) -> None:
                provider_sel.options.pop(deleted_id, None)
                if provider_sel.value == deleted_id:
                    provider_sel.value = None
                provider_sel.update()

            ui.button(icon="add", on_click=lambda: add_provider_dialog(on_provider_created)) \
                .props("flat round dense").classes("mb-1")

        claimants = db.list_claimants()
        claimant_options = {c["id"]: c["name"] for c in claimants}
        current_claimant = existing.get("claimant_id") if editing else None

        with ui.row().classes("w-full items-end gap-2"):
            claimant_sel = ui.select(
                claimant_options,
                label="Claimant *",
                value=current_claimant,
            ).classes("flex-1")

            def on_claimant_created(new_id: int, name: str, color: str = "#6366f1") -> None:
                claimant_sel.options[new_id] = name
                claimant_sel.value = new_id
                claimant_sel.update()

            def on_claimant_deleted(deleted_id: int) -> None:
                claimant_sel.options.pop(deleted_id, None)
                if claimant_sel.value == deleted_id:
                    claimant_sel.value = None
                claimant_sel.update()

            ui.button(icon="add", on_click=lambda: add_claimant_dialog(on_claimant_created)) \
                .props("flat round dense").classes("mb-1")

        amount = ui.number(
            "Amount (€)", format="%.2f",
            value=existing["amount"] if editing else None,
        ).classes("w-full")

        visit = ui.input(
            "Visit date",
            value=existing["visit_date"] if editing else (datetime.utcnow().date() - timedelta(days=1)).isoformat(),
        ).props("type=date").classes("w-full")

        # Portal reference numbers - handy once a claim is submitted.
        public_ref = ui.input(
            "Public insurer reference",
            value=existing.get("public_ref") or "" if editing else "",
        ).classes("w-full")
        private_ref = ui.input(
            "Private insurer reference",
            value=existing.get("private_ref") or "" if editing else "",
        ).classes("w-full")

        notes = ui.textarea(
            "Notes",
            value=existing["notes"] if editing else "",
        ).classes("w-full")

        def save() -> None:
            if not title.value or not title.value.strip():
                ui.notify("Please enter a title", type="warning")
                return
            if not claimant_sel.value:
                ui.notify("Please select a claimant", type="warning")
                return
            fields = dict(
                title=title.value.strip(),
                provider_id=provider_sel.value,
                amount=amount.value,
                currency="€",
                visit_date=visit.value or "",
                notes=(notes.value or "").strip(),
                public_ref=(public_ref.value or "").strip(),
                private_ref=(private_ref.value or "").strip(),
                claimant_id=claimant_sel.value,
            )
            if editing:
                db.update_claim(existing["id"], **fields)
                ui.notify("Claim updated", type="positive")
            else:
                new_id = db.create_claim(**fields)
                state["open_id"] = new_id
                ui.notify("Claim created", type="positive")
            dialog.close()
            refresh_page()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Save" if editing else "Create", on_click=save) \
                .props("color=primary")
    dialog.open()


def move_dialog(claim: dict, transition: dict) -> None:
    """Confirm a stage move, optionally uploading a confirmation document."""
    # A simple move with no document - just do it.
    if not transition["needs_doc"]:
        db.move_claim(claim["id"], transition["to"])
        ui.notify(f"Moved to {db.STAGES[transition['to']]}", type="positive")
        refresh_page()
        return

    uploaded: dict = {"name": None, "content": None}

    with ui.dialog() as dialog, ui.card().classes("w-96 gap-2"):
        ui.label(transition["label"]).classes("text-lg font-medium")
        ui.label(transition["doc_hint"] +
                 ". You can also continue without it and add the "
                 "document later.").classes("text-sm text-gray-600")

        def on_upload(e) -> None:
            uploaded["name"] = e.name
            uploaded["content"] = e.content.read()
            ui.notify(f"Selected: {e.name}")

        ui.upload(on_upload=on_upload, auto_upload=True,
                  label="Choose confirmation file").classes("w-full")

        def confirm(with_doc: bool) -> None:
            db.move_claim(claim["id"], transition["to"])
            if with_doc and uploaded["content"] is not None:
                db.add_attachment(
                    claim["id"], uploaded["name"],
                    uploaded["content"], kind="confirmation",
                )
            dialog.close()
            ui.notify(f"Moved to {db.STAGES[transition['to']]}",
                      type="positive")
            refresh_page()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Continue without",
                      on_click=lambda: confirm(False)).props("flat")
            ui.button("Confirm step",
                      on_click=lambda: confirm(True)).props("color=primary")
    dialog.open()


def upload_dialog(claim_id: str) -> None:
    """Open a dialog to attach a document to a claim."""
    doc_types = {
        "bill":         "Medical bill",
        "prescription": "Prescription",
        "bank_statement": "Bank statement",
        "other":        "Other",
    }
    with ui.dialog() as dialog, ui.card().classes("w-96 gap-2"):
        ui.label("Add document").classes("text-lg font-medium")
        kind_sel = ui.select(doc_types, value="bill", label="Document type").classes("w-full")

        async def on_upload(e) -> None:
            content = await e.file.read()
            db.add_attachment(claim_id, e.file.name, content, kind=kind_sel.value)
            dialog.close()
            ui.notify("Document attached", type="positive")
            refresh_page()

        ui.upload(on_upload=on_upload, auto_upload=True,
                  label="Choose file").classes("w-full")
        ui.button("Close", on_click=dialog.close).props("flat")
    dialog.open()


def confirm_delete_dialog(claim: dict) -> None:
    """Ask for confirmation before permanently deleting a claim."""
    atts = db.list_attachments(claim["id"])
    with ui.dialog() as dialog, ui.card().classes("w-96 gap-2"):
        ui.label("Delete claim?").classes("text-lg font-medium")
        ui.label(f'"{claim["title"]}" and its {len(atts)} document(s) '
                 "will be permanently removed from the database and disk.") \
            .classes("text-sm text-gray-600")

        def do_delete() -> None:
            db.delete_claim(claim["id"])
            if state["open_id"] == claim["id"]:
                state["open_id"] = None
            dialog.close()
            ui.notify("Claim deleted", type="warning")
            refresh_page()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Delete permanently", on_click=do_delete) \
                .props("color=negative")
    dialog.open()


# --------------------------------------------------------------------------
# Attachment download route
#
# A custom GET route streams a stored file back to the browser so the
# "open" button works for PDFs, images, anything.
# --------------------------------------------------------------------------

@app.get("/attachment/{att_id}")
def serve_attachment(att_id: str):
    from fastapi.responses import FileResponse, PlainTextResponse
    for claim in db.list_claims():
        for a in db.list_attachments(claim["id"]):
            if a["id"] == att_id:
                p = Path(a["stored_path"])
                if p.exists():
                    return FileResponse(p, filename=a["name"])
    return PlainTextResponse("Not found", status_code=404)


# --------------------------------------------------------------------------
# UI building blocks
# --------------------------------------------------------------------------

def build_attachment_row(att: dict) -> None:
    """Render one attachment line inside a claim's detail panel."""
    with ui.row().classes("items-center w-full gap-2 p-2 "
                          "border rounded bg-white"):
        icon = "receipt_long" if att["kind"] == "bill" else "description"
        ui.icon(icon).classes("text-gray-500")
        ui.link(att["name"], f"/attachment/{att['id']}", new_tab=True) \
            .classes("flex-1 truncate")
        ui.label(fmt_size(att["size"])).classes("text-xs text-gray-400")
        ui.badge(att["kind"]).props("color=grey-4 text-color=grey-9")

        def remove(att_id=att["id"]) -> None:
            db.delete_attachment(att_id)
            ui.notify("Document removed")
            refresh_page()

        ui.button(icon="close", on_click=remove) \
            .props("flat dense round size=sm")


def build_claim_detail(claim: dict) -> None:
    """Render the expanded detail panel for one claim."""
    with ui.column().classes("w-full gap-3 p-3 bg-gray-50 "
                             "border-t rounded-b"):
        # ---- next step / stage actions -----------------------------------
        transitions = db.TRANSITIONS.get(claim["stage"], [])
        if transitions:
            with ui.card().classes("w-full bg-green-50 gap-1"):
                ui.label("NEXT STEP").classes(
                    "text-xs font-bold text-green-800")
                with ui.row().classes("gap-2 flex-wrap"):
                    for t in transitions:
                        ui.button(
                            t["label"],
                            on_click=lambda t=t: move_dialog(claim, t),
                        ).props("color=primary size=sm")
        else:
            with ui.card().classes("w-full bg-gray-100"):
                ui.label("This claim is archived. Nothing further to do.") \
                    .classes("text-sm text-gray-600")

        # ---- two columns: attachments + history --------------------------
        with ui.row().classes("w-full gap-6 items-start"):

            # attachments column
            with ui.column().classes("flex-1 gap-2 min-w-0"):
                ui.label("ATTACHMENTS").classes(
                    "text-xs font-bold text-gray-400")
                attachments = db.list_attachments(claim["id"])
                if attachments:
                    for a in attachments:
                        build_attachment_row(a)
                else:
                    ui.label("No documents yet.") \
                        .classes("text-sm text-gray-400")
                with ui.row().classes("gap-2"):
                    ui.button(
                        "+ Add document",
                        on_click=lambda c=claim: upload_dialog(c["id"]),
                    ).props("outline size=sm")

            # history column
            with ui.column().classes("flex-1 gap-1 min-w-0"):
                ui.label("HISTORY").classes(
                    "text-xs font-bold text-gray-400")
                for h in db.list_history(claim["id"]):
                    with ui.column().classes("gap-0 mb-1"):
                        ui.label(h["text"]).classes("text-sm")
                        ui.label(fmt_datetime(h["ts"])) \
                            .classes("text-xs text-gray-400")

        # ---- footer: edit + delete ---------------------------------------
        with ui.row().classes("w-full justify-between border-t pt-2"):
            with ui.row().classes("gap-1"):
                ui.button("Edit details",
                          on_click=lambda: claim_form_dialog(claim)) \
                    .props("flat size=sm")
                if claim.get("claimant_id"):
                    ui.button(
                        icon="palette",
                        on_click=lambda: edit_claimant_color_dialog(
                            claim["claimant_id"],
                            claim.get("claimant_name", ""),
                            claim.get("claimant_color") or "#6366f1",
                        ),
                    ).props("flat round dense size=sm") \
                     .tooltip(f"Change badge color for {claim.get('claimant_name', '')}")
            ui.button("Delete claim",
                      on_click=lambda: confirm_delete_dialog(claim)) \
                .props("flat color=negative size=sm")


def build_claim_card(claim: dict) -> None:
    """Render a single collapsible claim card."""
    is_open = state["open_id"] == claim["id"]
    color = db.STAGE_COLORS[claim["stage"]]
    stale = db.is_stale(claim)
    age = db.days_in_stage(claim)
    age_label = "today" if age == 0 else f"{age}d in stage"

    with ui.card().classes("w-full p-0 overflow-hidden"):
        # ---- summary row (click to toggle) -------------------------------
        def toggle(cid=claim["id"]) -> None:
            state["open_id"] = None if is_open else cid
            refresh_page()

        with ui.row().classes(
            "items-center w-full gap-3 p-3 cursor-pointer "
            "hover:bg-gray-50 no-wrap"
        ).on("click", toggle):
            # colored stage marker
            ui.element("div").style(
                f"width:6px;align-self:stretch;border-radius:3px;"
                f"background:{color}")

            with ui.column().classes("flex-1 gap-0 min-w-0"):
                ui.label(claim["title"]).classes(
                    "text-base font-medium truncate")
                meta = []
                if claim.get("provider_name"):
                    meta.append(claim["provider_name"])
                if claim["amount"]:
                    meta.append(f"{claim['currency']}"
                                f"{claim['amount']:.2f}")
                meta.append(f"opened {fmt_date(claim['created_at'])}")
                ui.label("  ·  ".join(meta)) \
                    .classes("text-xs text-gray-500 truncate")

            with ui.column().classes("items-end gap-1"):
                with ui.row().classes("items-center gap-2 no-wrap"):
                    ui.label(claim["id"]).classes("text-xs font-mono text-gray-400")
                    if claim.get("claimant_name"):
                        claimant_color = claim.get("claimant_color") or "#6366f1"
                        ui.badge(claim["claimant_name"], color=claimant_color) \
                            .classes("cursor-pointer") \
                            .on("click.stop", lambda c=claim: edit_claimant_color_dialog(
                                c["claimant_id"], c.get("claimant_name", ""),
                                c.get("claimant_color") or "#6366f1"))
                    ui.badge(db.STAGES[claim["stage"]], color=color)
                lbl = ui.label(("⚠ " if stale else "") + age_label)
                lbl.classes("text-xs " +
                            ("text-amber-700 font-medium"
                             if stale else "text-gray-400"))

        # ---- detail panel ------------------------------------------------
        if is_open:
            build_claim_detail(claim)


# --------------------------------------------------------------------------
# Refreshable regions
# --------------------------------------------------------------------------

@ui.refreshable
def metrics_row() -> None:
    """Render the four dashboard metric cards."""
    s = db.dashboard_stats()
    per_claimant = db.outstanding_by_claimant()
    cards = [
        ("Active claims", str(s["active"]), f"{s['total']} total", False),
        ("Need attention", str(s["stale"]),
         "pending too long", s["stale"] > 0),
        ("Archived", str(s["archived"]), "completed", False),
    ]
    with ui.row().classes("w-full gap-3 no-wrap items-stretch"):
        # Outstanding card — per-claimant rows only
        with ui.card().classes("flex-1 gap-0"):
            ui.label("OUTSTANDING").classes("text-xs font-bold text-gray-400")
            if per_claimant:
                with ui.column().classes("gap-0 mt-1"):
                    for row in per_claimant:
                        with ui.row().classes("w-full justify-between gap-4"):
                            ui.label(row["claimant_name"]).classes("text-sm font-medium")
                            ui.label(f"€{row['total']:.2f}").classes("text-sm")
            else:
                ui.label("—").classes("text-2xl font-medium text-gray-300")

        for label, value, sub, flag in cards:
            with ui.card().classes("flex-1 gap-0"):
                ui.label(label.upper()).classes(
                    "text-xs font-bold text-gray-400")
                ui.label(value).classes(
                    "text-2xl font-medium " +
                    ("text-amber-700" if flag else ""))
                ui.label(sub).classes("text-xs text-gray-500")


@ui.refreshable
def claim_board() -> None:
    """Render all claims grouped by stage."""
    claims = db.list_claims(search=state["search"], stage=state["stage"])

    if not db.list_claims():
        with ui.column().classes("w-full items-center py-16"):
            ui.label("No claims yet.").classes("text-lg text-gray-400")
            ui.label('Click "New claim" to scan your first medical bill.') \
                .classes("text-sm text-gray-400")
        return

    if not claims:
        ui.label("No claims match your search.") \
            .classes("text-gray-400 py-16 text-center w-full")
        return

    for stage_id in db.STAGE_ORDER:
        group = [c for c in claims if c["stage"] == stage_id]
        if not group:
            continue
        with ui.column().classes("w-full gap-2 mb-4"):
            with ui.row().classes("items-baseline gap-2 w-full"):
                ui.label(db.STAGES[stage_id]) \
                    .classes("text-lg font-medium")
                ui.label(str(len(group))) \
                    .classes("text-xs text-gray-400 font-bold")
            for c in group:
                build_claim_card(c)


def refresh_page() -> None:
    """Re-render all refreshable regions after any data change."""
    metrics_row.refresh()
    toolbar.refresh()
    claim_board.refresh()


@ui.refreshable
def toolbar() -> None:
    counts = db.claim_counts_by_stage()

    def label(key: str, name: str) -> str:
        n = counts.get(key, 0)
        return f"{name} ({n})"

    options = {
        "active": label("active", "Active claims"),
        "all":    label("all",    "All stages"),
        **{k: label(k, db.STAGES[k]) for k in db.STAGE_ORDER},
    }

    with ui.row().classes("w-full gap-2 items-center no-wrap"):
        search = ui.input(
            placeholder="Search by title, provider, claimant or notes…",
            value=state["search"],
        ).classes("flex-1").props("clearable")

        def on_search(e) -> None:
            state["search"] = e.value or ""
            claim_board.refresh()
        search.on_value_change(on_search)

        stage_sel = ui.select(options, value=state["stage"]).classes("w-56")

        def on_stage(e) -> None:
            state["stage"] = e.value
            claim_board.refresh()
        stage_sel.on_value_change(on_stage)


# --------------------------------------------------------------------------
# Main page
# --------------------------------------------------------------------------

@ui.page("/")
def main_page() -> None:
    ui.colors(primary="#2c5f4f")
    ui.add_head_html(
        "<style>body{background:#f4f2ec}</style>")

    with ui.column().classes("w-full max-w-4xl mx-auto p-6 gap-4"):

        # ---- header ------------------------------------------------------
        with ui.row().classes("w-full items-end justify-between "
                              "border-b-2 border-gray-800 pb-3"):
            with ui.column().classes("gap-0"):
                ui.label("Insurance Claim Tracker") \
                    .classes("text-2xl font-medium")
                ui.label("Medical bills · public health service · "
                         "private insurance") \
                    .classes("text-xs text-gray-500")
            with ui.row().classes("gap-2"):
                def do_backup() -> None:
                    target = db.backup_to(db.DATA_DIR / "backups")
                    ui.notify(f"Backup written to {target}",
                              type="positive")
                ui.button("Backup", on_click=do_backup).props("outline")
                ui.button("Settings", on_click=lambda: ui.navigate.to("/settings")).props("outline")
                ui.button("+ New claim",
                          on_click=lambda: claim_form_dialog(None)) \
                    .props("color=primary")

        # ---- metrics -----------------------------------------------------
        metrics_row()

        # ---- toolbar -----------------------------------------------------
        toolbar()

        # ---- board -------------------------------------------------------
        claim_board()


# --------------------------------------------------------------------------
# Settings page
# --------------------------------------------------------------------------

@ui.page("/settings")
def settings_page() -> None:
    ui.colors(primary="#2c5f4f")
    ui.add_head_html("<style>body{background:#f4f2ec}</style>")

    with ui.column().classes("w-full max-w-3xl mx-auto p-6 gap-6"):

        with ui.row().classes("w-full items-center justify-between border-b-2 border-gray-800 pb-3"):
            ui.label("Settings").classes("text-2xl font-medium")
            ui.button("← Back", on_click=lambda: ui.navigate.to("/")).props("flat")

        # ---- Claimants section -------------------------------------------
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center justify-between mb-2"):
                ui.label("Claimants").classes("text-lg font-semibold")
                ui.button(icon="add", on_click=lambda: _add_claimant_inline(claimants_col)) \
                    .props("flat round dense").tooltip("Add claimant")

            claimants_col = ui.column().classes("w-full gap-1")
            _render_claimants(claimants_col)

        # ---- Providers section -------------------------------------------
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center justify-between mb-2"):
                ui.label("Providers").classes("text-lg font-semibold")
                ui.button(icon="add", on_click=lambda: _add_provider_inline(providers_col)) \
                    .props("flat round dense").tooltip("Add provider")

            providers_col = ui.column().classes("w-full gap-1")
            _render_providers(providers_col)


def _render_claimants(container: ui.column) -> None:
    container.clear()
    with container:
        claimants = db.list_claimants()
        if not claimants:
            ui.label("No claimants yet.").classes("text-sm text-gray-400")
            return
        for c in claimants:
            _claimant_row(container, c)


def _claimant_row(container: ui.column, c: dict) -> None:
    with ui.row().classes("w-full items-center gap-2 py-1"):
        # colored dot
        color = c["color"] or "#6366f1"
        ui.element("span").style(
            f"width:14px;height:14px;border-radius:50%;background:{color};display:inline-block;flex-shrink:0"
        )
        ui.label(c["name"]).classes("flex-1 text-sm")

        def open_edit(claimant=c):
            _edit_claimant_inline(container, claimant)
        def do_delete(claimant=c):
            try:
                db.delete_claimant(claimant["id"])
                _render_claimants(container)
            except ValueError as exc:
                ui.notify(str(exc), type="warning")

        ui.button(icon="edit", on_click=open_edit).props("flat round dense size=sm")
        ui.button(icon="delete", on_click=do_delete).props("flat round dense size=sm color=negative")


def _add_claimant_inline(container: ui.column) -> None:
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label("New claimant").classes("text-lg font-medium")
        name_input = ui.input("Full name").classes("w-full")
        color_input = ui.color_input("Badge color", value="#6366f1", preview=True).classes("w-full")
        color_input.picker.q_color.props('default-view="palette"')

        def save():
            name = (name_input.value or "").strip()
            if not name:
                ui.notify("Please enter a name", type="warning")
                return
            try:
                db.add_claimant(name, color=color_input.value or "#6366f1")
            except Exception:
                ui.notify("Claimant already exists", type="warning")
                return
            dialog.close()
            _render_claimants(container)

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Add", on_click=save).props("color=primary")
    dialog.open()


def _edit_claimant_inline(container: ui.column, c: dict) -> None:
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label("Edit claimant").classes("text-lg font-medium")
        name_input = ui.input("Full name", value=c["name"]).classes("w-full")
        color_input = ui.color_input("Badge color", value=c["color"] or "#6366f1", preview=True).classes("w-full")
        color_input.picker.q_color.props('default-view="palette"')

        def save():
            name = (name_input.value or "").strip()
            if not name:
                ui.notify("Please enter a name", type="warning")
                return
            try:
                db.update_claimant(c["id"], name, color_input.value or "#6366f1")
            except Exception:
                ui.notify("Name already taken", type="warning")
                return
            dialog.close()
            _render_claimants(container)

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Save", on_click=save).props("color=primary")
    dialog.open()


def _render_providers(container: ui.column) -> None:
    container.clear()
    with container:
        providers = db.list_providers()
        if not providers:
            ui.label("No providers yet.").classes("text-sm text-gray-400")
            return
        for p in providers:
            _provider_row(container, p)


def _provider_row(container: ui.column, p: dict) -> None:
    with ui.row().classes("w-full items-center gap-2 py-1"):
        ui.label(p["name"]).classes("flex-1 text-sm")

        def open_edit(provider=p):
            _edit_provider_inline(container, provider)
        def do_delete(provider=p):
            try:
                db.delete_provider(provider["id"])
                _render_providers(container)
            except ValueError as exc:
                ui.notify(str(exc), type="warning")

        ui.button(icon="edit", on_click=open_edit).props("flat round dense size=sm")
        ui.button(icon="delete", on_click=do_delete).props("flat round dense size=sm color=negative")


def _add_provider_inline(container: ui.column) -> None:
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label("New provider").classes("text-lg font-medium")
        name_input = ui.input("Name").classes("w-full")

        def save():
            name = (name_input.value or "").strip()
            if not name:
                ui.notify("Please enter a name", type="warning")
                return
            try:
                db.add_provider(name)
            except Exception:
                ui.notify("Provider already exists", type="warning")
                return
            dialog.close()
            _render_providers(container)

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Add", on_click=save).props("color=primary")
    dialog.open()


def _edit_provider_inline(container: ui.column, p: dict) -> None:
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label("Edit provider").classes("text-lg font-medium")
        name_input = ui.input("Name", value=p["name"]).classes("w-full")

        def save():
            name = (name_input.value or "").strip()
            if not name:
                ui.notify("Please enter a name", type="warning")
                return
            try:
                db.update_provider(p["id"], name)
            except Exception:
                ui.notify("Name already taken", type="warning")
                return
            dialog.close()
            _render_providers(container)

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Save", on_click=save).props("color=primary")
    dialog.open()


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def run() -> None:
    """Initialise the database and start the NiceGUI server."""
    db.init_db()
    ui.run(
        title="Insurance Claim Tracker",
        port=8080,
        reload=True,
        show=True,        # open the browser automatically
        favicon="🧾",
    )


# `python -m claim_tracker.app` and `python app.py` both work.
if __name__ in {"__main__", "__mp_main__"}:
    run()

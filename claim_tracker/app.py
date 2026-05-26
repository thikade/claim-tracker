"""NiceGUI frontend for the insurance claim tracker.

Run with:  python -m claim_tracker.app   (or python app.py from this folder)

The whole application is a single Python process: NiceGUI serves the web
UI and the SQLite database lives on disk next to the code. There is no
separate backend service.
"""
from __future__ import annotations

import base64
import os
from datetime import datetime, timedelta
from pathlib import Path

GIT_COMMIT = os.environ.get("GIT_COMMIT", "dev")[:7]

from nicegui import ui, app

from . import db
from .i18n import (
    STAGE_KEYS,
    TRANSITION_HINT_KEYS,
    TRANSITION_LABEL_KEYS,
    check_translations,
    t as _t,
)


# --------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------

def fmt_date(iso: str) -> str:
    """Render an ISO timestamp as a short local date."""
    if not iso:
        return ""
    try:
        fmt = "%d.%m.%Y" if state.get("lang") == "de" else "%d %b %Y"
        return datetime.fromisoformat(iso).strftime(fmt)
    except ValueError:
        return iso


def fmt_datetime(iso: str) -> str:
    """Render an ISO timestamp as a short local date + time."""
    try:
        fmt = "%d.%m.%Y %H:%M" if state.get("lang") == "de" else "%d %b %Y, %H:%M"
        return datetime.fromisoformat(iso).strftime(fmt)
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

state = {"search": "", "stage": "active", "open_id": None, "lang": "en"}


def t(key: str, **kwargs) -> str:
    """Translate key to the current UI language."""
    return _t(key, state["lang"], **kwargs)


# --------------------------------------------------------------------------
# Dialogs
# --------------------------------------------------------------------------

def add_claimant_dialog(on_created) -> None:
    """Open a dialog to add a new claimant with a badge color."""
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label(t("claimant.new")).classes("text-lg font-medium")
        name_input = ui.input(t("claimant.full_name")).classes("w-full")
        color_input = ui.color_input(t("claimant.badge_color"), value="#6366f1", preview=True).classes("w-full")
        color_input.picker.q_color.props('default-view="palette"')

        def save() -> None:
            name = (name_input.value or "").strip()
            if not name:
                ui.notify(t("common.name_required"), type="warning")
                return
            try:
                new_id = db.add_claimant(name, color=color_input.value or "#6366f1")
            except Exception:
                ui.notify(t("claimant.already_exists"), type="warning")
                return
            dialog.close()
            on_created(new_id, name, color_input.value or "#6366f1")

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(t("common.cancel"), on_click=dialog.close).props("flat")
            ui.button(t("common.add"), on_click=save).props("color=primary")
    dialog.open()


def delete_claimant_dialog(on_deleted=None) -> None:
    """Open a dialog listing unassigned claimants with a delete button each."""
    unassigned = db.list_unassigned_claimants()
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label(t("claimant.delete")).classes("text-lg font-medium")
        if not unassigned:
            ui.label(t("claimant.no_unassigned")).classes("text-gray-500 text-sm")
        else:
            for c in unassigned:
                def make_delete(cid: int, cname: str):
                    def do_delete():
                        try:
                            db.delete_claimant(cid)
                            ui.notify(t("common.deleted_named", name=cname), type="positive")
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
            ui.button(t("common.close"), on_click=dialog.close).props("flat")
    dialog.open()


def add_provider_dialog(on_created) -> None:
    """Open a dialog to add a new provider."""
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label(t("provider.new")).classes("text-lg font-medium")
        name_input = ui.input(t("common.name")).classes("w-full")

        def save() -> None:
            name = (name_input.value or "").strip()
            if not name:
                ui.notify(t("common.name_required"), type="warning")
                return
            try:
                new_id = db.add_provider(name)
            except Exception:
                ui.notify(t("provider.already_exists"), type="warning")
                return
            dialog.close()
            on_created(new_id, name)

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(t("common.cancel"), on_click=dialog.close).props("flat")
            ui.button(t("common.add"), on_click=save).props("color=primary")
    dialog.open()


def delete_provider_dialog(on_deleted=None) -> None:
    """Open a dialog listing unassigned providers with a delete button each."""
    unassigned = db.list_unassigned_providers()
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label(t("provider.delete")).classes("text-lg font-medium")
        if not unassigned:
            ui.label(t("provider.no_unassigned")).classes("text-gray-500 text-sm")
        else:
            for p in unassigned:
                def make_delete(pid: int, pname: str):
                    def do_delete():
                        try:
                            db.delete_provider(pid)
                            ui.notify(t("common.deleted_named", name=pname), type="positive")
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
            ui.button(t("common.close"), on_click=dialog.close).props("flat")
    dialog.open()


def edit_claimant_color_dialog(claimant_id: int, name: str, current_color: str) -> None:
    """Open a dialog to change a claimant's badge color."""
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label(t("claimant.badge_color_named", name=name)).classes("text-lg font-medium")
        color_input = ui.color_input(t("claimant.badge_color"), value=current_color, preview=True).classes("w-full")
        color_input.picker.q_color.props('default-view="palette"')

        def save() -> None:
            db.update_claimant_color(claimant_id, color_input.value or current_color)
            dialog.close()
            refresh_page()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(t("common.cancel"), on_click=dialog.close).props("flat")
            ui.button(t("common.save"), on_click=save).props("color=primary")
    dialog.open()


def claim_form_dialog(existing: dict | None = None, dupe_mode: bool = False) -> None:
    """Open a dialog to create a new claim, edit an existing one, or duplicate one."""
    editing = existing is not None and not dupe_mode
    prefill = existing is not None
    with ui.dialog() as dialog, ui.card().classes("w-96 gap-2"):
        title_key = "claim_form.duplicate_title" if dupe_mode else ("claim_form.edit_title" if editing else "claim_form.new_title")
        ui.label(t(title_key)) \
            .classes("text-xl font-medium")

        title = ui.input(
            t("claim_form.title"),
            placeholder=t("claim_form.title_placeholder"),
            value=existing["title"] if prefill else "",
            autocomplete=db.list_titles(),
        ).classes("w-full")

        providers = db.list_providers()
        provider_options = {p["id"]: p["name"] for p in providers}
        current_provider = existing.get("provider_id") if prefill else None

        with ui.row().classes("w-full items-end gap-2"):
            provider_sel = ui.select(
                provider_options,
                label=t("claim_form.provider"),
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
        selected_claimant_id: list[int | None] = [existing.get("claimant_id") if prefill else None]

        ui.label(t("claim_form.claimant_label")).classes("text-xs text-gray-500 -mb-1")
        badge_row = ui.row().classes("w-full flex-wrap gap-2 items-center")

        def render_claimant_badges() -> None:
            badge_row.clear()
            with badge_row:
                for c in db.list_claimants():
                    cid, name, color = c["id"], c["name"], c["color"] or "#6366f1"
                    selected = selected_claimant_id[0] == cid
                    opacity = "1" if selected else "0.3"
                    badge_el = ui.element("span").style(
                        f"background:{color};color:#fff;font-size:0.8rem;"
                        f"padding:4px 10px;border-radius:999px;cursor:pointer;"
                        f"user-select:none;opacity:{opacity}"
                    )
                    with badge_el:
                        ui.label(name).style("color:#fff;font-size:0.8rem")

                    def on_badge_click(cid=cid):
                        selected_claimant_id[0] = cid
                        render_claimant_badges()

                    badge_el.on("click", on_badge_click)

        def on_claimant_created(new_id: int, name: str, color: str = "#6366f1") -> None:
            selected_claimant_id[0] = new_id
            render_claimant_badges()

        render_claimant_badges()

        amount = ui.number(
            t("claim_form.amount"), format="%.2f",
            value=existing["amount"] if prefill else None,
        ).classes("w-full")

        default_date = (datetime.utcnow().date() - timedelta(days=1)).isoformat()
        visit = ui.input(
            t("claim_form.visit_date"),
            value=existing["visit_date"] if editing else default_date,
        ).props("type=date").classes("w-full")

        bill = ui.input(
            t("claim_form.bill_date"),
            value=(existing.get("bill_date") or existing["visit_date"]) if editing else default_date,
        ).props("type=date").classes("w-full")

        def sync_bill_date() -> None:
            if bill.value == "" or not editing:
                bill.value = visit.value

        visit.on("change", lambda _: sync_bill_date())

        # Portal reference numbers - handy once a claim is submitted.
        public_ref = ui.input(
            t("claim_form.public_ref"),
            value=existing.get("public_ref") or "" if prefill else "",
        ).classes("w-full")
        private_ref = ui.input(
            t("claim_form.private_ref"),
            value=existing.get("private_ref") or "" if prefill else "",
        ).classes("w-full")

        notes = ui.textarea(
            t("claim_form.notes"),
            value=existing["notes"] if prefill else "",
        ).classes("w-full")

        def save() -> None:
            if not title.value or not title.value.strip():
                ui.notify(t("claim_form.title_required"), type="warning")
                return
            if not selected_claimant_id[0]:
                ui.notify(t("claim_form.claimant_required"), type="warning")
                return
            fields = dict(
                title=title.value.strip(),
                provider_id=provider_sel.value,
                amount=amount.value,
                currency="€",
                visit_date=visit.value or "",
                bill_date=bill.value or "",
                notes=(notes.value or "").strip(),
                public_ref=(public_ref.value or "").strip(),
                private_ref=(private_ref.value or "").strip(),
                claimant_id=selected_claimant_id[0],
            )
            if editing:
                db.update_claim(existing["id"], **fields)
                ui.notify(t("claim_form.updated"), type="positive")
            else:
                new_id = db.create_claim(**fields)
                state["open_id"] = new_id
                ui.notify(t("claim_form.duplicated") if dupe_mode else t("claim_form.saved"), type="positive")
            dialog.close()
            refresh_page()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(t("common.cancel"), on_click=dialog.close).props("flat")
            ui.button(t("common.save") if editing else t("common.create"), on_click=save) \
                .props("color=primary")
    dialog.open()


def move_dialog(claim: dict, transition: dict) -> None:
    """Confirm a stage move, optionally uploading a confirmation document."""
    # A simple move with no document - just do it.
    if not transition["needs_doc"]:
        db.move_claim(claim["id"], transition["to"])
        ui.notify(t("move.moved", stage=t(STAGE_KEYS[transition["to"]])), type="positive")
        refresh_page()
        return

    uploaded: dict = {"name": None, "content": None}

    with ui.dialog() as dialog, ui.card().classes("w-96 gap-2"):
        label_key = TRANSITION_LABEL_KEYS[(claim["stage"], transition["to"])]
        ui.label(t(label_key)).classes("text-lg font-medium")
        hint_key = TRANSITION_HINT_KEYS[(claim["stage"], transition["to"])]
        ui.label(t(hint_key) + ". " +
                 t("move.also_continue")) \
            .classes("text-sm text-gray-600")

        def on_upload(e) -> None:
            uploaded["name"] = e.name
            uploaded["content"] = e.content.read()
            ui.notify(t("move.selected", name=e.name))

        ui.upload(on_upload=on_upload, auto_upload=True,
                  label=t("move.choose_file")).classes("w-full")

        def confirm(with_doc: bool) -> None:
            db.move_claim(claim["id"], transition["to"])
            if with_doc and uploaded["content"] is not None:
                db.add_attachment(
                    claim["id"], uploaded["name"],
                    uploaded["content"], kind="confirmation",
                )
            dialog.close()
            ui.notify(t("move.moved", stage=t(STAGE_KEYS[transition["to"]])),
                      type="positive")
            refresh_page()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(t("common.cancel"), on_click=dialog.close).props("flat")
            ui.button(t("move.continue_without"),
                      on_click=lambda: confirm(False)).props("flat")
            ui.button(t("move.confirm"),
                      on_click=lambda: confirm(True)).props("color=primary")
    dialog.open()


def upload_dialog(claim_id: str) -> None:
    """Open a dialog to attach one or more documents to a claim."""
    doc_types = {
        "bill":           t("doc_label.bill"),
        "prescription":   t("doc_label.prescription"),
        "bank_statement": t("doc_label.bank_statement"),
        "other":          t("doc_label.other"),
    }
    uploaded_files: list[str] = []
    needs_refresh = [False]

    with ui.dialog() as dialog, ui.card().classes("w-96 gap-2"):
        ui.label(t("upload.title")).classes("text-lg font-medium")
        kind_sel = ui.select(doc_types, value="bill", label=t("upload.kind_label")).classes("w-full")

        uploaded_list = ui.column().classes("w-full gap-1")

        async def on_upload(e) -> None:
            content = await e.file.read()
            db.add_attachment(claim_id, e.file.name, content, kind=kind_sel.value)
            uploaded_files.append(e.file.name)
            needs_refresh[0] = True
            with uploaded_list:
                ui.label(f"✓ {e.file.name} ({doc_types[kind_sel.value]})").classes("text-sm text-green-700")
            ui.notify(t("upload.attached"), type="positive")

        ui.upload(on_upload=on_upload, auto_upload=True, multiple=True) \
            .classes("w-full")

        def on_close() -> None:
            dialog.close()
            if needs_refresh[0]:
                refresh_page()

        ui.button(t("upload.done"), on_click=on_close).props("flat")
    dialog.open()


def confirm_delete_dialog(claim: dict) -> None:
    """Ask for confirmation before permanently deleting a claim."""
    atts = db.list_attachments(claim["id"])
    with ui.dialog() as dialog, ui.card().classes("w-96 gap-2"):
        ui.label(t("delete.title")).classes("text-lg font-medium")
        ui.label(t("delete.body", title=claim["title"], n=len(atts))) \
            .classes("text-sm text-gray-600")

        def do_delete() -> None:
            db.delete_claim(claim["id"])
            if state["open_id"] == claim["id"]:
                state["open_id"] = None
            dialog.close()
            ui.notify(t("delete.notified"), type="warning")
            refresh_page()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(t("common.cancel"), on_click=dialog.close).props("flat")
            ui.button(t("delete.confirm"), on_click=do_delete) \
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

def open_retype_dialog(att_id: str, current_kind: str) -> None:
    """Dialog to change the document type of an existing attachment."""
    doc_types = {
        "bill":           t("doc_label.bill"),
        "prescription":   t("doc_label.prescription"),
        "bank_statement": t("doc_label.bank_statement"),
        "confirmation":   t("doc_label.confirmation"),
        "other":          t("doc_label.other"),
    }
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-4"):
        ui.label(t("attachment.change_kind")).classes("text-lg font-medium")
        kind_sel = ui.select(doc_types, value=current_kind,
                             label=t("upload.kind_label")).classes("w-full")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(t("common.cancel"), on_click=dialog.close).props("flat")

            def save() -> None:
                db.update_attachment_kind(att_id, kind_sel.value)
                dialog.close()
                ui.notify(t("attachment.kind_updated"), type="positive")
                refresh_page()

            ui.button(t("common.save"), on_click=save).props("color=primary")
    dialog.open()


def build_attachment_row(att: dict) -> None:
    """Render one attachment line inside a claim's detail panel."""
    with ui.row().classes("items-center w-full gap-2 p-2 "
                          "border rounded bg-white"):
        icon = "receipt_long" if att["kind"] == "bill" else "description"
        ui.icon(icon).classes("text-gray-500")
        ui.link(att["name"], f"/attachment/{att['id']}", new_tab=True) \
            .classes("flex-1 truncate")
        ui.label(fmt_size(att["size"])).classes("text-xs text-gray-400")

        badge = ui.badge(t(f"doc_kind.{att['kind']}")).props("color=grey-4 text-color=grey-9") \
            .style("cursor:pointer") \
            .tooltip(t("attachment.click_to_change_kind"))

        def on_badge_click(att_id=att["id"], kind=att["kind"]) -> None:
            open_retype_dialog(att_id, kind)

        badge.on("click", on_badge_click)

        def remove(att_id=att["id"]) -> None:
            db.delete_attachment(att_id)
            ui.notify(t("attachment.removed"))
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
                ui.label(t("detail.next_step")).classes(
                    "text-xs font-bold text-green-800")
                with ui.row().classes("gap-2 flex-wrap"):
                    for tr in transitions:
                        label_key = TRANSITION_LABEL_KEYS[(claim["stage"], tr["to"])]
                        ui.button(
                            t(label_key),
                            on_click=lambda tr=tr: move_dialog(claim, tr),
                        ).props("color=primary size=sm")
        else:
            with ui.card().classes("w-full bg-gray-100"):
                ui.label(t("detail.archived_msg")) \
                    .classes("text-sm text-gray-600")

        # ---- two columns: attachments + history --------------------------
        with ui.row().classes("w-full gap-6 items-start"):

            # attachments column
            with ui.column().classes("flex-1 gap-2 min-w-0"):
                ui.label(t("detail.attachments")).classes(
                    "text-xs font-bold text-gray-400")
                attachments = db.list_attachments(claim["id"])
                if attachments:
                    for a in attachments:
                        build_attachment_row(a)
                else:
                    ui.label(t("detail.no_documents")) \
                        .classes("text-sm text-gray-400")
                with ui.row().classes("gap-2"):
                    ui.button(
                        t("detail.add_document_btn"),
                        on_click=lambda c=claim: upload_dialog(c["id"]),
                    ).props("outline size=sm")

            # history column
            with ui.column().classes("flex-1 gap-1 min-w-0"):
                ui.label(t("detail.history")).classes(
                    "text-xs font-bold text-gray-400")
                for h in db.list_history(claim["id"]):
                    with ui.row().classes("items-start gap-1 mb-1"):
                        def remove_entry(e, entry_id=h["id"]) -> None:
                            if not e.args.get('shiftKey'):
                                return
                            db.delete_history_entry(entry_id)
                            refresh_page()
                        ui.button(icon="close") \
                            .on('click', remove_entry) \
                            .props("flat round dense size=xs").classes("text-gray-300 mt-0.5") \
                            .tooltip(t("detail.shift_click_to_delete"))
                        with ui.column().classes("gap-0"):
                            ui.label(h["text"]).classes("text-sm")
                            ui.label(fmt_datetime(h["ts"])) \
                                .classes("text-xs text-gray-400")

        # ---- footer: edit + delete ---------------------------------------
        with ui.row().classes("w-full justify-between border-t pt-2"):
            with ui.row().classes("gap-1"):
                ui.button(t("detail.edit_details"),
                          on_click=lambda: claim_form_dialog(claim)) \
                    .props("flat size=sm")
                ui.button(t("detail.duplicate"),
                          on_click=lambda: claim_form_dialog(claim, dupe_mode=True)) \
                    .props("flat size=sm")
            ui.button(t("detail.delete_claim"),
                      on_click=lambda: confirm_delete_dialog(claim)) \
                .props("flat color=negative size=sm")


def build_claim_card(claim: dict) -> None:
    """Render a single collapsible claim card."""
    is_open = state["open_id"] == claim["id"]
    color = db.STAGE_COLORS[claim["stage"]]
    stale = db.is_stale(claim)
    age = db.days_in_stage(claim)
    age_label = t("card.today") if age == 0 else t("card.days_in_stage", n=age)

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
                meta.append(t("card.opened", date=fmt_date(claim["created_at"])))
                ui.label("  ·  ".join(meta)) \
                    .classes("text-xs text-gray-500 truncate")
                dates = []
                if claim.get("visit_date"):
                    dates.append(t("card.visited", date=fmt_date(claim["visit_date"])))
                if claim.get("bill_date"):
                    dates.append(t("card.billed", date=fmt_date(claim["bill_date"])))
                if dates:
                    ui.label("  /  ".join(dates)) \
                        .classes("text-xs text-gray-400 truncate")

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
                    ui.badge(t(STAGE_KEYS[claim["stage"]]), color=color)
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
        (t("metric.active"), str(s["active"]), t("metric.total_count", n=s["total"]), False),
        (t("metric.attention"), str(s["stale"]), t("metric.pending_too_long"), s["stale"] > 0),
        (t("metric.archived"), str(s["archived"]), t("metric.completed"), False),
    ]
    with ui.row().classes("w-full gap-3 no-wrap items-stretch"):
        # Outstanding card — per-claimant rows only
        with ui.card().classes("flex-1 gap-0"):
            ui.label(t("metric.outstanding")).classes("text-xs font-bold text-gray-400")
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
            ui.label(t("board.no_claims")).classes("text-lg text-gray-400")
            ui.label(t("board.no_claims_hint")) \
                .classes("text-sm text-gray-400")
        return

    if not claims:
        ui.label(t("board.no_matches")) \
            .classes("text-gray-400 py-16 text-center w-full")
        return

    for stage_id in db.STAGE_ORDER:
        group = [c for c in claims if c["stage"] == stage_id]
        if not group:
            continue
        with ui.column().classes("w-full gap-2 mb-4"):
            with ui.row().classes("items-baseline gap-2 w-full"):
                ui.label(t(STAGE_KEYS[stage_id])) \
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

    options = {
        "active": t("toolbar.active", n=counts.get("active", 0)),
        "all":    t("toolbar.all_stages", n=counts.get("all", 0)),
        **{k: f"{t(STAGE_KEYS[k])} ({counts.get(k, 0)})" for k in db.STAGE_ORDER},
    }

    with ui.row().classes("w-full gap-2 items-center no-wrap"):
        search = ui.input(
            placeholder=t("toolbar.search_placeholder"),
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
# Language helper
# --------------------------------------------------------------------------

def _set_lang(lang: str) -> None:
    state["lang"] = lang
    ui.navigate.to(ui.context.client.page.path)


# --------------------------------------------------------------------------
# Main page
# --------------------------------------------------------------------------

_DATE_WHEEL_JS = """
<script>
document.addEventListener('wheel', function(e) {
    if (e.target.type === 'date') {
        e.preventDefault();
        if (e.deltaY < 0) { e.target.stepUp(); } else { e.target.stepDown(); }
        e.target.dispatchEvent(new Event('change', { bubbles: true }));
    }
}, { passive: false });
</script>
"""


@ui.page("/")
def main_page() -> None:
    ui.colors(primary="#2c5f4f")
    ui.add_head_html("<style>body{background:#f4f2ec}</style>")
    ui.add_head_html(_DATE_WHEEL_JS)

    with ui.column().classes("w-full max-w-4xl mx-auto p-6 gap-4"):

        # ---- header ------------------------------------------------------
        with ui.row().classes("w-full items-end justify-between "
                              "border-b-2 border-gray-800 pb-3"):
            with ui.column().classes("gap-0"):
                ui.label(t("app.title")) \
                    .classes("text-2xl font-medium")
                ui.label(t("app.subtitle")) \
                    .classes("text-xs text-gray-500")
            with ui.row().classes("gap-2 items-center"):
                def do_backup() -> None:
                    target = db.backup_to(db.DATA_DIR / "backups")
                    ui.notify(t("header.backup_notify", path=str(target)),
                              type="positive")
                ui.button(t("header.backup"), on_click=do_backup).props("outline")
                ui.button(t("header.settings"), on_click=lambda: ui.navigate.to("/settings")).props("outline")
                ui.button(t("header.new_claim"),
                          on_click=lambda: claim_form_dialog(None)) \
                    .props("color=primary")
                with ui.button_group().props("outline"):
                    ui.button("DE", on_click=lambda: _set_lang("de")) \
                        .props(f"{'color=primary' if state['lang'] == 'de' else 'flat'} size=sm")
                    ui.button("EN", on_click=lambda: _set_lang("en")) \
                        .props(f"{'color=primary' if state['lang'] == 'en' else 'flat'} size=sm")

        # ---- metrics -----------------------------------------------------
        metrics_row()

        # ---- toolbar -----------------------------------------------------
        toolbar()

        # ---- board -------------------------------------------------------
        claim_board()

        # ---- footer ------------------------------------------------------
        ui.label(f"build {GIT_COMMIT}") \
            .classes("text-xs text-gray-400 w-full text-right pt-4")


# --------------------------------------------------------------------------
# Settings page
# --------------------------------------------------------------------------

@ui.page("/settings")
def settings_page() -> None:
    ui.colors(primary="#2c5f4f")
    ui.add_head_html("<style>body{background:#f4f2ec}</style>")
    ui.add_head_html(_DATE_WHEEL_JS)

    with ui.column().classes("w-full max-w-3xl mx-auto p-6 gap-6"):

        with ui.row().classes("w-full items-center justify-between border-b-2 border-gray-800 pb-3"):
            with ui.row().classes("items-center gap-4"):
                ui.label(t("header.settings")).classes("text-2xl font-medium")
                with ui.button_group().props("outline"):
                    ui.button("DE", on_click=lambda: _set_lang("de")) \
                        .props(f"{'color=primary' if state['lang'] == 'de' else 'flat'} size=sm")
                    ui.button("EN", on_click=lambda: _set_lang("en")) \
                        .props(f"{'color=primary' if state['lang'] == 'en' else 'flat'} size=sm")
            ui.button(t("settings.back"), on_click=lambda: ui.navigate.to("/")).props("flat")

        # ---- Claimants section -------------------------------------------
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center justify-between mb-2"):
                ui.label(t("settings.claimants_section")).classes("text-lg font-semibold")
                ui.button(icon="add", on_click=lambda: _add_claimant_inline(claimants_col)) \
                    .props("flat round dense").tooltip(t("claimant.add"))

            claimants_col = ui.column().classes("w-full gap-1")
            _render_claimants(claimants_col)

        # ---- Providers section -------------------------------------------
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center justify-between mb-2"):
                ui.label(t("settings.providers_section")).classes("text-lg font-semibold")
                ui.button(icon="add", on_click=lambda: _add_provider_inline(providers_col)) \
                    .props("flat round dense").tooltip(t("provider.add"))

            providers_col = ui.column().classes("w-full gap-1")
            _render_providers(providers_col)

        # ---- Staleness thresholds section --------------------------------
        with ui.card().classes("w-full"):
            ui.label(t("settings.staleness_title")).classes("text-lg font-semibold mb-2")
            ui.label(
                t("settings.staleness_desc")
            ).classes("text-sm text-gray-500 mb-3")

            public_input = ui.number(
                t("settings.staleness_public"),
                value=db.STALE_DAYS["public_pending"],
                min=1, step=1, format="%.0f",
            ).classes("w-full")
            private_input = ui.number(
                t("settings.staleness_private"),
                value=db.STALE_DAYS["private_pending"],
                min=1, step=1, format="%.0f",
            ).classes("w-full")

            def save_stale_days():
                try:
                    pub = int(public_input.value)
                    priv = int(private_input.value)
                    if pub < 1 or priv < 1:
                        raise ValueError
                except (TypeError, ValueError):
                    ui.notify(t("settings.staleness_invalid"), type="warning")
                    return
                db.set_stale_days(pub, priv)
                ui.notify(t("settings.staleness_updated"), type="positive")

            with ui.row().classes("w-full justify-end mt-2"):
                ui.button(t("common.save"), on_click=save_stale_days).props("color=primary")


def _render_claimants(container: ui.column) -> None:
    container.clear()
    with container:
        claimants = db.list_claimants()
        if not claimants:
            ui.label(t("settings.no_claimants")).classes("text-sm text-gray-400")
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
        ui.label(t("claimant.new")).classes("text-lg font-medium")
        name_input = ui.input(t("claimant.full_name")).classes("w-full")
        color_input = ui.color_input(t("claimant.badge_color"), value="#6366f1", preview=True).classes("w-full")
        color_input.picker.q_color.props('default-view="palette"')

        def save():
            name = (name_input.value or "").strip()
            if not name:
                ui.notify(t("common.name_required"), type="warning")
                return
            try:
                db.add_claimant(name, color=color_input.value or "#6366f1")
            except Exception:
                ui.notify(t("claimant.already_exists"), type="warning")
                return
            dialog.close()
            _render_claimants(container)

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(t("common.cancel"), on_click=dialog.close).props("flat")
            ui.button(t("common.add"), on_click=save).props("color=primary")
    dialog.open()


def _edit_claimant_inline(container: ui.column, c: dict) -> None:
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label(t("claimant.edit")).classes("text-lg font-medium")
        name_input = ui.input(t("claimant.full_name"), value=c["name"]).classes("w-full")
        color_input = ui.color_input(t("claimant.badge_color"), value=c["color"] or "#6366f1", preview=True).classes("w-full")
        color_input.picker.q_color.props('default-view="palette"')

        def save():
            name = (name_input.value or "").strip()
            if not name:
                ui.notify(t("common.name_required"), type="warning")
                return
            try:
                db.update_claimant(c["id"], name, color_input.value or "#6366f1")
            except Exception:
                ui.notify(t("common.name_taken"), type="warning")
                return
            dialog.close()
            _render_claimants(container)

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(t("common.cancel"), on_click=dialog.close).props("flat")
            ui.button(t("common.save"), on_click=save).props("color=primary")
    dialog.open()


def _render_providers(container: ui.column) -> None:
    container.clear()
    with container:
        providers = db.list_providers()
        if not providers:
            ui.label(t("settings.no_providers")).classes("text-sm text-gray-400")
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
        ui.label(t("provider.new")).classes("text-lg font-medium")
        name_input = ui.input(t("common.name")).classes("w-full")

        def save():
            name = (name_input.value or "").strip()
            if not name:
                ui.notify(t("common.name_required"), type="warning")
                return
            try:
                db.add_provider(name)
            except Exception:
                ui.notify(t("provider.already_exists"), type="warning")
                return
            dialog.close()
            _render_providers(container)

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(t("common.cancel"), on_click=dialog.close).props("flat")
            ui.button(t("common.add"), on_click=save).props("color=primary")
    dialog.open()


def _edit_provider_inline(container: ui.column, p: dict) -> None:
    with ui.dialog() as dialog, ui.card().classes("w-80 gap-2"):
        ui.label(t("provider.edit")).classes("text-lg font-medium")
        name_input = ui.input(t("common.name"), value=p["name"]).classes("w-full")

        def save():
            name = (name_input.value or "").strip()
            if not name:
                ui.notify(t("common.name_required"), type="warning")
                return
            try:
                db.update_provider(p["id"], name)
            except Exception:
                ui.notify(t("common.name_taken"), type="warning")
                return
            dialog.close()
            _render_providers(container)

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(t("common.cancel"), on_click=dialog.close).props("flat")
            ui.button(t("common.save"), on_click=save).props("color=primary")
    dialog.open()


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def run() -> None:
    """Initialise the database and start the NiceGUI server."""
    import os
    db.init_db()
    check_translations()
    ui.run(
        title=t("app.title"),
        port=8080,
        reload=os.getenv("CLAIMS_DEV", "0") == "1",
        show=os.getenv("CLAIMS_DEV", "0") == "1",
        favicon="💲",
    )


# `python -m claim_tracker.app` and `python app.py` both work.
if __name__ in {"__main__", "__mp_main__"}:
    run()

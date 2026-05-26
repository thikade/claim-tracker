"""German / English translations for the claims tracker UI.

Translation tables are keyed by short symbolic keys (e.g. "upload.title").
Both languages have explicit entries — a missing key logs a warning and
falls back through English to the key string itself, so a missing entry
is loud (in the log) but never crashes the UI.

Stage codes and transitions live in `db.py` as plain enums; the mapping
from those codes to translation keys is owned here (STAGE_KEYS,
TRANSITION_LABEL_KEYS, TRANSITION_HINT_KEYS) so `db.py` stays UI-agnostic.
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


# Stage code → translation key.
STAGE_KEYS: dict[str, str] = {
    "scanned":         "stage.scanned",
    "public_pending":  "stage.public_pending",
    "private_pending": "stage.private_pending",
    "archived":        "stage.archived",
}

# (from_stage, to_stage) → button label key for the transition.
TRANSITION_LABEL_KEYS: dict[tuple[str, str], str] = {
    ("scanned",         "public_pending"):  "transition.submit_public",
    ("scanned",         "private_pending"): "transition.submit_private",
    ("scanned",         "archived"):        "transition.archive_direct",
    ("public_pending",  "private_pending"): "transition.public_processed",
    ("public_pending",  "archived"):        "transition.archive_direct",
    ("private_pending", "archived"):        "transition.private_processed",
}

# (from_stage, to_stage) → doc-hint key. Only populated for transitions
# whose move_dialog prompts for a confirmation document upload.
TRANSITION_HINT_KEYS: dict[tuple[str, str], str] = {
    ("public_pending",  "private_pending"): "move.public_hint",
    ("private_pending", "archived"):        "move.private_hint",
}


_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # Application chrome
        "app.title":     "Insurance Claim Tracker",
        "app.subtitle":  "Medical bills · public health service · private insurance",

        # Header buttons
        "header.backup":         "Backup",
        "header.settings":       "Settings",
        "header.new_claim":      "+ New claim",
        "header.backup_notify":  "Backup written to {path}",

        # Dashboard metric cards
        "metric.outstanding":       "OUTSTANDING",
        "metric.active":            "ACTIVE CLAIMS",
        "metric.attention":         "NEED ATTENTION",
        "metric.archived":          "ARCHIVED",
        "metric.total_count":       "{n} total",
        "metric.pending_too_long":  "pending too long",
        "metric.completed":         "completed",

        # Toolbar
        "toolbar.search_placeholder": "Search by title, provider, claimant or notes…",
        "toolbar.active":             "Active claims ({n})",
        "toolbar.all_stages":         "All stages ({n})",

        # Claim stages (referenced via STAGE_KEYS)
        "stage.scanned":         "Claim created",
        "stage.public_pending":  "Public claim pending",
        "stage.private_pending": "Private claim pending",
        "stage.archived":        "Archived",

        # Claim card summary
        "card.opened":         "opened {date}",
        "card.visited":        "visited {date}",
        "card.billed":         "billed {date}",
        "card.today":          "today",
        "card.days_in_stage":  "{n}d in stage",

        # Claim detail panel
        "detail.next_step":              "NEXT STEP",
        "detail.archived_msg":           "This claim is archived. Nothing further to do.",
        "detail.attachments":            "ATTACHMENTS",
        "detail.no_documents":           "No documents yet.",
        "detail.add_document_btn":       "+ Add document",
        "detail.history":                "HISTORY",
        "detail.shift_click_to_delete":  "Shift-click to delete",
        "detail.edit_details":           "Edit details",
        "detail.duplicate":              "Duplicate",
        "detail.delete_claim":           "Delete claim",

        # Stage transitions (referenced via TRANSITION_LABEL_KEYS)
        "transition.submit_public":     "Submit to public health portal",
        "transition.submit_private":    "Submit directly to private insurer",
        "transition.archive_direct":    "Archive directly",
        "transition.public_processed":  "Public claim processed - file private claim",
        "transition.private_processed": "Private claim processed - archive",

        # Move-stage dialog
        "move.public_hint":       "Attach the public health service confirmation",
        "move.private_hint":      "Attach the private insurer confirmation",
        "move.also_continue":     "You can also continue without it and add the document later.",
        "move.choose_file":       "Choose confirmation file",
        "move.continue_without":  "Continue without",
        "move.confirm":           "Confirm step",
        "move.moved":             "Moved to {stage}",
        "move.selected":          "Selected: {name}",

        # Attachment kind — raw DB values (used in the small badge on each row).
        # Intentionally separate from doc_label.* below: they share German text
        # but feed different call sites and may diverge in future.
        "doc_kind.bill":            "bill",
        "doc_kind.prescription":    "prescription",
        "doc_kind.bank_statement":  "bank_statement",
        "doc_kind.confirmation":    "confirmation",
        "doc_kind.other":           "other",

        # Attachment kind — display labels (used in select dropdowns)
        "doc_label.bill":            "Medical bill",
        "doc_label.prescription":    "Prescription",
        "doc_label.bank_statement":  "Bank statement",
        "doc_label.confirmation":    "Confirmation",
        "doc_label.other":           "Other",

        # Attachment row controls
        "attachment.click_to_change_kind":  "Click to change document type",
        "attachment.change_kind":           "Change document type",
        "attachment.kind_updated":          "Document type updated",
        "attachment.removed":               "Document removed",

        # Upload-documents dialog
        "upload.title":       "Add documents",
        "upload.kind_label":  "Document type",
        "upload.attached":    "Document attached",
        "upload.done":        "Done",

        # Delete-claim confirmation dialog
        "delete.title":     "Delete claim?",
        "delete.body":      '"{title}" and its {n} document(s) will be permanently removed from the database and disk.',
        "delete.confirm":   "Delete permanently",
        "delete.notified":  "Claim deleted",

        # Claimants
        "claimant.new":                "New claimant",
        "claimant.edit":               "Edit claimant",
        "claimant.delete":             "Delete claimant",
        "claimant.full_name":          "Full name",
        "claimant.badge_color":        "Badge color",
        "claimant.badge_color_named":  "Badge color — {name}",
        "claimant.no_unassigned":      "No unassigned claimants.",
        "claimant.add":                "Add claimant",
        "claimant.already_exists":     "Claimant already exists",

        # Providers
        "provider.new":             "New provider",
        "provider.edit":            "Edit provider",
        "provider.delete":          "Delete provider",
        "provider.no_unassigned":   "No unassigned providers.",
        "provider.add":             "Add provider",
        "provider.already_exists":  "Provider already exists",

        # Create / edit / duplicate claim form
        "claim_form.title":              "Title",
        "claim_form.title_placeholder":  "e.g. Dr. Müller - physiotherapy",
        "claim_form.title_required":     "Please enter a title",
        "claim_form.provider":           "Provider / doctor",
        "claim_form.claimant_label":     "Claimant *",
        "claim_form.claimant_required":  "Please select a claimant",
        "claim_form.amount":             "Amount (€)",
        "claim_form.visit_date":         "Visit date",
        "claim_form.bill_date":          "Bill date",
        "claim_form.public_ref":         "Public insurer reference",
        "claim_form.private_ref":        "Private insurer reference",
        "claim_form.notes":              "Notes",
        "claim_form.edit_title":         "Edit claim",
        "claim_form.new_title":          "New claim",
        "claim_form.duplicate_title":    "Duplicate claim",
        "claim_form.saved":              "Claim saved",
        "claim_form.updated":            "Claim updated",
        "claim_form.duplicated":         "Claim duplicated",

        # Claim board empty states
        "board.no_claims":       "No claims yet.",
        "board.no_claims_hint":  'Click "New claim" to scan your first medical bill.',
        "board.no_matches":      "No claims match your search.",

        # Settings page
        "settings.back":               "← Back",
        "settings.claimants_section":  "Claimants",
        "settings.no_claimants":       "No claimants yet.",
        "settings.providers_section":  "Providers",
        "settings.no_providers":       "No providers yet.",
        "settings.staleness_title":    "Staleness thresholds",
        "settings.staleness_desc":     "A claim is flagged as stale when it has been in a pending stage longer than these limits.",
        "settings.staleness_public":   "Public insurer pending (days)",
        "settings.staleness_private":  "Private insurer pending (days)",
        "settings.staleness_invalid":  "Please enter valid positive numbers",
        "settings.staleness_updated":  "Staleness thresholds updated",

        # Reusable common terms
        "common.cancel":         "Cancel",
        "common.save":           "Save",
        "common.add":            "Add",
        "common.close":          "Close",
        "common.create":         "Create",
        "common.name":           "Name",
        "common.name_required":  "Please enter a name",
        "common.name_taken":     "Name already taken",
        "common.deleted_named":  "{name} deleted",
    },

    "de": {
        "app.title":     "Kostenerstattungs-Tracker",
        "app.subtitle":  "Arztkosten · Gesetzliche KV · Private KV",

        "header.backup":         "Sicherung",
        "header.settings":       "Einstellungen",
        "header.new_claim":      "+ Neuer Antrag",
        "header.backup_notify":  "Sicherung gespeichert unter {path}",

        "metric.outstanding":       "AUSSTEHEND",
        "metric.active":            "AKTIVE ANTRÄGE",
        "metric.attention":         "HANDLUNGSBEDARF",
        "metric.archived":          "ARCHIVIERT",
        "metric.total_count":       "{n} gesamt",
        "metric.pending_too_long":  "zu lange offen",
        "metric.completed":         "abgeschlossen",

        "toolbar.search_placeholder": "Nach Titel, Anbieter, Person oder Notizen suchen…",
        "toolbar.active":             "Aktive Anträge ({n})",
        "toolbar.all_stages":         "Alle Phasen ({n})",

        "stage.scanned":         "Antrag erstellt",
        "stage.public_pending":  "ÖKV-Antrag ausstehend",
        "stage.private_pending": "PKV-Antrag ausstehend",
        "stage.archived":        "Archiviert",

        "card.opened":         "erstellt {date}",
        "card.visited":        "Besuch {date}",
        "card.billed":         "Rechnung {date}",
        "card.today":          "heute",
        "card.days_in_stage":  "{n}T in Phase",

        "detail.next_step":              "NÄCHSTER SCHRITT",
        "detail.archived_msg":           "Dieser Antrag ist archiviert. Nichts weiteres erforderlich.",
        "detail.attachments":            "DOKUMENTE",
        "detail.no_documents":           "Noch keine Dokumente.",
        "detail.add_document_btn":       "+ Dokument hinzufügen",
        "detail.history":                "VERLAUF",
        "detail.shift_click_to_delete":  "Shift+Klick zum Löschen",
        "detail.edit_details":           "Details bearbeiten",
        "detail.duplicate":              "Duplizieren",
        "detail.delete_claim":           "Antrag löschen",

        "transition.submit_public":     "Bei ÖKV einreichen",
        "transition.submit_private":    "Direkt bei PKV einreichen",
        "transition.archive_direct":    "Direkt archivieren",
        "transition.public_processed":  "ÖKV bearbeitet – PKV-Antrag einreichen",
        "transition.private_processed": "PKV bearbeitet – archivieren",

        "move.public_hint":       "ÖKV-Bestätigung anhängen",
        "move.private_hint":      "PKV-Bestätigung anhängen",
        "move.also_continue":     "Sie können auch ohne Dokument fortfahren und es später hinzufügen.",
        "move.choose_file":       "Bestätigungsdatei auswählen",
        "move.continue_without":  "Ohne Dokument fortfahren",
        "move.confirm":           "Schritt bestätigen",
        "move.moved":             "Verschoben zu {stage}",
        "move.selected":          "Ausgewählt: {name}",

        "doc_kind.bill":            "Arztrechnung",
        "doc_kind.prescription":    "Verschreibung",
        "doc_kind.bank_statement":  "Kontoauszug",
        "doc_kind.confirmation":    "Bestätigung",
        "doc_kind.other":           "Sonstiges",

        "doc_label.bill":            "Arztrechnung",
        "doc_label.prescription":    "Verschreibung",
        "doc_label.bank_statement":  "Kontoauszug",
        "doc_label.confirmation":    "Bestätigung",
        "doc_label.other":           "Sonstiges",

        "attachment.click_to_change_kind":  "Klicken zum Ändern des Dokumenttyps",
        "attachment.change_kind":           "Dokumenttyp ändern",
        "attachment.kind_updated":          "Dokumenttyp aktualisiert",
        "attachment.removed":               "Dokument entfernt",

        "upload.title":       "Dokumente hinzufügen",
        "upload.kind_label":  "Dokumenttyp",
        "upload.attached":    "Dokument hinzugefügt",
        "upload.done":        "Fertig",

        "delete.title":     "Antrag löschen?",
        "delete.body":      '„{title}“ und {n} Dokument(e) werden dauerhaft aus der Datenbank und dem Datenträger gelöscht.',
        "delete.confirm":   "Dauerhaft löschen",
        "delete.notified":  "Antrag gelöscht",

        "claimant.new":                "Neue Person",
        "claimant.edit":               "Person bearbeiten",
        "claimant.delete":             "Person löschen",
        "claimant.full_name":          "Vollständiger Name",
        "claimant.badge_color":        "Abzeichenfarbe",
        "claimant.badge_color_named":  "Abzeichenfarbe — {name}",
        "claimant.no_unassigned":      "Keine nicht zugewiesenen Personen.",
        "claimant.add":                "Person hinzufügen",
        "claimant.already_exists":     "Person existiert bereits",

        "provider.new":             "Neuer Anbieter",
        "provider.edit":            "Anbieter bearbeiten",
        "provider.delete":          "Anbieter löschen",
        "provider.no_unassigned":   "Keine nicht zugewiesenen Anbieter.",
        "provider.add":             "Anbieter hinzufügen",
        "provider.already_exists":  "Anbieter existiert bereits",

        "claim_form.title":              "Bezeichnung",
        "claim_form.title_placeholder":  "z.B. Dr. Müller – Physiotherapie",
        "claim_form.title_required":     "Bitte Bezeichnung eingeben",
        "claim_form.provider":           "Arzt / Anbieter",
        "claim_form.claimant_label":     "Person *",
        "claim_form.claimant_required":  "Bitte Person auswählen",
        "claim_form.amount":             "Betrag (€)",
        "claim_form.visit_date":         "Besuchsdatum",
        "claim_form.bill_date":          "Rechnungsdatum",
        "claim_form.public_ref":         "ÖKV-Referenznummer",
        "claim_form.private_ref":        "PKV-Referenznummer",
        "claim_form.notes":              "Notizen",
        "claim_form.edit_title":         "Antrag bearbeiten",
        "claim_form.new_title":          "Neuer Antrag",
        "claim_form.duplicate_title":    "Antrag duplizieren",
        "claim_form.saved":              "Antrag gespeichert",
        "claim_form.updated":            "Antrag aktualisiert",
        "claim_form.duplicated":         "Antrag dupliziert",

        "board.no_claims":       "Noch keine Anträge.",
        "board.no_claims_hint":  'Auf „+ Neuer Antrag“ klicken, um die erste Rechnung zu erfassen.',
        "board.no_matches":      "Keine Anträge gefunden.",

        "settings.back":               "← Zurück",
        "settings.claimants_section":  "Personen",
        "settings.no_claimants":       "Noch keine Personen.",
        "settings.providers_section":  "Anbieter",
        "settings.no_providers":       "Noch keine Anbieter.",
        "settings.staleness_title":    "Überfälligkeits-Fristen",
        "settings.staleness_desc":     "Ein Antrag wird als überfällig markiert, wenn er länger als diese Frist in einer ausstehenden Phase verbleibt.",
        "settings.staleness_public":   "ÖKV ausstehend (Tage)",
        "settings.staleness_private":  "PKV ausstehend (Tage)",
        "settings.staleness_invalid":  "Bitte gültige positive Zahlen eingeben",
        "settings.staleness_updated":  "Fristen aktualisiert",

        "common.cancel":         "Abbrechen",
        "common.save":           "Speichern",
        "common.add":            "Hinzufügen",
        "common.close":          "Schließen",
        "common.create":         "Erstellen",
        "common.name":           "Name",
        "common.name_required":  "Bitte Namen eingeben",
        "common.name_taken":     "Name bereits vergeben",
        "common.deleted_named":  "{name} gelöscht",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    """Return the translation of *key* for the given language.

    Missing keys log a warning and fall back through English to the key
    string itself, so a missing entry surfaces in the log but never
    crashes the UI.
    """
    table = _TRANSLATIONS.get(lang, _TRANSLATIONS["en"])
    text = table.get(key)
    if text is None:
        text = _TRANSLATIONS["en"].get(key, key)
        if text == key:
            log.warning("i18n: unknown key %r", key)
        elif lang != "en":
            log.warning("i18n: missing %s translation for %r", lang, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError) as exc:
            log.warning("i18n format error: key=%r kwargs=%r err=%s", key, kwargs, exc)
            return text
    return text


def check_translations() -> None:
    """Log warnings for any key present in one language but missing in another.

    Run once at startup to surface translation drift during development.
    """
    en_keys = set(_TRANSLATIONS["en"])
    for lang, table in _TRANSLATIONS.items():
        if lang == "en":
            continue
        for k in sorted(en_keys - table.keys()):
            log.warning("i18n: %s missing key %r", lang, k)
        for k in sorted(table.keys() - en_keys):
            log.warning("i18n: %s has orphan key %r (not in en)", lang, k)

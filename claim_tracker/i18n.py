"""German / English translations for the claims tracker UI.

The English text is used as the key. t() falls back to the key itself for
any missing entry, so English requires no explicit entries here.
"""
from __future__ import annotations

_DE: dict[str, str] = {
    # App header
    "Insurance Claim Tracker": "Kostenerstattungs-Tracker",
    "Medical bills · public health service · private insurance": "Arztkosten · Gesetzliche KV · Private KV",

    # Header buttons
    "Backup": "Sicherung",
    "Settings": "Einstellungen",
    "+ New claim": "+ Neuer Antrag",

    # Dashboard metric cards
    "OUTSTANDING": "AUSSTEHEND",
    "ACTIVE CLAIMS": "AKTIVE ANTRÄGE",
    "NEED ATTENTION": "HANDLUNGSBEDARF",
    "ARCHIVED": "ARCHIVIERT",
    "{n} total": "{n} gesamt",
    "pending too long": "zu lange offen",
    "completed": "abgeschlossen",

    # Toolbar
    "Search by title, provider, claimant or notes…": "Nach Titel, Anbieter, Person oder Notizen suchen…",
    "Active claims ({n})": "Aktive Anträge ({n})",
    "All stages ({n})": "Alle Phasen ({n})",

    # Stage names (from db.STAGES)
    "Claim created": "Antrag erstellt",
    "Public claim pending": "ÖKV-Antrag ausstehend",
    "Private claim pending": "PKV-Antrag ausstehend",
    "Archived": "Archiviert",

    # Claim card (collapsed view)
    "opened {date}": "erstellt {date}",
    "visited {date}": "Besuch {date}",
    "billed {date}": "Rechnung {date}",
    "today": "heute",
    "{n}d in stage": "{n}T in Phase",

    # Claim detail panel
    "NEXT STEP": "NÄCHSTER SCHRITT",
    "This claim is archived. Nothing further to do.": "Dieser Antrag ist archiviert. Nichts weiteres erforderlich.",
    "ATTACHMENTS": "DOKUMENTE",
    "No documents yet.": "Noch keine Dokumente.",
    "+ Add document": "+ Dokument hinzufügen",
    "HISTORY": "VERLAUF",
    "Edit details": "Details bearbeiten",
    "Delete claim": "Antrag löschen",

    # Stage transition button labels (from db.TRANSITIONS)
    "Submit to public health portal": "Bei ÖKV einreichen",
    "Submit directly to private insurer": "Direkt bei PKV einreichen",
    "Archive directly": "Direkt archivieren",
    "Public claim processed - file private claim": "ÖKV bearbeitet – PKV-Antrag einreichen",
    "Private claim processed - archive": "PKV bearbeitet – archivieren",

    # Move dialog
    "Attach the public health service confirmation": "ÖKV-Bestätigung anhängen",
    "Attach the private insurer confirmation": "PKV-Bestätigung anhängen",
    "You can also continue without it and add the document later.":
        "Sie können auch ohne Dokument fortfahren und es später hinzufügen.",
    "Choose confirmation file": "Bestätigungsdatei auswählen",
    "Continue without": "Ohne Dokument fortfahren",
    "Confirm step": "Schritt bestätigen",
    "Moved to {stage}": "Verschoben zu {stage}",
    "Selected: {name}": "Ausgewählt: {name}",

    # Document type keys (raw kind values used in badge)
    "bill": "Arztrechnung",
    "prescription": "Verschreibung",
    "bank_statement": "Kontoauszug",
    "confirmation": "Bestätigung",
    "other": "Sonstiges",

    # Document type display labels (used in select dropdowns)
    "Medical bill": "Arztrechnung",
    "Prescription": "Verschreibung",
    "Bank statement": "Kontoauszug",
    "Confirmation": "Bestätigung",
    "Other": "Sonstiges",

    # Attachment
    "Click to change document type": "Klicken zum Ändern des Dokumenttyps",
    "Add document": "Dokument hinzufügen",
    "Document type": "Dokumenttyp",
    "Choose file": "Datei auswählen",
    "Document attached": "Dokument hinzugefügt",
    "Document removed": "Dokument entfernt",
    "Document type updated": "Dokumenttyp aktualisiert",
    "Change document type": "Dokumenttyp ändern",

    # Delete claim dialog
    "Delete claim?": "Antrag löschen?",
    '"{title}" and its {n} document(s) will be permanently removed from the database and disk.':
        '„{title}“ und {n} Dokument(e) werden dauerhaft aus der Datenbank und dem Datenträger gelöscht.',
    "Delete permanently": "Dauerhaft löschen",
    "Claim deleted": "Antrag gelöscht",

    # History
    "Remove this history entry?": "Diesen Verlaufseintrag entfernen?",
    "Remove": "Entfernen",

    # Claimant dialogs
    "New claimant": "Neue Person",
    "Edit claimant": "Person bearbeiten",
    "Delete claimant": "Person löschen",
    "Full name": "Vollständiger Name",
    "Badge color": "Abzeichenfarbe",
    "Badge color — {name}": "Abzeichenfarbe — {name}",
    "No unassigned claimants.": "Keine nicht zugewiesenen Personen.",
    "Add claimant": "Person hinzufügen",
    "Claimant already exists": "Person existiert bereits",
    "{name} deleted": "{name} gelöscht",
    "Claimant *": "Person *",

    # Provider dialogs
    "New provider": "Neuer Anbieter",
    "Edit provider": "Anbieter bearbeiten",
    "Delete provider": "Anbieter löschen",
    "No unassigned providers.": "Keine nicht zugewiesenen Anbieter.",
    "Add provider": "Anbieter hinzufügen",
    "Provider already exists": "Anbieter existiert bereits",

    # Common buttons / validation
    "Cancel": "Abbrechen",
    "Save": "Speichern",
    "Add": "Hinzufügen",
    "Close": "Schließen",
    "Create": "Erstellen",
    "Name": "Name",
    "Please enter a name": "Bitte Namen eingeben",
    "Name already taken": "Name bereits vergeben",
    "Please enter a title": "Bitte Bezeichnung eingeben",
    "Please select a claimant": "Bitte Person auswählen",
    "Claim created": "Antrag erstellt",
    "Claim updated": "Antrag aktualisiert",
    "Backup written to {path}": "Sicherung gespeichert unter {path}",

    # New/edit claim form fields
    "Title": "Bezeichnung",
    "e.g. Dr. Müller - physiotherapy": "z.B. Dr. Müller – Physiotherapie",
    "Provider / doctor": "Arzt / Anbieter",
    "Amount (€)": "Betrag (€)",
    "Visit date": "Besuchsdatum",
    "Bill date": "Rechnungsdatum",
    "Public insurer reference": "ÖKV-Referenznummer",
    "Private insurer reference": "PKV-Referenznummer",
    "Notes": "Notizen",
    "Edit claim": "Antrag bearbeiten",
    "New claim": "Neuer Antrag",

    # Claim board empty states
    "No claims yet.": "Noch keine Anträge.",
    'Click "New claim" to scan your first medical bill.':
        'Auf „+ Neuer Antrag“ klicken, um die erste Rechnung zu erfassen.',
    "No claims match your search.": "Keine Anträge gefunden.",

    # Settings page
    "← Back": "← Zurück",
    "Claimants": "Personen",
    "No claimants yet.": "Noch keine Personen.",
    "Providers": "Anbieter",
    "No providers yet.": "Noch keine Anbieter.",
    "Staleness thresholds": "Überfälligkeits-Fristen",
    "A claim is flagged as stale when it has been in a pending stage longer than these limits.":
        "Ein Antrag wird als überfällig markiert, wenn er länger als diese Frist in einer ausstehenden Phase verbleibt.",
    "Public insurer pending (days)": "ÖKV ausstehend (Tage)",
    "Private insurer pending (days)": "PKV ausstehend (Tage)",
    "Please enter valid positive numbers": "Bitte gültige positive Zahlen eingeben",
    "Staleness thresholds updated": "Fristen aktualisiert",
}


def t(key: str, lang: str, **kwargs) -> str:
    """Return the translation of *key* for the given language.

    Falls back to the key itself when no translation exists, so English needs
    no explicit entries and missing German entries degrade gracefully.
    """
    text = _DE.get(key, key) if lang == "de" else key
    return text.format(**kwargs) if kwargs else text

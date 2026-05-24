# Decision #002 — Datenbank-Technologie

**Timestamp:** 2026-05-24T22:42:00+02:00
**Status:** ACCEPTED
**Importance:** MEDIUM

---

## Fragestellung

Welche Datenbank-Technologie soll für die Chat-Registry verwendet werden?

## Decision Tree

```
START: DB-Technologie wählen
│
├─[Frage 1] Wird ein separater DB-Server benötigt?
│  ├─ JA → PostgreSQL, MySQL
│  └─ NEIN → Embedded DB (SQLite) ausreichend
│             └─ GEWÄHLT: Kein Mehrbenutzer-Betrieb,
│                keine Netzwerk-Zugriffe nötig
│
├─[Frage 2] Wie wichtig ist Portabilität?
│  ├─ SEHR → SQLite (eine Datei)
│  └─ WENIGER → Andere Embedded-DBs
│
└─[Frage 3] MCP-Integration vorhanden?
   └─ JA → SQLite hat MCP-Tool (mcp__sqlite)
      └─ GEWÄHLT: Direkte MCP-Nutzung möglich
```

## Entscheidung

**SQLite**

### Begründung
- Zero-Config: Keine Server-Installation nötig
- Portabel: Eine `.db`-Datei im Hypervisor-Root
- MCP-integriert: `mcp__sqlite` Tool direkt nutzbar
- Ausreichend: Chat-Metadaten sind strukturiert, aber low-volume
- Bewährt: Meistgenutzte Embedded-DB weltweit

## Konsequenzen
- **Positiv:** Keine externe Abhängigkeit, Backup = Datei kopieren
- **Negativ:** Kein Concurrent-Write (nicht benötigt)
- **Neutral:** SQL-Dialekt ist SQLite-spezifisch (Migration zu PostgreSQL später möglich)

---

# Decision #003 — Programmiersprache

**Timestamp:** 2026-05-24T22:43:00+02:00
**Status:** ACCEPTED
**Importance:** MEDIUM

---

## Entscheidung

**Python 3.11+**

### Begründung
- MCP-Tools sind auf Python ausgelegt (Filesystem, SQLite)
- Schnelle Iteration für CLI-Tool
- Rich/Typer Libraries für moderne CLI
- Pydantic für Typ-Validierung
- sqlite3 in Standardbibliothek

---

# Decision #004 — Hypervisor-Verzeichnis-Pfad

**Timestamp:** 2026-05-24T22:44:00+02:00
**Status:** ACCEPTED
**Importance:** HIGH

---

## Decision Tree

```
START: Hypervisor-Pfad festlegen
│
├─[Frage 1] Wo liegen die DeepCode-Chatverzeichnisse?
│  └─ ~/.deepcode/projects/chats (bestehend)
│
├─[Frage 2] Soll der Pfad hartkodiert oder konfigurierbar sein?
│  ├─ HARTKODIERT → Inflexibel
│  └─ KONFIGURIERBAR → DEEPCHATS_HOME Env-Variable
│     └─ GEWÄHLT: Default ~/.deepcode/projects/chats,
│        überschreibbar via Env
│
└─[Frage 3] Wo liegt die deepchats.db?
   └─ GEWÄHLT: Direkt im DEEPCHATS_HOME (nicht im deepchats-Repo)
```

## Entscheidung

- **Default-Pfad:** `C:\Users\mschm\.deepcode\projects\chats`
- **Konfigurierbar via:** `DEEPCHATS_HOME` Environment-Variable
- **DB-Pfad:** `$DEEPCHATS_HOME/.deepchats.db`

---

# Decision #005 — Namensschema-Format

**Timestamp:** 2026-05-24T22:45:00+02:00
**Status:** ACCEPTED
**Importance:** MEDIUM

---

## Entscheidung

**Format:** `YYYYMMDD_HHMMSS_[Typ]_[Thema]_[Aufgabe]`

### Sanitization-Regeln
- Alles lowercase
- Umlaute → ae, oe, ue, ss
- Sonderzeichen → `-` (außer `_` als Separator)
- Max. Länge: 120 Zeichen (Windows-Pfad-Kompatibilität)
- Keine Leerzeichen (Git-Bash-Kompatibilität)

### Beispiele
- `20260524_221500_code_sunca_api-endpoint-erstellen`
- `20260524_230000_debug_maos_memory-leak-finden`
- `20260525_090000_design_deepchats_architektur-planen`
- `20260525_140000_research_pv-bibliotheken_simulation-vergleich`

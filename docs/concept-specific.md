# deepchats — Implementation Specification v0.1.0

## Konkrete technische Spezifikation des Chat-Hypervisors

---

## 1. System-Architektur

### 1.1 Überblick

```
┌──────────────────────────────────────────────────┐
│                   CLI (Typer + Rich)              │
├──────────────────────────────────────────────────┤
│              ChatInitializer (Orchestrator)       │
│  ┌────────────────┐  ┌──────────────────┐        │
│  │ QuestionEngine │  │ DirectoryCreator │        │
│  └───────┬────────┘  └────────┬─────────┘        │
│          │                    │                   │
│  ┌───────┴────────────────────┴─────────┐        │
│  │         TypeRegistry (Plugins)       │        │
│  │  ┌─────────┐  ┌─────────┐  ┌───────┐ │        │
│  │  │chat_types│  │post_proc│  │builtin│ │        │
│  │  └─────────┘  └─────────┘  └───────┘ │        │
│  └──────────────────────────────────────┘        │
├──────────────────────────────────────────────────┤
│              SQLite (WAL Mode)                    │
│  chats │ tags │ chat_tags │ chat_links │          │
│  decisions │ checklists                          │
├──────────────────────────────────────────────────┤
│        Memory Knowledge Graph (MCP)               │
└──────────────────────────────────────────────────┘
```

### 1.2 Modul-Struktur

```
E:\git\deepchats\
├── app/
│   ├── __init__.py              # Package, Version
│   ├── types.py                 # ChatType, ChatCategory, ChatMetadata
│   ├── registry.py              # TypeRegistry, PostProcessorRegistry
│   ├── db.py                    # SQLite CRUD (851 Zeilen)
│   ├── questions.py             # QuestionEngine, QuestionSession
│   ├── init_chat.py             # ChatInitializer, DirectoryCreator
│   ├── post_chat.py             # PostChatRunner
│   ├── cli.py                   # Typer CLI (9 Commands)
│   ├── chat_types/              # Plugin-Verzeichnis
│   │   ├── __init__.py
│   │   ├── code.py              # ChatTypePlugin: code
│   │   ├── guide.py             # ChatTypePlugin: guide
│   │   └── meta.py              # ChatTypePlugin: meta
│   └── post_processors/         # Post-Processing-Plugins
│       ├── __init__.py
│       ├── base.py              # BasePostProcessor, PostProcessResult
│       ├── tagger.py            # AutoTagger
│       ├── similarity.py        # SimilarityMatcher
│       └── metrics.py           # MetricsCollector
├── scripts/
│   └── init-chat.sh             # Shell-Wrapper
├── tests/
│   ├── __init__.py
│   ├── test_types.py            # 16 Tests für Typ-System
│   ├── test_registry.py         # 13 Tests für Registry
│   └── test_db.py               # 15 Tests für Datenbank
├── docs/
│   ├── concept-general.md       # Wissenschaftliche Abhandlung
│   └── concept-specific.md      # Diese Datei
├── .checklists/
│   └── implementation-checklist.yaml  # 89-Task-Checkliste
├── .decisions/
│   ├── 001-architecture-style.md
│   ├── 002-005-infrastructure-decisions.md
│   └── 006-test-execution.md
├── pyproject.toml
├── .gitignore
└── README.md
```

## 2. Datenmodell

### 2.1 SQLite-Schema

#### Tabelle `chats` (Zentrale Entität)

| Spalte         | Typ     | Beschreibung                              |
|----------------|---------|-------------------------------------------|
| id             | TEXT PK | UUID-basierte Chat-ID (12 Zeichen)        |
| name           | TEXT    | Verzeichnisname nach Namensschema         |
| chat_type      | TEXT    | ChatType-Wert (code, debug, guide, ...)   |
| category       | TEXT    | ChatCategory (aktion, wissen, meta)       |
| topic          | TEXT    | Thema/Repo/Projekt                        |
| task           | TEXT    | Konkrete Aufgabe                          |
| created_at     | TEXT    | ISO 8601 UTC                               |
| updated_at     | TEXT    | ISO 8601 UTC                               |
| status         | TEXT    | active, completed, archived, abandoned    |
| repo_url       | TEXT    | GitHub-Repository-URL (nullable)          |
| language       | TEXT    | Programmiersprache (nullable)             |
| framework      | TEXT    | Framework (nullable)                      |
| priority       | INT     | 1–5                                       |
| parent_chat_id | TEXT FK | Selbstreferenz für fortgesetzte Chats     |
| dir_path       | TEXT    | Absoluter Pfad zum Verzeichnis            |
| message_count  | INT     | Geschätzte Nachrichtenanzahl              |
| outcome        | TEXT    | success, partial, failed (nullable)       |

#### Tabelle `tags`

| Spalte   | Typ      | Beschreibung                     |
|----------|----------|----------------------------------|
| id       | INT PK   | Auto-Increment                   |
| name     | TEXT UQ  | Tag-Name (lowercase)             |
| category | TEXT     | general, language, framework, auto |

#### Tabelle `chat_tags` (N:M)

| Spalte  | Typ    | FK                |
|---------|--------|-------------------|
| chat_id | TEXT   | chats(id) CASCADE |
| tag_id  | INT    | tags(id) CASCADE  |
| PK      | (chat_id, tag_id) |              |

#### Tabelle `chat_links`

| Spalte         | Typ    | Beschreibung                              |
|----------------|--------|-------------------------------------------|
| id             | INT PK | Auto-Increment                            |
| source_chat_id | TEXT   | FK → chats(id)                            |
| target_chat_id | TEXT   | FK → chats(id)                            |
| link_type      | TEXT   | related, similar, follows, parent         |
| weight         | REAL   | 0.0–1.0 Ähnlichkeits-Score               |
| created_at     | TEXT   | ISO 8601                                  |
| UNIQUE         | (source, target, type) |                      |

#### Tabelle `decisions`

| Spalte        | Typ    | Beschreibung                       |
|---------------|--------|------------------------------------|
| id            | INT PK | Auto-Increment                     |
| chat_id       | TEXT   | FK → chats(id)                     |
| timestamp     | TEXT   | ISO 8601                           |
| title         | TEXT   | Entscheidungstitel                 |
| content       | TEXT   | Markdown-Inhalt                     |
| importance    | TEXT   | LOW, MEDIUM, HIGH, CRITICAL        |
| decision_tree | TEXT   | ASCII Decision Tree (nullable)     |

#### Tabelle `checklists`

| Spalte     | Typ    | Beschreibung              |
|------------|--------|---------------------------|
| id         | INT PK | Auto-Increment            |
| chat_id    | TEXT   | FK → chats(id)            |
| created_at | TEXT   | ISO 8601                  |
| updated_at | TEXT   | ISO 8601                  |
| content    | TEXT   | YAML-Checklisten-Inhalt   |
| status     | TEXT   | in_progress, completed    |

## 3. Namensschema

### 3.1 Format

```
YYYYMMDD_HHMMSS_[Typ]_[Thema]_[Aufgabe]
```

### 3.2 Sanitization-Regeln

| Eingabe        | Ersetzung           |
|----------------|---------------------|
| ä, ö, ü, ß     | ae, oe, ue, ss      |
| Leerzeichen    | -                   |
| Sonderzeichen  | -                   |
| Mehrere --     | - (reduziert)       |
| Großbuchstaben | lowercase           |
| Maximallänge   | 120 Zeichen         |

### 3.3 Beispiele

```
20260524_221500_code_sunca_api-endpoint-erstellen
20260524_230000_debug_maos_memory-leak-finden
20260525_090000_design_deepchats_architektur-planen
20260525_140000_research_pv-bibliotheken_simulation-vergleich
20260525_163000_meta_deepchats_hypervisor-verbessern
```

## 4. Chat-Typ-Taxonomie (Implementierung)

### 4.1 AKTION (7 Typen)

```python
class ChatType(StrEnum):
    CODE = "code"        # Feature-Entwicklung
    DEBUG = "debug"      # Fehlersuche
    REFACTOR = "refactor" # Code-Umstrukturierung
    REVIEW = "review"    # Code-Review
    DEPLOY = "deploy"    # Deployment
    TEST = "test"        # Test-Erstellung
    SETUP = "setup"      # Projekt-Initialisierung
```

### 4.2 WISSEN (6 Typen)

```python
    GUIDE = "guide"      # Anleitung/Tutorial
    RESEARCH = "research" # Technologie-Evaluierung
    DESIGN = "design"    # Architektur-Design
    ANALYZE = "analyze"  # Code/Daten-Analyse
    LEARN = "learn"      # Konzeptverständnis
    DOCS = "docs"        # Dokumentation
```

### 4.3 META (3 Typen)

```python
    PLAN = "plan"        # Planung/Roadmap
    CHAT = "chat"        # Allgemeines Gespräch
    META = "meta"        # Prozess-Verbesserung
```

## 5. Erweiterbarkeit (Plugin-System)

### 5.1 Neuen Chat-Typ hinzufügen

1. Datei erstellen: `app/chat_types/neuer_typ.py`
2. `plugin`-Objekt exportieren:

```python
from app.registry import ChatTypePlugin, QuestionSet, QuestionTemplate
from app.types import ChatType

plugin: ChatTypePlugin = ChatTypePlugin(
    chat_type=ChatType.CODE,  # oder neuer StrEnum-Wert
    question_set=QuestionSet(
        chat_type=ChatType.CODE,
        fixed_questions=[...],
        anticipatable_topics=[...],
    ),
)
```

### 5.2 Neuen Post-Processor hinzufügen

1. Datei erstellen: `app/post_processors/neuer_processor.py`
2. `processor`-Objekt exportieren:

```python
class NeuerProcessor:
    name = "neuer_processor"
    description = "Beschreibung"
    priority = 50
    requires_llm = False

    def process(self, chat_id, db_path, context):
        # Implementierung
        return PostProcessResult(...)

processor = NeuerProcessor()
```

## 6. Init-Prozess (Detaillierter Ablauf)

### Schritt 1: Pre-Check
```
- Git Remote URL erkennen (git remote get-url origin)
- Aktuellen Branch ermitteln
- Letzte 5 Chats aus DB laden
- DEEPCHATS_HOME und DB-Pfad validieren
```

### Schritt 2: Chat-Typ-Auswahl
```
- CLI: --type code | interaktiv: Liste aller Typen anzeigen
- Typ-Validierung gegen ChatType Enum
- Registry-Eintrag laden (Metadaten, Icon, Beispiele)
```

### Schritt 3: Fixe Fragen
```
- Frage-Templates aus TypeRegistry laden
- Konditionale Fragen filtern (context-basierte Conditions)
- Jede Frage via Rich-Prompt stellen
- Validierung: Pflichtfelder, Typ-Konvertierung (bool, int, choice)
- Antworten in QuestionSession sammeln
```

### Schritt 4: KI-Antizipierte Fragen
```
- anticipatable_topics aus QuestionSet laden
- Neue QuestionTemplates generieren
- Bestätigung einholen ("Sollen N Zusatzfragen gestellt werden?")
- Fragen stellen und Antworten sammeln
```

### Schritt 5: Verzeichnis-Erstellung
```
- Namensgenerierung: YYYYMMDD_HHMMSS_Typ_Thema_Aufgabe
- Sanitization (Umlaute, Sonderzeichen, Länge)
- os.makedirs(full_path)
- Unterverzeichnisse: .checklists, .decisions
```

### Schritt 6: DB-Eintrag
```
- ChatMetadata-Objekt bauen
- create_chat() → SQLite INSERT
- Chat-ID generieren (uuid4().hex[:12])
```

### Schritt 7: Meta-Scaffolding
```
- .checklists/tasks.yaml mit Initial-Template
- .decisions/README.md mit Vorlage
- DB-Einträge für Checkliste
```

## 7. CLI-Commands (Vollständig)

| Command | Beschreibung | Beispiel |
|---------|-------------|---------|
| `deepchats init` | Chat initialisieren (interaktiv) | `deepchats init` |
| `deepchats init -t code --topic sunca --task "api bauen"` | Nicht-interaktiv | `deepchats init -n -t code --topic x --task y` |
| `deepchats list` | Alle Chats auflisten | `deepchats list -t code -s active` |
| `deepchats show <id>` | Chat-Details | `deepchats show abc123` |
| `deepchats search <query>` | Volltextsuche | `deepchats search "fastapi endpoint"` |
| `deepchats tag <id> --add python` | Tag hinzufügen | `deepchats tag abc123 -a python -a api` |
| `deepchats tag <id> --remove python` | Tag entfernen | `deepchats tag abc123 -r python` |
| `deepchats link <source> <target>` | Chats verknüpfen | `deepchats link abc123 def456 -t similar` |
| `deepchats stats` | Statistiken | `deepchats stats` |
| `deepchats config --show` | Konfiguration | `deepchats config --show` |
| `deepchats post-chat <id>` | Nachbereitung | `deepchats post-chat abc123` |
| `deepchats decision <id> -t "Titel" -c "Inhalt"` | Entscheidung dokumentieren | `deepchats decision abc123 -t "DB-Wahl"` |

## 8. Umgebungsvariablen

| Variable | Default | Beschreibung |
|----------|---------|-------------|
| `DEEPCHATS_HOME` | `~/.deepcode/projects/chats` | Hypervisor-Root |
| `DEEPCHATS_DB_PATH` | `$DEEPCHATS_HOME/.deepchats.db` | SQLite-Datenbank |

## 9. Installation

```bash
# Repository klonen
git clone https://github.com/MS892/deepchats.git
cd deepchats

# Installieren (development mode)
pip install -e ".[dev]"

# Konfigurieren
export DEEPCHATS_HOME="$HOME/.deepcode/projects/chats"

# Ersten Chat initialisieren
deepchats init
```

## 10. Test-Suite

```bash
# Alle Tests ausführen
pytest tests/ -v

# Mit Coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

**Testabdeckung:**
- `test_types.py`: 16 Typ-Validierungstests
- `test_registry.py`: 13 Registry/Plugin-Tests
- `test_db.py`: 15 Datenbank-CRUD-Tests
- Gesamt: 44 Tests über 3 Module

---

**Version:** 0.1.0
**Autor:** MS892
**Repository:** https://github.com/MS892/deepchats

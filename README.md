# 🌐 deepchats — Chat-Hypervisor

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)]()

**Interaktives Initialisierungssystem für KI-gestützte Chat-Kontexte.**

`deepchats` verwandelt flüchtige KI-Chat-Sessions in strukturierte,
durchsuchbare und verknüpfbare Wissensartefakte. Jeder Chat erhält ein
eigenes Verzeichnis mit Metadaten, Tags, Checklisten und
Entscheidungsdokumentation — automatisch organisiert durch ein
erweiterbares Typ-System.

---

## Quickstart

```bash
# Installation
git clone https://github.com/MS892/deepchats.git
cd deepchats
pip install -e .

# Ersten Chat starten
deepchats init

# Alle Chats anzeigen
deepchats list --recent 10

# Statistiken
deepchats stats
```

## Chat-Typen (16)

| Kategorie | Typen |
|-----------|-------|
| 🔨 **Aktion** | `code`, `debug`, `refactor`, `review`, `deploy`, `test`, `setup` |
| 🧠 **Wissen** | `guide`, `research`, `design`, `analyze`, `learn`, `docs` |
| 🌐 **Meta** | `plan`, `chat`, `meta` |

## Namensschema

```
YYYYMMDD_HHMMSS_[Typ]_[Thema]_[Aufgabe]

Beispiele:
  20260524_221500_code_sunca_api-endpoint-erstellen
  20260525_090000_design_deepchats_architektur-planen
```

## Erweiterbarkeit

Neue Chat-Typen und Post-Processoren können ohne Änderung am Core
hinzugefügt werden:

```python
# app/chat_types/mein_typ.py
plugin: ChatTypePlugin = ChatTypePlugin(
    chat_type=ChatType.CODE,
    question_set=QuestionSet(...),
)
```

## Dokumentation

- [Allgemeines Konzept (wissenschaftlich)](docs/concept-general.md)
- [Implementierungsspezifikation](docs/concept-specific.md)
- [Entscheidungsarchiv](.decisions/)

## CLI-Commands

```bash
deepchats init                  # Chat initialisieren
deepchats list                  # Chats auflisten
deepchats show <id>             # Details anzeigen
deepchats search <query>        # Volltextsuche
deepchats tag <id> --add <tag>  # Tags verwalten
deepchats link <a> <b>          # Chats verknüpfen
deepchats stats                 # Statistiken
deepchats post-chat <id>        # Nachbereitung
deepchats decision <id> -t "X"  # Entscheidung dokumentieren
```

## Lizenz

MIT — [MS892/deepchats](https://github.com/MS892/deepchats)

"""
Chat-Initialisierungs-Orchestrator.

Führt den vollständigen Init-Prozess durch:
1. Pre-Check (Git-Repo erkennen, letzte Chats laden)
2. Chat-Typ auswählen
3. Fixe Fragen stellen
4. KI-Zusatzfragen stellen
5. Verzeichnis mit Namensschema erstellen
6. Datenbank-Eintrag erstellen
7. Initial-Checklist und Decisions-Setup
8. Zusammenfassung ausgeben
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from app.db import (
    create_chat,
    create_checklist,
    get_db_path,
    get_home_dir,
    get_recent_chats,
    init_db,
)
from app.questions import QuestionEngine, QuestionSession
from app.registry import TypeRegistry
from app.types import (
    CHAT_TYPE_CATEGORY,
    CHAT_TYPE_DESCRIPTIONS,
    CHAT_TYPE_EXAMPLES,
    CHAT_TYPE_ICONS,
    ChatCategory,
    ChatMetadata,
    ChatType,
    get_types_by_category,
)


# =============================================================================
# Verzeichnis-Erstellung
# =============================================================================

class DirectoryCreator:
    """Erstellt das Chat-Verzeichnis nach dem Namensschema."""

    # Erlaubte Zeichen im Verzeichnisnamen (nach Sanitization)
    _SANITIZE_MAP: dict[str, str] = {
        "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
        "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
        " ": "-", "\\": "-", "/": "-", ":": "-",
        "*": "-", "?": "-", '"': "-", "'": "-",
        "<": "-", ">": "-", "|": "-", "&": "-",
        "+": "-", "#": "-", "@": "-", "!": "-",
        "(": "-", ")": "-", "[": "-", "]": "-",
        "{": "-", "}": "-", "`": "-", "´": "-",
    }
    _MAX_LENGTH = 120

    def __init__(self, home_dir: str | None = None) -> None:
        """Initialisiere den DirectoryCreator.

        Args:
            home_dir: Hypervisor-Root-Verzeichnis.
                      None = DEEPCHATS_HOME oder Default.
        """
        self.home_dir = home_dir or get_home_dir()

    def create(
        self,
        chat_type: ChatType,
        topic: str,
        task: str,
        timestamp: str | None = None,
    ) -> str:
        """Erstelle das Chat-Verzeichnis.

        Args:
            chat_type: Der Chat-Typ.
            topic: Thema/Repo.
            task: Aufgabe/Fragestellung.
            timestamp: Optionaler Zeitstempel (None = jetzt).

        Returns:
            Den absoluten Pfad zum erstellten Verzeichnis.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).strftime(
                "%Y%m%d_%H%M%S"
            )

        # Baue den Verzeichnisnamen
        dirname = self._build_name(timestamp, chat_type, topic, task)

        # Erstelle das Verzeichnis
        full_path = os.path.join(self.home_dir, dirname)
        os.makedirs(full_path, exist_ok=True)

        # Erstelle Unterverzeichnisse für Checklisten und Decisions
        os.makedirs(os.path.join(full_path, ".checklists"), exist_ok=True)
        os.makedirs(os.path.join(full_path, ".decisions"), exist_ok=True)

        return full_path

    def _build_name(
        self,
        timestamp: str,
        chat_type: ChatType,
        topic: str,
        task: str,
    ) -> str:
        """Baue den Verzeichnisnamen nach Schema.

        Format: YYYYMMDD_HHMMSS_[Typ]_[Thema]_[Aufgabe]
        """
        type_str = chat_type.value
        topic_clean = self._sanitize(topic)
        task_clean = self._sanitize(task)

        # Kürze falls nötig (Priorität: task kürzen, dann topic)
        name = f"{timestamp}_{type_str}_{topic_clean}_{task_clean}"
        if len(name) > self._MAX_LENGTH:
            # Kürze task
            available = (
                self._MAX_LENGTH
                - len(f"{timestamp}_{type_str}_{topic_clean}_")
                - 3
            )
            if available < 10:
                # Kürze topic
                available = (
                    self._MAX_LENGTH - len(f"{timestamp}_{type_str}_") - 3
                )
                topic_clean = topic_clean[:available]
            task_clean = task_clean[:available]
            name = f"{timestamp}_{type_str}_{topic_clean}_{task_clean}"

        # Entferne aufeinanderfolgende Bindestriche
        name = re.sub(r"-{2,}", "-", name)
        # Entferne führende/abschließende Bindestriche
        name = name.strip("-")

        return name.lower()

    def _sanitize(self, text: str) -> str:
        """Sanitize einen String für Dateinamen.

        - Umlaute ersetzen
        - Sonderzeichen durch Bindestrich
        - Mehrfache Bindestriche reduzieren
        """
        result = text
        for char, replacement in self._SANITIZE_MAP.items():
            result = result.replace(char, replacement)
        # Entferne alle nicht-erlaubten Zeichen
        result = re.sub(r"[^a-zA-Z0-9_-]", "", result)
        # Reduziere mehrfache Bindestriche
        result = re.sub(r"-{2,}", "-", result)
        return result.strip("-").lower() or "unnamed"


# =============================================================================
# Pre-Check
# =============================================================================

class PreChecker:
    """Führt Vorab-Prüfungen vor der Chat-Initialisierung durch."""

    def detect_git_repo(self, cwd: str | None = None) -> dict[str, str]:
        """Erkenne Git-Repository im aktuellen Verzeichnis.

        Returns:
            Dict mit repo_url, repo_name, branch (leer wenn kein Repo).
        """
        try:
            cwd = cwd or os.getcwd()
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=5,
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Extrahiere repo-name aus URL
                name = url.rstrip("/").split("/")[-1].replace(".git", "")
                if "github.com" in url:
                    # Konvertiere zu https-URL
                    if url.startswith("git@"):
                        url = url.replace(":", "/").replace("git@", "https://")
                    return {
                        "repo_url": url,
                        "repo_name": name,
                        "branch": self._get_current_branch(cwd),
                    }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return {}

    def _get_current_branch(self, cwd: str) -> str:
        """Ermittle den aktuellen Git-Branch."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=5,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def get_recent_context(
        self, db_path: str | None = None, limit: int = 5
    ) -> list[ChatMetadata]:
        """Lade die letzten Chats als Kontext."""
        try:
            return get_recent_chats(limit=limit, db_path=db_path)
        except Exception:
            return []


# =============================================================================
# Initialisierung von Checklist & Decisions
# =============================================================================

class MetaScaffolder:
    """Erstellt initiale .checklists und .decisions Strukturen."""

    def create_initial_checklist(
        self,
        chat_dir: str,
        chat_id: str,
        db_path: str,
        chat_type: ChatType,
        task: str,
    ) -> str:
        """Erstelle eine initiale Checkliste im Chat-Verzeichnis.

        Returns:
            Pfad zur erstellten Checkliste.
        """
        checklist_path = os.path.join(
            chat_dir, ".checklists", "tasks.yaml"
        )

        content = f"""# Checkliste für Chat: {chat_id}
# Typ: {chat_type.value}
# Aufgabe: {task}
# Erstellt: {datetime.now(timezone.utc).isoformat()}

meta:
  chat_id: {chat_id}
  chat_type: {chat_type.value}
  created_at: {datetime.now(timezone.utc).isoformat()}

phases:
  - id: phase-1
    name: "Hauptaufgabe"
    status: pending
    tasks: []

  - id: phase-2
    name: "Nachbereitung"
    status: pending
    tasks:
      - id: "post-1"
        name: "Ergebnisse dokumentieren"
        status: pending
      - id: "post-2"
        name: "Tags überprüfen und ergänzen"
        status: pending
"""

        # Schreibe Datei
        with open(checklist_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Erstelle DB-Eintrag
        create_checklist(chat_id, content, db_path)

        return checklist_path

    def create_decision_templates(self, chat_dir: str) -> str:
        """Erstelle eine .decisions/README.md mit Vorlage."""
        decisions_dir = os.path.join(chat_dir, ".decisions")
        readme_path = os.path.join(decisions_dir, "README.md")

        content = """# Decisions

Dieses Verzeichnis dokumentiert alle während des Chats getroffenen
Architektur- und Design-Entscheidungen.

## Format

Jede Entscheidung wird als Markdown-Datei abgelegt:
`YYYYMMDD_HHMMSS_kurztitel.md`

## Vorlage

```markdown
# Decision #NNN — Titel

**Timestamp:** YYYY-MM-DDTHH:MM:SS+02:00
**Status:** PROPOSED | ACCEPTED | REJECTED | SUPERSEDED
**Importance:** LOW | MEDIUM | HIGH | CRITICAL

---

## Fragestellung

...

## Decision Tree

```
START: Frage
│
├─ Option A → Konsequenz
└─ Option B → Konsequenz
```

## Entscheidung

...

## Begründung

...

## Konsequenzen

...

```
"""

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)

        return readme_path


# =============================================================================
# Haupt-Init-Prozess
# =============================================================================

class ChatInitializer:
    """Orchestriert den vollständigen Chat-Initialisierungsprozess."""

    def __init__(
        self,
        prompt_fn: Callable[[str, str, list[str] | None], str],
        confirm_fn: Callable[[str], bool],
        home_dir: str | None = None,
        db_path: str | None = None,
    ) -> None:
        """Initialisiere den ChatInitializer.

        Args:
            prompt_fn: Funktion für Benutzereingaben.
            confirm_fn: Funktion für Ja/Nein-Fragen.
            home_dir: Hypervisor-Root.
            db_path: SQLite-Datenbank-Pfad.
        """
        self.home_dir = home_dir or get_home_dir()
        self.db_path = db_path or get_db_path()
        self.registry = TypeRegistry()
        self.engine = QuestionEngine(self.registry, prompt_fn, confirm_fn)
        self.dir_creator = DirectoryCreator(self.home_dir)
        self.pre_checker = PreChecker()
        self.scaffolder = MetaScaffolder()

        # Stelle sicher, dass DB und Home existieren
        os.makedirs(self.home_dir, exist_ok=True)
        init_db(self.db_path)

    def run(
        self,
        chat_type: ChatType | None = None,
        topic: str | None = None,
        task: str | None = None,
        cwd: str | None = None,
    ) -> ChatMetadata:
        """Führe den vollständigen Init-Prozess aus.

        Args:
            chat_type: Optional vorausgewählter Chat-Typ.
            topic: Optional vorausgefülltes Thema.
            task: Optional vorausgefüllte Aufgabe.
            cwd: Aktuelles Arbeitsverzeichnis (für Git-Detection).

        Returns:
            Die erstellten Chat-Metadaten.
        """
        # --------------------------------------------------------------
        # Schritt 1: Pre-Check
        # --------------------------------------------------------------
        repo_info = self.pre_checker.detect_git_repo(cwd)
        recent_chats = self.pre_checker.get_recent_context(self.db_path)

        # --------------------------------------------------------------
        # Schritt 2: Chat-Typ auswählen
        # --------------------------------------------------------------
        if chat_type is None:
            chat_type = self._select_chat_type()
        else:
            chat_type = self._resolve_chat_type(chat_type)

        # --------------------------------------------------------------
        # Schritt 3: Fixe Fragen stellen
        # --------------------------------------------------------------
        context: dict[str, Any] = {}
        if repo_info:
            context["repo_url"] = repo_info.get("repo_url", "")
            context["repo_name"] = repo_info.get("repo_name", "")

        if topic:
            context["topic"] = topic

        if task:
            context["task"] = task

        session = self.engine.ask_fixed_questions(chat_type, context)

        # --------------------------------------------------------------
        # Schritt 4: KI-Zusatzfragen
        # --------------------------------------------------------------
        session = self.engine.ask_anticipated_questions(
            chat_type, session
        )

        # --------------------------------------------------------------
        # Schritt 5: Thema und Aufgabe extrahieren
        # --------------------------------------------------------------
        final_topic = (
            topic
            or session.get("topic")
            or repo_info.get("repo_name", "")
            or "general"
        )
        final_task = task or session.get("task") or "undefined"

        # --------------------------------------------------------------
        # Schritt 6: Verzeichnis erstellen
        # --------------------------------------------------------------
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dir_path = self.dir_creator.create(
            chat_type=chat_type,
            topic=final_topic,
            task=final_task,
            timestamp=timestamp,
        )

        # --------------------------------------------------------------
        # Schritt 7: Metadaten bauen & DB-Eintrag erstellen
        # --------------------------------------------------------------
        metadata = ChatMetadata(
            name=os.path.basename(dir_path),
            chat_type=chat_type,
            category=CHAT_TYPE_CATEGORY.get(
                chat_type, ChatCategory.AKTION
            ),
            topic=final_topic,
            task=final_task,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            repo_url=(
                repo_info.get("repo_url")
                or session.get("repo_url")
            ),
            language=session.get("language"),
            framework=session.get("framework"),
            priority=session.get("priority", 3),
            dir_path=dir_path,
        )

        chat_id = create_chat(metadata, self.db_path)
        metadata.id = chat_id

        # --------------------------------------------------------------
        # Schritt 8: Initial-Checklist & Decisions
        # --------------------------------------------------------------
        self.scaffolder.create_initial_checklist(
            dir_path, chat_id, self.db_path, chat_type, final_task
        )
        self.scaffolder.create_decision_templates(dir_path)

        return metadata

    def _select_chat_type(self) -> ChatType:
        """Interaktive Chat-Typ-Auswahl.

        Returns:
            Den ausgewählten ChatType.
        """
        # Zeige Kategorien
        categories = self.registry.get_categories()
        for category in [ChatCategory.AKTION, ChatCategory.WISSEN, ChatCategory.META]:
            if category in categories:
                entries = categories[category]
                # Die Auswahl-Logik wird von der CLI via prompt_fn gesteuert

        # Vereinfacht: CLI ruft prompt_fn mit allen Typen auf
        all_types = [e.chat_type.value for e in self.registry.list_all()]
        choice = self.engine.prompt(
            "Chat-Typ wählen (code, debug, guide, research, ...)",
            "choice",
            all_types,
        )
        return self._resolve_chat_type(choice)

    def _resolve_chat_type(self, value: Any) -> ChatType:
        """Konvertiere einen Wert in einen ChatType.

        Args:
            value: String, ChatType, oder None.

        Returns:
            Einen gültigen ChatType (default: CHAT).
        """
        if isinstance(value, ChatType):
            return value
        if isinstance(value, str):
            try:
                return ChatType(value.lower().strip())
            except ValueError:
                pass
        return ChatType.CHAT

    def get_summary(self, metadata: ChatMetadata) -> str:
        """Erstelle eine Zusammenfassung des initialisierten Chats.

        Args:
            metadata: Die Chat-Metadaten.

        Returns:
            Formatierte Zusammenfassung als String.
        """
        icon = CHAT_TYPE_ICONS.get(metadata.chat_type, "❓")
        desc = CHAT_TYPE_DESCRIPTIONS.get(metadata.chat_type, "")

        lines = [
            "=" * 60,
            f"  {icon} Chat initialisiert: {metadata.id}",
            "=" * 60,
            f"  Typ:       {metadata.chat_type.value} ({desc})",
            f"  Thema:     {metadata.topic}",
            f"  Aufgabe:   {metadata.task}",
            f"  Priorität: {'⭐' * metadata.priority}",
            f"  Pfad:      {metadata.dir_path}",
            f"  Erstellt:  {metadata.created_at}",
            "=" * 60,
        ]
        if metadata.repo_url:
            lines.insert(-3, f"  Repo:      {metadata.repo_url}")
        if metadata.language:
            lines.insert(-3, f"  Sprache:   {metadata.language}")
        if metadata.framework:
            lines.insert(-3, f"  Framework: {metadata.framework}")

        return "\n".join(lines)

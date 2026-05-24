"""
Plugin-Registry für deepchats.

Implementiert das Registry-Pattern für:
- Chat-Typen: Dynamische Entdeckung und Registrierung
- Fragen-Templates: Typ-spezifische Frage-Konfiguration
- Post-Processoren: Nachbereitungs-Module

Erweiterbarkeit:
Neue Chat-Typen und Post-Processoren werden als Module in
chat_types/ bzw. post_processors/ abgelegt und via importlib
automatisch entdeckt — keine Änderung am Core nötig.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol

from app.types import (
    CHAT_TYPE_CATEGORY,
    CHAT_TYPE_DEFAULT_QUESTIONS,
    CHAT_TYPE_DESCRIPTIONS,
    CHAT_TYPE_EXAMPLES,
    CHAT_TYPE_ICONS,
    ChatCategory,
    ChatType,
)


# =============================================================================
# Frage-Template
# =============================================================================

@dataclass
class QuestionTemplate:
    """Eine Frage, die im Init-Prozess gestellt wird.

    Attributes:
        key: Eindeutiger Schlüssel (z.B. "language", "framework")
        text: Fragetext (deutsch)
        field_type: Antwort-Typ (text, choice, bool, int)
        required: Ob die Frage beantwortet werden muss
        choices: Optionen für choice-Fragen (None für freie Texteingabe)
        default: Standardwert
        condition: Optionale Bedingung (Callable), die erfüllt sein muss,
                   damit die Frage gestellt wird
        help_text: Erklärender Hilfetext
    """

    key: str
    text: str
    field_type: str = "text"  # text, choice, bool, int
    required: bool = False
    choices: list[str] | None = None
    default: Any = None
    condition: Callable[[dict[str, Any]], bool] | None = None
    help_text: str = ""

    def should_ask(self, context: dict[str, Any]) -> bool:
        """Prüfe, ob diese Frage im gegebenen Kontext gestellt werden soll."""
        if self.condition is None:
            return True
        try:
            return self.condition(context)
        except Exception:
            return True


@dataclass
class QuestionSet:
    """Ein Satz von Fragen für einen bestimmten Chat-Typ.

    Besteht aus fixen Fragen (immer gestellt) und dynamischen Fragen
    (KI-antizipiert oder kontextabhängig).
    """

    chat_type: ChatType
    fixed_questions: list[QuestionTemplate] = field(default_factory=list)
    anticipatable_topics: list[str] = field(default_factory=list)

    def get_applicable_questions(
        self, context: dict[str, Any]
    ) -> list[QuestionTemplate]:
        """Gib alle im Kontext anwendbaren Fragen zurück."""
        return [q for q in self.fixed_questions if q.should_ask(context)]


# =============================================================================
# Chat-Typ-Plugin-Interface
# =============================================================================

class ChatTypePlugin(Protocol):
    """Interface für Chat-Typ-Plugins.

    Jedes Modul in chat_types/ muss ein Objekt namens 'plugin'
    exportieren, das diesem Interface entspricht.
    """

    chat_type: ChatType
    question_set: QuestionSet

    def on_pre_init(self, context: dict[str, Any]) -> dict[str, Any]:
        """Wird VOR der Initialisierung aufgerufen. Kann Kontext anreichern."""
        ...

    def on_post_init(self, chat_id: str, context: dict[str, Any]) -> None:
        """Wird NACH der Initialisierung aufgerufen."""
        ...


# =============================================================================
# Post-Processor-Interface
# =============================================================================

class PostProcessor(Protocol):
    """Interface für Post-Chat-Verarbeitungsmodule.

    Jedes Modul in post_processors/ muss ein Objekt namens 'processor'
    exportieren, das diesem Interface entspricht.
    """

    name: str
    description: str
    priority: int  # Niedrigere Zahl = frühere Ausführung
    requires_llm: bool

    def process(
        self, chat_id: str, db_path: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Führe die Nachbereitung für einen Chat durch."""
        ...


# =============================================================================
# TypeRegistry — Zentrale Registrierung für Chat-Typen
# =============================================================================

@dataclass
class TypeRegistryEntry:
    """Eintrag in der TypeRegistry für einen Chat-Typ."""

    chat_type: ChatType
    category: ChatCategory
    description: str
    icon: str
    examples: list[str]
    question_set: QuestionSet
    plugin: Optional[ChatTypePlugin] = None


class TypeRegistry:
    """Zentrale Registry für alle Chat-Typen.

    Unterstützt:
    - Eingebaute Typen (aus types.py)
    - Plugin-Typen (aus chat_types/)
    - Dynamische Registrierung zur Laufzeit

    Usage:
        registry = TypeRegistry()
        registry.discover_plugins()
        entry = registry.get(ChatType.CODE)
        print(entry.icon, entry.description)
    """

    def __init__(self) -> None:
        self._entries: dict[ChatType, TypeRegistryEntry] = {}
        self._register_builtins()

    # ------------------------------------------------------------------
    # Registrierung
    # ------------------------------------------------------------------

    def register(
        self,
        chat_type: ChatType,
        category: ChatCategory | None = None,
        description: str | None = None,
        icon: str | None = None,
        examples: list[str] | None = None,
        question_set: QuestionSet | None = None,
        plugin: ChatTypePlugin | None = None,
    ) -> TypeRegistryEntry:
        """Registriere einen Chat-Typ (überschreibt existierende Einträge)."""
        category = category or CHAT_TYPE_CATEGORY.get(
            chat_type, ChatCategory.AKTION
        )
        description = description or CHAT_TYPE_DESCRIPTIONS.get(
            chat_type, ""
        )
        icon = icon or CHAT_TYPE_ICONS.get(chat_type, "❓")
        examples = examples or CHAT_TYPE_EXAMPLES.get(chat_type, [])
        question_set = question_set or self._build_default_question_set(
            chat_type
        )

        entry = TypeRegistryEntry(
            chat_type=chat_type,
            category=category,
            description=description,
            icon=icon,
            examples=examples,
            question_set=question_set,
            plugin=plugin,
        )
        self._entries[chat_type] = entry
        return entry

    def _register_builtins(self) -> None:
        """Registriere alle in types.py definierten Chat-Typen."""
        for chat_type in ChatType:
            self.register(chat_type=chat_type)

    def _build_default_question_set(
        self, chat_type: ChatType
    ) -> QuestionSet:
        """Baue ein Default-QuestionSet aus den Metadaten."""
        default_texts = CHAT_TYPE_DEFAULT_QUESTIONS.get(chat_type, [])
        questions = [
            QuestionTemplate(
                key=f"default_{i}",
                text=text,
                field_type="text",
                required=False,
            )
            for i, text in enumerate(default_texts)
        ]
        return QuestionSet(
            chat_type=chat_type,
            fixed_questions=questions,
        )

    # ------------------------------------------------------------------
    # Plugin-Discovery
    # ------------------------------------------------------------------

    def discover_plugins(self, package_path: str = "app.chat_types") -> int:
        """Entdecke und registriere alle Chat-Typ-Plugins.

        Scannt das angegebene Package nach Modulen, die ein 'plugin'
        Objekt exportieren.

        Returns:
            Anzahl der gefundenen Plugins.
        """
        count = 0
        try:
            package = importlib.import_module(package_path)
            for _, module_name, _ in pkgutil.iter_modules(
                package.__path__, package.__name__ + "."
            ):
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, "plugin"):
                        plugin: ChatTypePlugin = module.plugin
                        self.register(
                            chat_type=plugin.chat_type,
                            question_set=plugin.question_set,
                            plugin=plugin,
                        )
                        count += 1
                except Exception as e:
                    # Plugin-Fehler sollten nicht den gesamten
                    # Discovery-Prozess abbrechen
                    import sys
                    print(
                        f"[WARN] Plugin {module_name} konnte nicht "
                        f"geladen werden: {e}",
                        file=sys.stderr,
                    )
        except ModuleNotFoundError:
            pass
        return count

    # ------------------------------------------------------------------
    # Abfragen
    # ------------------------------------------------------------------

    def get(self, chat_type: ChatType) -> TypeRegistryEntry | None:
        """Gib den Registry-Eintrag für einen Typ zurück."""
        return self._entries.get(chat_type)

    def list_all(self) -> list[TypeRegistryEntry]:
        """Liste alle registrierten Typen."""
        return list(self._entries.values())

    def list_by_category(
        self, category: ChatCategory
    ) -> list[TypeRegistryEntry]:
        """Liste alle Typen einer Kategorie."""
        return [
            e for e in self._entries.values() if e.category == category
        ]

    def get_categories(self) -> dict[ChatCategory, list[TypeRegistryEntry]]:
        """Gruppiere alle Typen nach Kategorie."""
        result: dict[ChatCategory, list[TypeRegistryEntry]] = {}
        for entry in self._entries.values():
            result.setdefault(entry.category, []).append(entry)
        return result

    def search(self, query: str) -> list[TypeRegistryEntry]:
        """Einfache Textsuche über Typ-Namen und Beschreibungen."""
        query_lower = query.lower()
        results = []
        for entry in self._entries.values():
            if (
                query_lower in entry.chat_type.value.lower()
                or query_lower in entry.description.lower()
            ):
                results.append(entry)
        return results

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, chat_type: ChatType) -> bool:
        return chat_type in self._entries


# =============================================================================
# PostProcessorRegistry
# =============================================================================

class PostProcessorRegistry:
    """Registry für Post-Chat-Verarbeitungsmodule.

    Usage:
        registry = PostProcessorRegistry()
        registry.discover_plugins()
        for proc in registry.get_all_sorted():
            proc.process(chat_id, db_path, context)
    """

    def __init__(self) -> None:
        self._processors: dict[str, PostProcessor] = {}

    def register(self, processor: PostProcessor) -> None:
        """Registriere einen Post-Processor."""
        self._processors[processor.name] = processor

    def unregister(self, name: str) -> None:
        """Entferne einen Post-Processor."""
        self._processors.pop(name, None)

    def get(self, name: str) -> PostProcessor | None:
        """Gib einen bestimmten Post-Processor zurück."""
        return self._processors.get(name)

    def get_all_sorted(self) -> list[PostProcessor]:
        """Gib alle Processoren sortiert nach Priorität zurück."""
        return sorted(
            self._processors.values(), key=lambda p: p.priority
        )

    def discover_plugins(
        self, package_path: str = "app.post_processors"
    ) -> int:
        """Entdecke und registriere alle Post-Processor-Plugins.

        Returns:
            Anzahl der gefundenen Plugins.
        """
        count = 0
        try:
            package = importlib.import_module(package_path)
            for _, module_name, _ in pkgutil.iter_modules(
                package.__path__, package.__name__ + "."
            ):
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, "processor"):
                        self.register(module.processor)
                        count += 1
                except Exception as e:
                    import sys
                    print(
                        f"[WARN] Post-Processor {module_name} konnte "
                        f"nicht geladen werden: {e}",
                        file=sys.stderr,
                    )
        except ModuleNotFoundError:
            pass
        return count

    def __len__(self) -> int:
        return len(self._processors)

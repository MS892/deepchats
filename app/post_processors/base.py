"""
Basisklasse für Post-Chat-Processoren.

Jeder Post-Processor implementiert dieses Interface und wird
via PostProcessorRegistry automatisch entdeckt und ausgeführt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class PostProcessResult:
    """Ergebnis eines Post-Processing-Schritts."""

    processor_name: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class BasePostProcessor(Protocol):
    """Interface für Post-Chat-Processoren.

    Jedes Modul in post_processors/ exportiert ein 'processor'-Objekt,
    das diesem Protokoll entspricht.

    Attributes:
        name: Eindeutiger Name des Processors.
        description: Beschreibung der Funktion.
        priority: Ausführungsreihenfolge (niedriger = früher).
        requires_llm: Ob dieser Processor ein LLM benötigt.
    """

    name: str
    description: str
    priority: int
    requires_llm: bool

    def process(
        self,
        chat_id: str,
        db_path: str,
        context: dict[str, Any],
    ) -> PostProcessResult:
        """Führe die Nachbereitung durch.

        Args:
            chat_id: Die ID des abgeschlossenen Chats.
            db_path: Pfad zur SQLite-Datenbank.
            context: Zusätzlicher Kontext (z.B. Chat-Inhalt).

        Returns:
            PostProcessResult mit Ergebnissen.
        """
        ...

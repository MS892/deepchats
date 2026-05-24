"""
Post-Chat-Orchestrator.

Führt alle registrierten Post-Processoren in der richtigen
Reihenfolge aus und aggregiert die Ergebnisse.
"""

from __future__ import annotations

from typing import Any

from app.db import get_db_path
from app.post_processors.base import PostProcessResult
from app.registry import PostProcessorRegistry


class PostChatRunner:
    """Orchestriert die Nachbereitung eines Chats."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialisiere den PostChatRunner.

        Args:
            db_path: Optionaler Datenbank-Pfad.
        """
        self.db_path = db_path or get_db_path()
        self.registry = PostProcessorRegistry()
        self.registry.discover_plugins()

    def run(
        self,
        chat_id: str,
        context: dict[str, Any] | None = None,
    ) -> list[PostProcessResult]:
        """Führe alle Post-Processoren für einen Chat aus.

        Args:
            chat_id: Die Chat-ID.
            context: Zusätzlicher Kontext (Metriken, Outcome, etc.).

        Returns:
            Liste aller PostProcessResult-Objekte.
        """
        results: list[PostProcessResult] = []
        ctx = context or {}

        processors = self.registry.get_all_sorted()

        for processor in processors:
            try:
                result = processor.process(chat_id, self.db_path, ctx)
                results.append(result)
            except Exception as e:
                results.append(
                    PostProcessResult(
                        processor_name=processor.name,
                        success=False,
                        errors=[str(e)],
                    )
                )

        return results

    def get_summary(
        self, results: list[PostProcessResult]
    ) -> str:
        """Erstelle eine Zusammenfassung der Post-Processing-Ergebnisse.

        Args:
            results: Liste der Ergebnisse.

        Returns:
            Formatierte Zusammenfassung.
        """
        lines = [
            "=" * 50,
            "  Post-Chat Analyse abgeschlossen",
            "=" * 50,
        ]

        success_count = sum(1 for r in results if r.success)
        lines.append(
            f"  Processoren: {success_count}/{len(results)} erfolgreich"
        )
        lines.append("")

        for result in results:
            status = "✅" if result.success else "❌"
            lines.append(f"  {status} {result.processor_name}")
            if result.suggestions:
                lines.append(
                    f"     → Vorschläge: {', '.join(result.suggestions[:5])}"
                )
            if result.errors:
                lines.append(
                    f"     → Fehler: {'; '.join(result.errors)}"
                )

        lines.append("=" * 50)
        return "\n".join(lines)


def run_post_chat(
    chat_id: str,
    context: dict[str, Any] | None = None,
    db_path: str | None = None,
) -> list[PostProcessResult]:
    """Convenience-Funktion: Führe Post-Chat für einen Chat aus.

    Args:
        chat_id: Die Chat-ID.
        context: Zusätzlicher Kontext.
        db_path: Optionaler DB-Pfad.

    Returns:
        Liste der Ergebnisse.
    """
    runner = PostChatRunner(db_path)
    return runner.run(chat_id, context)

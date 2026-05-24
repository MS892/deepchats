"""
MetricsCollector — Erfasst Metriken nach Chat-Ende.

Sammelt Statistiken über Chat-Dauer, Outcome und andere
quantitative Metriken für die Langzeit-Analyse.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.db import get_chat, update_chat
from app.post_processors.base import PostProcessResult


class MetricsCollector:
    """Sammelt und persistiert Chat-Metriken."""

    name = "metrics_collector"
    description = "Metrik-Erfassung für Chat-Statistiken"
    priority = 90  # Als letztes ausführen
    requires_llm = False

    def process(
        self,
        chat_id: str,
        db_path: str,
        context: dict[str, Any],
    ) -> PostProcessResult:
        """Erfasse Metriken für einen Chat.

        Args:
            chat_id: Chat-ID.
            db_path: Datenbank-Pfad.
            context: Sollte 'outcome', 'message_count' enthalten.

        Returns:
            PostProcessResult mit erfassten Metriken.
        """
        chat = get_chat(chat_id, db_path)
        if chat is None:
            return PostProcessResult(
                processor_name=self.name,
                success=False,
                errors=["Chat nicht gefunden"],
            )

        updates: dict[str, str | int] = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Outcome
        outcome = context.get("outcome")
        if outcome and outcome in ("success", "partial", "failed"):
            updates["outcome"] = outcome

        # Message Count
        msg_count = context.get("message_count", 0)
        if msg_count:
            updates["message_count"] = int(msg_count)

        # Status auf 'completed' setzen
        if not outcome and not msg_count:
            # Keine expliziten Metriken — trotzdem aktualisieren
            pass
        else:
            updates["status"] = "completed"

        # Persistiere
        success = update_chat(chat_id, updates, db_path)

        return PostProcessResult(
            processor_name=self.name,
            success=success,
            data={"updates_applied": updates},
        )


# Export für Plugin-Discovery
processor = MetricsCollector()

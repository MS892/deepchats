"""
SimilarityMatcher — Findet ähnliche Chats basierend auf Tags und Themen.

Nutzt Tag-Overlap und einfache Text-Ähnlichkeit (Jaccard-Index),
um verwandte Chats zu identifizieren und zu verknüpfen.
"""

from __future__ import annotations

from app.db import get_chat, link_chats, search_chats
from app.post_processors.base import PostProcessResult


class SimilarityMatcher:
    """Findet und verknüpft ähnliche Chat-Kontexte."""

    name = "similarity_matcher"
    description = "Ähnlichkeitsanalyse und Chat-Verknüpfung"
    priority = 20
    requires_llm = False

    # Schwellwerte
    _MIN_SIMILARITY_SCORE = 0.3  # Minimaler Score für Verknüpfung
    _MAX_LINKS = 5  # Maximale Anzahl neuer Links

    def process(
        self,
        chat_id: str,
        db_path: str,
        context: dict[str, Any],
    ) -> PostProcessResult:
        """Finde ähnliche Chats und erstelle Verknüpfungen.

        Args:
            chat_id: Der gerade abgeschlossene Chat.
            db_path: Datenbank-Pfad.
            context: Chat-Metadaten.

        Returns:
            PostProcessResult mit gefundenen ähnlichen Chats.
        """
        # Lade den aktuellen Chat
        current = get_chat(chat_id, db_path)
        if current is None:
            return PostProcessResult(
                processor_name=self.name,
                success=False,
                errors=["Chat nicht gefunden"],
            )

        # Suche nach potenziell ähnlichen Chats
        candidates = search_chats(current.topic, db_path, limit=20)

        # Berechne Ähnlichkeits-Scores
        scored = []
        current_tags = set(current.tags)

        for candidate in candidates:
            if candidate.id == chat_id:
                continue

            candidate_tags = set(candidate.tags)
            score = self._calculate_similarity(
                current_tags,
                current.topic,
                current.task,
                candidate_tags,
                candidate.topic,
                candidate.task,
            )

            if score >= self._MIN_SIMILARITY_SCORE:
                scored.append((candidate.id, score))

        # Sortiere nach Score (absteigend)
        scored.sort(key=lambda x: x[1], reverse=True)

        # Erstelle Links für die besten Matches
        links_created = []
        for target_id, score in scored[: self._MAX_LINKS]:
            link_chats(
                chat_id,
                target_id,
                link_type="similar",
                weight=score,
                db_path=db_path,
            )
            links_created.append(
                {"target_id": target_id, "score": round(score, 3)}
            )

        return PostProcessResult(
            processor_name=self.name,
            success=True,
            data={
                "links_created": len(links_created),
                "links": links_created,
            },
        )

    def _calculate_similarity(
        self,
        tags_a: set[str],
        topic_a: str,
        task_a: str,
        tags_b: set[str],
        topic_b: str,
        task_b: str,
    ) -> float:
        """Berechne einen gewichteten Ähnlichkeits-Score.

        Formel:
            score = 0.4 * tag_jaccard + 0.3 * topic_sim + 0.3 * task_sim
        """
        # Tag-Ähnlichkeit (Jaccard-Index)
        if tags_a or tags_b:
            intersection = len(tags_a & tags_b)
            union = len(tags_a | tags_b)
            tag_sim = intersection / union if union > 0 else 0.0
        else:
            tag_sim = 0.0

        # Text-Ähnlichkeit (einfaches Word-Overlap)
        topic_sim = self._word_overlap(topic_a, topic_b)
        task_sim = self._word_overlap(task_a, task_b)

        return 0.4 * tag_sim + 0.3 * topic_sim + 0.3 * task_sim

    def _word_overlap(self, text_a: str, text_b: str) -> float:
        """Einfache Word-Overlap-Ähnlichkeit."""
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        if not words_a or not words_b:
            return 0.0

        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return intersection / union if union > 0 else 0.0


# Export für Plugin-Discovery
processor = SimilarityMatcher()

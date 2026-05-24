"""
Fragen-Engine für den Chat-Initialisierungsprozess.

Stellt strukturierte Fragen basierend auf Chat-Typ und Kontext.
Unterstützt:
- Fixe Fragen aus der TypeRegistry
- Konditionale Fragen (nur wenn Bedingung erfüllt)
- KI-antizipierte Zusatzfragen (LLM-generiert)
- Validierung der Antworten
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from app.registry import QuestionTemplate, TypeRegistry
from app.types import ChatType


# =============================================================================
# Antwort-Datenmodell
# =============================================================================

@dataclass
class Answer:
    """Eine gegebene Antwort auf eine Frage."""

    question_key: str
    question_text: str
    value: Any
    field_type: str


@dataclass
class QuestionSession:
    """Ergebnis einer Frage-Session."""

    chat_type: ChatType
    answers: list[Answer] = field(default_factory=list)
    skipped_count: int = 0

    def get(self, key: str, default: Any = None) -> Any:
        """Gib den Wert einer Antwort via Key zurück."""
        for answer in self.answers:
            if answer.question_key == key:
                return answer.value
        return default

    def to_context(self) -> dict[str, Any]:
        """Konvertiere Antworten in ein Context-Dict."""
        return {a.question_key: a.value for a in self.answers}


# =============================================================================
# Frage-Engine Interface
# =============================================================================

class QuestionEngine:
    """Abstrakte Basisklasse für Frage-Engines.

    Ermöglicht verschiedene Interaktionsmodi (CLI, API, TUI)
    durch Austausch der prompt-Funktion.
    """

    def __init__(
        self,
        registry: TypeRegistry,
        prompt_fn: Callable[[str, str, list[str] | None], str],
        confirm_fn: Callable[[str], bool],
    ) -> None:
        """Initialisiere die Engine.

        Args:
            registry: Die TypeRegistry für Frage-Templates.
            prompt_fn: Funktion(text, field_type, choices) -> Antwort-String.
            confirm_fn: Funktion(text) -> bool.
        """
        self.registry = registry
        self.prompt = prompt_fn
        self.confirm = confirm_fn

    def ask_fixed_questions(
        self,
        chat_type: ChatType,
        context: dict[str, Any] | None = None,
    ) -> QuestionSession:
        """Stelle alle fixen Fragen für einen Chat-Typ.

        Args:
            chat_type: Der gewählte Chat-Typ.
            context: Bestehender Kontext (aus vorherigen Antworten).

        Returns:
            Eine QuestionSession mit allen Antworten.
        """
        session = QuestionSession(chat_type=chat_type)
        ctx = context or {}

        entry = self.registry.get(chat_type)
        if entry is None:
            return session

        questions = entry.question_set.get_applicable_questions(ctx)

        for question in questions:
            # Prüfe ob Frage im aktuellen Kontext gestellt werden soll
            if not question.should_ask(ctx):
                session.skipped_count += 1
                continue

            # Stelle die Frage
            value = self._ask_question(question, ctx)

            if value is not None:
                answer = Answer(
                    question_key=question.key,
                    question_text=question.text,
                    value=value,
                    field_type=question.field_type,
                )
                session.answers.append(answer)
                ctx[question.key] = value
            else:
                session.skipped_count += 1

        return session

    def _ask_question(
        self,
        question: QuestionTemplate,
        context: dict[str, Any],
    ) -> Any:
        """Stelle eine einzelne Frage und validiere die Antwort.

        Args:
            question: Das Frage-Template.
            context: Aktueller Antwort-Kontext.

        Returns:
            Die gegebene Antwort (oder None wenn übersprungen).
        """
        # Baue den Prompt-Text
        prompt_text = question.text
        if question.help_text:
            prompt_text += f"\n  ({question.help_text})"
        if question.default is not None:
            prompt_text += f"\n  [Standard: {question.default}]"

        # Stelle die Frage
        raw_answer = self.prompt(
            prompt_text,
            question.field_type,
            question.choices,
        )

        # Überspringen
        if raw_answer.strip() == "" and not question.required:
            return question.default

        # Pflichtfrage: wiederholen bis beantwortet
        while question.required and raw_answer.strip() == "":
            raw_answer = self.prompt(
                f"⚠️  {question.text} (Pflichtfeld)",
                question.field_type,
                question.choices,
            )

        # Typ-Konvertierung
        return self._convert_answer(raw_answer, question)

    def _convert_answer(
        self,
        raw: str,
        question: QuestionTemplate,
    ) -> Any:
        """Konvertiere die rohe String-Antwort in den Zieltyp."""
        if question.field_type == "bool":
            raw_lower = raw.lower().strip()
            return raw_lower in ("y", "yes", "j", "ja", "true", "1", "wahr")

        if question.field_type == "int":
            try:
                return int(raw.strip())
            except ValueError:
                return question.default or 0

        if question.field_type == "choice" and question.choices:
            # Prüfe ob die Antwort in den Choices ist
            raw_stripped = raw.strip()
            for choice in question.choices:
                if choice.lower() == raw_stripped.lower():
                    return choice
            # Versuche nummerische Auswahl
            try:
                idx = int(raw_stripped) - 1
                if 0 <= idx < len(question.choices):
                    return question.choices[idx]
            except ValueError:
                pass
            return raw_stripped

        return raw.strip()

    def generate_anticipated_questions(
        self,
        chat_type: ChatType,
        session: QuestionSession,
        max_questions: int = 4,
    ) -> list[QuestionTemplate]:
        """Generiere KI-antizipierte Zusatzfragen.

        Analysiert den bisherigen Kontext und schlägt typspezifische
        Fragen vor, die noch nicht gestellt wurden.

        Diese Methode kann von einer LLM-Integration überschrieben werden.
        Die Basis-Implementierung nutzt die anticipatable_topics aus
        dem QuestionSet.

        Args:
            chat_type: Der Chat-Typ.
            session: Die bisherige Frage-Session.
            max_questions: Maximale Anzahl Zusatzfragen.

        Returns:
            Liste von zusätzlichen QuestionTemplates.
        """
        entry = self.registry.get(chat_type)
        if entry is None:
            return []

        asked_keys = {a.question_key for a in session.answers}
        context = session.to_context()

        questions = []

        # Generiere Fragen basierend auf anticipatable_topics
        for topic in entry.question_set.anticipatable_topics:
            if len(questions) >= max_questions:
                break
            key = f"ai_{topic.lower().replace(' ', '_')}"
            if key not in asked_keys:
                questions.append(
                    QuestionTemplate(
                        key=key,
                        text=f"KI-Vorschlag — {topic}: Möchtest du dazu "
                        f"noch etwas Spezifisches festlegen?",
                        field_type="text",
                        required=False,
                        help_text=f"Optional: Konkretisiere deine "
                        f"Anforderungen zu '{topic}'.",
                    )
                )

        return questions

    def ask_anticipated_questions(
        self,
        chat_type: ChatType,
        session: QuestionSession,
        max_questions: int = 4,
    ) -> QuestionSession:
        """Stelle KI-antizipierte Zusatzfragen.

        Args:
            chat_type: Der Chat-Typ.
            session: Die bisherige Frage-Session.
            max_questions: Maximale Anzahl Zusatzfragen.

        Returns:
            Die aktualisierte QuestionSession.
        """
        questions = self.generate_anticipated_questions(
            chat_type, session, max_questions
        )

        if not questions:
            return session

        # Frage ob Zusatzfragen gestellt werden sollen
        if not self.confirm(
            f"Sollen {len(questions)} kontextrelevante "
            f"Zusatzfragen gestellt werden?"
        ):
            return session

        ctx = session.to_context()

        for question in questions:
            if question.should_ask(ctx):
                value = self._ask_question(question, ctx)
                if value is not None:
                    session.answers.append(
                        Answer(
                            question_key=question.key,
                            question_text=question.text,
                            value=value,
                            field_type=question.field_type,
                        )
                    )
                    ctx[question.key] = value

        return session

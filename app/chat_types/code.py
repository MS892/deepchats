"""
Chat-Typ-Plugin: code

Demonstriert die Erweiterung des Systems um typspezifische Logik.
Jedes Plugin exportiert ein 'plugin'-Objekt vom Typ ChatTypePlugin.
"""

from app.registry import ChatTypePlugin, QuestionSet, QuestionTemplate
from app.types import ChatType


def _has_repo(context: dict) -> bool:
    """Konditionale Frage: Nur wenn ein Repo existiert."""
    return bool(context.get("repo_url"))


plugin: ChatTypePlugin = ChatTypePlugin(
    chat_type=ChatType.CODE,
    question_set=QuestionSet(
        chat_type=ChatType.CODE,
        fixed_questions=[
            QuestionTemplate(
                key="language",
                text="Welche Programmiersprache wird verwendet?",
                field_type="choice",
                required=True,
                choices=[
                    "Python", "TypeScript", "JavaScript",
                    "Rust", "Go", "Java", "C#", "C++", "Andere",
                ],
                help_text="Die Hauptsprache des Projekts.",
            ),
            QuestionTemplate(
                key="framework",
                text="Welches Framework (falls zutreffend)?",
                field_type="text",
                required=False,
                help_text="z.B. FastAPI, React, Django, Spring Boot",
            ),
            QuestionTemplate(
                key="files_affected",
                text="Welche Dateien/Module sind betroffen?",
                field_type="text",
                required=False,
                help_text="Pfade relativ zum Repo-Root, durch Komma getrennt",
            ),
            QuestionTemplate(
                key="has_tests",
                text="Gibt es bestehende Tests, die aktualisiert werden müssen?",
                field_type="bool",
                required=False,
                default=True,
            ),
            QuestionTemplate(
                key="pr_number",
                text="PR-Nummer (falls Verbindung zu GitHub PR)?",
                field_type="text",
                required=False,
                condition=_has_repo,
                help_text="Optional: Verknüpft diesen Chat mit einer PR",
            ),
        ],
        anticipatable_topics=[
            "API-Design",
            "Datenbank-Migrationen",
            "Error-Handling",
            "Performance-Optimierung",
            "Security-Hardening",
        ],
    ),
)

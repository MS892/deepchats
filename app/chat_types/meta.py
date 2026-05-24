"""
Chat-Typ-Plugin: meta

Für Tooling, Prozessverbesserung und metakognitive Arbeit.
"""

from app.registry import ChatTypePlugin, QuestionSet, QuestionTemplate
from app.types import ChatType


plugin: ChatTypePlugin = ChatTypePlugin(
    chat_type=ChatType.META,
    question_set=QuestionSet(
        chat_type=ChatType.META,
        fixed_questions=[
            QuestionTemplate(
                key="process_area",
                text="Welcher Prozess oder Tool soll verbessert werden?",
                field_type="choice",
                required=True,
                choices=[
                    "Chat-Initialisierung (deepchats selbst)",
                    "Code-Workflow (git, CI/CD, Testing)",
                    "Dokumentations-Prozess",
                    "Entscheidungsfindung",
                    "Wissensmanagement",
                    "Anderer Prozess",
                ],
                help_text="Der zu verbessernde Bereich.",
            ),
            QuestionTemplate(
                key="pain_point",
                text="Was ist der konkrete Schmerzpunkt?",
                field_type="text",
                required=True,
                help_text="Beschreibe, was aktuell nicht gut funktioniert.",
            ),
            QuestionTemplate(
                key="scope",
                text="Soll die Lösung generisch oder spezifisch sein?",
                field_type="choice",
                required=False,
                choices=[
                    "Generisch (für alle Chats/Typen)",
                    "Typspezifisch (nur für bestimmten Chat-Typ)",
                    "Projektspezifisch (nur für ein Repo)",
                ],
                default="Generisch (für alle Chats/Typen)",
                help_text="Reichweite der Änderung.",
            ),
            QuestionTemplate(
                key="backward_compat",
                text="Müssen bestehende Strukturen erhalten bleiben?",
                field_type="bool",
                required=False,
                default=True,
                help_text="Rückwärtskompatibilität zu existierenden Chats.",
            ),
        ],
        anticipatable_topics=[
            "Plugin-Entwicklung",
            "Registry-Erweiterung",
            "Datenbank-Migration",
            "UI/UX-Verbesserung",
        ],
    ),
)

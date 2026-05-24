"""
Chat-Typ-Plugin: guide

Für Tutorials, Anleitungen und Schritt-für-Schritt-Erklärungen.
"""

from app.registry import ChatTypePlugin, QuestionSet, QuestionTemplate
from app.types import ChatType


plugin: ChatTypePlugin = ChatTypePlugin(
    chat_type=ChatType.GUIDE,
    question_set=QuestionSet(
        chat_type=ChatType.GUIDE,
        fixed_questions=[
            QuestionTemplate(
                key="knowledge_level",
                text="Welcher Wissensstand besteht bereits?",
                field_type="choice",
                required=True,
                choices=[
                    "Anfänger (keine Vorkenntnisse)",
                    "Grundkenntnisse (Basics bekannt)",
                    "Fortgeschritten (praktische Erfahrung)",
                    "Experte (tiefes Verständnis)",
                ],
                help_text="Bestimmt die Detailtiefe der Erklärung.",
            ),
            QuestionTemplate(
                key="practical",
                text="Soll das Ergebnis praktisch anwendbar sein?",
                field_type="bool",
                required=False,
                default=True,
                help_text="Wenn ja: mit Code-Beispielen und Übungen.",
            ),
            QuestionTemplate(
                key="depth",
                text="Bevorzugte Tiefe?",
                field_type="choice",
                required=False,
                choices=[
                    "Überblick (30.000 Fuß)",
                    "Verständnis (Konzepte + Beispiele)",
                    "Tiefgang (Interna + Edge Cases)",
                ],
                default="Verständnis (Konzepte + Beispiele)",
                help_text="Wie tief soll die Erklärung gehen?",
            ),
            QuestionTemplate(
                key="output_format",
                text="Wie soll das Ergebnis aufbereitet werden?",
                field_type="choice",
                required=False,
                choices=[
                    "Fließtext-Erklärung",
                    "Schritt-für-Schritt-Anleitung",
                    "FAQ / Q&A",
                    "Cheat-Sheet",
                ],
                default="Schritt-für-Schritt-Anleitung",
            ),
        ],
        anticipatable_topics=[
            "Framework-Grundlagen",
            "Best Practices",
            "Migration-Guide",
            "Troubleshooting",
        ],
    ),
)

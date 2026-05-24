"""
Chat-Typ-Plugin: thinktank

Maximal pedantischer, wissenschaftlich notierter Analyse-Chat.
Hinterfragt jede Fragestellung aus sämtlichen Blickwinkeln,
dokumentiert Ergebnisse in SQLite, generiert diagrammfähige
Auswertungen und schlägt Folgefragen vor.
"""

from app.registry import ChatTypePlugin, QuestionSet, QuestionTemplate
from app.types import ChatType


def _is_research(context: dict) -> bool:
    return context.get("task_type") == "research"


plugin: ChatTypePlugin = ChatTypePlugin(
    chat_type=ChatType.RESEARCH,
    question_set=QuestionSet(
        chat_type=ChatType.RESEARCH,
        fixed_questions=[
            QuestionTemplate(
                key="task_type",
                text="Art der Thinktank-Analyse?",
                field_type="choice",
                required=True,
                choices=[
                    "research (breite Recherche + Analyse)",
                    "strategy (strategische Planung)",
                    "audit (bestehendes prüfen + optimieren)",
                    "ideation (kreative Lösungsfindung)",
                    "mixed (Kombination aus obigen)",
                ],
                help_text="Bestimmt die Analysetiefe und Methodik.",
            ),
            QuestionTemplate(
                key="depth",
                text="Analysetiefe?",
                field_type="choice",
                required=True,
                choices=[
                    "exhaustive (jeder Stein wird umgedreht)",
                    "deep (gründlich, aber fokussiert)",
                    "broad (breites Spektrum, moderate Tiefe)",
                ],
                default="exhaustive (jeder Stein wird umgedreht)",
                help_text="Thinktank-Standard: exhaustive.",
            ),
            QuestionTemplate(
                key="output_sql",
                text="Ergebnisse in SQLite-Datenbank speichern?",
                field_type="bool",
                required=False,
                default=True,
                help_text="Ermöglicht spätere SQL-basierte Auswertungen.",
            ),
            QuestionTemplate(
                key="output_diagrams",
                text="Diagramm-fähige Datensätze generieren?",
                field_type="bool",
                required=False,
                default=True,
                help_text="CSV/JSON für Visualisierungen (PlantUML, Mermaid).",
            ),
            QuestionTemplate(
                key="anticipate_questions",
                text="Am Ende Folgefragen antizipieren?",
                field_type="bool",
                required=False,
                default=True,
                help_text="Thinktank schlägt wichtigste Anschlussfragen vor.",
            ),
            QuestionTemplate(
                key="constraints",
                text="Gibt es Randbedingungen oder Einschränkungen?",
                field_type="text",
                required=False,
                help_text="z.B. Budget, Zeitrahmen, rechtliche Grenzen.",
            ),
        ],
        anticipatable_topics=[
            "Risikoanalyse & Worst-Case-Szenarien",
            "Unkonventionelle Methoden & Laterales Denken",
            "Quantitative Modellierung & Simulation",
            "Regulatorische Grauzonen & Optimierung",
            "Cross-Domain Knowledge Transfer",
            "Historische Präzedenzfälle",
            "Emerging Trends & Weak Signals",
        ],
    ),
)

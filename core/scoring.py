"""
core/scoring.py
Berechnet Subskalen-Rohwerte und klassifiziert sie.
"""

from __future__ import annotations
from dataclasses import dataclass


CLASSIFICATION_LABELS = {
    "unauffaellig": "unauffällig",
    "grenzwertig": "grenzwertig",
    "auffaellig": "auffällig",
}


@dataclass
class SubscaleResult:
    name: str
    raw_score: int
    max_score: int
    classification_key: str  # 'unauffaellig' | 'grenzwertig' | 'auffaellig'

    @property
    def classification_label(self) -> str:
        return CLASSIFICATION_LABELS[self.classification_key]

    @property
    def color(self) -> str:
        """Gibt eine Farbe für die UI-Darstellung zurück."""
        return {
            "unauffaellig": "#2ecc71",
            "grenzwertig":  "#f39c12",
            "auffaellig":   "#e74c3c",
        }[self.classification_key]


def compute_scores(
    answers: dict[int, int],   # {question_id: answer_index (0-3)}
    subscales: dict,            # aus config["subscales"]
    answer_values: list[int],   # globale Punktwerte (Fallback)
    question_answer_values: dict | None = None,  # {"1": [0,0,1,2], ...} – pro Frage
) -> list[SubscaleResult]:
    """
    Berechnet für jede Subskala den Rohwert und die Klassifikation.

    :param answers: {Frage-ID (int): ausgewählter Antwort-Index (0–3)}
    :param subscales: dict aus config.json
    :param answer_values: Liste der 4 Punktwerte pro Antwortoption (globaler Standard)
    :param question_answer_values: optionale per-Frage-Überschreibung der Punktwerte
    :return: Liste von SubscaleResult
    """
    q_vals = question_answer_values or {}
    results = []

    for name, info in subscales.items():
        items: list[int] = info["items"]
        thresholds: dict = info["thresholds"]

        raw_score = 0
        max_score = 0
        for qid in items:
            vals = q_vals.get(str(qid), answer_values)
            answer_index = answers.get(qid, 0)
            raw_score += vals[answer_index]
            max_score += vals[-1]  # höchster Wert für diese Frage

        # Klassifikation
        if raw_score >= thresholds["auffaellig"]:
            key = "auffaellig"
        elif raw_score >= thresholds["grenzwertig"]:
            key = "grenzwertig"
        else:
            key = "unauffaellig"

        results.append(SubscaleResult(
            name=name,
            raw_score=raw_score,
            max_score=max_score,
            classification_key=key,
        ))

    return results

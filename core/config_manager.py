"""
core/config_manager.py
Singleton-Manager für das Lesen und Schreiben der config.json.
"""

import json
import hashlib
import os
import copy

# Gültige Auswerter-Schlüssel (Reihenfolge wird in der UI verwendet)
RESPONDENT_KEYS = ["Mutter", "Vater", "Lehrer", "Selbst", "Sonstige"]


def _default_thresholds(grenzwertig: int, auffaellig: int) -> dict:
    """Erzeugt ein per-Auswerter-Schwellenwert-Dict mit identischen Startwerten."""
    return {r: {"grenzwertig": grenzwertig, "auffaellig": auffaellig}
            for r in RESPONDENT_KEYS}


_DEFAULT_CONFIG = {
    "admin_password_hash": "ac9689e2272427085e35b9d3e3e8bed88cb3434828b43b86fc0596cad4c6e270",
    "answer_labels": ["gar nicht", "kaum", "manchmal", "häufig"],
    "answer_values": [0, 0, 1, 2],
    "question_answer_values": {},
    "questionnaire_instruction": "Bitte kreuzen Sie für jede Aussage an, wie häufig das beschriebene Verhalten auf die beurteilte Person zutrifft.",
    "expiry_date": "",
    "questions": {str(i): f"Frage {i}: [Bitte Text einfügen]" for i in range(1, 34)},
    "subscales": {
        "Emotionale Probleme": {
            "items": [1, 2, 4, 7, 13, 19, 21, 23, 30],
            "thresholds": _default_thresholds(6, 8)
        },
        "Verhaltensprobleme": {
            "items": [10, 12, 20, 25, 26, 28, 31, 32, 33],
            "thresholds": _default_thresholds(6, 8)
        },
        "Verhaltensprobleme in Peergroup": {
            "items": [3, 6, 9, 24, 29],
            "thresholds": _default_thresholds(4, 6)
        },
        "Hyperaktivität & Impulsivität": {
            "items": [5, 14, 15, 16, 17],
            "thresholds": _default_thresholds(4, 6)
        },
        "Aufmerksamkeit- und Konzentrationsstörung": {
            "items": [8, 11, 18, 22, 27],
            "thresholds": _default_thresholds(4, 6)
        }
    }
}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = None
        return cls._instance

    def load(self):
        """Lädt die Konfiguration von der Datei. Bei Fehler: Standardwerte."""
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge mit Defaults, damit fehlende Felder aufgefüllt werden
            merged = copy.deepcopy(_DEFAULT_CONFIG)
            merged.update(data)
            self._config = merged
            self._migrate_thresholds()
        except (FileNotFoundError, json.JSONDecodeError):
            self._config = copy.deepcopy(_DEFAULT_CONFIG)
            self.save()

    def _migrate_thresholds(self):
        """Migriert alte flat-Schwellenwerte {grenzwertig, auffaellig} in das
        neue per-Auswerter-Format {Mutter: {...}, Vater: {...}, ...}."""
        changed = False
        for name, info in self._config["subscales"].items():
            t = info["thresholds"]
            first_val = next(iter(t.values()), None)
            if first_val is None or isinstance(first_val, dict):
                continue  # bereits im neuen Format
            # Altes Format: gleiche Werte für alle Auswerter übernehmen
            info["thresholds"] = {r: copy.deepcopy(t) for r in RESPONDENT_KEYS}
            changed = True
        if changed:
            self.save()

    def save(self):
        """Speichert die aktuelle Konfiguration in die Datei."""
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    @property
    def config(self):
        if self._config is None:
            self.load()
        return self._config

    # ------------------------------------------------------------------ #
    #  Convenience-Getter                                                  #
    # ------------------------------------------------------------------ #

    def get_questions(self) -> dict:
        return self.config["questions"]

    def get_answer_labels(self) -> list:
        return self.config["answer_labels"]

    def get_answer_values(self) -> list:
        return self.config["answer_values"]

    def get_question_answer_values(self) -> dict:
        """Gibt {str(qid): [w0, w1, w2, w3]} zurück (nur Fragen mit Überschreibung)."""
        return self.config.get("question_answer_values", {})

    def get_questionnaire_instruction(self) -> str:
        return self.config.get("questionnaire_instruction", "")

    def get_expiry_date(self) -> str:
        """Gibt das Ablaufdatum als String (YYYY-MM-DD) oder '' zurück."""
        return self.config.get("expiry_date", "")

    def get_subscales(self) -> dict:
        return self.config["subscales"]

    def get_subscale_thresholds(self, subscale_name: str) -> dict:
        return self.config["subscales"][subscale_name]["thresholds"]

    def get_subscales_for_respondent(self, respondent: str) -> dict:
        """Gibt die Subskalen-Definition zurück, wobei 'thresholds' auf die
        auswerter-spezifischen Werte aufgelöst ist (flach: grenzwertig/auffaellig).
        Unbekannte Auswerter (freie Sonstige-Eingabe) verwenden 'Sonstige'."""
        key = respondent if respondent in RESPONDENT_KEYS else "Sonstige"
        result = {}
        for name, info in self.config["subscales"].items():
            t = info["thresholds"]
            first_val = next(iter(t.values()), None)
            if isinstance(first_val, dict):
                resolved = t.get(key, t.get("Sonstige", {"grenzwertig": 4, "auffaellig": 6}))
            else:
                resolved = t  # Fallback für altes Format
            result[name] = {"items": info["items"], "thresholds": resolved}
        return result

    # ------------------------------------------------------------------ #
    #  Admin / Passwort                                                    #
    # ------------------------------------------------------------------ #

    def verify_password(self, password: str) -> bool:
        h = hashlib.sha256(password.encode()).hexdigest()
        return h == self.config["admin_password_hash"]

    def set_password(self, new_password: str):
        self.config["admin_password_hash"] = hashlib.sha256(
            new_password.encode()
        ).hexdigest()
        self.save()

    # ------------------------------------------------------------------ #
    #  Admin-Schreibzugriff                                                #
    # ------------------------------------------------------------------ #

    def set_question_text(self, q_id: int, text: str):
        self.config["questions"][str(q_id)] = text
        self.save()

    def set_answer_label(self, index: int, label: str):
        self.config["answer_labels"][index] = label
        self.save()

    def set_answer_value(self, index: int, value: int):
        self.config["answer_values"][index] = int(value)
        self.save()

    def set_threshold(self, subscale: str, respondent: str, key: str, value: int):
        """Setzt einen Schwellenwert für eine bestimmte Auswerter-Rolle.
        key: 'grenzwertig' oder 'auffaellig'"""
        self.config["subscales"][subscale]["thresholds"].setdefault(
            respondent, {"grenzwertig": 4, "auffaellig": 6}
        )[key] = int(value)
        self.save()

    def set_subscale_items(self, subscale: str, items: list):
        self.config["subscales"][subscale]["items"] = [int(x) for x in items]
        self.save()

    def bulk_save(self):
        """Alle Änderungen auf einmal speichern (wird aus Admin-View aufgerufen)."""
        self.save()

"""
views/questionnaire_view.py
Fragebogen: 33 Fragen mit je 4 Antwort-Radiobuttons + Fortschrittsbalken.
"""

import customtkinter as ctk
from core.config_manager import ConfigManager


class QuestionnaireView(ctk.CTkFrame):
    def __init__(self, master, on_submit_callback):
        """
        :param master: Übergeordnetes Fenster
        :param on_submit_callback: Funktion(answers: dict[int, int]) → aufgerufen nach "Auswerten"
        """
        super().__init__(master, fg_color="transparent")
        self._on_submit = on_submit_callback
        self._cfg = ConfigManager()
        self._answers: dict[int, ctk.IntVar] = {}
        self._build_ui()

    # ------------------------------------------------------------------ #

    def _build_ui(self):
        # ---------- Kopfzeile ----------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 0))

        ctk.CTkLabel(
            header,
            text="Fragebogen",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        self._progress_label = ctk.CTkLabel(
            header,
            text="0 / 33 beantwortet",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
        )
        self._progress_label.pack(side="right")

        self._progress_bar = ctk.CTkProgressBar(self, width=400)
        self._progress_bar.pack(fill="x", padx=24, pady=(6, 4))
        self._progress_bar.set(0)

        # ---------- Instruktionstext ----------
        self._instruction_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13, slant="italic"),
            text_color="gray60",
            wraplength=700,
            justify="left",
            anchor="w",
        )
        self._instruction_label.pack(fill="x", padx=28, pady=(4, 8))

        # ---------- Scrollbarer Bereich ----------
        self._scroll = ctk.CTkScrollableFrame(self, label_text="")
        self._scroll.pack(fill="both", expand=True, padx=24, pady=(0, 8))
        self._scroll.columnconfigure(0, weight=1)

        self._question_widgets = []
        self._render_questions()

        # ---------- Auswerten-Button ----------
        self._submit_btn = ctk.CTkButton(
            self,
            text="Auswerten",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=200,
            height=44,
            state="disabled",
            command=self._submit,
        )
        self._submit_btn.pack(pady=(4, 16))

    # ------------------------------------------------------------------ #

    def _render_questions(self):
        """Rendert alle 33 Fragen neu (wird auch beim Reload aus Admin verwendet)."""
        for widget in self._scroll.winfo_children():
            widget.destroy()

        self._answers.clear()
        questions = self._cfg.get_questions()
        labels = self._cfg.get_answer_labels()

        # Instruktionstext aktualisieren
        instruction = self._cfg.get_questionnaire_instruction()
        self._instruction_label.configure(text=instruction)

        for idx in range(1, 34):
            qid = idx
            text = questions.get(str(qid), f"Frage {qid}: [Bitte Text einfügen]")
            var = ctk.IntVar(value=-1)
            self._answers[qid] = var

            # Fragen-Container
            card = ctk.CTkFrame(self._scroll, corner_radius=10)
            card.grid(row=idx - 1, column=0, sticky="ew", padx=4, pady=4)
            card.columnconfigure(0, weight=1)

            # Fragentext
            ctk.CTkLabel(
                card,
                text=text,
                font=ctk.CTkFont(size=15),
                wraplength=600,
                justify="left",
                anchor="w",
            ).grid(row=0, column=0, columnspan=4, sticky="w", padx=14, pady=(10, 6))

            # Antwort-Radiobuttons
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))

            for i, lbl in enumerate(labels):
                rb = ctk.CTkRadioButton(
                    btn_row,
                    text=lbl,
                    variable=var,
                    value=i,
                    font=ctk.CTkFont(size=12),
                    command=lambda qid_=qid: self._on_answer_change(qid_),
                )
                rb.pack(side="left", padx=12)

    # ------------------------------------------------------------------ #

    def _on_answer_change(self, qid: int):
        answered = sum(1 for v in self._answers.values() if v.get() >= 0)
        total = len(self._answers)

        self._progress_bar.set(answered / total)
        self._progress_label.configure(text=f"{answered} / {total} beantwortet")

        if answered == total:
            self._submit_btn.configure(state="normal")
        else:
            self._submit_btn.configure(state="disabled")

    def _submit(self):
        answer_dict = {qid: var.get() for qid, var in self._answers.items()}
        self._on_submit(answer_dict)

    # ------------------------------------------------------------------ #

    def reload(self):
        """Lädt Fragetexte + Antwortlabels neu nach Admin-Änderungen."""
        self._render_questions()
        self._progress_bar.set(0)
        self._progress_label.configure(text="0 / 33 beantwortet")
        self._submit_btn.configure(state="disabled")

    def reset(self):
        """Setzt alle Antworten zurück."""
        self.reload()

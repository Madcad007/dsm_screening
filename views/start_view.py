"""
views/start_view.py
Startseite: Respondenten-Auswahl (Mutter / Vater / Lehrer / Sonstige)
"""

import customtkinter as ctk


RESPONDENT_OPTIONS = ["Mutter", "Vater", "Lehrer", "Selbst", "Sonstige"]


class StartView(ctk.CTkFrame):
    def __init__(self, master, on_start_callback):
        """
        :param master: Das übergeordnete CTk-Fenster
        :param on_start_callback: Funktion(respondent: str) → wird bei Start aufgerufen
        """
        super().__init__(master, fg_color="transparent")
        self._on_start = on_start_callback
        self._selected = ctk.StringVar(value="")
        self._build_ui()

    # ------------------------------------------------------------------ #

    def _build_ui(self):
        # ---------- Titel ----------
        ctk.CTkLabel(
            self,
            text="DSM-Screening",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(pady=(48, 4))

        ctk.CTkLabel(
            self,
            text="Bitte wählen Sie die ausfüllende Person aus.",
            font=ctk.CTkFont(size=14),
            text_color="gray60",
        ).pack(pady=(0, 32))

        # ---------- RadioButton-Gruppe ----------
        radio_frame = ctk.CTkFrame(self, fg_color="transparent")
        radio_frame.pack(pady=8)

        for option in RESPONDENT_OPTIONS:
            ctk.CTkRadioButton(
                radio_frame,
                text=option,
                variable=self._selected,
                value=option,
                font=ctk.CTkFont(size=14),
                command=self._on_radio_change,
            ).pack(anchor="w", padx=32, pady=6)

        # ---------- Sonstige-Textfeld ----------
        self._sonstige_entry = ctk.CTkEntry(
            self,
            placeholder_text="Bitte Bezeichnung eingeben …",
            width=280,
            font=ctk.CTkFont(size=13),
        )
        # Wird erst sichtbar wenn "Sonstige" gewählt
        self._sonstige_entry.pack(pady=(4, 24))
        self._sonstige_entry.pack_forget()

        # ---------- Start-Button ----------
        self._start_btn = ctk.CTkButton(
            self,
            text="Fragebogen starten",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=220,
            height=44,
            state="disabled",
            command=self._on_start_clicked,
        )
        self._start_btn.pack(pady=8)

    # ------------------------------------------------------------------ #

    def _on_radio_change(self):
        selection = self._selected.get()
        if selection == "Sonstige":
            self._sonstige_entry.pack(pady=(4, 24))
        else:
            self._sonstige_entry.pack_forget()
        self._validate_form()

    def _validate_form(self, *_):
        selection = self._selected.get()
        if selection == "Sonstige":
            if self._sonstige_entry.get().strip():
                self._start_btn.configure(state="normal")
            else:
                self._start_btn.configure(state="disabled")
                self._sonstige_entry.bind("<KeyRelease>", self._validate_form)
        elif selection:
            self._start_btn.configure(state="normal")
        else:
            self._start_btn.configure(state="disabled")

    def _on_start_clicked(self):
        selection = self._selected.get()
        if selection == "Sonstige":
            custom = self._sonstige_entry.get().strip()
            respondent = custom if custom else "Sonstige"
        else:
            respondent = selection
        self._on_start(respondent)

    # ------------------------------------------------------------------ #

    def reset(self):
        """Setzt die View zurück (für neuen Durchlauf)."""
        self._selected.set("")
        self._sonstige_entry.delete(0, "end")
        self._sonstige_entry.pack_forget()
        self._start_btn.configure(state="disabled")

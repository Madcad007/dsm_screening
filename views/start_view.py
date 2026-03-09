"""
views/start_view.py
Startseite: Kind-Daten + Respondenten-Auswahl
"""

import datetime
import customtkinter as ctk


RESPONDENT_OPTIONS = ["Mutter", "Vater", "Lehrer", "Selbst", "Sonstige"]


class StartView(ctk.CTkFrame):
    def __init__(self, master, on_start_callback):
        """
        :param master: Das übergeordnete CTk-Fenster
        :param on_start_callback: Funktion(respondent, child_info) → wird bei Start aufgerufen
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
        ).pack(pady=(36, 4))

        ctk.CTkLabel(
            self,
            text="Bitte Angaben zum Kind und ausfüllender Person eintragen.",
            font=ctk.CTkFont(size=14),
            text_color="gray60",
        ).pack(pady=(0, 20))

        # ---------- Kind-Daten ----------
        card = ctk.CTkFrame(self, corner_radius=10)
        card.pack(pady=(0, 18), padx=40, fill="x")

        ctk.CTkLabel(
            card, text="Angaben zum Kind",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="gray60",
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(12, 4))

        # Nachname
        ctk.CTkLabel(card, text="Nachname", font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, sticky="w", padx=(16, 4), pady=(4, 2)
        )
        self._nachname_entry = ctk.CTkEntry(
            card, placeholder_text="Nachname", width=180, font=ctk.CTkFont(size=13)
        )
        self._nachname_entry.grid(row=2, column=0, sticky="ew", padx=(16, 8), pady=(0, 10))
        self._nachname_entry.bind("<KeyRelease>", self._validate_form)

        # Vorname
        ctk.CTkLabel(card, text="Vorname", font=ctk.CTkFont(size=12)).grid(
            row=1, column=1, sticky="w", padx=(8, 4), pady=(4, 2)
        )
        self._vorname_entry = ctk.CTkEntry(
            card, placeholder_text="Vorname", width=180, font=ctk.CTkFont(size=13)
        )
        self._vorname_entry.grid(row=2, column=1, sticky="ew", padx=(8, 8), pady=(0, 10))
        self._vorname_entry.bind("<KeyRelease>", self._validate_form)

        # Geburtsdatum
        ctk.CTkLabel(card, text="Geburtsdatum (TT.MM.JJJJ)", font=ctk.CTkFont(size=12)).grid(
            row=1, column=2, sticky="w", padx=(8, 4), pady=(4, 2)
        )
        self._geb_entry = ctk.CTkEntry(
            card, placeholder_text="TT.MM.JJJJ", width=140, font=ctk.CTkFont(size=13)
        )
        self._geb_entry.grid(row=2, column=2, sticky="ew", padx=(8, 8), pady=(0, 10))
        self._geb_entry.bind("<KeyRelease>", self._validate_form)

        # Datum der Angabe (=heute)
        ctk.CTkLabel(card, text="Datum der Angabe (TT.MM.JJJJ)", font=ctk.CTkFont(size=12)).grid(
            row=1, column=3, sticky="w", padx=(8, 16), pady=(4, 2)
        )
        self._date_entry = ctk.CTkEntry(
            card, placeholder_text="TT.MM.JJJJ", width=140, font=ctk.CTkFont(size=13)
        )
        self._date_entry.insert(0, datetime.date.today().strftime("%d.%m.%Y"))
        self._date_entry.grid(row=2, column=3, sticky="ew", padx=(8, 16), pady=(0, 10))
        self._date_entry.bind("<KeyRelease>", self._validate_form)

        for c in range(4):
            card.columnconfigure(c, weight=1)

        # ---------- RadioButton-Gruppe ----------
        ctk.CTkLabel(
            self, text="Ausfüllende Person",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="gray60",
        ).pack(anchor="w", padx=40)

        radio_frame = ctk.CTkFrame(self, fg_color="transparent")
        radio_frame.pack(pady=(4, 2), anchor="w", padx=40)

        for option in RESPONDENT_OPTIONS:
            ctk.CTkRadioButton(
                radio_frame,
                text=option,
                variable=self._selected,
                value=option,
                font=ctk.CTkFont(size=14),
                command=self._on_radio_change,
            ).pack(side="left", padx=12, pady=6)

        # ---------- Sonstige-Textfeld ----------
        self._sonstige_entry = ctk.CTkEntry(
            self,
            placeholder_text="Bitte Bezeichnung eingeben …",
            width=280,
            font=ctk.CTkFont(size=13),
        )
        self._sonstige_entry.pack(pady=(4, 8))
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
        self._start_btn.pack(pady=16)

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
        has_respondent = bool(
            selection and
            (selection != "Sonstige" or self._sonstige_entry.get().strip())
        )
        has_child = (
            bool(self._nachname_entry.get().strip()) and
            bool(self._vorname_entry.get().strip()) and
            bool(self._geb_entry.get().strip()) and
            bool(self._date_entry.get().strip())
        )
        if has_respondent and has_child:
            self._start_btn.configure(state="normal")
        else:
            self._start_btn.configure(state="disabled")
        if selection == "Sonstige":
            self._sonstige_entry.bind("<KeyRelease>", self._validate_form)

    def _on_start_clicked(self):
        selection = self._selected.get()
        if selection == "Sonstige":
            custom = self._sonstige_entry.get().strip()
            respondent = custom if custom else "Sonstige"
        else:
            respondent = selection
        child_info = {
            "nachname":        self._nachname_entry.get().strip(),
            "vorname":         self._vorname_entry.get().strip(),
            "geburtsdatum":    self._geb_entry.get().strip(),
            "assessment_date": self._date_entry.get().strip(),
        }
        self._on_start(respondent, child_info)

    # ------------------------------------------------------------------ #

    def reset(self):
        """Setzt die View zurück (für neuen Durchlauf)."""
        self._selected.set("")
        self._sonstige_entry.delete(0, "end")
        self._sonstige_entry.pack_forget()
        self._nachname_entry.delete(0, "end")
        self._vorname_entry.delete(0, "end")
        self._geb_entry.delete(0, "end")
        self._date_entry.delete(0, "end")
        self._date_entry.insert(0, datetime.date.today().strftime("%d.%m.%Y"))
        self._start_btn.configure(state="disabled")

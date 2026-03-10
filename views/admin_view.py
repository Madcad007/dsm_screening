"""
views/admin_view.py
Admin-Bereich: Passwortgeschützte Einstellungen.
Tabs: Fragetexte | Antwortoptionen | Schwellenwerte | Passwort ändern
"""

import tkinter.colorchooser as _colorchooser

import customtkinter as ctk
from core.config_manager import ConfigManager, RESPONDENT_KEYS


class AdminLoginDialog(ctk.CTkToplevel):
    """Modaler Dialog zur Passwort-Eingabe."""

    def __init__(self, master, on_success):
        super().__init__(master)
        self.title("Admin-Login")
        self.geometry("360x200")
        self.resizable(False, False)
        self.grab_set()
        self._on_success = on_success
        self._cfg = ConfigManager()
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self,
            text="Admin-Passwort",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(24, 4))

        self._pw_entry = ctk.CTkEntry(
            self, show="•", width=240, placeholder_text="Passwort eingeben"
        )
        self._pw_entry.pack(pady=8)
        self._pw_entry.bind("<Return>", lambda _: self._check())

        self._error_label = ctk.CTkLabel(
            self, text="", text_color="#e74c3c", font=ctk.CTkFont(size=12)
        )
        self._error_label.pack()

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=12)
        ctk.CTkButton(btn_row, text="Abbrechen", width=110, command=self.destroy).pack(
            side="left", padx=6
        )
        ctk.CTkButton(
            btn_row, text="Anmelden", width=110, command=self._check
        ).pack(side="left", padx=6)

    def _check(self):
        pw = self._pw_entry.get()
        if self._cfg.verify_password(pw):
            self.destroy()
            self._on_success()
        else:
            self._error_label.configure(text="Falsches Passwort.")
            self._pw_entry.delete(0, "end")


# ======================================================================


class AdminView(ctk.CTkToplevel):
    """Vollständiger Admin-Bereich (in einem separaten Fenster)."""

    def __init__(self, master, on_close_callback=None):
        super().__init__(master)
        self.title("Admin-Einstellungen")
        self.geometry("1060x700")
        self.minsize(900, 520)
        self.grab_set()
        self._cfg = ConfigManager()
        self._on_close_callback = on_close_callback
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build()

    # ------------------------------------------------------------------ #

    def _build(self):
        ctk.CTkLabel(
            self,
            text="Admin-Einstellungen",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(16, 8))

        self._tabview = ctk.CTkTabview(self)
        self._tabview.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        for tab_name in [
            "Fragetexte",
            "Antwortoptionen",
            "Schwellenwerte",
            "Passwort ändern",
        ]:
            self._tabview.add(tab_name)

        # Subskalen-Farben (vor den Tabs laden, da Fragetexte-Tab sie benötigt)
        self._subscale_colors: dict[str, str] = dict(self._cfg.get_subscale_colors())
        self._color_buttons: dict[str, ctk.CTkButton] = {}

        self._build_questions_tab()
        self._build_answers_tab()
        self._build_thresholds_tab()
        self._build_password_tab()

        # Speichern-Button
        ctk.CTkButton(
            self,
            text="Alle Änderungen speichern",
            width=220,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save_all,
        ).pack(pady=(0, 12))

    # ------------------------------------------------------------------ #
    # TAB: Fragetexte
    # ------------------------------------------------------------------ #

    def _build_questions_tab(self):
        frame = self._tabview.tab("Fragetexte")
        frame.columnconfigure(0, weight=1)

        # --- Instruktionstext-Eingabe ---
        instr_frame = ctk.CTkFrame(frame, fg_color="transparent")
        instr_frame.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(
            instr_frame,
            text="Hinweistext vor den Fragen:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(side="left", padx=(0, 8))
        self._instruction_entry = ctk.CTkEntry(
            instr_frame,
            font=ctk.CTkFont(size=12),
            placeholder_text="Anleitung für Ausfüllende …",
        )
        self._instruction_entry.insert(0, self._cfg.get_questionnaire_instruction())
        self._instruction_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        scroll = ctk.CTkScrollableFrame(frame, label_text="")
        scroll.pack(fill="both", expand=True)
        scroll.columnconfigure(1, weight=1)   # Textfeld expandiert
        scroll.columnconfigure(2, minsize=180)
        for _c in (0, 3, 4, 5, 6):
            scroll.columnconfigure(_c, minsize=44)

        questions      = self._cfg.get_questions()
        subscales      = self._cfg.get_subscales()
        global_vals    = self._cfg.get_answer_values()
        q_answer_vals  = self._cfg.get_question_answer_values()

        # Rückwärtskarte: qid → Subskala-Name
        qid_to_subscale: dict[int, str] = {}
        for name, info in subscales.items():
            for qid in info["items"]:
                qid_to_subscale[int(qid)] = name

        subscale_names   = list(subscales.keys())
        category_options = ["– Keine –"] + subscale_names

        self._question_entries: dict[int, ctk.CTkEntry] = {}
        self._question_category_vars: dict[int, ctk.StringVar] = {}
        self._question_value_entries: dict[int, list[ctk.CTkEntry]] = {}
        self._question_optionmenus: dict[int, ctk.CTkOptionMenu] = {}

        # --- Kopfzeile ---
        for ci, hl in enumerate(["Frage", "Fragetext", "Kategorie", "W1", "W2", "W3", "W4"]):
            ctk.CTkLabel(
                scroll, text=hl,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="gray60",
                anchor="w",
            ).grid(row=0, column=ci, padx=(8 if ci == 0 else 3, 3), pady=(4, 2), sticky="w")

        # --- Datenzeilen ---
        for i in range(1, 34):
            qid  = i
            text = questions.get(str(qid), "")

            ctk.CTkLabel(
                scroll, text=f"F{i}:",
                font=ctk.CTkFont(size=12),
                width=40, anchor="e",
            ).grid(row=i, column=0, sticky="e", padx=(8, 2), pady=3)

            entry = ctk.CTkEntry(scroll, font=ctk.CTkFont(size=12))
            entry.insert(0, text)
            entry.grid(row=i, column=1, sticky="ew", padx=(0, 6), pady=3)
            self._question_entries[qid] = entry

            # Kategorie-Dropdown
            cur_cat = qid_to_subscale.get(qid, "– Keine –")
            cat_var = ctk.StringVar(value=cur_cat)
            self._question_category_vars[qid] = cat_var
            om = ctk.CTkOptionMenu(
                scroll,
                variable=cat_var,
                values=category_options,
                width=175,
                font=ctk.CTkFont(size=11),
                dynamic_resizing=False,
                command=lambda v, q=qid: self._on_category_change(q, v),
            )
            om.grid(row=i, column=2, padx=(0, 6), pady=3, sticky="w")
            self._question_optionmenus[qid] = om
            self._apply_dropdown_color(qid, cur_cat)

            # Per-Frage-Antwortwerte
            cur_vals = q_answer_vals.get(str(qid), global_vals)
            val_entries: list[ctk.CTkEntry] = []
            for vi in range(4):
                ve = ctk.CTkEntry(scroll, width=40, font=ctk.CTkFont(size=11))
                ve.insert(0, str(cur_vals[vi]) if vi < len(cur_vals) else "0")
                ve.grid(row=i, column=3 + vi, padx=3, pady=3)
                val_entries.append(ve)
            self._question_value_entries[qid] = val_entries

    # ------------------------------------------------------------------ #
    # TAB: Antwortoptionen
    # ------------------------------------------------------------------ #

    def _build_answers_tab(self):
        frame = self._tabview.tab("Antwortoptionen")

        ctk.CTkLabel(
            frame,
            text="Für jede der 4 Antwortoptionen: Beschriftung und Punktwert",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
        ).pack(pady=(8, 12))

        labels = self._cfg.get_answer_labels()
        values = self._cfg.get_answer_values()

        self._answer_label_entries: list[ctk.CTkEntry] = []
        self._answer_value_entries: list[ctk.CTkEntry] = []

        grid = ctk.CTkFrame(frame, fg_color="transparent")
        grid.pack()
        grid.columnconfigure((1, 2), weight=1)

        ctk.CTkLabel(grid, text="Option", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, padx=8, pady=4
        )
        ctk.CTkLabel(
            grid, text="Beschriftung", font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=1, padx=8, pady=4)
        ctk.CTkLabel(
            grid, text="Punktwert", font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=2, padx=8, pady=4)

        for i in range(4):
            ctk.CTkLabel(grid, text=f"Option {i + 1}", font=ctk.CTkFont(size=12)).grid(
                row=i + 1, column=0, padx=8, pady=6
            )

            lbl_entry = ctk.CTkEntry(grid, width=160, font=ctk.CTkFont(size=12))
            lbl_entry.insert(0, labels[i] if i < len(labels) else "")
            lbl_entry.grid(row=i + 1, column=1, padx=8, pady=6)
            self._answer_label_entries.append(lbl_entry)

            val_entry = ctk.CTkEntry(grid, width=80, font=ctk.CTkFont(size=12))
            val_entry.insert(0, str(values[i]) if i < len(values) else "0")
            val_entry.grid(row=i + 1, column=2, padx=8, pady=6)
            self._answer_value_entries.append(val_entry)

    # ------------------------------------------------------------------ #
    # TAB: Schwellenwerte
    # ------------------------------------------------------------------ #

    def _build_thresholds_tab(self):
        frame = self._tabview.tab("Schwellenwerte")

        ctk.CTkLabel(
            frame,
            text="Schwellenwerte pro Subskala und Auswerter (Rohpunkte)",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
        ).pack(pady=(8, 8))

        # ---------- Auswerter-Auswahl ----------
        seg_frame = ctk.CTkFrame(frame, fg_color="transparent")
        seg_frame.pack(pady=(0, 10))

        ctk.CTkLabel(
            seg_frame, text="Auswerter:", font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 8))

        self._threshold_respondent_var = ctk.StringVar(value=RESPONDENT_KEYS[0])
        ctk.CTkSegmentedButton(
            seg_frame,
            values=RESPONDENT_KEYS,
            variable=self._threshold_respondent_var,
            command=self._load_threshold_entries,
        ).pack(side="left")

        # ---------- Tabellen-Grid ----------
        subscales = self._cfg.get_subscales()

        grid = ctk.CTkFrame(frame, fg_color="transparent")
        grid.pack(pady=4)

        ctk.CTkLabel(
            grid, text="Subskala", font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=12, pady=4, sticky="w")
        ctk.CTkLabel(
            grid, text="Grenzwertig ab", font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=1, padx=12, pady=4)
        ctk.CTkLabel(
            grid, text="Auffällig ab", font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=2, padx=12, pady=4)
        ctk.CTkLabel(
            grid, text="Farbe", font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=3, padx=12, pady=4)

        self._threshold_entries: dict[str, dict[str, ctk.CTkEntry]] = {}

        for row_idx, name in enumerate(subscales.keys(), start=1):
            ctk.CTkLabel(
                grid,
                text=name,
                font=ctk.CTkFont(size=12),
                wraplength=240,
                anchor="w",
            ).grid(row=row_idx, column=0, padx=12, pady=6, sticky="w")

            gz_entry = ctk.CTkEntry(grid, width=100, font=ctk.CTkFont(size=12))
            gz_entry.grid(row=row_idx, column=1, padx=12, pady=6)

            af_entry = ctk.CTkEntry(grid, width=100, font=ctk.CTkFont(size=12))
            af_entry.grid(row=row_idx, column=2, padx=12, pady=6)

            self._threshold_entries[name] = {
                "grenzwertig": gz_entry,
                "auffaellig": af_entry,
            }

            color = self._subscale_colors.get(name, "#9e9e9e")
            tc = self._contrast_color(color)
            color_btn = ctk.CTkButton(
                grid,
                text=" ",
                width=80,
                height=28,
                fg_color=color,
                hover_color=color,
                text_color=tc,
                font=ctk.CTkFont(size=11),
                command=lambda n=name: self._pick_subscale_color(n),
            )
            color_btn.grid(row=row_idx, column=3, padx=12, pady=6)
            self._color_buttons[name] = color_btn

        # ---------- In-Memory-Datenpuffer für alle Auswerter ----------
        # {respondent: {subscale: {key: int}}}
        self._threshold_data: dict[str, dict[str, dict[str, int]]] = {}
        for resp in RESPONDENT_KEYS:
            self._threshold_data[resp] = {}
            for name, info in subscales.items():
                t = info["thresholds"]
                first_val = next(iter(t.values()), None)
                if isinstance(first_val, dict):
                    vals = t.get(resp, t.get("Sonstige", {"grenzwertig": 4, "auffaellig": 6}))
                else:
                    vals = t  # Fallback altes Format
                self._threshold_data[resp][name] = {
                    "grenzwertig": int(vals.get("grenzwertig", 4)),
                    "auffaellig": int(vals.get("auffaellig", 6)),
                }

        self._current_threshold_respondent = RESPONDENT_KEYS[0]
        self._load_threshold_entries(RESPONDENT_KEYS[0])

    def _sync_threshold_entries_to_data(self):
        """Schreibt die aktuellen Entry-Werte in den In-Memory-Puffer."""
        resp = self._current_threshold_respondent
        for name, entry_dict in self._threshold_entries.items():
            for key, entry in entry_dict.items():
                try:
                    self._threshold_data[resp][name][key] = int(entry.get())
                except ValueError:
                    pass

    def _load_threshold_entries(self, respondent: str):
        """Speichert aktuelle Eingaben, dann lädt die Werte des neuen Auswerters."""
        self._sync_threshold_entries_to_data()
        self._current_threshold_respondent = respondent
        for name, entry_dict in self._threshold_entries.items():
            vals = self._threshold_data[respondent][name]
            for key, entry in entry_dict.items():
                entry.delete(0, "end")
                entry.insert(0, str(vals.get(key, 4)))

    # ------------------------------------------------------------------ #
    # TAB: Passwort ändern
    # ------------------------------------------------------------------ #

    def _build_password_tab(self):
        frame = self._tabview.tab("Passwort ändern")

        ctk.CTkLabel(
            frame,
            text="Admin-Passwort ändern",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(24, 16))

        def make_row(label_text, show="•"):
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(pady=6)
            ctk.CTkLabel(row, text=label_text, width=180, anchor="e").pack(side="left", padx=8)
            entry = ctk.CTkEntry(row, show=show, width=200)
            entry.pack(side="left")
            return entry

        self._old_pw = make_row("Altes Passwort:")
        self._new_pw1 = make_row("Neues Passwort:")
        self._new_pw2 = make_row("Neues Passwort (wdh.):")

        # ---------- Ablaufdatum ----------
        ctk.CTkLabel(
            frame,
            text="Ablaufdatum des Programms",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(pady=(20, 4))
        ctk.CTkLabel(
            frame,
            text="Format: JJJJ-MM-TT (leer lassen = kein Ablaufdatum)",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
        ).pack()
        expiry_row = ctk.CTkFrame(frame, fg_color="transparent")
        expiry_row.pack(pady=6)
        ctk.CTkLabel(expiry_row, text="Ablaufdatum:", width=180, anchor="e").pack(side="left", padx=8)
        self._expiry_entry = ctk.CTkEntry(expiry_row, width=200, placeholder_text="JJJJ-MM-TT")
        self._expiry_entry.insert(0, self._cfg.get_expiry_date())
        self._expiry_entry.pack(side="left")

        self._pw_change_msg = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12)
        )
        self._pw_change_msg.pack(pady=4)

        ctk.CTkButton(
            frame,
            text="Passwort ändern",
            width=180,
            command=self._change_password,
        ).pack(pady=8)

    # ------------------------------------------------------------------ #
    # Speichern-Logik
    # ------------------------------------------------------------------ #

    def _save_all(self):
        """Speichert alle Änderungen aus allen Tabs."""
        # -- Instruktionstext --
        instr = self._instruction_entry.get().strip()
        self._cfg.config["questionnaire_instruction"] = instr

        # -- Ablaufdatum --
        self._cfg.config["expiry_date"] = self._expiry_entry.get().strip()

        # -- Fragetexte + Kategorie-Zuordnung + Per-Frage-Werte --
        subscale_new_items: dict[str, list] = {
            name: [] for name in self._cfg.get_subscales()
        }
        q_answer_vals_new: dict[str, list] = {}

        for qid, entry in self._question_entries.items():
            text = entry.get().strip()
            if text:
                self._cfg.config["questions"][str(qid)] = text

            # Kategorie → Items neu aufbauen
            cat = self._question_category_vars[qid].get()
            if cat in subscale_new_items:
                subscale_new_items[cat].append(qid)

            # Per-Frage-Antwortwerte
            vals = []
            valid = True
            for ve in self._question_value_entries[qid]:
                try:
                    vals.append(int(ve.get()))
                except ValueError:
                    valid = False
                    break
            if valid:
                q_answer_vals_new[str(qid)] = vals

        # Subskalen-Items zurückschreiben
        for name, items in subscale_new_items.items():
            self._cfg.config["subscales"][name]["items"] = sorted(items)

        self._cfg.config["question_answer_values"] = q_answer_vals_new

        # -- Antwortoptionen --
        for i in range(4):
            lbl = self._answer_label_entries[i].get().strip()
            if lbl:
                self._cfg.config["answer_labels"][i] = lbl
            try:
                val = int(self._answer_value_entries[i].get())
                self._cfg.config["answer_values"][i] = val
            except ValueError:
                pass

        # -- Schwellenwerte --
        self._sync_threshold_entries_to_data()
        for name in self._threshold_entries:
            self._cfg.config["subscales"][name]["thresholds"] = {
                resp: dict(self._threshold_data[resp][name])
                for resp in RESPONDENT_KEYS
            }

        # -- Subskalen-Farben --
        for name, color in self._subscale_colors.items():
            if name in self._cfg.config["subscales"]:
                self._cfg.config["subscales"][name]["color"] = color

        self._cfg.save()
        self._show_save_toast()

    def _show_save_toast(self):
        toast = ctk.CTkToplevel(self)
        toast.geometry("280x60")
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        # Center over admin window
        x = self.winfo_x() + self.winfo_width() // 2 - 140
        y = self.winfo_y() + self.winfo_height() - 100
        toast.geometry(f"+{x}+{y}")
        ctk.CTkLabel(
            toast,
            text="✓  Einstellungen gespeichert",
            font=ctk.CTkFont(size=13),
            text_color="#2ecc71",
        ).pack(expand=True)
        toast.after(2000, toast.destroy)

    def _change_password(self):
        old = self._old_pw.get()
        new1 = self._new_pw1.get()
        new2 = self._new_pw2.get()

        if not self._cfg.verify_password(old):
            self._pw_change_msg.configure(
                text="Altes Passwort ist falsch.", text_color="#e74c3c"
            )
            return
        if len(new1) < 4:
            self._pw_change_msg.configure(
                text="Passwort muss mind. 4 Zeichen haben.", text_color="#f39c12"
            )
            return
        if new1 != new2:
            self._pw_change_msg.configure(
                text="Passwörter stimmen nicht überein.", text_color="#e74c3c"
            )
            return

        self._cfg.set_password(new1)
        self._pw_change_msg.configure(
            text="Passwort erfolgreich geändert!", text_color="#2ecc71"
        )
        self._old_pw.delete(0, "end")
        self._new_pw1.delete(0, "end")
        self._new_pw2.delete(0, "end")

    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # Hilfs-Methoden für Kategoriefarben
    # ------------------------------------------------------------------ #

    def _contrast_color(self, hex_color: str) -> str:
        """Gibt dunklen oder hellen Textfarbe zurück, je nach Hintergrundluminanz."""
        h = hex_color.lstrip("#")
        if len(h) != 6:
            return "#1a1a1a"
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#1a1a1a" if luminance > 0.5 else "#ffffff"

    def _apply_dropdown_color(self, qid: int, category: str):
        """Färbt das Kategorie-OptionMenu für qid passend zur Kategorie ein."""
        om = self._question_optionmenus.get(qid)
        if om is None:
            return
        color = "#9e9e9e" if category == "– Keine –" else self._subscale_colors.get(category, "#9e9e9e")
        tc = self._contrast_color(color)
        om.configure(fg_color=color, button_color=color, text_color=tc)

    def _on_category_change(self, qid: int, value: str):
        """Callback wenn der Nutzer eine andere Kategorie auswählt."""
        self._apply_dropdown_color(qid, value)

    def _pick_subscale_color(self, subscale_name: str):
        """Betriebssystem-Farbwahldialog für eine Subskala."""
        current = self._subscale_colors.get(subscale_name, "#aaaaaa")
        result = _colorchooser.askcolor(
            color=current,
            title=f"Farbe für „{subscale_name}“",
            parent=self,
        )
        if result and result[1]:
            hex_color = result[1]
            self._subscale_colors[subscale_name] = hex_color
            tc = self._contrast_color(hex_color)
            btn = self._color_buttons.get(subscale_name)
            if btn:
                btn.configure(fg_color=hex_color, hover_color=hex_color, text_color=tc)
            # Alle Dropdowns mit dieser Subskala sofort aktualisieren
            for qid in self._question_optionmenus:
                if self._question_category_vars[qid].get() == subscale_name:
                    self._apply_dropdown_color(qid, subscale_name)

    # ------------------------------------------------------------------ #

    def _close(self):
        if self._on_close_callback:
            self._on_close_callback()
        self.destroy()

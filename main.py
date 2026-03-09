"""
main.py
Einstiegspunkt der DSM-Screening-Anwendung.
Verwaltet die Navigation zwischen den Views.
"""

import customtkinter as ctk
import datetime

from core.config_manager import ConfigManager
from core.scoring import compute_scores
from views.start_view import StartView
from views.questionnaire_view import QuestionnaireView
from views.results_view import ResultsView
from views.admin_view import AdminLoginDialog, AdminView

# ---------- Globales Erscheinungsbild ----------
_APPEARANCE_MODE = "light"
ctk.set_appearance_mode(_APPEARANCE_MODE)
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DSM-Screening")
        self.geometry("860x760")
        self.minsize(720, 600)

        self._cfg = ConfigManager()
        self._cfg.load()

        self._respondent: str = ""
        self._child_info: dict = {}
        self._current_view = None
        self._admin_window = None
        self._appearance_mode = "light"

        self._build_titlebar()
        self._build_copyright_bar()
        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.pack(fill="both", expand=True)

        # Views vorinitialisieren
        self._start_view = StartView(self._container, on_start_callback=self._on_start)
        self._questionnaire_view = QuestionnaireView(
            self._container, on_submit_callback=self._on_submit
        )
        self._results_view = ResultsView(
            self._container, on_restart_callback=self._on_restart
        )

        self._show_view(self._start_view)
        self.after(200, self._check_expiry)

    # ------------------------------------------------------------------ #
    # Titelleiste mit Admin-Schaltfläche
    # ------------------------------------------------------------------ #

    def _build_titlebar(self):
        bar = ctk.CTkFrame(self, height=40, fg_color=("gray88", "gray17"))
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        ctk.CTkLabel(
            bar,
            text="DSM-Screening",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=16)

        ctk.CTkButton(
            bar,
            text="⚙ Admin",
            width=90,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self._open_admin,
        ).pack(side="right", padx=12, pady=6)

        self._theme_btn = ctk.CTkButton(
            bar,
            text="🌙 Dunkel",
            width=80,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self._toggle_theme,
        )
        self._theme_btn.pack(side="right", padx=(0, 4), pady=6)

    def _build_copyright_bar(self):
        """Schmaler Info-Balken mit Autor und Rechtlichem."""
        bar = ctk.CTkFrame(self, height=22, fg_color=("gray96", "gray12"))
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)
        ctk.CTkLabel(
            bar,
            text=(
                "Entwickelt von Dr. M. S. Kerdar, Bad Kissingen \u2022 © 09.03.2026 \u2013 "
                "Alle Rechte vorbehalten. Nur für den autorisierten Einsatz. "
                "Weitergabe, Vervielfältigung oder kommerzielle Nutzung ohne Genehmigung untersagt."
            ),
            font=ctk.CTkFont(size=9),
            text_color=("gray40", "gray60"),
            anchor="center",
        ).pack(expand=True, padx=8)

    def _toggle_theme(self):
        if self._appearance_mode == "light":
            self._appearance_mode = "dark"
            ctk.set_appearance_mode("dark")
            self._theme_btn.configure(text="☀ Hell")
        else:
            self._appearance_mode = "light"
            ctk.set_appearance_mode("light")
            self._theme_btn.configure(text="🌙 Dunkel")

    def _check_expiry(self):
        """Prüft das Ablaufdatum. Bei Ablauf wird die App gesperrt."""
        expiry_str = self._cfg.get_expiry_date().strip()
        if not expiry_str:
            return
        try:
            expiry = datetime.date.fromisoformat(expiry_str)
        except ValueError:
            return
        today = datetime.date.today()
        remaining = (expiry - today).days

        if remaining < 0:
            # Programm gesperrt – Hauptfenster deaktivieren
            self.withdraw()
            dlg = ctk.CTkToplevel()
            dlg.title("Programm abgelaufen")
            dlg.geometry("460x230")
            dlg.resizable(False, False)
            dlg.attributes("-topmost", True)

            def _do_quit():
                try:
                    dlg.destroy()
                except Exception:
                    pass
                try:
                    self.destroy()
                except Exception:
                    pass
                import sys
                sys.exit(0)

            def _open_settings_from_dlg():
                """Admin-Login öffnen, um das Ablaufdatum anzupassen."""
                def _on_auth():
                    def _on_admin_closed_expiry():
                        self._cfg.load()
                        self._admin_window = None
                        try:
                            dlg.destroy()
                        except Exception:
                            pass
                        # Hauptfenster wieder anzeigen und Ablaufdatum neu prüfen
                        self.deiconify()
                        self.after(100, self._check_expiry)

                    self._admin_window = AdminView(
                        self, on_close_callback=_on_admin_closed_expiry
                    )
                    self._admin_window.attributes("-topmost", True)
                    self._admin_window.focus()

                AdminLoginDialog(dlg, on_success=_on_auth)

            dlg.protocol("WM_DELETE_WINDOW", _do_quit)
            ctk.CTkLabel(
                dlg,
                text=(
                    f"Dieses Programm ist am {expiry_str} abgelaufen\n"
                    "und kann nicht mehr gestartet werden.\n\n"
                    "Bitte wenden Sie sich an Dr. M. S. Kerdar."
                ),
                font=ctk.CTkFont(size=14),
                text_color="#e74c3c",
                justify="center",
            ).pack(expand=True, pady=(24, 8))

            btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
            btn_row.pack(pady=(0, 20))
            ctk.CTkButton(
                btn_row, text="⚙ Einstellungen öffnen", width=190,
                fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"),
                text_color=("gray10", "gray90"),
                command=_open_settings_from_dlg,
            ).pack(side="left", padx=(0, 10))
            ctk.CTkButton(
                btn_row, text="Programm beenden", width=160,
                fg_color="#e74c3c", hover_color="#c0392b",
                command=_do_quit,
            ).pack(side="left")
            return  # Keine weitere Initialisierung

        if remaining == 0:
            msg = "Dieses Programm läuft heute ab."
        elif remaining <= 14:
            msg = f"Dieses Programm läuft in {remaining} Tag(en) ab ({expiry_str})."
        else:
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("Programm-Ablaufdatum")
        dlg.geometry("420x160")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.attributes("-topmost", True)
        ctk.CTkLabel(
            dlg, text=msg,
            font=ctk.CTkFont(size=14),
            wraplength=380,
            text_color="#f39c12",
        ).pack(expand=True, pady=(24, 8))
        ctk.CTkButton(dlg, text="OK", width=100, command=dlg.destroy).pack(pady=(0, 16))

    # ------------------------------------------------------------------ #
    # View-Navigation
    # ------------------------------------------------------------------ #

    def _show_view(self, view: ctk.CTkFrame):
        if self._current_view is not None:
            self._current_view.pack_forget()
        self._current_view = view
        view.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    # Callbacks der Views
    # ------------------------------------------------------------------ #

    def _on_start(self, respondent: str, child_info: dict | None = None):
        """Start-View → Fragebogen"""
        self._respondent = respondent
        self._child_info = child_info or {}
        self._questionnaire_view.reload()
        self._show_view(self._questionnaire_view)

    def _on_submit(self, answers: dict):
        """Fragebogen abgeschickt → Auswertung berechnen & anzeigen"""
        answer_values = self._cfg.get_answer_values()
        question_answer_values = self._cfg.get_question_answer_values()
        subscales = self._cfg.get_subscales_for_respondent(self._respondent)
        results = compute_scores(answers, subscales, answer_values, question_answer_values)
        self._results_view.show_results(
            respondent=self._respondent,
            results=results,
            answers=answers,
            child_info=self._child_info,
        )
        self._show_view(self._results_view)

    def _on_restart(self):
        """Ergebnisse → zurück zum Start"""
        self._start_view.reset()
        self._show_view(self._start_view)

    # ------------------------------------------------------------------ #
    # Admin
    # ------------------------------------------------------------------ #

    def _open_admin(self):
        if self._admin_window is not None and self._admin_window.winfo_exists():
            self._admin_window.focus()
            return

        def _on_auth_success():
            self._admin_window = AdminView(self, on_close_callback=self._on_admin_closed)
            self._admin_window.focus()

        AdminLoginDialog(self, on_success=_on_auth_success)

    def _on_admin_closed(self):
        """Wird nach Schließen des Admin-Fensters aufgerufen → Fragebogen neu laden."""
        self._cfg.load()
        self._questionnaire_view.reload()
        self._admin_window = None


# ======================================================================

if __name__ == "__main__":
    app = App()
    app.mainloop()

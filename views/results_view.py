"""
views/results_view.py
Ergebnistabelle + Zusammenfassungstext mit Clipboard-Kopie + PDF-Export.
"""

import datetime
import tkinter.filedialog as fd

import customtkinter as ctk
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from core.config_manager import ConfigManager
from core.scoring import SubscaleResult


# Farben für die Klassifikations-Badges
BADGE_COLORS = {
    "unauffaellig": ("#2ecc71", "#1a7a43"),
    "grenzwertig":  ("#f39c12", "#a06a0a"),
    "auffaellig":   ("#e74c3c", "#922b21"),
}

# Grammatikalische Konstruktion je Auswerter
_RESPONDENT_PHRASE = {
    "Mutter":  "im Urteil der Mutter",
    "Vater":   "im Urteil des Vaters",
    "Lehrer":  "im Urteil des Lehrers",
    "Selbst":  "im Selbsturteil",
}


def _respondent_phrase(respondent: str) -> str:
    return _RESPONDENT_PHRASE.get(respondent, f'im Urteil von „{respondent}"')


def _join_german(items: list[str]) -> str:
    """Verknüpft eine Liste mit Komma und abschließendem 'und'."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " und " + items[-1]


def build_summary_text(respondent: str, results: list[SubscaleResult]) -> str:
    """Erzeugt den deutschen Zusammenfassungstext."""
    auffaellig  = [r.name for r in results if r.classification_key == "auffaellig"]
    grenzwertig = [r.name for r in results if r.classification_key == "grenzwertig"]
    unauffaellig = [r.name for r in results if r.classification_key == "unauffaellig"]

    phrase = _respondent_phrase(respondent)
    intro = f"Im DSM-Verhaltensfragebogen ergeben sich {phrase}"

    segments = []
    if auffaellig:
        segments.append(f"auffällige Werte bzgl. {_join_german(auffaellig)}")
    if grenzwertig:
        segments.append(f"grenzwertige Werte bzgl. {_join_german(grenzwertig)}")
    if unauffaellig:
        segments.append(f"unauffällige Werte bzgl. {_join_german(unauffaellig)}")

    if not segments:
        return f"{intro} keine auswertbaren Ergebnisse."

    if len(segments) == 1:
        return f"{intro} {segments[0]}."

    body = "; ".join(segments[:-1]) + f"; sowie {segments[-1]}"
    return f"{intro} {body}."


# ======================================================================


class ResultsView(ctk.CTkFrame):
    def __init__(self, master, on_restart_callback):
        super().__init__(master, fg_color="transparent")
        self._on_restart = on_restart_callback
        self._build_shell()

    # ------------------------------------------------------------------ #

    def _build_shell(self):
        """Baut den äußeren Frame auf."""
        ctk.CTkLabel(
            self,
            text="Auswertungsergebnis",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(pady=(32, 4))

        self._respondent_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="gray60",
        )
        self._respondent_label.pack(pady=(0, 12))

        # Ergebnistabelle
        self._scroll = ctk.CTkScrollableFrame(self, label_text="")
        self._scroll.pack(fill="both", expand=True, padx=32, pady=(0, 4))
        self._scroll.columnconfigure((0, 1, 2, 3), weight=1)

        # Zusammenfassung
        ctk.CTkLabel(
            self,
            text="Zusammenfassung",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(padx=32, pady=(8, 2), anchor="w")

        self._summary_box = ctk.CTkTextbox(
            self,
            height=70,
            font=ctk.CTkFont(size=12),
            wrap="word",
            state="disabled",
        )
        self._summary_box.pack(fill="x", padx=32, pady=(0, 4))

        # Clipboard-Hinweis + Copy-Button
        hint_row = ctk.CTkFrame(self, fg_color="transparent")
        hint_row.pack(padx=32, pady=(0, 8), fill="x")

        self._copy_hint = ctk.CTkLabel(
            hint_row,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            anchor="w",
        )
        self._copy_hint.pack(side="left")

        ctk.CTkButton(
            hint_row,
            text="� Als PDF speichern",
            width=160,
            height=28,
            font=ctk.CTkFont(size=12),
            command=self._save_pdf,
        ).pack(side="right", padx=(0, 8))

        ctk.CTkButton(
            hint_row,
            text="�📋 Kopieren",
            width=110,
            height=28,
            font=ctk.CTkFont(size=12),
            command=self._copy_to_clipboard,
        ).pack(side="right")

        # Neu starten
        ctk.CTkButton(
            self,
            text="Neu starten",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=200,
            height=44,
            command=self._on_restart,
        ).pack(pady=(0, 20))

    # ------------------------------------------------------------------ #

    def show_results(
        self,
        respondent: str,
        results: list[SubscaleResult],
        answers: dict | None = None,
        child_info: dict | None = None,
    ):
        """Füllt die Tabelle und die Zusammenfassung."""
        self._respondent_label.configure(text=f"Auswerter: {respondent}")
        self._current_summary    = build_summary_text(respondent, results)
        self._current_respondent = respondent
        self._current_results    = results
        self._current_answers    = answers or {}
        self._child_info         = child_info or {}

        # --- Tabelle befüllen ---
        for widget in self._scroll.winfo_children():
            widget.destroy()

        headers = ["Bereich", "Rohwert", "Max.", "Bewertung"]
        col_weights = [4, 1, 1, 2]
        for col, (h, w) in enumerate(zip(headers, col_weights)):
            self._scroll.columnconfigure(col, weight=w)
            ctk.CTkLabel(
                self._scroll,
                text=h,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="gray60",
                anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=(12, 4), pady=(4, 2))

        sep = ctk.CTkFrame(self._scroll, height=2, fg_color="gray30")
        sep.grid(row=1, column=0, columnspan=4, sticky="ew", padx=8, pady=(0, 4))

        for row_idx, result in enumerate(results, start=2):
            ctk.CTkLabel(
                self._scroll,
                text=result.name,
                font=ctk.CTkFont(size=13),
                anchor="w",
                wraplength=280,
            ).grid(row=row_idx, column=0, sticky="ew", padx=(12, 4), pady=6)

            ctk.CTkLabel(
                self._scroll,
                text=str(result.raw_score),
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="center",
            ).grid(row=row_idx, column=1, sticky="ew", padx=4, pady=6)

            ctk.CTkLabel(
                self._scroll,
                text=str(result.max_score),
                font=ctk.CTkFont(size=13),
                text_color="gray60",
                anchor="center",
            ).grid(row=row_idx, column=2, sticky="ew", padx=4, pady=6)

            badge_light, badge_dark = BADGE_COLORS[result.classification_key]
            badge_frame = ctk.CTkFrame(
                self._scroll,
                fg_color=(badge_light, badge_dark),
                corner_radius=8,
            )
            badge_frame.grid(row=row_idx, column=3, sticky="ew", padx=(4, 12), pady=4)
            ctk.CTkLabel(
                badge_frame,
                text=result.classification_label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white",
            ).pack(padx=10, pady=4)

        sep2 = ctk.CTkFrame(self._scroll, height=1, fg_color="gray40")
        sep2.grid(row=len(results) + 2, column=0, columnspan=4, sticky="ew", padx=8, pady=(8, 4))

        total = sum(r.raw_score for r in results)
        total_max = sum(r.max_score for r in results)
        ctk.CTkLabel(
            self._scroll,
            text="Gesamtsumme",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=len(results) + 3, column=0, sticky="ew", padx=(12, 4), pady=8)
        ctk.CTkLabel(
            self._scroll,
            text=str(total),
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="center",
        ).grid(row=len(results) + 3, column=1, sticky="ew", padx=4, pady=8)
        ctk.CTkLabel(
            self._scroll,
            text=str(total_max),
            font=ctk.CTkFont(size=13),
            text_color="gray60",
            anchor="center",
        ).grid(row=len(results) + 3, column=2, sticky="ew", padx=4, pady=8)

        # --- Zusammenfassung ---
        self._summary_box.configure(state="normal")
        self._summary_box.delete("1.0", "end")
        self._summary_box.insert("1.0", self._current_summary)
        self._summary_box.configure(state="disabled")

        # Automatisch in die Zwischenablage kopieren
        self._copy_to_clipboard(auto=True)

    # ------------------------------------------------------------------ #

    def _copy_to_clipboard(self, auto: bool = False):
        text = getattr(self, "_current_summary", "")
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        hint = "✓ Automatisch in die Zwischenablage kopiert" if auto else "✓ In die Zwischenablage kopiert"
        self._copy_hint.configure(text=hint)
        # Hinweis nach 4 Sekunden ausblenden
        self.after(4000, lambda: self._copy_hint.configure(text=""))

    # ------------------------------------------------------------------ #

    @staticmethod
    def _safe(text: str) -> str:
        """Entfernt Zeichen, die in Dateinamen unzulässig sind."""
        for ch in r'\/:*?"<>|':
            text = text.replace(ch, "")
        return text.strip()

    def _build_pdf_filename(self) -> str:
        """Erstellt den Dateinamen im Format DSM_Nachname_Vorname_geb_TT-MM-JJ_datum-TT-MM-JJJJ."""
        ci = getattr(self, "_child_info", {})
        nachname = self._safe(ci.get("nachname", "Unbekannt"))
        vorname  = self._safe(ci.get("vorname",  "Unbekannt"))

        # Geburtsdatum TT.MM.JJJJ → TT-MM-JJ (2-stelliges Jahr)
        geb_raw = ci.get("geburtsdatum", "")
        try:
            geb_dt = datetime.datetime.strptime(geb_raw, "%d.%m.%Y")
            geb_str = geb_dt.strftime("%d-%m-%y")
        except ValueError:
            geb_str = self._safe(geb_raw) or "unbekannt"

        # Datum der Angabe TT.MM.JJJJ → TT-MM-JJJJ
        dat_raw = ci.get("assessment_date", "")
        try:
            dat_dt = datetime.datetime.strptime(dat_raw, "%d.%m.%Y")
            dat_str = dat_dt.strftime("%d-%m-%Y")
        except ValueError:
            dat_str = self._safe(dat_raw) or datetime.date.today().strftime("%d-%m-%Y")

        return f"DSM_{nachname}_{vorname}_geb_{geb_str}_datum-{dat_str}.pdf"

    def _save_pdf(self):
        """Erstellt eine PDF-Datei mit Ergebnissen und Fragebogen-Antworten."""
        path = fd.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF-Datei", "*.pdf")],
            title="PDF speichern unter…",
            initialfile=self._build_pdf_filename(),
        )
        if not path:
            return

        ci = getattr(self, "_child_info", {})
        cfg         = ConfigManager()
        questions   = cfg.get_questions()
        labels      = cfg.get_answer_labels()

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "title", parent=styles["Heading1"], fontSize=16, spaceAfter=4
        )
        sub_style = ParagraphStyle(
            "sub", parent=styles["Normal"], fontSize=9,
            textColor=colors.grey, spaceAfter=12
        )
        h2_style = ParagraphStyle(
            "h2", parent=styles["Heading2"], fontSize=12, spaceBefore=14, spaceAfter=4
        )
        body_style = ParagraphStyle(
            "body", parent=styles["Normal"], fontSize=10, spaceAfter=4
        )
        small_style = ParagraphStyle(
            "small", parent=styles["Normal"], fontSize=8, textColor=colors.grey
        )

        story = []

        # ---- Kopf ----
        nachname = ci.get("nachname", "")
        vorname  = ci.get("vorname",  "")
        geb      = ci.get("geburtsdatum", "")
        adat     = ci.get("assessment_date", datetime.date.today().strftime("%d.%m.%Y"))
        kind_str = f"{nachname}, {vorname}" if nachname or vorname else "–"

        story.append(Paragraph("DSM-Screening – Auswertungsbericht", title_style))
        story.append(Paragraph(
            f"Kind: {kind_str} • Geburtsdatum: {geb or '–'} • "
            f"Auswerter: {self._current_respondent} • Datum der Angabe: {adat}",
            sub_style,
        ))
        story.append(HRFlowable(
            width="100%", thickness=1, color=colors.lightgrey, spaceAfter=8
        ))

        # ---- Ergebnistabelle ----
        story.append(Paragraph("Ergebnisse nach Subskala", h2_style))

        CLASS_COLORS = {
            "unauffaellig": colors.HexColor("#2ecc71"),
            "grenzwertig":  colors.HexColor("#f39c12"),
            "auffaellig":   colors.HexColor("#e74c3c"),
        }
        tdata = [["Bereich", "Rohwert", "Max.", "Bewertung"]]
        for r in self._current_results:
            tdata.append([r.name, str(r.raw_score), str(r.max_score), r.classification_label])
        total     = sum(r.raw_score for r in self._current_results)
        total_max = sum(r.max_score for r in self._current_results)
        tdata.append(["Gesamtsumme", str(total), str(total_max), ""])

        col_widths = [9*cm, 2*cm, 2*cm, 3.5*cm]
        t = Table(tdata, colWidths=col_widths, repeatRows=1)
        ts = TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),   colors.HexColor("#2c3e50")),
            ("TEXTCOLOR",     (0, 0), (-1, 0),   colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),   "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1),  9),
            ("ROWBACKGROUNDS",(0, 1), (-1, -2),  [colors.HexColor("#f9f9f9"), colors.white]),
            ("BACKGROUND",    (0, -1),(-1, -1),  colors.HexColor("#ecf0f1")),
            ("FONTNAME",      (0, -1),(-1, -1),  "Helvetica-Bold"),
            ("ALIGN",         (1, 0), (2, -1),   "CENTER"),
            ("ALIGN",         (3, 1), (3, -2),   "CENTER"),
            ("GRID",          (0, 0), (-1, -1),  0.4, colors.lightgrey),
            ("TOPPADDING",    (0, 0), (-1, -1),  4),
            ("BOTTOMPADDING", (0, 0), (-1, -1),  4),
        ])
        for i, r in enumerate(self._current_results, start=1):
            c = CLASS_COLORS[r.classification_key]
            ts.add("BACKGROUND", (3, i), (3, i), c)
            ts.add("TEXTCOLOR",  (3, i), (3, i), colors.white)
        t.setStyle(ts)
        story.append(t)

        # ---- Zusammenfassung ----
        story.append(Spacer(1, 0.4*cm))
        story.append(Paragraph("Zusammenfassung", h2_style))
        story.append(Paragraph(self._current_summary, body_style))

        # ---- Fragebogen-Antworten ----
        if self._current_answers:
            story.append(HRFlowable(
                width="100%", thickness=0.5, color=colors.lightgrey, spaceBefore=10
            ))
            story.append(Paragraph("Fragebogen – Einzelantworten", h2_style))

            q_tdata = [["Nr.", "Frage", "Antwort"]]
            for qid in range(1, 34):
                q_text       = questions.get(str(qid), f"Frage {qid}")
                answer_index = self._current_answers.get(qid, -1)
                if 0 <= answer_index < len(labels):
                    answer_text = labels[answer_index]
                else:
                    answer_text = "–"
                q_tdata.append([str(qid), q_text, answer_text])

            qt = Table(q_tdata, colWidths=[1*cm, 13*cm, 2.5*cm], repeatRows=1)
            qt.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),   colors.HexColor("#2c3e50")),
                ("TEXTCOLOR",     (0, 0), (-1, 0),   colors.white),
                ("FONTNAME",      (0, 0), (-1, 0),   "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, -1),  8),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1),  [colors.HexColor("#f9f9f9"), colors.white]),
                ("GRID",          (0, 0), (-1, -1),  0.4, colors.lightgrey),
                ("ALIGN",         (0, 0), (0, -1),   "CENTER"),
                ("ALIGN",         (2, 0), (2, -1),   "CENTER"),
                ("VALIGN",        (0, 0), (-1, -1),  "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1),  3),
                ("BOTTOMPADDING", (0, 0), (-1, -1),  3),
            ]))
            story.append(qt)

        # ---- Fußzeile ----
        story.append(Spacer(1, 0.6*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Paragraph(
            "DSM-Screening • Entwickelt von Dr. M. S. Kerdar, Bad Kissingen "
            "• © 09.03.2026 – Alle Rechte vorbehalten.",
            small_style,
        ))

        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm,  bottomMargin=2*cm,
        )
        doc.build(story)

        filename = path.replace("\\", "/").split("/")[-1]
        self._copy_hint.configure(text=f"✓ PDF gespeichert: {filename}")
        self.after(6000, lambda: self._copy_hint.configure(text=""))

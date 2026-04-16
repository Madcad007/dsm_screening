"""
core/pdf_blank.py
Erzeugt ein druckbares Blanko-Fragebogen-PDF zum Ankreuzen.
Wird nur verwendet, wenn kein elektronisches Gerät verfügbar ist.
"""

import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Circle as _RLCircle, Drawing as _Drawing
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak, Table, TableStyle
)


# ─────────────────────────────────────────────────────────
# Öffentliche API
# ─────────────────────────────────────────────────────────

def generate_blank_pdf(
    path: str,
    child_info: dict,
    respondent: str,
    questions: dict,
    answer_labels: list[str],
    instruction: str,
) -> None:
    """
    Erzeugt eine 2-seitige Blanko-PDF-Datei.

    :param path:          Vollständiger Dateipfad (*.pdf)
    :param child_info:    dict mit nachname, vorname, geburtsdatum, assessment_date
    :param respondent:    Auswerter-Bezeichnung (z. B. "Mutter")
    :param questions:     dict {str(qid): Fragetext, ...}  (Schlüssel "1" … "33")
    :param answer_labels: Liste der 4 Antwortbeschriftungen
    :param instruction:   Instruktionstext (wird kursiv über die Fragen gesetzt)
    """
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "blank_title",
        parent=styles["Heading1"],
        fontSize=12,
        spaceAfter=3,
        leading=15,
    )
    label_style = ParagraphStyle(
        "blank_label",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.grey,
        leading=9,
        spaceAfter=0,
    )
    field_style = ParagraphStyle(
        "blank_field",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        spaceAfter=0,
    )
    instr_style = ParagraphStyle(
        "blank_instr",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#444444"),
        spaceAfter=3,
        spaceBefore=4,
        leading=11,
    )
    q_num_style = ParagraphStyle(
        "blank_qnum",
        parent=styles["Normal"],
        fontSize=7,
        fontName="Helvetica-Bold",
        leading=9,
        textColor=colors.HexColor("#2c3e50"),
    )
    q_text_style = ParagraphStyle(
        "blank_qtext",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
    )
    ans_style = ParagraphStyle(
        "blank_ans",
        parent=styles["Normal"],
        fontSize=6,
        leading=8,
    )
    footer_style = ParagraphStyle(
        "blank_footer",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.grey,
        leading=10,
    )

    story = []

    # ── Titel ─────────────────────────────────────────────
    story.append(Paragraph("DSM-Screening – Fragebogen zum Ankreuzen", title_style))
    story.append(HRFlowable(
        width="100%", thickness=1.2, color=colors.HexColor("#2c3e50"), spaceAfter=8
    ))

    # ── Kopf-Felder zum Eintragen ─────────────────────────
    nachname = child_info.get("nachname", "")
    vorname  = child_info.get("vorname", "")
    geb      = child_info.get("geburtsdatum", "")
    adat     = child_info.get("assessment_date", "")
    respondent_val = respondent or ""

    def _field_cell(label: str, value: str, width: float) -> Table:
        """Beschriftung + eingetragener Wert (oder leer) mit Unterlinie."""
        inner = Table(
            [[Paragraph(label, label_style)],
             [Paragraph(value, field_style)]],
            colWidths=[width],
        )
        inner.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("LINEBELOW",     (0, 1), (0, 1), 0.8, colors.HexColor("#555555")),
        ]))
        return inner

    # Zeile 1: Nachname | Vorname | Geburtsdatum
    # Verfügbare Breite bei 1.8 cm Rand links/rechts: 17.4 cm
    row1 = Table(
        [[_field_cell("Nachname", nachname, 6.8 * cm),
          _field_cell("Vorname",  vorname,  6.8 * cm),
          _field_cell("Geburtsdatum", geb,  4.7 * cm)]],
        colWidths=[7.1 * cm, 7.1 * cm, 4.8 * cm],
        hAlign="LEFT",
    )
    row1.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(row1)

    # Zeile 2: Ausfüllende Person | Datum der Angabe
    row2 = Table(
        [[_field_cell("Ausfüllende Person", respondent_val, 9.1 * cm),
          _field_cell("Datum der Angabe",   adat,           9.1 * cm)]],
        colWidths=[9.4 * cm, 9.4 * cm],
        hAlign="LEFT",
    )
    row2.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(row2)

    story.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa"), spaceAfter=3
    ))

    # ── Instruktionstext ──────────────────────────────────
    if instruction:
        story.append(Paragraph(instruction, instr_style))

    # ── Fragen: einspaltig, Seite 1: 1–16, Seite 2: 17–33 ─────────────────
    full_w = 18.6 * cm
    num_w  = 0.50 * cm
    txt_w  = full_w - num_w
    aw     = txt_w / 4

    def _make_q_row(qid: int) -> Table:
        text = questions.get(str(qid), f"Frage {qid}: [Bitte Text einfügen]")
        ans_cells = [_circle_option(lbl, ans_style, label_width=aw - 0.32 * cm)
                     for lbl in answer_labels]
        ans_row = Table(
            [ans_cells],
            colWidths=[aw] * len(ans_cells),
            hAlign="LEFT",
        )
        ans_row.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        outer = Table(
            [[Paragraph(f"<b>{qid}.</b>", q_num_style),
              Paragraph(text, q_text_style)],
             ["", ans_row]],
            colWidths=[num_w, txt_w],
            hAlign="LEFT",
        )
        outer.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("LINEBELOW",     (0, 1), (-1, 1), 0.3, colors.HexColor("#cccccc")),
        ]))
        return outer

    # Seite 1: Fragen 1–16
    for qid in range(1, 17):
        story.append(_make_q_row(qid))

    # ── Seitenumbruch nach Frage 16 ───────────────────────
    story.append(PageBreak())

    # Kurzer Wiederholungs-Kopf auf Seite 2
    kind_str = f"{nachname}, {vorname}" if (nachname or vorname) else ""
    p2_hdr_style = ParagraphStyle(
        "p2hdr", parent=styles["Normal"],
        fontSize=8, textColor=colors.grey, leading=11, spaceAfter=4,
    )
    hdr2_parts = ["<b>DSM-Screening</b>"]
    if kind_str:
        hdr2_parts.append(f"Name: {kind_str}")
    if geb:
        hdr2_parts.append(f"Geb.: {geb}")
    if adat:
        hdr2_parts.append(f"Datum: {adat}")
    story.append(Paragraph(" | ".join(hdr2_parts), p2_hdr_style))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa"), spaceAfter=5
    ))

    # Seite 2: Fragen 17–33
    for qid in range(17, 34):
        story.append(_make_q_row(qid))

    # ── Fußzeile ──────────────────────────────────────────
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph(
        "DSM-Screening • Entwickelt von Dr. M. S. Kerdar, Bad Kissingen "
        "• © 09.03.2026 – Alle Rechte vorbehalten.",
        footer_style,
    ))

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,          # Hochformat 210 × 297 mm
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )
    doc.build(story)


# ─────────────────────────────────────────────────────────
# Interne Hilfsfunktionen
# ─────────────────────────────────────────────────────────

def _circle_option(label: str, style, label_width: float = 3.1 * cm) -> Table:
    """Gibt ein Inline-Table zurück: gezeichneter Kreis (○) + Beschriftungstext."""
    d = _Drawing(8, 8)
    c = _RLCircle(4, 4, 3.2)
    c.fillColor = colors.white
    c.strokeColor = colors.HexColor("#333333")
    c.strokeWidth = 0.6
    d.add(c)
    t = Table([[d, Paragraph(label, style)]], colWidths=[0.32 * cm, label_width])
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 1),
    ]))
    return t

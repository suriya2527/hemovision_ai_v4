"""PDF screening report (ReportLab)."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

WINE, BEIGE, SAGE = colors.HexColor("#590907"), colors.HexColor("#E8D2B5"), colors.HexColor("#A5A79B")
TIPS = ["Consider arranging a hemoglobin/CBC test for confirmation.",
        "Include iron-containing foods such as leafy greens, lentils, beans, eggs, meat where appropriate, and iron-fortified foods.",
        "Vitamin C-containing foods can help the body absorb dietary iron.",
        "Avoid starting iron supplements solely based on this application result.",
        "Discuss persistent tiredness, dizziness, breathlessness, or other concerns with a qualified healthcare professional."]
TIPS_NOTE = "These are general educational tips and do not replace medical advice."
DISCLAIMER = ("This is an academic research prototype and the prediction is not a clinical diagnosis. "
              "Confirmatory hemoglobin or CBC testing is required.")

def model_notice(mode):
    if mode == "Demo Mode": return "Demo mode: ML model not connected. Demonstration result only."
    if mode == "Synthetic ML Prototype":
        return "Prototype prediction generated using a synthetic-data ML model. Synthetic-data model used. This model has not been clinically validated."
    return ""

def build_pdf(user, s, cmp):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=15*mm, bottomMargin=15*mm, title="HemoVision Report")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=WINE, fontSize=24, alignment=0, spaceAfter=0)
    h2 = ParagraphStyle("h2", parent=ss["Heading3"], textColor=WINE, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=10, leading=14)
    P = lambda t, st=body: Paragraph(escape(str(t)), st)

    def table(rows):
        t = Table([[P(a), P(b)] for a, b in rows], colWidths=[60*mm, 110*mm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), BEIGE), ("GRID", (0, 0), (-1, -1), .4, SAGE),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        return t

    pr = [("Patient Name", user.full_name), ("Age", user.age), ("Gender", user.gender)]
    if user.blood_group: pr.append(("Blood Group", user.blood_group))
    pr.append(("Screening Date", s.screening_date.strftime("%d %b %Y, %H:%M")))
    el = [P("HEMOVISION AI", h1), P("Anemia Screening Report", ParagraphStyle("s", parent=body, textColor=SAGE, fontSize=13)), Spacer(1, 8),
          P("Patient Details", h2), table(pr), P("Screening Result", h2),
          table([("Risk Classification", s.risk_level), ("Result", s.prediction), ("Confidence", f"{s.confidence*100:.0f}%"),
                 ("Screening Risk Score", f"{s.risk_score*100:.0f}%"), ("Model Mode", s.model_mode)])]
    if model_notice(s.model_mode): el += [Spacer(1, 4), P(model_notice(s.model_mode), ParagraphStyle("n", parent=body, textColor=WINE))]
    labels = {"mean_intensity": "Mean Intensity", "std_intensity": "Standard Deviation", "contrast": "Contrast", "homogeneity": "Homogeneity",
              "energy": "Energy", "correlation": "Correlation", "entropy": "Entropy"}
    el += [P("Image Analysis Summary", h2), table([(labels[k], f"{v:.4f}") for k, v in s.features.items()]), P("Trend", h2)]
    el.append(table([("Previous Screening Risk", f"{cmp['previous']}%"), ("Current Screening Risk", f"{cmp['current']}%"),
                     ("Change", f"{cmp['change']:+d} percentage points")]) if cmp else P("First recorded screening."))
    if cmp: el.append(P(cmp["message"]))
    el.append(P("Recommendation", h2))
    if s.is_higher:
        el += [P("• " + t) for t in TIPS] + [P(TIPS_NOTE, ParagraphStyle("i", parent=body, fontName="Helvetica-Oblique"))]
    else:
        el += [P("Low anemia screening risk was identified by this prototype."),
               P("This screening result does not rule out anemia. A hemoglobin/CBC test is required for confirmation.")]
    box = Table([[P(DISCLAIMER)]], colWidths=[170*mm])
    box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, WINE), ("BACKGROUND", (0, 0), (-1, -1), BEIGE), ("PADDING", (0, 0), (-1, -1), 8)]))
    el += [Spacer(1, 12), box]
    doc.build(el)
    buf.seek(0)
    return buf

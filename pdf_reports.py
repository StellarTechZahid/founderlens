"""
Builds the two PDF deliverables from a finished result:

    evaluation_sheet.pdf  - scores for the 20 criteria + verdict + priority actions
    research_report.pdf   - the 20 research areas, key risks and a 90-day plan

Same typeface (Bricolage Grotesque) and the same "lens" motif as the website. Falls back
to Helvetica automatically if the font files are missing.
"""
import os
import re
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, PageBreak, Flowable, HRFlowable,
)

from framework import MARKETS, MARKET_LABEL

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "assets", "fonts")

# --------------------------------- brand ----------------------------------
GREEN = colors.HexColor("#0B8457")   # Pakistan
BLUE = colors.HexColor("#2D3CFF")    # Global
INK = colors.HexColor("#000000")
TEXT = colors.HexColor("#262626")
MUTED = colors.HexColor("#6B6B6B")
LINE = colors.HexColor("#E2E3E6")
WASH = colors.HexColor("#F4F5F7")
MARKET_COLOR = {"pakistan": GREEN, "global": BLUE}

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# --------------------------------- fonts ----------------------------------
F_REG, F_MED, F_BOLD, F_DISPLAY = "Helvetica", "Helvetica", "Helvetica-Bold", "Helvetica-Bold"
_CHARS = None
_fonts_ready = False


def _setup_fonts():
    global F_REG, F_MED, F_BOLD, F_DISPLAY, _CHARS, _fonts_ready
    if _fonts_ready:
        return
    _fonts_ready = True
    try:
        files = {
            "Bricolage": "Bricolage-Regular.ttf",
            "BricolageMedium": "Bricolage-Medium.ttf",
            "BricolageBold": "Bricolage-Bold.ttf",
            "BricolageDisplay": "Bricolage-Display.ttf",
        }
        for name, fn in files.items():
            pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, fn)))
        pdfmetrics.registerFontFamily("Bricolage", normal="Bricolage", bold="BricolageBold",
                                      italic="Bricolage", boldItalic="BricolageBold")
        F_REG, F_MED, F_BOLD, F_DISPLAY = "Bricolage", "BricolageMedium", "BricolageBold", "BricolageDisplay"
        _CHARS = set(pdfmetrics.getFont("Bricolage").face.charToGlyph.keys())
    except Exception:  # noqa: BLE001 - any font problem -> built-in fonts
        _CHARS = None


def clean(value) -> str:
    """Make text safe for the PDF: escape XML, keep newlines, replace glyphs the font lacks."""
    text = "" if value is None else str(value)
    text = text.replace("\u2713", "yes").replace("\u2192", "to").replace("\u2011", "-")
    text = text.replace("\r", "")
    out = []
    for ch in text:
        if ch in "\n\t":
            out.append(ch)
        elif _CHARS is not None:
            out.append(ch if ord(ch) in _CHARS else "?")
        else:  # Helvetica: stick to Latin-1 + common punctuation
            out.append(ch if ord(ch) < 256 or ch in "\u2013\u2014\u2018\u2019\u201c\u201d\u2022\u2026" else "?")
    return escape("".join(out)).replace("\n", "<br/>")


# -------------------------------- styles ----------------------------------
def _styles():
    _setup_fonts()
    base = dict(fontName=F_REG, textColor=TEXT, alignment=TA_LEFT)
    return {
        "eyebrow": ParagraphStyle("eyebrow", fontName=F_MED, fontSize=10, leading=13, textColor=MUTED),
        "title": ParagraphStyle("title", fontName=F_DISPLAY, fontSize=34, leading=34, textColor=INK, spaceAfter=4),
        "meta": ParagraphStyle("meta", fontName=F_REG, fontSize=9.5, leading=13, textColor=MUTED),
        "h1": ParagraphStyle("h1", fontName=F_DISPLAY, fontSize=20, leading=22, textColor=INK, spaceBefore=6, spaceAfter=6),
        "h2": ParagraphStyle("h2", fontName=F_BOLD, fontSize=11.5, leading=14, textColor=INK),
        "body": ParagraphStyle("body", fontSize=9.5, leading=14, **base),
        "small": ParagraphStyle("small", fontName=F_REG, fontSize=8, leading=11, textColor=MUTED),
        "cell": ParagraphStyle("cell", fontSize=8.6, leading=12, **base),
        "cellb": ParagraphStyle("cellb", fontName=F_BOLD, fontSize=8.8, leading=12, textColor=INK),
        "th": ParagraphStyle("th", fontName=F_BOLD, fontSize=8, leading=10, textColor=MUTED),
        "bullet": ParagraphStyle("bullet", fontSize=9.2, leading=13.2, leftIndent=11, bulletIndent=0, spaceAfter=1.5, **base),
        "label": ParagraphStyle("label", fontName=F_BOLD, fontSize=8.5, leading=11, textColor=MUTED, spaceBefore=5, spaceAfter=2),
        "verdict": ParagraphStyle("verdict", fontName=F_DISPLAY, fontSize=17, leading=19, textColor=INK),
    }


# ------------------------------- flowables --------------------------------
class LensGraphic(Flowable):
    """Two circles (Pakistan green, Global blue). Each fills from the bottom up to its score;
    the overlap - the lens - carries the overall score."""

    def __init__(self, pk, gl, overall, width=CONTENT_W, height=62 * mm):
        super().__init__()
        self.pk, self.gl, self.overall = pk, gl, overall
        self.width, self.height = width, height

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        r = 23 * mm
        d = 27 * mm
        cx = self.width / 2
        cy = self.height / 2 + 2 * mm
        centers = {"pakistan": cx - d / 2, "global": cx + d / 2}
        scores = {"pakistan": self.pk, "global": self.gl}
        for market in MARKETS:
            x = centers[market]
            s = scores[market] or 0
            level = (cy - r) + (2 * r) * (s / 10.0)
            c.saveState()
            p = c.beginPath()
            p.circle(x, cy, r)
            c.clipPath(p, stroke=0, fill=0)
            c.setFillColor(MARKET_COLOR[market])
            c.setFillAlpha(0.88)
            c.rect(x - r - 1, cy - r - 1, 2 * r + 2, level - (cy - r) + 1, stroke=0, fill=1)
            c.restoreState()
        c.setStrokeColor(INK)
        c.setLineWidth(0.9)
        for market in MARKETS:
            c.circle(centers[market], cy, r, stroke=1, fill=0)
        # lens outline, heavier: stroke each circle only where it lies inside the other
        c.setLineWidth(2.2)
        for a, b in (("pakistan", "global"), ("global", "pakistan")):
            c.saveState()
            p = c.beginPath()
            p.circle(centers[a], cy, r)
            c.clipPath(p, stroke=0, fill=0)
            c.circle(centers[b], cy, r, stroke=1, fill=0)
            c.restoreState()
        # numbers
        c.setFillColor(colors.white)
        c.setStrokeColor(INK)
        c.setLineWidth(1.2)
        c.circle(cx, cy, 8.2 * mm, stroke=1, fill=1)
        c.setFillColor(INK)
        c.setFont(F_DISPLAY, 21)
        c.drawCentredString(cx, cy - 2, "-" if self.overall is None else f"{self.overall:.1f}")
        c.setFont(F_REG, 7)
        c.drawCentredString(cx, cy - 11, "overall")
        c.setFillColor(INK)
        for market in MARKETS:
            x = centers[market]
            c.setFont(F_BOLD, 10)
            label = MARKET_LABEL[market]
            val = scores[market]
            txt = f"{label}  {'-' if val is None else f'{val:.1f}'}"
            if market == "pakistan":
                c.drawRightString(x - r, cy - r - 9, txt)
            else:
                c.drawString(x + r, cy - r - 9, txt)


class ScoreBar(Flowable):
    """A thin bar with the score at its right end."""

    def __init__(self, score, color, width=30 * mm, label=""):
        super().__init__()
        self.score, self.color, self.width, self.height, self.label = score, color, width, 9, label

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        track_w = self.width - 24
        c.setFillColor(LINE)
        c.roundRect(0, 3, track_w, 3.4, 1.7, stroke=0, fill=1)
        if self.score:
            c.setFillColor(self.color)
            c.roundRect(0, 3, track_w * self.score / 10.0, 3.4, 1.7, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont(F_BOLD, 9)
        c.drawRightString(self.width - 3, 1.5, "-" if self.score is None else f"{self.score}/10")


class LogoMark(Flowable):
    def __init__(self, size=7 * mm):
        super().__init__()
        self.size = size

    def wrap(self, aw, ah):
        return self.size * 1.6, self.size

    def draw(self):
        c = self.canv
        r = self.size / 2
        c.setFillAlpha(0.85)
        c.setFillColor(GREEN)
        c.circle(r, r, r, stroke=0, fill=1)
        c.setFillColor(BLUE)
        c.circle(r * 1.6, r, r, stroke=0, fill=1)


# ----------------------------- page decoration -----------------------------
def _make_page_decor(doc_title, project):
    def decorate(canvas, doc):
        canvas.saveState()
        # header
        r = 2.4 * mm
        y = PAGE_H - 11 * mm
        canvas.setFillAlpha(0.85)
        canvas.setFillColor(GREEN)
        canvas.circle(MARGIN + r, y, r, stroke=0, fill=1)
        canvas.setFillColor(BLUE)
        canvas.circle(MARGIN + r * 2.1, y, r, stroke=0, fill=1)
        canvas.setFillAlpha(1)
        canvas.setFillColor(INK)
        canvas.setFont(F_BOLD, 10)
        canvas.drawString(MARGIN + r * 4.2, y - 3.4, "FoundersLens")
        canvas.setFillColor(MUTED)
        canvas.setFont(F_REG, 8.5)
        canvas.drawRightString(PAGE_W - MARGIN, y - 3, doc_title)
        # footer
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.6)
        canvas.line(MARGIN, 13 * mm, PAGE_W - MARGIN, 13 * mm)
        canvas.setFillColor(MUTED)
        canvas.setFont(F_REG, 8)
        canvas.drawString(MARGIN, 8.5 * mm, clean_plain(project))
        canvas.drawRightString(PAGE_W - MARGIN, 8.5 * mm, f"Page {doc.page}")
        canvas.restoreState()
    return decorate


def clean_plain(text):
    """Like clean() but without XML escaping - for text drawn straight on the canvas."""
    text = "" if text is None else str(text)
    out = []
    for ch in text:
        if _CHARS is not None:
            out.append(ch if ord(ch) in _CHARS else "?")
        else:
            out.append(ch if ord(ch) < 256 else "?")
    return "".join(out)


def _doc(path, title, project):
    doc = BaseDocTemplate(path, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=22 * mm, bottomMargin=20 * mm,
                          title=f"{title} - {project}", author="FoundersLens")
    frame = Frame(MARGIN, 20 * mm, CONTENT_W, PAGE_H - 42 * mm, id="f", leftPadding=0,
                  rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame],
                                       onPage=_make_page_decor(title, project))])
    return doc


def _date(result):
    meta = result.get("meta", {})
    return meta.get("generated_at") or datetime.now().strftime("%d %B %Y")


def _bullets(items, st):
    return [Paragraph(clean(i), st["bullet"], bulletText="\u2022") for i in items if str(i).strip()]


def _rule():
    return HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=4, spaceAfter=6)


# ---------------------------- evaluation sheet -----------------------------
def build_evaluation_pdf(result: dict, path: str):
    st = _styles()
    intake, ev = result.get("intake", {}), result.get("evaluation", {})
    project = intake.get("company_name") or "Untitled project"
    doc = _doc(path, "Evaluation sheet", project)
    s = []

    s.append(Paragraph("Evaluation sheet", st["eyebrow"]))
    s.append(Paragraph(clean(project), st["title"]))
    meta = " | ".join(x for x in [
        f"Prepared for {intake.get('full_name')}" if intake.get("full_name") else "",
        f"Stage: {intake.get('stage')}" if intake.get("stage") else "",
        _date(result)] if x)
    s.append(Paragraph(clean(meta), st["meta"]))
    s.append(Spacer(1, 4 * mm))
    s.append(LensGraphic(ev["pakistan"]["score"], ev["global"]["score"], ev.get("overall_score")))
    s.append(Spacer(1, 2 * mm))

    # verdict
    s.append(Paragraph(f'{clean(ev.get("overall_verdict", ""))}: {clean(ev.get("recommendation", ""))}', st["verdict"]))
    s.append(Spacer(1, 2 * mm))
    s.append(Paragraph(clean(ev.get("recommendation_reasoning", "")), st["body"]))
    s.append(Spacer(1, 4 * mm))

    # idea summary
    s.append(Paragraph("The idea", st["label"]))
    s.append(Paragraph(clean(ev.get("idea_summary", "")), st["body"]))
    s.append(Spacer(1, 3 * mm))

    # market summaries side by side
    cols = []
    for market in MARKETS:
        m = ev[market]
        head = Paragraph(
            f'<font color="{MARKET_COLOR[market].hexval().replace("0x", "#")}">{MARKET_LABEL[market]}</font>'
            f' &nbsp;{m["score"] if m["score"] is not None else "-"}/10 &nbsp;<font color="#6B6B6B" size="8.5">{clean(m["verdict"])}</font>',
            st["h2"])
        cols.append([head, Spacer(1, 2), Paragraph(clean(m.get("summary", "")), st["cell"])])
    t = Table([cols], colWidths=[CONTENT_W / 2 - 3 * mm, CONTENT_W / 2 - 3 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LINEABOVE", (0, 0), (-1, 0), 0.6, LINE),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (0, 0), 8 * mm)]))
    s.append(t)
    s.append(Spacer(1, 3 * mm))

    sr = Table([[
        [Paragraph("Biggest strength", st["label"]), Paragraph(clean(ev.get("biggest_strength")), st["cell"])],
        [Paragraph("Biggest risk", st["label"]), Paragraph(clean(ev.get("biggest_risk")), st["cell"])],
    ]], colWidths=[CONTENT_W / 2 - 3 * mm, CONTENT_W / 2 - 3 * mm], hAlign="LEFT")
    sr.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (0, 0), 8 * mm)]))
    s.append(sr)

    # priority actions
    s.append(Spacer(1, 6 * mm))
    block = [Paragraph("Priority actions", st["h1"])]
    for i, a in enumerate(ev.get("priority_actions", []), 1):
        block.append(Paragraph(clean(a), st["bullet"], bulletText=f"{i}."))
    s.append(KeepTogether(block))


    # criteria tables
    cw = [8 * mm, 44 * mm, 33 * mm, CONTENT_W - 85 * mm]
    for market in MARKETS:
        m = ev[market]
        s.append(PageBreak())
        s.append(Paragraph(f'{MARKET_LABEL[market]} market: {m["score"] if m["score"] is not None else "-"}/10, {clean(m["verdict"])}', st["h1"]))
        rows = [[Paragraph("#", st["th"]), Paragraph("Criterion", st["th"]),
                 Paragraph("Score", st["th"]), Paragraph("Why", st["th"])]]
        for c in m["criteria"]:
            rows.append([
                Paragraph(str(c["id"]), st["cell"]),
                Paragraph(clean(c["name"]), st["cellb"]),
                ScoreBar(c["score"], MARKET_COLOR[market], width=29 * mm),
                Paragraph(clean(c["rationale"]), st["cell"]),
            ])
        t = Table(rows, colWidths=cw, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK),
            ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        s.append(t)

    s.append(Spacer(1, 8 * mm))
    s.append(_rule())
    s.append(Paragraph(
        "How to read this sheet. An AI agent scored each criterion from 1 to 10 using the FoundersLens "
        "evaluation framework (ten criteria for Pakistan, ten for the global market). A market score is the "
        "average of its ten criteria and the overall score is the average of the two market scores. "
        "Bands: 8 and above Strong, 6.5 to 7.9 Promising, 5 to 6.4 Needs validation, 3.5 to 4.9 High risk, "
        "below 3.5 Weak. Scores are directional judgements, not verified market data.", st["small"]))
    doc.build(s)
    return path


# ----------------------------- research report -----------------------------
def _section_block(sec, market, st):
    color = MARKET_COLOR[market].hexval().replace("0x", "#")
    head = Table([[
        Paragraph(f'<font color="{color}">{sec["id"]}</font> &nbsp;{clean(sec["name"])}', st["h2"]),
        Paragraph(f'Confidence: <b>{clean(sec["confidence"])}</b>', st["small"]),
    ]], colWidths=[CONTENT_W - 32 * mm, 32 * mm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("LINEABOVE", (0, 0), (-1, 0), 0.6, LINE),
                              ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                              ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    parts = [head]
    parts += _bullets(sec["findings"], st)
    if sec["analysis"]:
        parts += [Spacer(1, 2), Paragraph(clean(sec["analysis"]), st["body"])]
    if sec["data_points"]:
        parts.append(Paragraph("Figures to verify", st["label"]))
        parts += _bullets(sec["data_points"], st)
    if sec["validate_next"]:
        parts.append(Paragraph("Verify next", st["label"]))
        parts += _bullets(sec["validate_next"], st)
    parts.append(Spacer(1, 4))
    return parts


def build_research_pdf(result: dict, path: str):
    st = _styles()
    intake, ev, rs = result.get("intake", {}), result.get("evaluation", {}), result.get("research", {})
    project = intake.get("company_name") or "Untitled project"
    doc = _doc(path, "Research report", project)
    s = []

    s.append(Paragraph("Research report", st["eyebrow"]))
    s.append(Paragraph(clean(project), st["title"]))
    meta = " | ".join(x for x in [
        f"Prepared for {intake.get('full_name')}" if intake.get("full_name") else "",
        f"Stage: {intake.get('stage')}" if intake.get("stage") else "", _date(result)] if x)
    s.append(Paragraph(clean(meta), st["meta"]))
    s.append(Spacer(1, 5 * mm))
    s.append(Paragraph("The idea", st["label"]))
    s.append(Paragraph(clean(ev.get("idea_summary", "")), st["body"]))
    s.append(Spacer(1, 3 * mm))

    # at a glance
    cols = []
    for market in MARKETS:
        color = MARKET_COLOR[market].hexval().replace("0x", "#")
        m = ev.get(market, {})
        cols.append([
            Paragraph(f'<font color="{color}">{MARKET_LABEL[market]}</font> &nbsp;{m.get("score", "-")}/10 '
                      f'&nbsp;<font color="#6B6B6B" size="8.5">{clean(m.get("verdict", ""))}</font>', st["h2"]),
            Spacer(1, 2),
            Paragraph(clean(rs.get(market, {}).get("snapshot", "")), st["cell"]),
        ])
    t = Table([cols], colWidths=[CONTENT_W / 2 - 3 * mm] * 2, hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEABOVE", (0, 0), (-1, 0), 0.6, LINE),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (0, 0), 8 * mm)]))
    s.append(t)

    for market in MARKETS:
        s.append(PageBreak())
        color = MARKET_COLOR[market].hexval().replace("0x", "#")
        s.append(Paragraph(f'<font color="{color}">{MARKET_LABEL[market]}</font> market research', st["h1"]))
        s.append(Paragraph("Ten research areas. Estimates are labelled; each area lists what to verify next.", st["small"]))
        s.append(Spacer(1, 2 * mm))
        for sec in rs.get(market, {}).get("sections", []):
            s.append(KeepTogether(_section_block(sec, market, st)))

        risks = rs.get(market, {}).get("key_risks", [])
        if risks:
            s.append(Spacer(1, 4 * mm))
            rows = [[Paragraph("Key risk", st["th"]), Paragraph("Mitigation", st["th"])]]
            for r in risks:
                rows.append([Paragraph(clean(r["risk"]), st["cellb"]), Paragraph(clean(r["mitigation"]), st["cell"])])
            tb = Table(rows, colWidths=[CONTENT_W * 0.42, CONTENT_W * 0.58], repeatRows=1, hAlign="LEFT")
            tb.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK),
                                    ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
            s.append(KeepTogether([Paragraph(f"{MARKET_LABEL[market]}: key risks", st["h2"]), Spacer(1, 3), tb]))
        plan = rs.get(market, {}).get("validation_plan", [])
        if plan:
            s.append(Spacer(1, 4 * mm))
            rows = [[Paragraph("When", st["th"]), Paragraph("Action", st["th"])]]
            for p in plan:
                rows.append([Paragraph(clean(p["when"]), st["cellb"]), Paragraph(clean(p["action"]), st["cell"])])
            tb = Table(rows, colWidths=[CONTENT_W * 0.18, CONTENT_W * 0.82], repeatRows=1, hAlign="LEFT")
            tb.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK),
                                    ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
            s.append(KeepTogether([Paragraph(f"{MARKET_LABEL[market]}: next 90 days", st["h2"]), Spacer(1, 3), tb]))

    s.append(Spacer(1, 8 * mm))
    s.append(_rule())
    s.append(Paragraph(
        "About this research. It was written by an AI agent from its own knowledge, not from live web "
        "browsing, so it can be out of date or wrong. Figures marked (estimate) are reasoned guesses, not "
        "sourced statistics. Confidence shows how sure the agent is of each area. Treat everything here as a "
        "set of hypotheses to check with customer interviews, price tests, competitor review, official filings "
        "and transparent financial assumptions before making decisions.", st["small"]))
    doc.build(s)
    return path


# --------------------------------- entry -----------------------------------
def build_pdfs(result: dict, out_dir: str, eval_name="evaluation_sheet.pdf", research_name="research_report.pdf"):
    os.makedirs(out_dir, exist_ok=True)
    e = build_evaluation_pdf(result, os.path.join(out_dir, eval_name))
    r = build_research_pdf(result, os.path.join(out_dir, research_name))
    return e, r


def slugify(text):
    return re.sub(r"[^a-zA-Z0-9]+", "-", text or "project").strip("-").lower() or "project"

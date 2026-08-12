"""Build a polished single-column EMSE review PDF from paper/manuscript.md.

The builder is deliberately offline. It converts the checked-in Markdown,
generated figures, and BibTeX database into a readable review manuscript; it
does not call any model or recompute frozen statistics.
"""

from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "paper/manuscript.md"
BIBLIOGRAPHY = ROOT / "paper/references.bib"
OUTPUT = Path(
    os.environ.get(
        "EMSE_REVIEW_PDF_OUTPUT",
        str(ROOT / "output/pdf/schema_order_emse_promptse.pdf"),
    )
)

NAVY = colors.HexColor("#172033")
BLUE = colors.HexColor("#2563A6")
MUTED = colors.HexColor("#59657A")
LIGHT = colors.HexColor("#F4F7FA")
GRID = colors.HexColor("#CCD4DF")

TABLE_CAPTIONS = (
    "Study stages, record panels, interfaces, and formal status",
    "Execution windows, endpoint provenance, and request settings",
    "Decomposed text-mode effects, supplemental endpoint results, and deployment-level decisions",
    "Leaf-value accuracy contrasts for the decomposed studies",
    "Post-hoc effect-concentration stress tests",
    "Selected high-effect Qwen text-mode cases; post-hoc and non-representative",
)

SUM_FONT_NAME = "ReviewSegoeUISymbol"
SUM_FONT_PATH = Path("C:/Windows/Fonts/seguisym.ttf")
HAS_SUM_FONT = False


@dataclass
class BibEntry:
    key: str
    kind: str
    fields: dict[str, str]


def clean_latex(value: str) -> str:
    replacements = {
        r"{\l}": "l",
        r"{\"o}": "ö",
        r"{\"a}": "ä",
        r"{\'e}": "é",
        "{": "",
        "}": "",
        "--": "–",
        r"\&": "&",
        r"\%": "%",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return re.sub(r"\[A-Za-z]+", "", value).strip()


def parse_bibtex(text: str) -> dict[str, BibEntry]:
    entries: dict[str, BibEntry] = {}
    pos = 0
    while True:
        match = re.search(r"@([A-Za-z]+)\s*\{\s*([^,\s]+)\s*,", text[pos:])
        if not match:
            break
        kind, key = match.group(1).lower(), match.group(2)
        body_start = pos + match.end()
        depth = 1
        cursor = body_start
        while cursor < len(text) and depth:
            if text[cursor] == "{":
                depth += 1
            elif text[cursor] == "}":
                depth -= 1
            cursor += 1
        body = text[body_start : cursor - 1]
        fields: dict[str, str] = {}
        index = 0
        while index < len(body):
            field_match = re.search(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*", body[index:])
            if not field_match:
                break
            field = field_match.group(1).lower()
            value_start = index + field_match.end()
            if value_start >= len(body):
                break
            if body[value_start] == "{":
                local_depth = 1
                value_end = value_start + 1
                while value_end < len(body) and local_depth:
                    if body[value_end] == "{":
                        local_depth += 1
                    elif body[value_end] == "}":
                        local_depth -= 1
                    value_end += 1
                value = body[value_start + 1 : value_end - 1]
            elif body[value_start] == '"':
                value_end = body.find('"', value_start + 1) + 1
                value = body[value_start + 1 : value_end - 1]
            else:
                next_comma = body.find(",", value_start)
                value_end = len(body) if next_comma < 0 else next_comma
                value = body[value_start:value_end]
            fields[field] = clean_latex(value.strip())
            index = value_end
        entries[key] = BibEntry(key=key, kind=kind, fields=fields)
        pos = cursor
    return entries


def author_parts(entry: BibEntry) -> list[str]:
    return [clean_latex(part.strip()) for part in entry.fields.get("author", "").split(" and ")]


def surname(author: str) -> str:
    if author.startswith("{") and author.endswith("}"):
        return clean_latex(author)
    if "," in author:
        return author.split(",", 1)[0].strip()
    return author.split()[-1] if author.split() else "Unknown"


def cite_label(entry: BibEntry) -> str:
    names = author_parts(entry)
    year = entry.fields.get("year", "n.d.")
    if not names:
        lead = entry.fields.get("title", entry.key)
    elif len(names) == 1:
        # Keep institutional authors distinct in prose citations. Otherwise
        # ``Google Cloud`` and ``Alibaba Cloud`` both collapse to ``Cloud``.
        author = names[0]
        institutional = any(
            marker in author.lower()
            for marker in ("cloud", "alibaba", "google", "openai", "anthropic")
        )
        lead = author if institutional else surname(author)
    elif len(names) == 2:
        lead = f"{surname(names[0])} and {surname(names[1])}"
    else:
        lead = f"{surname(names[0])} et al."
    return f"{lead}, {year}"


def bibliography_text(entry: BibEntry) -> str:
    fields = entry.fields
    names = author_parts(entry)
    author = ", ".join(names[:-1]) + (" and " + names[-1] if len(names) > 1 else names[0] if names else "")
    year = fields.get("year", "n.d.")
    title = fields.get("title", "")
    source = fields.get("journal") or fields.get("booktitle") or fields.get("institution") or fields.get("howpublished", "")
    details: list[str] = []
    if fields.get("volume"):
        details.append(fields["volume"] + (f"({fields['number']})" if fields.get("number") else ""))
    if fields.get("pages"):
        details.append(fields["pages"])
    source_text = source + ((", " + ", ".join(details)) if details else "")
    doi = fields.get("doi")
    url = f"https://doi.org/{doi}" if doi else fields.get("url", "")
    pieces = [f"{author} ({year}).", f"{title}."]
    if source_text:
        pieces.append(source_text + ".")
    if url:
        pieces.append(url)
    return " ".join(piece for piece in pieces if piece)


def latex_formula_to_text(value: str) -> str:
    compact = " ".join(line.strip() for line in value.splitlines())
    if compact.startswith("E_i(A,B)="):
        return "Eᵢ(A,B) = D_cross(Aᵢ,Bᵢ) - ½ [D_within(Aᵢ) + D_within(Bᵢ)]"
    if compact.startswith(r"\mathbb{E}[E_i]"):
        return "E[Eᵢ] = ½ Σ_z (pᵢ(z) - qᵢ(z))²"
    compact = compact.replace(r"\mathrm", "").replace(r"\mathbb", "")
    compact = compact.replace(r"\left", "").replace(r"\right", "")
    compact = compact.replace(r"\frac{1}{2}", "½").replace(r"\sum_z", "Σz")
    compact = compact.replace(r"\ell_2", "L_2").replace(r"\mathbb{E}", "E")
    compact = compact.replace("{", "").replace("}", "")
    return compact


def latex_formula_to_markup(value: str) -> str:
    """Render the two manuscript equations with ReportLab-safe subscripts."""
    compact = " ".join(line.strip() for line in value.splitlines())
    if compact.startswith("E_i(A,B)="):
        return (
            "<i>E</i><sub>i</sub>(<i>A</i>,<i>B</i>) = "
            "<i>D</i><sub>cross</sub>(<i>A</i><sub>i</sub>,<i>B</i><sub>i</sub>) "
            "- 1/2 [<i>D</i><sub>within</sub>(<i>A</i><sub>i</sub>) + "
            "<i>D</i><sub>within</sub>(<i>B</i><sub>i</sub>)]"
        )
    if compact.startswith(r"\mathbb{E}[E_i]"):
        summation = (
            f"<font name='{SUM_FONT_NAME}'>&#8721;</font><sub>z</sub>"
            if HAS_SUM_FONT
            else "SUM<sub>z</sub>"
        )
        return (
            "<i>E</i>[<i>E</i><sub>i</sub>] = 1/2 " + summation + " "
            "(<i>p</i><sub>i</sub>(<i>z</i>) - <i>q</i><sub>i</sub>(<i>z</i>))"
            "<super>2</super>"
        )
    return html.escape(latex_formula_to_text(value))


def latex_inline_to_markup(value: str) -> str:
    r"""Render simple inline math without relying on unavailable Unicode glyphs.

    The review-PDF path uses ReportLab rather than a TeX engine.  In
    particular, the Times/Unicode fallback used for ``\ell`` is not reliably
    embedded by every PDF viewer and previously appeared as missing squares in
    the sentence describing the squared L2 distance.  The manuscript only
    needs a small set of scalar/subscript expressions, so emit those with
    ReportLab's stable markup and use an ASCII ``L`` for ``\ell``.
    """
    compact = " ".join(line.strip() for line in value.splitlines())
    compact = re.sub(r"\\mathrm\{([^{}]+)\}", r"\1", compact)
    compact = re.sub(r"\\mathbb\{([^{}]+)\}", r"\1", compact)
    compact = compact.replace(r"\left", "").replace(r"\right", "")
    compact = compact.replace(r"\ell_2", "L_2")
    compact = compact.replace(r"\frac{1}{2}", "1/2")
    compact = compact.replace("{", "").replace("}", "")
    escaped = html.escape(compact)
    escaped = re.sub(
        r"([A-Za-z])_([A-Za-z0-9]+)",
        lambda match: f"<i>{match.group(1)}</i><sub>{match.group(2)}</sub>",
        escaped,
    )
    return escaped if "<sub>" in escaped else f"<i>{escaped}</i>"


def inline_markup(value: str, bib: dict[str, BibEntry]) -> str:
    tokens: list[str] = []

    def hold(rendered: str) -> str:
        token = f"@@H{len(tokens)}@@"
        tokens.append(rendered)
        return token

    def citation(match: re.Match[str]) -> str:
        keys = re.findall(r"@([A-Za-z0-9_:+.-]+)", match.group(1))
        labels = [cite_label(bib[key]) if key in bib else key for key in keys]
        return hold("(" + "; ".join(html.escape(label) for label in labels) + ")")

    value = re.sub(r"\[((?:-?@[A-Za-z0-9_:+.-]+(?:\s*;\s*)?)+)\]", citation, value)
    value = re.sub(r"`([^`]+)`", lambda m: hold("<font name='Courier'>" + html.escape(m.group(1)) + "</font>"), value)
    value = re.sub(r"\*\*([^*]+)\*\*", lambda m: hold("<b>" + html.escape(m.group(1)) + "</b>"), value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", lambda m: hold("<i>" + html.escape(m.group(1)) + "</i>"), value)
    value = re.sub(r"\\\((.+?)\\\)", lambda m: hold(latex_inline_to_markup(m.group(1))), value)
    rendered = html.escape(value)
    for index, replacement in enumerate(tokens):
        rendered = rendered.replace(f"@@H{index}@@", replacement)
    return rendered


def make_styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Times-Roman",
        fontSize=10.2,
        leading=13.4,
        textColor=NAVY,
        alignment=TA_JUSTIFY,
        spaceAfter=5.5,
        allowWidows=0,
        allowOrphans=0,
    )
    return {
        "body": base,
        "body_left": ParagraphStyle(
            "BodyLeft", parent=base, alignment=TA_LEFT
        ),
        "title": ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "author": ParagraphStyle(
            "Author", parent=base, fontName="Helvetica", fontSize=11.5, leading=15, alignment=TA_LEFT
        ),
        "meta": ParagraphStyle(
            "Meta", parent=base, fontName="Helvetica", fontSize=9.2, leading=12, textColor=MUTED
        ),
        "abstract": ParagraphStyle(
            "Abstract", parent=base, fontSize=9.5, leading=12.3, leftIndent=5 * mm, rightIndent=5 * mm
        ),
        "h1": ParagraphStyle(
            "H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14.5,
            leading=18, textColor=NAVY, spaceBefore=12, spaceAfter=6, keepWithNext=True
        ),
        "h2": ParagraphStyle(
            "H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11.6,
            leading=14, textColor=BLUE, spaceBefore=9, spaceAfter=4, keepWithNext=True
        ),
        "caption": ParagraphStyle(
            "Caption", parent=base, fontName="Helvetica", fontSize=8.3, leading=10.5,
            alignment=TA_LEFT, textColor=MUTED, spaceBefore=3, spaceAfter=8
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=base, leftIndent=6 * mm, firstLineIndent=-3 * mm, bulletIndent=1 * mm
        ),
        "equation": ParagraphStyle(
            "Equation", parent=base, fontName="Times-Italic", fontSize=11, leading=15,
            alignment=TA_CENTER, spaceBefore=5, spaceAfter=7
        ),
        "reference": ParagraphStyle(
            "Reference", parent=base, fontSize=7.8, leading=9.2, leftIndent=6 * mm,
            firstLineIndent=-6 * mm, alignment=TA_LEFT, spaceAfter=1.3
        ),
    }


def parse_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and lines[index].strip().startswith("|"):
        rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
        index += 1
    return rows, index


def table_flowable(rows: list[list[str]], index: int, styles: dict[str, ParagraphStyle], bib: dict[str, BibEntry]) -> list[Any]:
    cleaned = [rows[0]] + rows[2:]
    width = len(cleaned[0])
    available = 174 * mm
    if width >= 7:
        col_widths = [available * 0.18] + [available * 0.82 / (width - 1)] * (width - 1)
        font_size = 6.2
    elif width == 6:
        col_widths = [available * 0.22, available * 0.19] + [available * 0.59 / 4] * 4
        font_size = 6.6
    elif width == 5:
        col_widths = [available * 0.22, available * 0.18] + [available * 0.60 / 3] * 3
        font_size = 7.0
    else:
        col_widths = [available / width] * width
        font_size = 7.3
    cell_style = ParagraphStyle(
        f"Cell{index}", parent=styles["body"], fontName="Helvetica", fontSize=font_size,
        leading=font_size + 2, alignment=TA_LEFT, spaceAfter=0
    )
    header_style = ParagraphStyle(
        f"Header{index}", parent=cell_style, fontName="Helvetica-Bold", textColor=colors.white
    )
    data: list[list[Paragraph]] = []
    for row_index, row in enumerate(cleaned):
        padded = row + [""] * (width - len(row))
        style = header_style if row_index == 0 else cell_style
        data.append([Paragraph(inline_markup(cell, bib), style) for cell in padded[:width]])
    table = LongTable(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
    commands: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]
    for row_index in range(1, len(data)):
        if row_index % 2 == 0:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), LIGHT))
    table.setStyle(TableStyle(commands))
    caption = TABLE_CAPTIONS[index] if index < len(TABLE_CAPTIONS) else f"Additional result table {index + 1}"
    return [Paragraph(f"<b>Table {index + 1}</b> {html.escape(caption)}", styles["caption"]), table, Spacer(1, 3 * mm)]


def figure_flowable(path: Path, alt: str, styles: dict[str, ParagraphStyle]) -> list[Any]:
    with PILImage.open(path) as source:
        width, height = source.size
    draw_width = 174 * mm
    draw_height = draw_width * height / width
    if draw_height > 150 * mm:
        draw_height = 150 * mm
        draw_width = draw_height * width / height
    match = re.match(r"Figure\s+(\d+)\.\s*(.*)", alt)
    if match:
        caption = f"<b>Fig. {match.group(1)}</b> {html.escape(match.group(2))}"
    else:
        caption = html.escape(alt)
    return [Image(str(path), width=draw_width, height=draw_height), Paragraph(caption, styles["caption"])]


def header_footer(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    page = canvas.getPageNumber()
    if page > 1:
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, A4[1] - 11 * mm, "Sun • Testing JSON Schema Instruction Artifacts")
        canvas.drawRightString(A4[0] - 18 * mm, A4[1] - 11 * mm, "Manuscript")
        canvas.setStrokeColor(GRID)
        canvas.line(18 * mm, A4[1] - 13 * mm, A4[0] - 18 * mm, A4[1] - 13 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(A4[0] / 2, 9 * mm, str(page))
    canvas.restoreState()


def build_story(manuscript: str, bib: dict[str, BibEntry], styles: dict[str, ParagraphStyle]) -> list[Any]:
    lines = manuscript.splitlines()
    title = lines[0].removeprefix("# ").strip()
    story: list[Any] = [Spacer(1, 8 * mm), Paragraph(html.escape(title), styles["title"])]
    story.extend(
        [
            Paragraph("Shengyao Sun", styles["author"]),
            Paragraph("Shanghai Jiao Tong University, Shanghai, China", styles["meta"]),
            Paragraph("Corresponding author: sthfornothing@sjtu.edu.cn", styles["meta"]),
            Paragraph("ORCID: 0009-0008-9175-8226", styles["meta"]),
            Spacer(1, 3 * mm),
            Paragraph("Manuscript", styles["meta"]),
            HRFlowable(width="100%", thickness=0.8, color=GRID, spaceBefore=6, spaceAfter=8),
        ]
    )

    index = lines.index("## Abstract")
    table_index = 0
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            raw = " ".join(part.strip() for part in paragraph)
            # Long hashes and other unbreakable identifiers should not be
            # typeset with full justification: ReportLab stretches the spaces
            # between ordinary words to fill the line, producing the visibly
            # broken SHA-256 paragraph in the review PDF.
            if section_name == "Abstract":
                style = styles["abstract"]
            elif "SHA-256" in raw or raw.count("`sha256") >= 1:
                style = styles["body_left"]
            else:
                style = styles["body"]
            story.append(Paragraph(inline_markup(raw, bib), style))
            paragraph.clear()

    section_name = ""
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush()
            index += 1
            continue
        if stripped == "## References":
            flush()
            break
        if stripped.startswith("## "):
            flush()
            section_name = stripped[3:].strip()
            story.append(Paragraph(html.escape(section_name), styles["h1"]))
            index += 1
            continue
        if stripped.startswith("### "):
            flush()
            story.append(Paragraph(html.escape(stripped[4:].strip()), styles["h2"]))
            index += 1
            continue
        image_match = re.fullmatch(r"!\[(.+?)\]\((.+?)\)", stripped)
        if image_match:
            flush()
            path = ROOT / "paper" / image_match.group(2)
            story.extend(figure_flowable(path, image_match.group(1), styles))
            index += 1
            continue
        if stripped.startswith("|"):
            flush()
            rows, index = parse_table(lines, index)
            story.extend(table_flowable(rows, table_index, styles, bib))
            table_index += 1
            continue
        if stripped == r"\[":
            flush()
            index += 1
            equation: list[str] = []
            while index < len(lines) and lines[index].strip() != r"\]":
                equation.append(lines[index])
                index += 1
            story.append(Paragraph(latex_formula_to_markup("\n".join(equation)), styles["equation"]))
            index += 1
            continue
        if stripped.startswith("- "):
            flush()
            while index < len(lines) and lines[index].strip().startswith("- "):
                item = lines[index].strip()[2:]
                story.append(Paragraph("• " + inline_markup(item, bib), styles["bullet"]))
                index += 1
            continue
        if re.match(r"^\d+\. ", stripped):
            flush()
            while index < len(lines) and re.match(r"^\d+\. ", lines[index].strip()):
                item_match = re.match(r"^(\d+)\.\s+(.*)", lines[index].strip())
                assert item_match
                story.append(Paragraph(item_match.group(1) + ". " + inline_markup(item_match.group(2), bib), styles["bullet"]))
                index += 1
            continue
        if stripped.startswith("**Keywords:**"):
            flush()
            story.append(Paragraph(inline_markup(stripped, bib), styles["abstract"]))
            story.append(Spacer(1, 3 * mm))
            index += 1
            continue
        paragraph.append(line)
        index += 1
    flush()

    story.append(Paragraph("References", styles["h1"]))
    cited_keys = set(
        re.findall(r"(?<![A-Za-z0-9._%+-])@([A-Za-z0-9_:+.-]+)", manuscript)
    )
    cited = [bib[key] for key in cited_keys if key in bib]
    cited.sort(key=lambda entry: (surname(author_parts(entry)[0]).lower() if author_parts(entry) else entry.key, entry.fields.get("year", "")))
    for entry in cited:
        story.append(Paragraph(html.escape(bibliography_text(entry)), styles["reference"]))
    return story


def main() -> int:
    global HAS_SUM_FONT
    if SUM_FONT_PATH.exists():
        pdfmetrics.registerFont(TTFont(SUM_FONT_NAME, str(SUM_FONT_PATH)))
        HAS_SUM_FONT = True
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    bib = parse_bibtex(BIBLIOGRAPHY.read_text(encoding="utf-8"))
    styles = make_styles()
    story = build_story(manuscript, bib, styles)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=17 * mm,
        title="Testing JSON Schema Instruction Artifacts",
        author="Shengyao Sun",
        subject="Testing JSON Schema instruction artifacts",
        creator="Offline reproducible paper builder",
    )
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

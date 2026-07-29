from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SOURCE = PAPER / "manuscript.md"
TMLR = PAPER / "tmlr"
TEMPLATE = ROOT / "tmp" / "tmlr-style-file"

TABLE_CAPTIONS = (
    "Primary 100-record study systems and operational summary.",
    "Decomposed follow-up and official-endpoint replication.",
    "Primary-study normalized excess disagreement.",
    "Primary-study quality metrics by representation.",
)


def escape_latex(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def inline(text: str) -> str:
    text = (
        text.replace("\u2011", "-")
        .replace("\u2013", "--")
        .replace("\u2014", "---")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", "``")
        .replace("\u201d", "''")
        .replace("\u2212", "-")
    )
    tokens: list[str] = []

    def hold(value: str) -> str:
        index = len(tokens)
        tokens.append(value)
        return f"@@T{index}@@"

    text = re.sub(r"\\\((.+?)\\\)", lambda match: hold(r"\(" + match.group(1) + r"\)"), text)

    def citation(match: re.Match[str]) -> str:
        parts = [part.strip() for part in match.group(1).split(";")]
        keys = [part.lstrip("-@").strip() for part in parts]
        if len(parts) == 1 and parts[0].startswith("-@"):
            return hold(r"\citeyearpar{" + keys[0] + "}")
        return hold(r"\citep{" + ",".join(keys) + "}")

    text = re.sub(r"\[((?:-?@[A-Za-z0-9_:+.-]+(?:\s*;\s*)?)+)\]", citation, text)
    def code(match: re.Match[str]) -> str:
        value = match.group(1)
        if len(value) >= 32:
            chunks = [value[index : index + 8] for index in range(0, len(value), 8)]
            return hold(
                r"\texttt{" + r"\allowbreak{}".join(escape_latex(chunk) for chunk in chunks) + "}"
            )
        return hold(r"\texttt{" + escape_latex(value) + "}")

    text = re.sub(r"`([^`]+)`", code, text)
    text = re.sub(
        r"\*\*([^*]+)\*\*",
        lambda match: hold(r"\textbf{" + escape_latex(match.group(1)) + "}"),
        text,
    )
    text = re.sub(
        r"(?<!\*)\*([^*]+)\*(?!\*)",
        lambda match: hold(r"\emph{" + escape_latex(match.group(1)) + "}"),
        text,
    )
    rendered = escape_latex(text)
    for index in reversed(range(len(tokens))):
        rendered = rendered.replace(f"@@T{index}@@", tokens[index])
    return rendered


def strip_number(title: str) -> str:
    return re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", title).strip()


def table_to_latex(rows: list[list[str]], table_index: int) -> list[str]:
    width = len(rows[0])
    alignment = "l" + "r" * (width - 1)
    caption = (
        TABLE_CAPTIONS[table_index]
        if table_index < len(TABLE_CAPTIONS)
        else f"Additional result table {table_index + 1}."
    )
    output = [
        r"\begin{table}[t]",
        rf"\caption{{{caption}}}",
        rf"\label{{tab:markdown-{table_index + 1}}}",
        r"\centering",
        r"\resizebox{\linewidth}{!}{%",
        rf"\begin{{tabular}}{{{alignment}}}",
        r"\toprule",
        " & ".join(r"\textbf{" + inline(cell.strip()) + "}" for cell in rows[0]) + r" \\",
        r"\midrule",
    ]
    for row in rows[2:]:
        padded = row + [""] * (width - len(row))
        output.append(" & ".join(inline(cell.strip()) for cell in padded[:width]) + r" \\")
    output.extend([r"\bottomrule", r"\end{tabular}%", r"}", r"\end{table}"])
    return output


def parse_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and lines[index].strip().startswith("|"):
        rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
        index += 1
    return rows, index


def convert_body(lines: list[str]) -> list[str]:
    output: list[str] = []
    index = 0
    table_index = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            output.append(inline(" ".join(part.strip() for part in paragraph)))
            output.append("")
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            output.append(r"\subsection{" + inline(strip_number(stripped[4:])) + "}")
            index += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            output.append(r"\section{" + inline(strip_number(stripped[3:])) + "}")
            index += 1
            continue
        image = re.fullmatch(r"!\[(.+?)\]\((.+?)\)", stripped)
        if image:
            flush_paragraph()
            caption = re.sub(r"^Figure\s+\d+\.\s*", "", image.group(1))
            path = "../" + image.group(2)
            label = Path(image.group(2)).stem.replace("_", "-")
            output.extend(
                [
                    r"\begin{figure}[t]",
                    r"\centering",
                    rf"\includegraphics[width=\linewidth]{{{path}}}",
                    r"\caption{" + inline(caption) + "}",
                    rf"\label{{fig:{label}}}",
                    r"\end{figure}",
                ]
            )
            index += 1
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            rows, index = parse_table(lines, index)
            output.extend(table_to_latex(rows, table_index))
            table_index += 1
            continue
        if stripped == r"\[":
            flush_paragraph()
            output.append(r"\[")
            index += 1
            while index < len(lines) and lines[index].strip() != r"\]":
                output.append(lines[index])
                index += 1
            output.append(r"\]")
            index += 1
            continue
        if re.match(r"^- ", stripped):
            flush_paragraph()
            output.append(r"\begin{itemize}")
            while index < len(lines) and lines[index].strip().startswith("- "):
                output.append(r"\item " + inline(lines[index].strip()[2:]))
                index += 1
            output.append(r"\end{itemize}")
            continue
        if re.match(r"^\d+\. ", stripped):
            flush_paragraph()
            output.append(r"\begin{enumerate}")
            while index < len(lines) and re.match(r"^\d+\. ", lines[index].strip()):
                item = re.sub(r"^\d+\. ", "", lines[index].strip())
                output.append(r"\item " + inline(item))
                index += 1
            output.append(r"\end{enumerate}")
            continue
        paragraph.append(line)
        index += 1

    flush_paragraph()
    return output


def main() -> int:
    text = SOURCE.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].removeprefix("# ").strip()

    abstract_start = lines.index("## Abstract") + 1
    introduction_start = lines.index("## 1. Introduction")
    references_start = lines.index("## References")
    abstract_lines = [
        line.strip()
        for line in lines[abstract_start:introduction_start]
        if line.strip() and not line.strip().startswith("**Keywords:")
    ]
    keywords = next(
        line.strip().replace("**Keywords:**", "").strip()
        for line in lines[abstract_start:introduction_start]
        if line.strip().startswith("**Keywords:")
    )
    body = convert_body(lines[introduction_start:references_start])

    preamble = [
        r"\documentclass[10pt]{article}",
        r"\usepackage{tmlr}",
        r"\usepackage{amsmath,amssymb}",
        r"\usepackage{graphicx}",
        r"\usepackage{booktabs}",
        r"\usepackage{hyperref}",
        r"\usepackage{url}",
        r"\hypersetup{hidelinks}",
        "",
        r"\title{" + inline(title) + "}",
        r"\author{\name Anonymous Author(s)}",
        r"\def\month{MM}",
        r"\def\year{YYYY}",
        r"\def\openreview{\url{https://openreview.net/forum?id=XXXX}}",
        "",
        r"\begin{document}",
        r"\maketitle",
        r"\begingroup\renewcommand\thefootnote{}\footnotetext{Generative AI tools were used for language editing and code assistance. The authors designed the study and verified all claims, calculations, citations, code, and reported results.}\endgroup",
        r"\begin{abstract}",
        inline(" ".join(abstract_lines)),
        r"\end{abstract}",
        r"\noindent\textbf{Keywords:} " + inline(keywords),
        "",
    ]
    ending = [
        r"\bibliography{references}",
        r"\bibliographystyle{tmlr}",
        r"\end{document}",
        "",
    ]

    TMLR.mkdir(parents=True, exist_ok=True)
    (TMLR / "main.tex").write_text("\n".join(preamble + body + ending), encoding="utf-8")
    shutil.copyfile(PAPER / "references.bib", TMLR / "references.bib")
    print(f"Wrote {TMLR / 'main.tex'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

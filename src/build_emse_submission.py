"""Generate a flat, editable LaTeX source package for EMSE review."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import build_tmlr_submission as markdown_latex


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SOURCE = PAPER / "manuscript.md"
OUTPUT = PAPER / "emse"


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

    markdown_latex.TABLE_CAPTIONS = (
        "Study stages, record panels, interfaces, and formal status.",
        "Execution windows, endpoint provenance, and request settings.",
        "Decomposed text-mode effects, supplemental endpoint results, and deployment-level decisions.",
        "Leaf-value accuracy contrasts for the decomposed studies.",
        "Post-hoc effect-concentration stress tests.",
        "Selected high-effect Qwen text-mode cases; post-hoc and non-representative.",
    )
    body = markdown_latex.convert_body(lines[introduction_start:references_start])
    # The source package is flat, as requested by Springer submission guidance.
    body = [re.sub(r"\{\.\./figures/(figure[0-9A-Za-z_-]+\.png)\}", r"{\1}", line) for line in body]

    preamble = [
        r"\documentclass[11pt,a4paper]{article}",
        r"\usepackage[margin=25mm]{geometry}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{authblk}",
        r"\usepackage{amsmath,amssymb}",
        r"\usepackage{graphicx}",
        r"\usepackage{booktabs}",
        r"\usepackage{microtype}",
        r"\usepackage{natbib}",
        r"\usepackage[hidelinks]{hyperref}",
        r"\usepackage{xurl}",
        r"\usepackage{caption}",
        r"\captionsetup{font=small,labelfont=bf}",
        "",
        r"\title{" + markdown_latex.inline(title) + "}",
        r"\author{Shengyao Sun\thanks{Corresponding author: \href{mailto:sthfornothing@sjtu.edu.cn}{sthfornothing@sjtu.edu.cn}; ORCID: \href{https://orcid.org/0009-0008-9175-8226}{0009-0008-9175-8226}}}",
        r"\affil{Shanghai Jiao Tong University, Shanghai, China}",
        r"\date{}",
        "",
        r"\begin{document}",
        r"\maketitle",
        r"\begin{abstract}",
        markdown_latex.inline(" ".join(abstract_lines)),
        r"\end{abstract}",
        r"\noindent\textbf{Keywords:} " + markdown_latex.inline(keywords),
        "",
    ]
    ending = [
        r"\bibliographystyle{plainnat}",
        r"\bibliography{references}",
        r"\end{document}",
        "",
    ]

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "main.tex").write_text("\n".join(preamble + body + ending), encoding="utf-8")
    shutil.copyfile(PAPER / "references.bib", OUTPUT / "references.bib")
    for figure in sorted((PAPER / "figures").glob("figure*.png")):
        shutil.copyfile(figure, OUTPUT / figure.name)
    print(f"Wrote flat EMSE source package to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

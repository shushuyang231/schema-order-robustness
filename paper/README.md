# Paper package / 论文文件包

This directory contains the current single-blind EMSE PROMPT-SE manuscript and
its frozen, offline-reproducible paper artifacts. The experimental branch is
closed; no build or audit command calls a model API.

本目录是当前 EMSE PROMPT-SE 单盲稿件及其冻结、可离线复现的论文材料。实验
分支已经关闭，构建和审计命令都不会调用模型 API。

## Main submission files / 主要文件

- `manuscript.md` — authoritative English manuscript (8,540 audited words).
- `references.bib` — bibliography used by the manuscript.
- `emse/main.tex` — flat editable LaTeX review source.
- `../output/pdf/schema_order_emse_promptse_revision.pdf` — latest rendered
  18-page A4 review PDF.
- `emse/cover_letter.md` — special-issue cover-letter draft.
- `emse/submission_checklist.md` — journal and administration checklist.
- `emse/AUTHOR_METADATA_REQUIRED.md` — author-confirmed metadata and ORCID.

## Evidence and reproduction / 证据与复现

Frozen aggregate reports are under `../results/`; protocols and decision
records are under `../protocol/`; generated tables and figures are under
`tables/` and `figures/`. Rebuild and audit the complete package with:

```powershell
.\scripts\reproduce_paper_offline.ps1
```

The command compiles Python sources, runs offline tests, rebuilds tables and
figures from frozen reports, audits manuscript claims and citations, regenerates
the LaTeX/PDF package, and validates Online Resource 1. Raw provider responses,
credentials, and restricted benchmark contexts are intentionally not included.

## Author metadata / 作者信息

The title page identifies Shengyao Sun as an undergraduate student at Shanghai
Jiao Tong University, Shanghai, China. Corresponding email:
`sthfornothing@sjtu.edu.cn`. ORCID:
`0009-0008-9175-8226`.

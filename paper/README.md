# Paper status

This directory contains the rewritten single-blind EMSE PROMPT-SE manuscript
and its frozen, offline-reproducible paper artifacts. The experimental branch
is closed; no build or audit command calls a model API.

## Main submission files

- `manuscript.md` — authoritative English manuscript (9,454 audited words).
- `references.bib` — bibliography; every entry is cited and every citation is
  defined.
- `emse/main.tex` — flat editable LaTeX review source.
- `../output/pdf/schema_order_emse_promptse.pdf` — rendered A4 review PDF.
- `emse/cover_letter.md` — special-issue cover-letter draft.
- `emse/submission_checklist.md` — journal and human-administration checks.
- `emse/AUTHOR_METADATA_REQUIRED.md` — author-confirmed title-page metadata and
  ORCID status.

The paper uses single-blind author identification and includes the declarations
required by EMSE. Generative-AI assistance and human accountability are
documented in the reproducibility section.

## Evidence and audit files

- `claim_evidence_audit.md` — claim-to-report mapping and wording boundaries.
- `reviews/emse_rewrite_plan.md` — frozen journal-reframing plan.
- `reviews/post_tmlr_venue_novelty_adversarial_audit.md` — venue and closest-work
  audit after the earlier desk rejection.
- `artifact_manifest.json` — hashes for all generated figures and tables.
- `draft_audit.json` — citation, headline-number, section, table, and figure
  audit.
- `robustness/dialect_validation_audit.json` — Draft 7 versus Draft 2020-12
  validation audit.

## Figures, tables, and reproduction

Figures are under `figures/`; generated result tables are under `tables/`.
Regenerate and audit the complete submission offline with:

```powershell
.\scripts\reproduce_paper_offline.ps1
```

The command compiles Python sources, runs the unit tests, rebuilds tables and
figures from frozen reports, audits the manuscript, regenerates the flat LaTeX
and PDF, and writes Online Resource 1 to
`output/artifact/schema_order_emse_online_resource1.zip`.

## Author metadata

The title page identifies Shengyao Sun as an undergraduate student at Shanghai
Jiao Tong University in Shanghai, China, with `sthfornothing@sjtu.edu.cn` as
the corresponding email. ORCID: `0009-0008-9175-8226`.

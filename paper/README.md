# Paper status

This directory contains the anonymous TMLR manuscript and its frozen,
offline-reproducible paper artifacts.

## Submission files

- `manuscript.md` — source manuscript.
- `references.bib` — bibliography used by the manuscript.
- `tmlr/main.tex` — anonymous review-mode source using the official TMLR style.
- `tmlr/submission_checklist.md` — submission and human-administration checks.
- `../output/pdf/schema_order_tmlr_anonymous.pdf` — rendered 15-page review PDF.

The first page discloses the use of generative AI for language editing and code
assistance. No author-identifying information is present in the review PDF.

## Evidence and audit files

- `claim_evidence_audit.md` — claim-level evidence, calculations, caveats, and
  redistribution boundaries.
- `reviews/statistical_review.md` — simulated statistical-methods review.
- `reviews/scope_review.md` — simulated TMLR scope/novelty review.
- `reviews/revision_log.md` — fixes made in response to those reviews.
- `artifact_manifest.json` — source and output hashes for generated figures and
  tables.
- `robustness/dialect_validation_audit.json` — Draft 7 versus Draft 2020-12
  validation audit.

## Figures and tables

All submission figures are under `figures/`, and their source tables are under
`tables/`. `chart_contract.md` records chart semantics and QA decisions.

Regenerate them from frozen summary reports without inference:

```powershell
.\.venv\Scripts\python.exe src\build_paper_artifacts.py
```

Run all offline manuscript and artifact gates:

```powershell
.\scripts\reproduce_paper_offline.ps1
```

This script never calls a model API. The anonymous supplement is written to
`output/artifact/schema_order_tmlr_anonymous_artifact.zip`.

## Remaining human checks

Before upload, the authors must proofread the PDF, confirm third-party
redistribution rights, complete OpenReview profiles and declarations, and
replace the placeholder paper URL after an anonymous submission URL exists.

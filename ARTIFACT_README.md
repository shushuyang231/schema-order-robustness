# Online Resource 1 - Schema-order robustness artifact

This offline artifact supports *Testing JSON Schema Instruction Artifacts:
Distributional Robustness under Validation-Equivalent Serialization and JSON
Mode*. It contains the transformation, evaluation, canonicalization, and
paper-build code; frozen manifests and aggregate reports; generated tables and
figures; and unit tests. Reproduction never calls a model API.

## Reproduce locally

On Windows PowerShell:

```powershell
.\scripts\reproduce_paper_offline.ps1
```

The script compiles Python sources, runs the offline unit tests, rebuilds paper
tables and figures from frozen reports, audits citations and headline values,
regenerates the flat EMSE LaTeX source and review PDF, and validates the
Online Resource archive and secret scan. Use `-Python <path>` to select a
Python 3.12 interpreter. Install the declared dependencies from
`requirements-paper.txt` and `requirements-lock.txt`.

## Reproducibility levels

- **Directly reproducible offline:** schema transformations and
  canonicalization on redistributable examples, unit tests, paper tables and
  figures, source-report hashes, and manuscript consistency checks.
- **Auditable from frozen aggregate reports:** deployment-specific estimates,
  confidence intervals, p-values, operational counts, token totals, and
  provider/request metadata.
- **Not redistributed:** raw provider responses, credentials, reasoning text,
  restricted gold answers, and benchmark contexts whose redistribution is not
  authorized. The API runners are included for method inspection only.

The public archive intentionally omits private gateway communications and
unpublished provider data. See `LICENSES.md` for the licensing and data-use
boundaries.

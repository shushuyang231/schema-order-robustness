# Online Resource 1 — schema-order robustness artifact

This offline artifact supports the paper *Testing JSON Schema Instruction
Artifacts: Distributional Robustness under Validation-Equivalent Serialization
and JSON Mode*. It contains the transformation, evaluation, canonicalization,
and paper-build code; frozen manifests and aggregate reports; generated tables
and figures; and unit tests. It never calls a model API during reproduction.

## Reproduce locally

On Windows PowerShell:

```powershell
.\scripts\reproduce_paper_offline.ps1
```

The script:

1. compiles the Python sources;
2. runs 33 offline unit tests whose inputs can be redistributed;
3. rebuilds paper tables and figures from frozen aggregate JSON reports;
4. audits citations, sections, figures, and headline values;
5. generates the flat EMSE LaTeX source and review PDF; and
6. validates the Online Resource ZIP allowlist, secret scan, and archive
   integrity.

Use `-Python <path>` to select a Python 3.12 interpreter. Install the declared
dependencies from `requirements-paper.txt` and `requirements-lock.txt`.

## Reproducibility levels

- **Directly reproducible offline:** transformation and canonicalization on
  redistributable examples, unit tests, paper tables and figures, source-report
  hashes, and manuscript consistency checks.
- **Auditable from frozen aggregate reports:** deployment-specific estimates,
  confidence intervals, p-values, operational counts, token totals, and
  provider/request metadata.
- **Not redistributed:** raw provider responses, credentials, reasoning text,
  restricted gold answers, and benchmark contexts whose redistribution is not
  authorized. The full development tree additionally has 10 protocol-construction
  tests whose inputs fall in these excluded categories; they pass in the private
  working tree but are deliberately absent from this archive. See `LICENSES.md`.

The API runners remain included for method inspection, but neither the
reproduction command nor the paper-build scripts invoke them.

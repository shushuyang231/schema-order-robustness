# Anonymous paper artifact

This artifact supports the paper *Equivalent Schemas, Different
Distributions*. It is designed for offline inspection and regeneration of
paper tables and figures. It never calls a model API.

## Reproduce locally

On Windows PowerShell:

```powershell
.\scripts\reproduce_paper_offline.ps1
```

The script:

1. compiles local Python sources;
2. runs the unit-test suite;
3. rebuilds all paper tables and figures from frozen aggregate JSON reports;
4. audits manuscript citations, required sections, figure presence, and
   reported values; and
5. verifies that the anonymous ZIP allowlist excludes raw responses,
   credentials, restricted gold, and downloaded benchmark data.

Use `-Python <path>` to select another Python 3.12 interpreter. Exact packages
from the validated environment are recorded in `requirements-lock.txt`.

## Reproducibility levels

- **Directly reproducible offline:** transformations on synthetic examples,
  unit tests, paper tables, paper figures, source-report hashes, and manuscript
  consistency checks.
- **Auditable from frozen reports and hashes:** model-specific estimates,
  intervals, p-values, operational counts, and provider metadata.
- **Not redistributed:** raw provider responses, reasoning text, benchmark
  contexts, and restricted gold answers. See `LICENSES.md`.

The inference runner remains included for method inspection and reuse, but the
offline reproduction script does not invoke it.

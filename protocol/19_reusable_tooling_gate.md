# Reusable Schema Metamorphic Tooling Gate

Date: 2026-07-18

## Decision

**PASS_FOR_PAPER_ENGINEERING**

The project now has a dataset-independent public-side preparation CLI in
`src/prepare_schema_metamorphic_tasks.py`.  It converts a generic JSONL task file
into the five frozen schema representations, a repeated-call manifest, and a
per-record hash/equivalence audit.  Its output is directly accepted by the
existing resumable gateway runner.

## Public input contract

Each JSONL row must contain:

- `record_id`
- `context`
- `question`
- `json_schema` as a JSON object or JSON-encoded object

Optional `metadata` is copied.  Known answer-side fields (`answer`,
`expected_answer`, `gold`, `ground_truth`, `sol_sql`, and `test_cases`) cause a
hard failure instead of being silently discarded.

## Automated checks

- every input Schema passes `Draft202012Validator.check_schema`;
- duplicate and empty record IDs fail explicitly;
- each transformed Schema has the same normalized validation signature;
- applicability and SHA256 are recorded for every variant;
- output JSONL serialization and record-ID hashes are deterministic;
- repeat conditions and expected request counts are frozen in the manifest;
- existing prompt leakage checks and request-key resume behavior remain active.

## Offline end-to-end smoke result

Input: `data/public/example_schema_tasks.jsonl`

- Records: 1
- Schema representations: 5
- Repeats: 2
- Expected mock predictions: 10
- Successful mock predictions: 10
- Parse success: 10/10 exact JSON
- Schema pass: 10/10
- Second invocation: 10/10 jobs skipped
- Output lines after resume check: 10 (no duplicates)

Audit artifact: `results/offline/schema_tool_smoke/audit.json`

The example public input SHA256 is
`8df15e8178be2aa90042ec7ef756cb7e650f456d967397a7a7ad25cac5c2a26a` and
the generated public task output SHA256 is
`9aafb1c901cf2426fe87fcd2938a13a7a76cc5d6b126453f76dbbb986aa9785d`.

## Test result

Command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Result: **15/15 tests passed** under Python 3.12.13.

Five new tests cover transformation signature preservation, deterministic
public-only preparation, restricted-field rejection, duplicate-ID rejection,
and manifest request counts.  The ten earlier statistical/cross-model tests also
continue to pass.

## Remaining paper-engineering work

This gate establishes a reusable task-preparation and execution path.  It does
not yet establish a polished distributable package, official-model provenance,
or external replication.  Before claiming a released tool, add a license,
top-level CLI/version metadata, a minimal public example evaluator, and a clean
repository export that excludes restricted data and API results as required.


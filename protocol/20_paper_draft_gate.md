# Paper Draft and Figure Gate

Date: 2026-07-18

## Decision

**PASS_FIRST_DRAFT — complete internal-review draft produced; not submission-ready.**

## Produced artifacts

- Full English manuscript: `paper/manuscript.md`
- Author-facing Chinese explanation: `paper/作者理解指南.md`
- Bibliography: `paper/references.bib`
- Method workflow figure: `paper/figures/figure1_method.png`
- Two-panel effect/accuracy forest plot: `paper/figures/figure2_forest.png`
- Four exact-value CSV tables under `paper/tables/`
- Figure contract and QA notes: `paper/chart_contract.md`
- Generated-artifact hashes: `paper/artifact_manifest.json`

## Validation completed

- Manuscript length: 4,232 English tokens counted as word-like units by the audit script.
- Citation keys: 10 used, 10 defined, zero missing, zero unused.
- Required sections: all present.
- Referenced figures: 2/2 present and readable.
- Paper table shapes: 8 distribution-effect rows and 10 quality rows, as expected.
- Exactly two comparisons meet the frozen 0.05 practical rule.
- Draft 7 versus Draft 2020-12 audit: zero disagreements across 500 Schema representations and 5,000 formal responses.
- Project tests: 15/15 passed.

Machine-readable result: `paper/draft_audit.json` with status `PASS`.

## Claim boundary preserved

The draft explicitly states that:

- the experiment is prompt-based Schema-guided generation, not native constrained decoding;
- aliases are unverified gateway identifiers;
- the GPT experiment did not reproduce the preregistered practical magnitude;
- no corrected average leaf-accuracy degradation was established;
- the post-hoc analysis did not establish a between-model difference or internal mechanism.

## Remaining submission blockers

1. Obtain advisor/domain-expert review and revise the research narrative.
2. Resolve model provenance where possible or accept it as a high-severity limitation.
3. Select a venue and convert the manuscript into its official template and page limit.
4. Expand and manually verify the bibliography against the chosen venue's related-work expectations.
5. Prepare a clean public artifact that excludes restricted gold, credentials, and non-redistributable API responses.
6. Decide whether an independently verifiable official endpoint or fixed open-weight replication is feasible before submission.


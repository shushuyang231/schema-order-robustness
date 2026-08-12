# Project handoff — JSON Schema instruction-artifact robustness paper

Last updated: 2026-08-12

## Current objective

The paper has been rewritten for the Empirical Software Engineering special
issue **PROMPT-SE 2026** as a Research Paper.

Current title:

> Testing JSON Schema Instruction Artifacts: Distributional Robustness under
> Validation-Equivalent Serialization and JSON Mode

The contribution is an empirical software-engineering method for regression
testing LM-facing JSON Schema artifacts. It is not a claim about an internal
model mechanism, universal accuracy harm, or strict constrained decoding.

## Frozen evidence

The core analysis contains 17,900 successful black-box responses:

- Initial five-way 100-record study: 2,500 Sonnet gateway and 2,500 GPT gateway
  responses.
- Disjoint 200-record decomposition: 3,000 Sonnet and 3,000 GPT responses.
- Official DeepSeek replication: 3,000 responses.
- Official Qwen-Plus text study: 2,400 responses over 160 records.
- Matched Qwen-Plus JSON Mode study: 1,500 responses over 100 records.

A separate 600-response Qwen3.7 fixed-snapshot pilot is disclosed but excluded
from the formal Qwen-Plus inference and from the 17,900 total.

### Decomposed text-mode results

| Deployment | Property order | Additional member order | Frozen practical decision |
|---|---:|---:|---|
| Sonnet gateway alias | 0.0584 | 0.0768 | both confirmed |
| GPT gateway alias | 0.0329 | 0.0380 | both below 0.05 |
| DeepSeek official endpoint | 0.0133 | 0.0182 | both below 0.05 |
| Qwen-Plus official endpoint | 0.1255 | 0.1229 | both confirmed |

The GPT and DeepSeek estimates are detectable but below the frozen practical
threshold; they are negative practical replications, not null effects. Direct
Sonnet-versus-GPT differences did not survive multiplicity correction, so the
paper does not claim a confirmed provider/model ranking.

### JSON Mode boundary

- JSON Mode means `response_format={"type":"json_object"}`; it is not strict
  JSON Schema constrained decoding.
- Within JSON Mode, property-order and additional-member effects are 0.1582 and
  0.1219; both meet the 0.05 within-mode rule.
- Matched JSON-minus-text changes are +0.0191 and -0.0249. Both intervals include
  zero, both point estimates are below the frozen 0.03 material-interaction
  threshold, and both Holm p-values are 0.4951.
- Permitted wording: JSON Mode did not demonstrate material attenuation in this
  Qwen deployment.
- Forbidden wording: JSON Mode has no effect; the modes are equivalent.

### Quality and heterogeneity

- No universal average Schema-compliance or leaf-value-accuracy degradation is
  established.
- Retain the GPT additional-member leaf-accuracy result (-0.0248, CI excluding
  zero, Holm p=0.0208) as a secondary exception below the earlier 0.03
  engineering context.
- All systems have a median record effect of zero; mean effects are concentrated.
- Cross-system record concordance is not confirmed. Matched Qwen text versus
  JSON Mode has Spearman rho 0.618/0.626, both global Holm p=0.0040; this remains
  post-hoc exploratory.

## Engineering artifact

`src/canonicalize_json_schema.py` recursively sorts object members and only
unique `required` arrays, preserving all other arrays. All stored
`original`/`properties_reversed`/`keywords_reversed` triples collapse for all
200 decomposed records. This is a conservative intervention, not a general JSON
Schema equivalence checker.

## Post-submission endpoint expansion

Three separately labelled deployments traversed their frozen 3,000-request
job lists: SJTU Zhiyuan-1 `deepseek-chat`, SJTU Zhiyuan-1
`deepseek-reasoner`, and TokenRhythm `deepseek-v4-flash`. The final aggregate
completion audit found 9,000/9,000 unique successful request keys. The logs
retain 28 top-level transport-error rows; all 11 previously missing keys were
recovered without changing records, prompts, request parameters, or analysis
rules.

The runner previously returned success after traversing all job positions even
when isolated errors remained. It now returns nonzero unless every frozen key
has a successful row. `src/audit_endpoint_panel_runs.py` is the offline
completion/provenance gate. The completed panel was then evaluated offline
under the frozen six-test Holm family.

The analysis and reporting boundary is frozen in
`protocol/35_endpoint_panel_completion_and_analysis_amendment.md`: the original
17,900 responses remain the scientific core; the three new runs are
supplemental deployment evidence, are not pooled as independent model samples,
and cannot support a hardware-causal claim. Deployment-local two-contrast Holm
decisions are retained, while any panel-level claim uses Holm across all six
active deployment-by-contrast tests.

## Completed paper package

- Authoritative manuscript: `paper/manuscript.md` (9,454 audited words).
- Flat editable source: `paper/emse/main.tex` plus `references.bib` and four
  flat figure files.
- Review PDF: `output/pdf/schema_order_emse_promptse.pdf` (20 A4 pages).
- Online Resource 1: `output/artifact/schema_order_emse_online_resource1.zip`
  (154 allowlisted material files, no raw provider outputs, credentials,
  restricted gold, or downloaded benchmark contexts).
- Cover letter: `paper/emse/cover_letter.md`.
- Standalone EMSE title page: `output/pdf/schema_order_emse_title_page.pdf`.
- Submission checklist: `paper/emse/submission_checklist.md`.
- Claim audit: `paper/claim_evidence_audit.md`.

The PDF was rendered to PNG at 110 dpi and representative pages covering the
abstract, execution-settings table, endpoint-panel results table, equations,
discussion, and references were visually inspected.
There are no clipped figures, broken tables, blank pages, or unresolved
citations. Figures use both color and marker shape and have external captions.

## Verification status

`scripts/reproduce_paper_offline.ps1` completes with
`OFFLINE_REPRODUCTION_PASS`:

- Python compilation: pass.
- Private working-tree tests: 45/45 pass.
- Frozen figure/table rebuild: pass.
- Manuscript citation/headline/section audit: pass.
- Flat EMSE source build: pass.
- EMSE review PDF build: pass.
- Online Resource ZIP allowlist, secret scan, and integrity test: pass.
- Fresh extraction self-test: 35/35 redistributable-input tests and the full
  seven-step offline reproduction pass. The private working tree additionally
  has 10 protocol-construction tests whose benchmark contexts/raw-response
  inputs are intentionally not redistributed.

No step calls a model API.

## Author metadata

EMSE uses single-blind review. The confirmed title-page metadata is Shengyao
Sun, Shanghai Jiao Tong University, Shanghai, China; corresponding email
`sthfornothing@sjtu.edu.cn`. The cover letter identifies the author as an
undergraduate student. No department was invented. ORCID is
`0009-0008-9175-8226`.

## Adversarial-review disposition

The actionable suggestions were incorporated: a clearer method contribution,
retry/error accounting, an execution-settings table in the main text, exact
prompt and request-contract disclosure, threshold sensitivity at 0.03/0.05/0.08,
high-effect case inspection, gateway-provenance limits, and an explicit
three-layer reproducibility claim. The two reported rendering defects were
fixed in the revision PDF: long SHA-256 paragraphs are left-aligned and the
two display equations use readable mathematical markup. The review's 10-page
ACM-format recommendation was rejected because it confused the completed EASE
Prompt-SE workshop with the currently open EMSE PROMPT-SE special issue.

An August 2026 informal communication from the third-party gateway operator
states that the Sonnet and GPT routes ultimately used Anthropic and OpenAI
commercial API platforms, respectively. Because the operator could not provide
written routing, billing, or subscription evidence, the manuscript treats this
as provenance-supporting rather than dispositive and continues to report both
deployments as gateway aliases. The gateway identity and chat screenshots remain
private because they are unnecessary for result auditing and expose third-party
identifying information.

## Final hashes

- Manuscript SHA-256:
  `86303C0462C56974DF9FA469BA8506A60D862102FDB218D533EB7017E8EA6726`
- EMSE `main.tex` SHA-256:
  `0104D9ACCFF9872BB5DF1A713310F978BB328683202AC4700001348700AC6D69`
- Review PDF SHA-256:
  `32BCB639BD935B186860BB104CEB886674F7B725A545B4A5A6EB561C1366672F`
- Online Resource 1 SHA-256:
  `7F921BC6AB702DEB4874381B950F51AAE786D3479FD0A833FA39EE1310605491`

## Exact next local command

No further API calls are needed. The endpoint panel is complete and the
offline audit/evaluation has been run:

```powershell
& ".\scripts\evaluate_endpoint_panel_offline.ps1"
```

# Project handoff — JSON Schema instruction-artifact robustness paper

Last updated: 2026-08-02

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

## Completed paper package

- Authoritative manuscript: `paper/manuscript.md` (8,004 audited words).
- Flat editable source: `paper/emse/main.tex` plus `references.bib` and four
  flat figure files.
- Review PDF: `output/pdf/schema_order_emse_promptse.pdf` (17 A4 pages).
- Online Resource 1: `output/artifact/schema_order_emse_online_resource1.zip`
  (137 allowlisted material files, no raw provider outputs, credentials,
  restricted gold, or downloaded benchmark contexts).
- Cover letter: `paper/emse/cover_letter.md`.
- Submission checklist: `paper/emse/submission_checklist.md`.
- Claim audit: `paper/claim_evidence_audit.md`.

The PDF was rendered to PNG at 110 dpi and every page was visually inspected.
There are no clipped figures, broken tables, blank pages, or unresolved
citations. Figures use both color and marker shape and have external captions.

## Verification status

`scripts/reproduce_paper_offline.ps1` completes with
`OFFLINE_REPRODUCTION_PASS`:

- Python compilation: pass.
- Private working-tree tests: 43/43 pass.
- Frozen figure/table rebuild: pass.
- Manuscript citation/headline/section audit: pass.
- Flat EMSE source build: pass.
- EMSE review PDF build: pass.
- Online Resource ZIP allowlist, secret scan, and integrity test: pass.
- Fresh extraction self-test: 33/33 redistributable-input tests and the full
  seven-step offline reproduction pass. The private working tree additionally
  has 10 protocol-construction tests whose benchmark contexts/raw-response
  inputs are intentionally not redistributed.

No step calls a model API.

## Author metadata

EMSE uses single-blind review. The confirmed title-page metadata is Shengyao
Sun, Shanghai Jiao Tong University, Shanghai, China; corresponding email
`sthfornothing@sjtu.edu.cn`. The cover letter identifies the author as an
undergraduate student. No department was invented. ORCID is omitted because the
author does not currently have one.

## Adversarial-review disposition

The actionable suggestions were incorporated: a clearer method contribution,
retry/error accounting, threshold sensitivity at 0.03/0.05/0.08, high-effect
case inspection, gateway-provenance limits, and an explicit three-layer
reproducibility claim. The review's 10-page ACM-format recommendation was
rejected because it confused the completed EASE Prompt-SE workshop with the
currently open EMSE PROMPT-SE special issue.

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
  `26EF8A3755178C280607B4208C7F9ED0A82CB07333CC2443C29C0BA8598B763C`
- EMSE `main.tex` SHA-256:
  `C6F6BB91822BC145C74E92AFCB6B4AFEAC284379D3F059078A261202A80E4CD8`
- Review PDF SHA-256:
  `4AE1A92E8A967D6404C642BEC8D16E1C2B0626E24592BD0F5DB48CF7D9379E91`
- Online Resource 1 SHA-256:
  `64C134C1A56DF4A7D9D15F0A5B487BBB5A6FF78A9902D3E0B71CE39BEF13E8FC`

## Exact next local command

Do not call another model API. Review the completed submission checklist:

```powershell
Get-Content -Raw paper\emse\submission_checklist.md
```

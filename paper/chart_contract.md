# Paper Figure Contracts

## Figure 1 — Method workflow

- Analytical question: how does the experiment separate representation effects from ordinary model stochasticity?
- Takeaway: the task and prompt template stay fixed, four validation-equivalent Schema transformations are repeated, and cross-representation disagreement is adjusted by within-representation disagreement.
- Family/type: process flow diagram; code-native static PNG.
- Evidence grain: 100 records, five representations, five repeats, two gateway aliases, 5,000 successful responses.
- Palette: blue for transformations, orange for independent oracles, neutral grey for the pipeline; arrows and labels provide non-color distinction.
- Output: `paper/figures/figure1_method.png`, 1800 × 560, 180 DPI.

## Figure 2 — Primary effects and quality boundary

- Analytical question: do validation-equivalent reorderings shift normalized outputs beyond repeated-prompt noise, and do they change average leaf accuracy?
- Takeaway: two Sonnet-alias effects exceed the preregistered 0.05 practical threshold; GPT-alias effects are smaller, while no Holm-corrected leaf-accuracy effect is supported.
- Family/type: uncertainty and benchmark; two-panel forest plot.
- Evidence grain: eight model–variant comparisons from 100 record clusters each; 95% record-cluster bootstrap intervals.
- Panel A: token-normalized excess disagreement with zero and 0.05 reference lines.
- Panel B: variant-minus-original leaf-value accuracy difference with zero reference line.
- Palette: filled blue circle for Sonnet alias, open orange square for GPT alias; shape and fill preserve distinction without color.
- Output: `paper/figures/figure2_forest.png`, 1900 × 1080, 180 DPI.
- QA surface: full-resolution local PNG inspection and manuscript-width inspection.

## Omitted chart

No time-series, scatter, or feature-association chart is included. The experiment has no temporal process, and no corrected schema-feature association survived; plotting those analyses in the main paper would overemphasize null post-hoc results. Exact exploratory values remain in Table 4 and the analysis appendix.

## Figure 3 — Decomposed confirmation effects

- Analytical question: on 200 disjoint records, do property order and additional Schema-object member order produce noise-adjusted distribution shifts, and are those shifts accompanied by average accuracy changes?
- Takeaway: both Sonnet-alias contrasts meet the preregistered 0.05 practical rule; GPT-alias and official DeepSeek contrasts remain positive but below that rule. Only the GPT additional-member contrast has a corrected secondary leaf-accuracy decrease.
- Family/type: uncertainty and benchmark; two-panel forest plot.
- Evidence grain: six system–contrast comparisons from 200 record clusters each; 3,000 successful responses per observed system.
- Panel A: token-normalized excess disagreement with zero and 0.05 reference lines.
- Panel B: treatment-minus-baseline leaf-value accuracy difference with zero reference line.
- Palette: filled blue circle for Sonnet alias, open orange square for GPT alias, and filled green triangle for the official DeepSeek endpoint; shape and fill preserve distinction without color.
- Claim guard: the caption distinguishes model-specific preregistered decisions from post-hoc direct cross-model tests; it does not state that Sonnet is significantly more sensitive.
- Output: `paper/figures/figure3_decomposed_confirmation.png`, 1900 × 900, 180 DPI.
- QA surface: full-resolution local PNG inspection and manuscript-width inspection.

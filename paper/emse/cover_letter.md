# Cover letter — EMSE PROMPT-SE 2026

6 August 2026

Dear Editors of the PROMPT-SE 2026 Special Issue,

Please consider the manuscript “Testing JSON Schema Instruction Artifacts:
Distributional Robustness under Validation-Equivalent Serialization and JSON
Mode” as a Research Paper for the Empirical Software Engineering special issue
“Empirical Studies on Prompts and other Instruction Artifacts in Software
Engineering (PROMPT-SE 2026).”

The paper treats serialized JSON Schema as a first-class instruction artifact
in LM-enabled software. It studies a concrete maintenance failure mode:
serializers, middleware, or code generators can reorder a Schema without
changing its validator-visible contract, while the same reserialization can
change an LM component's output distribution. The work fits the special issue's
focus on empirical testing, quality assurance, reproducibility, and evolution
of structured instruction artifacts.

The manuscript contributes (1) a JSON-Schema-semantics-derived metamorphic
testing method; (2) a stochasticity-adjusted distributional estimator with
record-cluster inference; (3) positive and negative practical replications
across gateway and official provider deployments; (4) a matched Qwen-Plus
text-versus-JSON-Mode boundary experiment; and (5) a conservative
canonicalizer and CI regression workflow. The core evidence comprises 17,900
successful black-box responses. All deterministic analyses, frozen protocols,
aggregate results, and figures are supplied in the accompanying reproduction
package.

This manuscript reports original, unpublished work. It is not under
consideration by another journal or conference. There is no substantially
overlapping published conference paper. The author declares no competing
interests and received no external funding for the work.

Thank you for your consideration.

Sincerely,

Shengyao Sun
Undergraduate student, Shanghai Jiao Tong University
Shanghai, China
sthfornothing@sjtu.edu.cn

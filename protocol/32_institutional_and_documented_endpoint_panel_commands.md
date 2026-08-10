# Execution commands for Protocol 32

Run these commands from the project root. The commands do not print or save a
key. Keep each key only in the current PowerShell process and clear it when
finished.

## 1. Set a key without putting it in the command line

The smoke helper can prompt interactively, so the simplest option is to omit
the environment variable and type the key at its hidden prompt. If pasting
into a hidden prompt is inconvenient, use the following temporary process
environment pattern (the key is not shown in the command itself):

```powershell
$secret = Read-Host "Paste the endpoint API key" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
$env:SJTU_ZHIYUAN1_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
```

Use the same pattern with `TOKENRHYTHM_API_KEY` for TokenRhythm. Do not put
either variable in a `.env` file, GitHub Actions file, manifest, or screenshot.

## 2. Catalog-only and three-call smoke gates

Run catalog-only first for each fixed row. A failed catalog gate sends no
completion calls.

```powershell
$py = ".\.venv\Scripts\python.exe"

# SJTU Zhiyuan-1: set $env:SJTU_ZHIYUAN1_API_KEY immediately before these calls.
& $py src\smoke_openai_compatible.py --provider-label sjtu_zhiyuan1 --base-url https://models.sjtu.edu.cn/api/v1 --model deepseek-chat --api-key-env SJTU_ZHIYUAN1_API_KEY --catalog-only
& $py src\smoke_openai_compatible.py --provider-label sjtu_zhiyuan1 --base-url https://models.sjtu.edu.cn/api/v1 --model deepseek-reasoner --api-key-env SJTU_ZHIYUAN1_API_KEY --catalog-only
& $py src\smoke_openai_compatible.py --provider-label sjtu_zhiyuan1 --base-url https://models.sjtu.edu.cn/api/v1 --model minimax-m2.7 --api-key-env SJTU_ZHIYUAN1_API_KEY --catalog-only
& $py src\smoke_openai_compatible.py --provider-label sjtu_zhiyuan1 --base-url https://models.sjtu.edu.cn/api/v1 --model qwen3.6-27b --api-key-env SJTU_ZHIYUAN1_API_KEY --catalog-only

# TokenRhythm: set $env:TOKENRHYTHM_API_KEY immediately before these calls.
& $py src\smoke_openai_compatible.py --provider-label tokenrhythm --base-url https://tokenrhythm.studio/v1 --model deepseek-v4-flash --api-key-env TOKENRHYTHM_API_KEY --catalog-only
& $py src\smoke_openai_compatible.py --provider-label tokenrhythm --base-url https://tokenrhythm.studio/v1 --model glm-5.2 --api-key-env TOKENRHYTHM_API_KEY --catalog-only
& $py src\smoke_openai_compatible.py --provider-label tokenrhythm --base-url https://tokenrhythm.studio/v1 --model kimi-k2.7-code --api-key-env TOKENRHYTHM_API_KEY --catalog-only
& $py src\smoke_openai_compatible.py --provider-label tokenrhythm --base-url https://tokenrhythm.studio/v1 --model minimax-m2.7 --api-key-env TOKENRHYTHM_API_KEY --catalog-only
& $py src\smoke_openai_compatible.py --provider-label tokenrhythm --base-url https://tokenrhythm.studio/v1 --model qwen3.7-max --api-key-env TOKENRHYTHM_API_KEY --catalog-only
```

Only for a row whose catalog-only command returns `catalog_passed: true`, run
the corresponding exactly-three-completion smoke gate (remove
`--catalog-only`). The helper creates a sanitized file in
`data/raw/official_smoke/`; pass that exact file to the full run.

## 3. Build manifests before any catalog or smoke request

The manifests are frozen before any catalog or smoke request. Use the baseline
manifest only as a source of the fixed public record IDs and conditions. The
commands below do not contact an API. They have already been generated in this
workspace; rerun them only if you intentionally create a new dated protocol.

```powershell
$base = "protocol\sob_official_deepseek_v4_flash_manifest.json"
$protocol = "protocol/32_institutional_and_documented_endpoint_panel.md"

& $py src\build_endpoint_manifest.py --base-manifest $base --output protocol\sob_sjtu_deepseek_chat_manifest.json --model-alias deepseek-chat --provider-label sjtu_zhiyuan1 --base-url https://models.sjtu.edu.cn/api/v1 --api-key-env SJTU_ZHIYUAN1_API_KEY --smoke-provider sjtu_zhiyuan1 --protocol $protocol --endpoint-provenance sjtu_zhiyuan1_institutional_endpoint --request-interval-seconds 6.1
& $py src\build_endpoint_manifest.py --base-manifest $base --output protocol\sob_sjtu_deepseek_reasoner_manifest.json --model-alias deepseek-reasoner --provider-label sjtu_zhiyuan1 --base-url https://models.sjtu.edu.cn/api/v1 --api-key-env SJTU_ZHIYUAN1_API_KEY --smoke-provider sjtu_zhiyuan1 --protocol $protocol --endpoint-provenance sjtu_zhiyuan1_institutional_endpoint --request-interval-seconds 6.1
& $py src\build_endpoint_manifest.py --base-manifest $base --output protocol\sob_sjtu_minimax_m27_manifest.json --model-alias minimax-m2.7 --provider-label sjtu_zhiyuan1 --base-url https://models.sjtu.edu.cn/api/v1 --api-key-env SJTU_ZHIYUAN1_API_KEY --smoke-provider sjtu_zhiyuan1 --protocol $protocol --endpoint-provenance sjtu_zhiyuan1_institutional_endpoint --request-interval-seconds 6.1
& $py src\build_endpoint_manifest.py --base-manifest $base --output protocol\sob_sjtu_qwen36_27b_manifest.json --model-alias qwen3.6-27b --provider-label sjtu_zhiyuan1 --base-url https://models.sjtu.edu.cn/api/v1 --api-key-env SJTU_ZHIYUAN1_API_KEY --smoke-provider sjtu_zhiyuan1 --protocol $protocol --endpoint-provenance sjtu_zhiyuan1_institutional_endpoint --request-interval-seconds 6.1

& $py src\build_endpoint_manifest.py --base-manifest $base --output protocol\sob_tokenrhythm_deepseek_v4_flash_manifest.json --model-alias deepseek-v4-flash --provider-label tokenrhythm --base-url https://tokenrhythm.studio/v1 --api-key-env TOKENRHYTHM_API_KEY --smoke-provider tokenrhythm --protocol $protocol --endpoint-provenance documented_aggregator_endpoint
& $py src\build_endpoint_manifest.py --base-manifest $base --output protocol\sob_tokenrhythm_glm52_manifest.json --model-alias glm-5.2 --provider-label tokenrhythm --base-url https://tokenrhythm.studio/v1 --api-key-env TOKENRHYTHM_API_KEY --smoke-provider tokenrhythm --protocol $protocol --endpoint-provenance documented_aggregator_endpoint
& $py src\build_endpoint_manifest.py --base-manifest $base --output protocol\sob_tokenrhythm_kimi_k27_code_manifest.json --model-alias kimi-k2.7-code --provider-label tokenrhythm --base-url https://tokenrhythm.studio/v1 --api-key-env TOKENRHYTHM_API_KEY --smoke-provider tokenrhythm --protocol $protocol --endpoint-provenance documented_aggregator_endpoint
& $py src\build_endpoint_manifest.py --base-manifest $base --output protocol\sob_tokenrhythm_minimax_m27_manifest.json --model-alias minimax-m2.7 --provider-label tokenrhythm --base-url https://tokenrhythm.studio/v1 --api-key-env TOKENRHYTHM_API_KEY --smoke-provider tokenrhythm --protocol $protocol --endpoint-provenance documented_aggregator_endpoint
& $py src\build_endpoint_manifest.py --base-manifest $base --output protocol\sob_tokenrhythm_qwen37_max_manifest.json --model-alias qwen3.7-max --provider-label tokenrhythm --base-url https://tokenrhythm.studio/v1 --api-key-env TOKENRHYTHM_API_KEY --smoke-provider tokenrhythm --protocol $protocol --endpoint-provenance documented_aggregator_endpoint
```

## 4. Full run command template

Do not start a full run until the smoke gate for that exact model is passed.
Replace `<smoke-file>` with the sanitized JSON filename printed by the helper.

```powershell
& $py src\run_sob_metamorphic.py --public-input data\processed\sob_decomposed_200_public.jsonl --manifest protocol\sob_sjtu_deepseek_chat_manifest.json --output results\api\sob_sjtu_deepseek_chat.jsonl --model-alias deepseek-chat --base-url https://models.sjtu.edu.cn/api/v1 --api-key-env SJTU_ZHIYUAN1_API_KEY --provider-label sjtu_zhiyuan1 --smoke-record data\raw\official_smoke\<smoke-file>.json --no-key-prompt
```

The same template applies to each other generated manifest/output. The SJTU
manifest's 6.1-second interval respects the reported ten-requests-per-minute
limit. Clear the process key after all desired runs:

```powershell
Remove-Item Env:SJTU_ZHIYUAN1_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:TOKENRHYTHM_API_KEY -ErrorAction SilentlyContinue
```

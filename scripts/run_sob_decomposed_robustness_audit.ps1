$ErrorActionPreference = "Stop"

$python = ".venv\Scripts\python.exe"
$qwenReport = "results\api\sob_official_qwen_plus_resource_full160_report.json"
$modeReport = "results\api\sob_official_qwen_plus_mode_interaction_100_report.json"

if (-not (Test-Path -LiteralPath $qwenReport)) {
    throw "Finish the frozen Qwen-Plus 160-record evaluation before this audit."
}
$qwen = Get-Content -Raw -Encoding UTF8 -LiteralPath $qwenReport | ConvertFrom-Json
if ($qwen.operational_gate -ne $true) {
    throw "The Qwen-Plus operational gate did not pass."
}
if (-not (Test-Path -LiteralPath $modeReport)) {
    throw "Finish the frozen Qwen-Plus JSON Mode interaction evaluation first."
}
$mode = Get-Content -Raw -Encoding UTF8 -LiteralPath $modeReport | ConvertFrom-Json
if ($mode.operational_gate -ne $true) {
    throw "The Qwen-Plus JSON Mode interaction operational gate did not pass."
}

& $python "src\analyze_sob_decomposed_robustness.py" `
    --public-input "data\processed\sob_decomposed_200_public.jsonl" `
    --gold-input "data\restricted\sob_decomposed_200_gold.jsonl" `
    --run "sonnet_gateway" `
        "protocol\sob_decomposed_sonnet5_manifest.json" `
        "results\api\sob_decomposed_sonnet5.jsonl" `
    --run "gpt_gateway" `
        "protocol\sob_decomposed_gpt55_manifest.json" `
        "results\api\sob_decomposed_gpt55.jsonl" `
    --run "deepseek_official" `
        "protocol\sob_official_deepseek_v4_flash_manifest.json" `
        "results\api\sob_official_deepseek_v4_flash.jsonl" `
    --run "qwen_plus_official" `
        "protocol\sob_official_qwen_plus_resource_full160_manifest.json" `
        "results\api\sob_official_qwen_plus_resource.jsonl" `
    --run "qwen_plus_json_mode" `
        "protocol\sob_official_qwen_plus_json_mode_100_manifest.json" `
        "results\api\sob_official_qwen_plus_json_mode_100.jsonl" `
    --json-output "results\api\sob_decomposed_robustness_audit.json" `
    --markdown-output "results\api\sob_decomposed_robustness_audit.md"
if ($LASTEXITCODE -ne 0) {
    throw "Decomposed robustness audit failed."
}

Get-Content -Raw -Encoding UTF8 -LiteralPath `
    "results\api\sob_decomposed_robustness_audit.md"

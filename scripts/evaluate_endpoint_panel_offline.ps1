[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = (Resolve-Path (Join-Path $projectRoot ".venv\Scripts\python.exe")).Path

$specs = @(
    [pscustomobject]@{
        Label = "sjtu_deepseek_chat_recovery"
        Manifest = "protocol\sob_sjtu_deepseek_chat_manifest.json"
        Predictions = "results\api\sob_sjtu_deepseek_chat.jsonl"
        Json = "results\api\sob_sjtu_deepseek_chat_report.json"
        Markdown = "results\api\sob_sjtu_deepseek_chat_report.md"
    },
    [pscustomobject]@{
        Label = "sjtu_deepseek_reasoner"
        Manifest = "protocol\sob_sjtu_deepseek_reasoner_manifest.json"
        Predictions = "results\api\sob_sjtu_deepseek_reasoner.jsonl"
        Json = "results\api\sob_sjtu_deepseek_reasoner_report.json"
        Markdown = "results\api\sob_sjtu_deepseek_reasoner_report.md"
    },
    [pscustomobject]@{
        Label = "tokenrhythm_deepseek_v4_flash"
        Manifest = "protocol\sob_tokenrhythm_deepseek_v4_flash_manifest.json"
        Predictions = "results\api\sob_tokenrhythm_deepseek_v4_flash.jsonl"
        Json = "results\api\sob_tokenrhythm_deepseek_v4_flash_report.json"
        Markdown = "results\api\sob_tokenrhythm_deepseek_v4_flash_report.md"
    }
)

Push-Location $projectRoot
try {
    & $python src\audit_endpoint_panel_runs.py
    if ($LASTEXITCODE -ne 0) {
        throw "Endpoint logs are incomplete. Finish only the missing request keys before inference."
    }

    foreach ($spec in $specs) {
        & $python src\evaluate_sob_decomposed_confirmation.py `
            --public-input data\processed\sob_decomposed_200_public.jsonl `
            --gold-input data\restricted\sob_decomposed_200_gold.jsonl `
            --manifest $spec.Manifest `
            --predictions $spec.Predictions `
            --json-output $spec.Json `
            --markdown-output $spec.Markdown
        if ($LASTEXITCODE -ne 0) {
            throw "Frozen evaluation failed for $($spec.Label)."
        }
    }

    & $python src\summarize_endpoint_panel.py `
        --report $($specs[0].Label) $($specs[0].Json) `
        --report $($specs[1].Label) $($specs[1].Json) `
        --report $($specs[2].Label) $($specs[2].Json) `
        --json-output results\api\sob_endpoint_panel_summary.json `
        --markdown-output results\api\sob_endpoint_panel_summary.md
    if ($LASTEXITCODE -ne 0) {
        throw "Endpoint panel summary failed."
    }

    Get-Content -Raw -Encoding UTF8 results\api\sob_endpoint_panel_summary.md
}
finally {
    Pop-Location
}

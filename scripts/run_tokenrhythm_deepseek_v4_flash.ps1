[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

if (-not $env:TOKENRHYTHM_API_KEY) {
    throw "TOKENRHYTHM_API_KEY is not set in this PowerShell process. Set it with the hidden SecureString prompt first."
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = (Resolve-Path (Join-Path $projectRoot ".venv\Scripts\python.exe")).Path
$smokeDir = Join-Path $projectRoot "data\raw\official_smoke"
$model = "deepseek-v4-flash"
$provider = "tokenrhythm"
$baseUrl = "https://tokenrhythm.studio/v1"
$manifest = "protocol\sob_tokenrhythm_deepseek_v4_flash_manifest.json"
$output = "results\api\sob_tokenrhythm_deepseek_v4_flash.jsonl"

Push-Location $projectRoot
try {
    Write-Host "[1/2] TokenRhythm catalog + three-call smoke gate" -ForegroundColor Cyan
    & $python src\smoke_openai_compatible.py `
        --provider-label $provider `
        --base-url $baseUrl `
        --model $model `
        --api-key-env TOKENRHYTHM_API_KEY `
        --repeats 3 `
        --request-interval 1.0
    if ($LASTEXITCODE -ne 0) {
        throw "TokenRhythm smoke gate command failed; no 3,000-call run was started."
    }

    $pattern = "tokenrhythm_$($model)_*.json"
    $smokePath = Get-ChildItem $smokeDir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like $pattern } |
        Sort-Object LastWriteTime |
        Select-Object -Last 1
    if (-not $smokePath) {
        throw "No model-specific TokenRhythm smoke record was found."
    }
    $smoke = Get-Content $smokePath.FullName -Raw | ConvertFrom-Json
    if ($smoke.gate.gate_passed -ne $true) {
        throw "TokenRhythm smoke gate did not pass; no 3,000-call run was started."
    }
    Write-Host "Gate passed: $($smokePath.Name)" -ForegroundColor Green

    Write-Host "[2/2] Starting/resuming the frozen 3,000-request run" -ForegroundColor Cyan
    Write-Host "Rerunning this same script resumes from successful request keys in $output." -ForegroundColor DarkYellow
    & $python src\run_sob_metamorphic.py `
        --public-input data\processed\sob_decomposed_200_public.jsonl `
        --manifest $manifest `
        --output $output `
        --model-alias $model `
        --base-url $baseUrl `
        --api-key-env TOKENRHYTHM_API_KEY `
        --provider-label $provider `
        --smoke-record $smokePath.FullName `
        --no-key-prompt
    if ($LASTEXITCODE -ne 0) {
        throw "TokenRhythm full run paused; rerun this same script after checking service availability."
    }
}
finally {
    Pop-Location
}

Write-Host "TokenRhythm deepseek-v4-flash run completed." -ForegroundColor Green

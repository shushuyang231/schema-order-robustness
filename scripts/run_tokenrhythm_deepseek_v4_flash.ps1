[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$createdProcessKey = $false
if (-not $env:TOKENRHYTHM_API_KEY) {
    $secret = Read-Host "Paste TokenRhythm API key" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
    try {
        $env:TOKENRHYTHM_API_KEY =
            [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        $createdProcessKey = $true
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
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
    $pattern = "tokenrhythm_$($model)_*.json"
    $priorSmokeFiles = @(Get-ChildItem $smokeDir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like $pattern } |
        Sort-Object LastWriteTime)
    $smokePath = $null
    foreach ($candidate in ($priorSmokeFiles | Sort-Object LastWriteTime -Descending)) {
        $candidateRecord = Get-Content $candidate.FullName -Encoding UTF8 -Raw | ConvertFrom-Json
        if ($candidateRecord.gate.gate_passed -eq $true) {
            $smokePath = $candidate
            break
        }
    }

    if (-not $smokePath -and $priorSmokeFiles.Count -gt 0) {
        throw "A prior TokenRhythm completion gate exists and failed. The frozen rule forbids repeating gates until one passes; no 3,000-call run was started."
    }
    if (-not $smokePath) {
        Write-Host "[1/2] First and only TokenRhythm catalog + three-call smoke gate" -ForegroundColor Cyan
        & $python src\smoke_openai_compatible.py `
            --provider-label $provider `
            --base-url $baseUrl `
            --model $model `
            --api-key-env TOKENRHYTHM_API_KEY `
            --repeats 3 `
            --request-interval 1.0
        if ($LASTEXITCODE -ne 0) {
            throw "TokenRhythm smoke gate command failed; no 3,000-call run was started and the failed gate is retained."
        }
        $smokePath = Get-ChildItem $smokeDir -File |
            Where-Object { $_.Name -like $pattern } |
            Sort-Object LastWriteTime |
            Select-Object -Last 1
        $smoke = Get-Content $smokePath.FullName -Encoding UTF8 -Raw | ConvertFrom-Json
        if ($smoke.gate.gate_passed -ne $true) {
            throw "TokenRhythm smoke gate did not pass; no 3,000-call run was started."
        }
    }
    else {
        Write-Host "[1/2] Reusing the previously passed TokenRhythm smoke record; no new gate calls." -ForegroundColor Cyan
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
    if ($createdProcessKey) {
        Remove-Item Env:TOKENRHYTHM_API_KEY -ErrorAction SilentlyContinue
    }
}

Write-Host "TokenRhythm deepseek-v4-flash run completed." -ForegroundColor Green

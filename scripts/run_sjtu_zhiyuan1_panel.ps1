[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

if (-not $env:SJTU_ZHIYUAN1_API_KEY) {
    throw "SJTU_ZHIYUAN1_API_KEY is not set in this PowerShell process. Set it with the hidden SecureString prompt first."
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = (Resolve-Path (Join-Path $projectRoot ".venv\Scripts\python.exe")).Path
$smokeDir = Join-Path $projectRoot "data\raw\official_smoke"

$specs = @(
    [pscustomobject]@{
        Model = "deepseek-chat"
        Manifest = "protocol\sob_sjtu_deepseek_chat_manifest.json"
        Output = "results\api\sob_sjtu_deepseek_chat.jsonl"
    },
    [pscustomobject]@{
        Model = "deepseek-reasoner"
        Manifest = "protocol\sob_sjtu_deepseek_reasoner_manifest.json"
        Output = "results\api\sob_sjtu_deepseek_reasoner.jsonl"
    },
    [pscustomobject]@{
        Model = "minimax-m2.7"
        Manifest = "protocol\sob_sjtu_minimax_m27_manifest.json"
        Output = "results\api\sob_sjtu_minimax_m27.jsonl"
    },
    [pscustomobject]@{
        Model = "qwen3.6-27b"
        Manifest = "protocol\sob_sjtu_qwen36_27b_manifest.json"
        Output = "results\api\sob_sjtu_qwen36_27b.jsonl"
    }
)

$smokeFiles = @{}
$passed = New-Object System.Collections.Generic.List[object]
$completed = New-Object System.Collections.Generic.List[object]
$failed = New-Object System.Collections.Generic.List[object]

Push-Location $projectRoot
try {
    Write-Host "[1/2] Three-call smoke gates (6.1 s interval; no full experiment yet)" -ForegroundColor Cyan
    foreach ($spec in $specs) {
        Write-Host "  Smoke: $($spec.Model)" -ForegroundColor Yellow
        & $python src\smoke_openai_compatible.py `
            --provider-label sjtu_zhiyuan1 `
            --base-url https://models.sjtu.edu.cn/api/v1 `
            --model $spec.Model `
            --api-key-env SJTU_ZHIYUAN1_API_KEY `
            --repeats 3 `
            --request-interval 6.1
        $smokeExit = $LASTEXITCODE
        $pattern = "sjtu_zhiyuan1_$($spec.Model)_*.json"
        $smokePath = Get-ChildItem $smokeDir -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like $pattern } |
            Sort-Object LastWriteTime |
            Select-Object -Last 1
        if ($smokeExit -ne 0 -or -not $smokePath) {
            Write-Warning "Smoke gate did not complete for $($spec.Model); this model is retained as operationally failed."
            continue
        }
        $smoke = Get-Content $smokePath.FullName -Raw | ConvertFrom-Json
        if ($smoke.gate.gate_passed -ne $true) {
            Write-Warning "Smoke gate failed for $($spec.Model); no full calls will be sent to this model."
            continue
        }
        $smokeFiles[$spec.Model] = $smokePath.FullName
        $passed.Add($spec)
        Write-Host "  Gate passed: $($spec.Model) -> $($smokePath.Name)" -ForegroundColor Green
    }

    if ($passed.Count -eq 0) {
        throw "No SJTU model passed the exact three-call smoke gate; no 3,000-call run was started."
    }

    Write-Host "[2/2] Starting $($passed.Count) fixed 3,000-request model run(s)." -ForegroundColor Cyan
    Write-Host "The frozen 6.1-second interval means roughly five hours per model; rerunning resumes from existing successful request keys." -ForegroundColor DarkYellow
    foreach ($spec in $passed) {
        Write-Host "  Full run: $($spec.Model)" -ForegroundColor Yellow
        & $python src\run_sob_metamorphic.py `
            --public-input data\processed\sob_decomposed_200_public.jsonl `
            --manifest $spec.Manifest `
            --output $spec.Output `
            --model-alias $spec.Model `
            --base-url https://models.sjtu.edu.cn/api/v1 `
            --api-key-env SJTU_ZHIYUAN1_API_KEY `
            --provider-label sjtu_zhiyuan1 `
            --smoke-record $smokeFiles[$spec.Model] `
            --no-key-prompt
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Full run paused for $($spec.Model). Its successful request keys remain resumable; continuing to the next predeclared model."
            $failed.Add($spec)
            continue
        }
        $completed.Add($spec)
    }
}
finally {
    Pop-Location
}

if ($failed.Count -gt 0) {
    Write-Warning "Some fixed models paused and can be resumed with the same script: $((@($failed | ForEach-Object Model) -join ', ')). Completed: $((@($completed | ForEach-Object Model) -join ', '))."
    exit 1
}
Write-Host "All selected SJTU runs completed." -ForegroundColor Green

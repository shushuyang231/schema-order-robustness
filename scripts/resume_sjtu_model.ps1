[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("deepseek-chat", "deepseek-reasoner")]
    [string]$Model
)

$ErrorActionPreference = "Stop"
$createdProcessKey = $false

if (-not $env:SJTU_ZHIYUAN1_API_KEY) {
    $secret = Read-Host "Paste SJTU API key" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
    try {
        $env:SJTU_ZHIYUAN1_API_KEY =
            [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        $createdProcessKey = $true
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

$specs = @{
    "deepseek-chat" = [pscustomobject]@{
        Manifest = "protocol\sob_sjtu_deepseek_chat_manifest.json"
        Output = "results\api\sob_sjtu_deepseek_chat.jsonl"
        Smoke = "data\raw\official_smoke\sjtu_zhiyuan1_deepseek-chat_20260810T155406197510Z.json"
    }
    "deepseek-reasoner" = [pscustomobject]@{
        Manifest = "protocol\sob_sjtu_deepseek_reasoner_manifest.json"
        Output = "results\api\sob_sjtu_deepseek_reasoner.jsonl"
        Smoke = "data\raw\official_smoke\sjtu_zhiyuan1_deepseek-reasoner_20260810T062235728658Z.json"
    }
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = (Resolve-Path (Join-Path $projectRoot ".venv\Scripts\python.exe")).Path
$spec = $specs[$Model]

Push-Location $projectRoot
try {
    if (-not (Test-Path $spec.Smoke)) {
        throw "The frozen passed smoke record is missing: $($spec.Smoke)"
    }
    Write-Host "Resuming $Model from successful request keys in $($spec.Output)." -ForegroundColor Cyan
    Write-Host "No new catalog or smoke requests will be sent." -ForegroundColor DarkYellow
    & $python src\run_sob_metamorphic.py `
        --public-input data\processed\sob_decomposed_200_public.jsonl `
        --manifest $spec.Manifest `
        --output $spec.Output `
        --model-alias $Model `
        --base-url https://models.sjtu.edu.cn/api/v1 `
        --api-key-env SJTU_ZHIYUAN1_API_KEY `
        --provider-label sjtu_zhiyuan1 `
        --smoke-record $spec.Smoke `
        --no-key-prompt
    if ($LASTEXITCODE -ne 0) {
        throw "$Model paused after endpoint errors. Successful request keys remain resumable with this same one-line command."
    }
}
finally {
    Pop-Location
    if ($createdProcessKey) {
        Remove-Item Env:SJTU_ZHIYUAN1_API_KEY -ErrorAction SilentlyContinue
    }
}

Write-Host "$Model completed." -ForegroundColor Green

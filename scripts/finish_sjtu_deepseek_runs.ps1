[CmdletBinding()]
param()

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

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Push-Location $projectRoot
try {
    Write-Host "[1/2] Completing only missing deepseek-chat request keys" -ForegroundColor Cyan
    & "$PSScriptRoot\resume_sjtu_model.ps1" -Model deepseek-chat
    if ($LASTEXITCODE -ne 0) {
        throw "deepseek-chat remains incomplete; rerun this same one-line command after service recovery."
    }

    Write-Host "[2/2] Completing only missing deepseek-reasoner request keys" -ForegroundColor Cyan
    & "$PSScriptRoot\resume_sjtu_model.ps1" -Model deepseek-reasoner
    if ($LASTEXITCODE -ne 0) {
        throw "deepseek-reasoner remains incomplete; rerun this same one-line command after service recovery."
    }
}
finally {
    Pop-Location
    if ($createdProcessKey) {
        Remove-Item Env:SJTU_ZHIYUAN1_API_KEY -ErrorAction SilentlyContinue
    }
}

Write-Host "Both SJTU DeepSeek logs now have complete successful request-key coverage." -ForegroundColor Green

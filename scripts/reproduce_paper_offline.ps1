param(
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not $Python) {
    $venvPython = Join-Path $root ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $Python = $venvPython
    } else {
        $Python = (Get-Command python -ErrorAction Stop).Source
    }
}

Write-Host "[1/5] Compile Python sources"
& $Python -m compileall -q src tests
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed." }

Write-Host "[2/5] Run unit tests"
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed." }

Write-Host "[3/5] Rebuild paper tables and figures from frozen reports"
& $Python src\build_paper_artifacts.py
if ($LASTEXITCODE -ne 0) { throw "Paper artifact build failed." }

Write-Host "[4/5] Audit manuscript claims and citations"
& $Python src\audit_paper_draft.py
if ($LASTEXITCODE -ne 0) { throw "Manuscript audit failed." }

Write-Host "[5/5] Build and verify the anonymous artifact ZIP"
& $Python src\build_anonymous_artifact.py
if ($LASTEXITCODE -ne 0) { throw "Anonymous artifact build failed." }

Write-Host "OFFLINE_REPRODUCTION_PASS"

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

Write-Host "[1/7] Compile Python sources"
& $Python -m compileall -q src tests
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed." }

Write-Host "[2/7] Run unit tests"
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed." }

Write-Host "[3/7] Rebuild paper tables and figures from frozen reports"
& $Python src\build_paper_artifacts.py
if ($LASTEXITCODE -ne 0) { throw "Paper artifact build failed." }

Write-Host "[4/7] Audit manuscript claims and citations"
& $Python src\audit_paper_draft.py
if ($LASTEXITCODE -ne 0) { throw "Manuscript audit failed." }

Write-Host "[5/7] Build the flat EMSE LaTeX source package"
& $Python src\build_emse_submission.py
if ($LASTEXITCODE -ne 0) { throw "EMSE source build failed." }

Write-Host "[6/7] Build the EMSE review PDF"
& $Python src\build_emse_review_pdf.py
if ($LASTEXITCODE -ne 0) { throw "EMSE PDF build failed." }

Write-Host "[7/7] Build and verify EMSE Online Resource 1"
& $Python src\build_emse_artifact.py
if ($LASTEXITCODE -ne 0) { throw "EMSE artifact build failed." }

Write-Host "OFFLINE_REPRODUCTION_PASS"

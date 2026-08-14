[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$requirements = "backend\requirements-dev.txt"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $FilePath $($Arguments -join ' ')"
    }
}

Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath $venvPython)) {
        Invoke-Checked -FilePath "py" -Arguments @("-3.11", "-m", "venv", ".venv")
    }

    Invoke-Checked -FilePath $venvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
    Invoke-Checked -FilePath $venvPython -Arguments @("-m", "pip", "install", "-r", $requirements)
    # Use the native shim explicitly. npm.ps1 reconstructs its invocation from
    # source text and mis-parses argument splatting inside a PowerShell function.
    Invoke-Checked -FilePath "npm.cmd" -Arguments @("ci")
    Invoke-Checked -FilePath "npm.cmd" -Arguments @("--prefix", "frontend", "ci")
    Invoke-Checked -FilePath "npm.cmd" -Arguments @("run", "build")

    if (-not (Test-Path -LiteralPath ".env")) {
        Copy-Item -LiteralPath ".env.example" -Destination ".env"
        Write-Host "Created offline-first .env defaults." -ForegroundColor Yellow
    }

    Write-Host "Core dependencies are ready." -ForegroundColor Green
} finally {
    Pop-Location
}

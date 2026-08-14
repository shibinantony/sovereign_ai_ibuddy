[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PythonArgs
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$venvFastApi = Join-Path $projectRoot ".venv\Lib\site-packages\fastapi\__init__.py"

if (-not (Test-Path -LiteralPath $venvPython) -or
    -not (Test-Path -LiteralPath $venvFastApi)) {
    throw "iBuddy's Python environment is not ready. Run 'npm run setup' first."
}

& $venvPython @PythonArgs
exit $LASTEXITCODE

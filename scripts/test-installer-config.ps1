[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$examplePath = Join-Path $projectRoot ".env.example"
. (Join-Path $PSScriptRoot "installer-config.ps1")

function Assert-EnvLine {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string[]]$Lines,
        [Parameter(Mandatory = $true)]
        [string]$Expected
    )

    if (-not ($Lines -ccontains $Expected)) {
        throw "Expected environment line was not found: $Expected"
    }
}

$tempParent = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$tempRoot = Join-Path $tempParent ("ibuddy-installer-test-" + [Guid]::NewGuid().ToString("N"))
$resolvedTempRoot = [System.IO.Path]::GetFullPath($tempRoot)
$tempPrefix = $tempParent.TrimEnd('\') + '\'
if (-not $resolvedTempRoot.StartsWith($tempPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $resolvedTempRoot) -notmatch '^ibuddy-installer-test-[a-f0-9]{32}$') {
    throw "Refusing to use an unexpected installer test path: $resolvedTempRoot"
}

New-Item -ItemType Directory -Path $resolvedTempRoot | Out-Null
try {
    $existingEnvironment = Join-Path $resolvedTempRoot "existing.env"
    $runtimePath = "C:\iBuddy Device\runtime\llama.cpp\llama-server.exe"
    $modelPath = "C:\iBuddy Device\models\Qwen3.gguf"
    $databasePath = "C:\iBuddy Device\data\ibuddy.db"
    $existingLines = @(
        "# Preserve comments and every user-controlled value."
        "IBUDDY_MODEL_BACKEND=hosted"
        "IBUDDY_OFFLINE=true"
        "LLAMA_CPP_SERVER_PATH=C:\old\server.exe"
        "LLAMA_CPP_MODEL_PATH=C:\old\model.gguf"
        "LLAMA_CPP_HOST=localhost"
        "LLAMA_CPP_PORT=19090"
        "LLAMA_CPP_CONTEXT_SIZE=4096"
        "LLAMA_CPP_THREADS=12"
        "LLAMA_CPP_GPU_LAYERS=7"
        "LLAMA_CPP_STARTUP_TIMEOUT_SECONDS=240"
        "LLAMA_CPP_ENABLE_THINKING=true"
        "IBUDDY_DATABASE_PATH=C:\old\history.db"
        "SEARCH_PROVIDER=brave"
        "SEARCH_RESULT_COUNT=9"
        "SEARCH_TIMEOUT_SECONDS=17"
        "HF_TOKEN=preserve-this-value"
        "CUSTOM_SETTING=value=with=equals"
    )
    [System.IO.File]::WriteAllLines(
        $existingEnvironment,
        $existingLines,
        (New-Object System.Text.UTF8Encoding($false))
    )

    Set-InstallerEnvironmentPaths `
        -Path $existingEnvironment `
        -ExamplePath $examplePath `
        -RuntimePath $runtimePath `
        -ModelPath $modelPath `
        -DatabasePath $databasePath

    $expectedLines = @(
        "# Preserve comments and every user-controlled value."
        "IBUDDY_MODEL_BACKEND=hosted"
        "IBUDDY_OFFLINE=true"
        "LLAMA_CPP_SERVER_PATH=$runtimePath"
        "LLAMA_CPP_MODEL_PATH=$modelPath"
        "LLAMA_CPP_HOST=localhost"
        "LLAMA_CPP_PORT=19090"
        "LLAMA_CPP_CONTEXT_SIZE=4096"
        "LLAMA_CPP_THREADS=12"
        "LLAMA_CPP_GPU_LAYERS=7"
        "LLAMA_CPP_STARTUP_TIMEOUT_SECONDS=240"
        "LLAMA_CPP_ENABLE_THINKING=true"
        "IBUDDY_DATABASE_PATH=$databasePath"
        "SEARCH_PROVIDER=brave"
        "SEARCH_RESULT_COUNT=9"
        "SEARCH_TIMEOUT_SECONDS=17"
        "HF_TOKEN=preserve-this-value"
        "CUSTOM_SETTING=value=with=equals"
    )
    $actualLines = @(Get-Content -LiteralPath $existingEnvironment)
    if (($actualLines -join "`n") -cne ($expectedLines -join "`n")) {
        throw "Installer path updates changed user-controlled environment content."
    }

    $newEnvironment = Join-Path $resolvedTempRoot "new.env"
    Set-InstallerEnvironmentPaths `
        -Path $newEnvironment `
        -ExamplePath $examplePath `
        -RuntimePath $runtimePath `
        -ModelPath $modelPath `
        -DatabasePath $databasePath
    $newLines = @(Get-Content -LiteralPath $newEnvironment)
    Assert-EnvLine -Lines $newLines -Expected "IBUDDY_MODEL_BACKEND=llama_cpp"
    Assert-EnvLine -Lines $newLines -Expected "IBUDDY_OFFLINE=true"
    Assert-EnvLine -Lines $newLines -Expected "SEARCH_PROVIDER=auto"
    Assert-EnvLine -Lines $newLines -Expected "LLAMA_CPP_SERVER_PATH=$runtimePath"
    Assert-EnvLine -Lines $newLines -Expected "LLAMA_CPP_MODEL_PATH=$modelPath"
    Assert-EnvLine -Lines $newLines -Expected "IBUDDY_DATABASE_PATH=$databasePath"

    $relativePathWasRejected = $false
    try {
        Set-InstallerEnvironmentPaths `
            -Path $existingEnvironment `
            -ExamplePath $examplePath `
            -RuntimePath "runtime\llama-server.exe" `
            -ModelPath $modelPath `
            -DatabasePath $databasePath
    } catch {
        $relativePathWasRejected = $_.Exception.Message -like "Installer-owned environment paths must be absolute:*"
    }
    if (-not $relativePathWasRejected) {
        throw "A relative installer-owned environment path was not rejected."
    }

    Write-Host "Installer configuration preservation checks passed." -ForegroundColor Green
} finally {
    if (Test-Path -LiteralPath $resolvedTempRoot) {
        Remove-Item -LiteralPath $resolvedTempRoot -Recurse -Force
    }
}

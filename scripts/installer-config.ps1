Set-StrictMode -Version 2.0

function Set-InstallerEnvironmentPaths {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$ExamplePath,
        [Parameter(Mandatory = $true)]
        [string]$RuntimePath,
        [Parameter(Mandatory = $true)]
        [string]$ModelPath,
        [Parameter(Mandatory = $true)]
        [string]$DatabasePath
    )

    # These are the only values owned by the installer. Policy choices such as
    # offline mode, backend selection, search behavior, and performance tuning
    # must survive verification and repair runs unchanged.
    $values = [ordered]@{
        LLAMA_CPP_SERVER_PATH = $RuntimePath
        LLAMA_CPP_MODEL_PATH = $ModelPath
        IBUDDY_DATABASE_PATH = $DatabasePath
    }
    foreach ($value in $values.Values) {
        if (-not [System.IO.Path]::IsPathRooted([string]$value)) {
            throw "Installer-owned environment paths must be absolute: $value"
        }
    }

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        if (-not (Test-Path -LiteralPath $ExamplePath -PathType Leaf)) {
            throw "The environment template was not found: $ExamplePath"
        }
        Copy-Item -LiteralPath $ExamplePath -Destination $Path
    }
    $lines = New-Object 'System.Collections.Generic.List[string]'
    Get-Content -LiteralPath $Path | ForEach-Object { [void]$lines.Add([string]$_) }

    foreach ($key in $values.Keys) {
        $replacement = "$key=$($values[$key])"
        $pattern = '^\s*' + [Regex]::Escape([string]$key) + '\s*='
        $found = $false
        for ($index = 0; $index -lt $lines.Count; $index++) {
            if ($lines[$index] -match $pattern) {
                $lines[$index] = $replacement
                $found = $true
            }
        }
        if (-not $found) {
            [void]$lines.Add($replacement)
        }
    }

    [System.IO.File]::WriteAllLines(
        $Path,
        $lines,
        (New-Object System.Text.UTF8Encoding($false))
    )
}

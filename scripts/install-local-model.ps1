[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$coreRequirements = Join-Path $projectRoot "backend\requirements.txt"
$environmentPath = Join-Path $projectRoot ".env"
$environmentExamplePath = Join-Path $projectRoot ".env.example"
. (Join-Path $PSScriptRoot "installer-config.ps1")

$modelRepo = "Qwen/Qwen3-8B-GGUF"
$modelFileName = "Qwen3-8B-Q5_K_M.gguf"
# Pin the official revision whose Hugging Face file metadata publishes the hash below.
$modelRevision = "4f02e7c52b572082828edf5058a87e2e7dc3e4d5"
$modelSha256 = "068bae163faa96ad48032daf4e071a6a28fe67d8dcc95367609c2ff165e52738"
$llamaReleaseTag = "b10408"
$llamaAssetName = "llama-b10408-bin-win-cpu-x64.zip"
$llamaArchiveSha256 = "63790dfd3c754ef8838606926f1952d9a4f5d74b5e6d5925da1868f56d5d9049"
$llamaReleaseApi = "https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/$llamaReleaseTag"
$llamaAssetUrl = "https://github.com/ggml-org/llama.cpp/releases/download/$llamaReleaseTag/$llamaAssetName"

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

function Test-Sha256 {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Expected
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }

    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    return $actual -eq $Expected.ToLowerInvariant()
}

function Remove-InstallItem {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [switch]$Recurse
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $resolved = [System.IO.Path]::GetFullPath($Path)
    $rootPrefix = $script:installRoot.TrimEnd('\') + '\'
    if (-not $resolved.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the iBuddy install root: $resolved"
    }

    if ($Recurse) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    } else {
        Remove-Item -LiteralPath $resolved -Force
    }
}

function Ensure-CoreEnvironment {
    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        Write-Host "Creating the Python 3.11 virtual environment..." -ForegroundColor Cyan
        Invoke-Checked -FilePath "py" -Arguments @("-3.11", "-m", "venv", (Join-Path $projectRoot ".venv"))
    }

    Write-Host "Ensuring iBuddy core Python dependencies..." -ForegroundColor Cyan
    Invoke-Checked -FilePath $venvPython -Arguments @("-m", "pip", "install", "-r", $coreRequirements)
    Invoke-Checked -FilePath $venvPython -Arguments @(
        "-c",
        "import fastapi, httpx, huggingface_hub, uvicorn"
    )
}

function Test-InstalledLlamaRuntime {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RuntimeDirectory
    )

    $executable = Join-Path $RuntimeDirectory "llama-server.exe"
    $manifestPath = Join-Path $RuntimeDirectory ".ibuddy-install.json"
    if (-not (Test-Path -LiteralPath $executable -PathType Leaf) -or
        -not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        return $false
    }

    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        if ([int]$manifest.schemaVersion -ne 2) {
            return $false
        }
        if ([string]$manifest.releaseTag -ne $llamaReleaseTag -or
            [string]$manifest.assetName -ne $llamaAssetName -or
            [string]$manifest.archiveSha256 -ne $llamaArchiveSha256 -or
            -not [bool]$manifest.githubDigestVerified) {
            return $false
        }
        $expectedExecutableHash = [string]$manifest.executableSha256
        if ($expectedExecutableHash -notmatch '^[a-fA-F0-9]{64}$') {
            return $false
        }

        if (-not (Test-Sha256 -Path $executable -Expected $expectedExecutableHash)) {
            return $false
        }

        $runtimeFiles = @($manifest.runtimeFiles)
        if ($runtimeFiles.Count -eq 0) {
            return $false
        }

        $runtimePrefix = [System.IO.Path]::GetFullPath($RuntimeDirectory).TrimEnd('\') + '\'
        $serverWasRecorded = $false
        foreach ($entry in $runtimeFiles) {
            $relativePath = [string]$entry.path
            $expectedHash = [string]$entry.sha256
            if ([string]::IsNullOrWhiteSpace($relativePath) -or
                [System.IO.Path]::IsPathRooted($relativePath) -or
                $expectedHash -notmatch '^[a-fA-F0-9]{64}$') {
                return $false
            }

            $installedPath = [System.IO.Path]::GetFullPath((Join-Path $RuntimeDirectory $relativePath))
            if (-not $installedPath.StartsWith($runtimePrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
                -not (Test-Path -LiteralPath $installedPath -PathType Leaf)) {
                return $false
            }

            if ((Get-Item -LiteralPath $installedPath).Length -ne [long]$entry.length -or
                -not (Test-Sha256 -Path $installedPath -Expected $expectedHash)) {
                return $false
            }
            if ($relativePath.Replace('/', '\') -eq "llama-server.exe") {
                $serverWasRecorded = $true
            }
        }

        return $serverWasRecorded
    } catch {
        Write-Warning "The existing llama.cpp manifest could not be validated: $($_.Exception.Message)"
        return $false
    }
}

function Install-LlamaRuntime {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RuntimeDirectory
    )

    if (Test-InstalledLlamaRuntime -RuntimeDirectory $RuntimeDirectory) {
        Write-Host "Verified existing llama.cpp runtime; download skipped." -ForegroundColor Green
        return
    }

    $runtimeParent = Split-Path -Parent $RuntimeDirectory
    if (-not (Test-Path -LiteralPath $runtimeParent -PathType Container)) {
        New-Item -ItemType Directory -Path $runtimeParent -Force | Out-Null
    }

    Write-Host "Verifying pinned llama.cpp $llamaReleaseTag release metadata..." -ForegroundColor Cyan
    $headers = @{
        Accept = "application/vnd.github+json"
        "User-Agent" = "iBuddy-local-model-installer"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    $release = Invoke-RestMethod -Uri $llamaReleaseApi -Headers $headers -UseBasicParsing
    if ([string]$release.tag_name -ne $llamaReleaseTag) {
        throw "Expected llama.cpp release $llamaReleaseTag; GitHub returned '$($release.tag_name)'."
    }

    $matchingAssets = @(
        $release.assets | Where-Object {
            [string]$_.name -eq $llamaAssetName
        }
    )
    if ($matchingAssets.Count -ne 1) {
        throw "Expected exactly one '$llamaAssetName' asset in release $llamaReleaseTag; found $($matchingAssets.Count)."
    }

    $asset = $matchingAssets[0]
    if ([string]$asset.browser_download_url -ne $llamaAssetUrl) {
        throw "GitHub returned an unexpected download URL for the pinned llama.cpp asset."
    }

    $digest = [string]$asset.digest
    if ($digest -notmatch '^sha256:([a-fA-F0-9]{64})$') {
        throw "GitHub did not supply a valid SHA256 digest for the pinned llama.cpp asset."
    }
    $publishedArchiveHash = $Matches[1].ToLowerInvariant()
    if ($publishedArchiveHash -ne $llamaArchiveSha256) {
        throw "The published llama.cpp digest does not match the installer pin. Expected $llamaArchiveSha256; received $publishedArchiveHash."
    }

    $operationId = [Guid]::NewGuid().ToString("N")
    $archivePath = Join-Path $script:installRoot ".llama-cpp-$operationId.zip"
    $extractDirectory = Join-Path $script:installRoot ".llama-cpp-extract-$operationId"
    $candidateDirectory = Join-Path $script:installRoot ".llama-cpp-candidate-$operationId"
    $backupDirectory = Join-Path $script:installRoot ".llama-cpp-backup-$operationId"

    try {
        Write-Host "Downloading pinned llama.cpp $llamaReleaseTag..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri $llamaAssetUrl -Headers $headers -UseBasicParsing -OutFile $archivePath
        if (-not (Test-Path -LiteralPath $archivePath -PathType Leaf) -or
            (Get-Item -LiteralPath $archivePath).Length -le 0) {
            throw "The llama.cpp archive download did not produce a non-empty file."
        }

        $archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($archiveHash -ne $llamaArchiveSha256) {
            throw "llama.cpp archive SHA256 mismatch. Expected $llamaArchiveSha256; received $archiveHash."
        }
        Write-Host "Verified the pinned llama.cpp SHA256 digest." -ForegroundColor Green

        New-Item -ItemType Directory -Path $extractDirectory -Force | Out-Null
        Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDirectory -Force
        $serverExecutables = @(Get-ChildItem -LiteralPath $extractDirectory -Filter "llama-server.exe" -File -Recurse)
        if ($serverExecutables.Count -ne 1) {
            throw "Expected one llama-server.exe in the archive; found $($serverExecutables.Count)."
        }

        $payloadDirectory = $serverExecutables[0].Directory.FullName
        Move-Item -LiteralPath $payloadDirectory -Destination $candidateDirectory
        $candidateExecutable = Join-Path $candidateDirectory "llama-server.exe"
        if (-not (Test-Path -LiteralPath $candidateExecutable -PathType Leaf)) {
            throw "The extracted llama.cpp candidate is missing llama-server.exe."
        }

        $executableHash = (Get-FileHash -LiteralPath $candidateExecutable -Algorithm SHA256).Hash.ToLowerInvariant()
        $runtimeFiles = @(
            Get-ChildItem -LiteralPath $candidateDirectory -File -Recurse |
                Sort-Object -Property FullName |
                ForEach-Object {
                    [ordered]@{
                        path = $_.FullName.Substring($candidateDirectory.Length + 1).Replace('\', '/')
                        length = $_.Length
                        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                    }
                }
        )
        $manifest = [ordered]@{
            schemaVersion = 2
            releaseTag = $llamaReleaseTag
            assetName = $llamaAssetName
            sourceUrl = $llamaAssetUrl
            archiveSha256 = $archiveHash
            githubDigestVerified = $true
            executableSha256 = $executableHash
            runtimeFiles = $runtimeFiles
            installedAtUtc = [DateTime]::UtcNow.ToString("o")
        }
        $manifestJson = $manifest | ConvertTo-Json -Depth 5
        [System.IO.File]::WriteAllText(
            (Join-Path $candidateDirectory ".ibuddy-install.json"),
            $manifestJson,
            (New-Object System.Text.UTF8Encoding($false))
        )

        if (Test-Path -LiteralPath $RuntimeDirectory) {
            Move-Item -LiteralPath $RuntimeDirectory -Destination $backupDirectory
        }

        try {
            Move-Item -LiteralPath $candidateDirectory -Destination $RuntimeDirectory
            if (-not (Test-InstalledLlamaRuntime -RuntimeDirectory $RuntimeDirectory)) {
                throw "The installed llama.cpp runtime failed post-install validation."
            }
        } catch {
            if (Test-Path -LiteralPath $RuntimeDirectory) {
                Remove-InstallItem -Path $RuntimeDirectory -Recurse
            }
            if (Test-Path -LiteralPath $backupDirectory) {
                Move-Item -LiteralPath $backupDirectory -Destination $RuntimeDirectory
            }
            throw
        }

        if (Test-Path -LiteralPath $backupDirectory) {
            Remove-InstallItem -Path $backupDirectory -Recurse
        }

        Write-Host "Installed and verified llama.cpp at $RuntimeDirectory" -ForegroundColor Green
    } finally {
        Remove-InstallItem -Path $archivePath
        Remove-InstallItem -Path $extractDirectory -Recurse
        Remove-InstallItem -Path $candidateDirectory -Recurse
    }
}

function Invoke-HuggingFaceModelDownload {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ModelsDirectory,
        [switch]$Force
    )

    $forceLiteral = if ($Force) { "True" } else { "False" }
    $pythonCode = "import os; from huggingface_hub import hf_hub_download; print(hf_hub_download(repo_id='$modelRepo', filename='$modelFileName', revision='$modelRevision', local_dir=os.environ['IBUDDY_MODEL_DOWNLOAD_DIR'], token=False, force_download=$forceLiteral))"
    $previousDownloadDirectory = $env:IBUDDY_MODEL_DOWNLOAD_DIR
    try {
        $env:IBUDDY_MODEL_DOWNLOAD_DIR = $ModelsDirectory
        Invoke-Checked -FilePath $venvPython -Arguments @("-c", $pythonCode)
    } finally {
        if ($null -eq $previousDownloadDirectory) {
            Remove-Item Env:IBUDDY_MODEL_DOWNLOAD_DIR -ErrorAction SilentlyContinue
        } else {
            $env:IBUDDY_MODEL_DOWNLOAD_DIR = $previousDownloadDirectory
        }
    }
}

function Install-Model {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ModelsDirectory
    )

    $modelPath = Join-Path $ModelsDirectory $modelFileName
    if (Test-Sha256 -Path $modelPath -Expected $modelSha256) {
        Write-Host "Verified existing Qwen3-8B Q5_K_M model; download skipped." -ForegroundColor Green
        return
    }

    Write-Host "Downloading the official Qwen3-8B Q5_K_M GGUF (about 5.85 GB)..." -ForegroundColor Cyan
    Write-Host "The Hugging Face cache supports validated reuse and resumable transfers." -ForegroundColor DarkGray
    Invoke-HuggingFaceModelDownload -ModelsDirectory $ModelsDirectory

    if (-not (Test-Sha256 -Path $modelPath -Expected $modelSha256)) {
        Write-Warning "The cached model did not match the official SHA256; forcing one clean re-download."
        Invoke-HuggingFaceModelDownload -ModelsDirectory $ModelsDirectory -Force
    }

    if (-not (Test-Sha256 -Path $modelPath -Expected $modelSha256)) {
        throw "Qwen3-8B model SHA256 validation failed after download. Expected $modelSha256."
    }

    Write-Host "Downloaded and SHA256-verified $modelPath" -ForegroundColor Green
}

if ($env:OS -ne "Windows_NT") {
    throw "This installer currently supports the official llama.cpp Windows CPU x64 package."
}

$nativeArchitecture = if (-not [string]::IsNullOrWhiteSpace($env:PROCESSOR_ARCHITEW6432)) {
    $env:PROCESSOR_ARCHITEW6432
} else {
    $env:PROCESSOR_ARCHITECTURE
}
if ($nativeArchitecture -ne "AMD64") {
    throw "This installer requires 64-bit x86 Windows (AMD64); detected $nativeArchitecture."
}

if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw "LOCALAPPDATA is unavailable. iBuddy needs a device-local application-data directory."
}

$localAppData = [System.IO.Path]::GetFullPath($env:LOCALAPPDATA)
if (-not [System.IO.Path]::IsPathRooted($localAppData)) {
    throw "LOCALAPPDATA must resolve to an absolute path."
}

$script:installRoot = [System.IO.Path]::GetFullPath((Join-Path $localAppData "iBuddy"))
$runtimeDirectory = Join-Path $script:installRoot "runtime\llama.cpp"
$modelsDirectory = Join-Path $script:installRoot "models"
$modelPath = Join-Path $modelsDirectory $modelFileName
$databasePath = Join-Path $script:installRoot "data\ibuddy.db"

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
New-Item -ItemType Directory -Path $script:installRoot -Force | Out-Null
New-Item -ItemType Directory -Path $modelsDirectory -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path -Parent $databasePath) -Force | Out-Null

Push-Location $projectRoot
try {
    Ensure-CoreEnvironment
    Install-LlamaRuntime -RuntimeDirectory $runtimeDirectory
    Install-Model -ModelsDirectory $modelsDirectory

    Set-InstallerEnvironmentPaths `
        -Path $environmentPath `
        -ExamplePath $environmentExamplePath `
        -RuntimePath (Join-Path $runtimeDirectory "llama-server.exe") `
        -ModelPath $modelPath `
        -DatabasePath $databasePath

    Write-Host "Local model installation is complete." -ForegroundColor Green
    Write-Host "Generation and chat history are device-local. Web search follows the policy preserved in .env." -ForegroundColor Green
    Write-Host "Run: npm run dev" -ForegroundColor Green
} finally {
    Pop-Location
}

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$downloadRoot = Join-Path $repoRoot 'tools\downloads'
$binaryRoot = Join-Path $repoRoot 'tools\llama.cpp\b10566\bin'
$modelRoot = Join-Path $repoRoot 'models\qwen2.5-1.5b-instruct-q4_k_m'

$mainArchive = Join-Path $downloadRoot 'llama-b10566-bin-win-cuda-12.4-x64.zip'
$cudaArchive = Join-Path $downloadRoot 'cudart-llama-bin-win-cuda-12.4-x64.zip'
$llamaExecutable = Join-Path $binaryRoot 'llama-completion.exe'
$modelPath = Join-Path $modelRoot 'qwen2.5-1.5b-instruct-q4_k_m.gguf'

$mainUrl = 'https://github.com/ggml-org/llama.cpp/releases/download/b10566/llama-b10566-bin-win-cuda-12.4-x64.zip'
$cudaUrl = 'https://github.com/ggml-org/llama.cpp/releases/download/b10566/cudart-llama-bin-win-cuda-12.4-x64.zip'
$mainSha256 = '6805bde00c16006cdcc757a132f7ba95d82b5f1e6ddba7e1d91f80c4e6930dcb'
$cudaSha256 = '8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6'
$executableSha256 = 'de3a1b707adb9d0b9241d93e1fe6547e108e978b64d350ae4c465ad5c6e5775f'
$modelSha256 = '6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e'
$modelRevision = '91cad51170dc346986eccefdc2dd33a9da36ead9'

function Assert-Sha256 {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Expected
    )

    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
    if ($actual -ne $Expected) {
        throw "SHA-256 mismatch for $Path. Expected $Expected, got $actual."
    }
    Write-Output "Verified SHA-256: $Path"
}

function Get-PinnedFile {
    param(
        [Parameter(Mandatory)][string]$Url,
        [Parameter(Mandatory)][string]$Destination,
        [Parameter(Mandatory)][string]$Sha256
    )

    if (-not (Test-Path -LiteralPath $Destination)) {
        Write-Output "Downloading: $Url"
        Invoke-WebRequest -Uri $Url -OutFile $Destination
    }
    Assert-Sha256 -Path $Destination -Expected $Sha256
}

New-Item -ItemType Directory -Force -Path $downloadRoot, $binaryRoot, $modelRoot | Out-Null

Get-PinnedFile -Url $mainUrl -Destination $mainArchive -Sha256 $mainSha256
Get-PinnedFile -Url $cudaUrl -Destination $cudaArchive -Sha256 $cudaSha256

if (-not (Test-Path -LiteralPath $llamaExecutable)) {
    Expand-Archive -LiteralPath $mainArchive -DestinationPath $binaryRoot -Force
    Expand-Archive -LiteralPath $cudaArchive -DestinationPath $binaryRoot -Force
}
Assert-Sha256 -Path $llamaExecutable -Expected $executableSha256

if (-not (Get-Command 'hf' -ErrorAction SilentlyContinue)) {
    throw "The Hugging Face CLI command 'hf' is required."
}

if (-not (Test-Path -LiteralPath $modelPath)) {
    & hf download Qwen/Qwen2.5-1.5B-Instruct-GGUF `
        qwen2.5-1.5b-instruct-q4_k_m.gguf `
        --revision $modelRevision `
        --local-dir $modelRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Hugging Face model download failed with exit code $LASTEXITCODE."
    }
}
Assert-Sha256 -Path $modelPath -Expected $modelSha256

& $llamaExecutable --version
& $llamaExecutable --list-devices

Write-Output 'Stage 2 local artifacts are installed and verified.'

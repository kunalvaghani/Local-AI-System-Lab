[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'

function Write-Section {
    param([Parameter(Mandatory)][string]$Title)
    Write-Output ""
    Write-Output "== $Title =="
}

function Get-CommandVersion {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string[]]$Arguments
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        return 'NOT FOUND'
    }

    try {
        $result = & $Name @Arguments 2>&1 | Select-Object -First 3
        return ($result -join [Environment]::NewLine).Trim()
    }
    catch {
        return "AVAILABLE, VERSION CHECK FAILED: $($_.Exception.Message)"
    }
}

Write-Output 'Local AI Systems Lab - Environment Check'
Write-Output "Captured: $([DateTimeOffset]::Now.ToString('o'))"

Write-Section 'Operating system'
Write-Output "Kernel: $([System.Environment]::OSVersion.VersionString)"
Write-Output "64-bit OS: $([System.Environment]::Is64BitOperatingSystem)"
try {
    $windows = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    Write-Output "ProductName (registry): $($windows.ProductName)"
    Write-Output "DisplayVersion: $($windows.DisplayVersion)"
    Write-Output "Build: $($windows.CurrentBuild).$($windows.UBR)"
}
catch {
    Write-Output "Windows registry details unavailable: $($_.Exception.Message)"
}

Write-Section 'CPU and memory'
try {
    $cpuName = Get-ItemPropertyValue -LiteralPath 'HKLM:\HARDWARE\DESCRIPTION\System\CentralProcessor\0' -Name 'ProcessorNameString'
    Write-Output "CPU: $($cpuName.Trim())"
}
catch {
    Write-Output "CPU model unavailable: $($_.Exception.Message)"
}
Write-Output "Logical processors: $([System.Environment]::ProcessorCount)"
try {
    Add-Type -AssemblyName Microsoft.VisualBasic
    $computer = [Microsoft.VisualBasic.Devices.ComputerInfo]::new()
    Write-Output "Physical RAM bytes: $($computer.TotalPhysicalMemory)"
    Write-Output "Available RAM bytes (snapshot): $($computer.AvailablePhysicalMemory)"
}
catch {
    Write-Output "Physical memory unavailable: $($_.Exception.Message)"
}

Write-Section 'NVIDIA GPU'
if (Get-Command 'nvidia-smi' -ErrorAction SilentlyContinue) {
    & nvidia-smi '--query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,compute_cap' '--format=csv,noheader'
}
else {
    Write-Output 'nvidia-smi: NOT FOUND'
}

Write-Section 'Development tools'
Write-Output "PowerShell: $($PSVersionTable.PSVersion)"
Write-Output "Git: $(Get-CommandVersion -Name 'git' -Arguments @('--version'))"
Write-Output "Python: $(Get-CommandVersion -Name 'python' -Arguments @('--version'))"
Write-Output "Python launcher: $(Get-CommandVersion -Name 'py' -Arguments @('--version'))"
Write-Output "pip: $(Get-CommandVersion -Name 'python' -Arguments @('-m', 'pip', '--version'))"
Write-Output "pytest: $(Get-CommandVersion -Name 'python' -Arguments @('-m', 'pytest', '--version'))"
Write-Output "CMake: $(Get-CommandVersion -Name 'cmake' -Arguments @('--version'))"
Write-Output "Node.js: $(Get-CommandVersion -Name 'node' -Arguments @('--version'))"
Write-Output "npm: $(Get-CommandVersion -Name 'npm' -Arguments @('--version'))"
Write-Output ".NET SDK: $(Get-CommandVersion -Name 'dotnet' -Arguments @('--version'))"
Write-Output "Ollama: $(Get-CommandVersion -Name 'ollama' -Arguments @('--version'))"
Write-Output "Hugging Face CLI: $(Get-CommandVersion -Name 'hf' -Arguments @('version'))"
Write-Output "llama.cpp CLI: $(Get-CommandVersion -Name 'llama-cli' -Arguments @('--version'))"
Write-Output "CUDA compiler: $(Get-CommandVersion -Name 'nvcc' -Arguments @('--version'))"
Write-Output "Firecrawl CLI: $(Get-CommandVersion -Name 'firecrawl' -Arguments @('--status'))"

Write-Section 'Stage 0 interpretation'
Write-Output 'Missing pytest, llama.cpp, CUDA, or Firecrawl tooling does not fail Stage 0.'
Write-Output 'No package was installed, no service was started, and no model was downloaded.'

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("StopKnownBackend", "StopKnownFrontend")]
    [string]$Action
)

$ErrorActionPreference = "Stop"

function Get-LoopbackListenerPid {
    param([int]$Port)

    $pattern = "^\s*TCP\s+127\.0\.0\.1:$Port\s+\S+\s+LISTENING\s+(\d+)\s*$"
    $match = & "$env:SystemRoot\System32\netstat.exe" -ano -p tcp |
        Select-String -Pattern $pattern |
        Select-Object -First 1
    if ($null -eq $match) {
        throw "No IPv4 loopback listener was found on port $Port."
    }
    return [int]$match.Matches[0].Groups[1].Value
}

function Stop-VerifiedListener {
    param(
        [int]$Port,
        [string[]]$ExpectedProcessNames,
        [scriptblock]$VerifyService
    )

    & $VerifyService
    $listenerPid = Get-LoopbackListenerPid -Port $Port
    $process = Get-Process -Id $listenerPid -ErrorAction Stop
    if ($process.ProcessName -notin $ExpectedProcessNames) {
        throw "Port $Port belongs to $($process.ProcessName), not a recognized Local AI process."
    }

    Write-Host "[AUTO] Stopping recognized stale Local AI $($process.ProcessName) process $listenerPid on port $Port..."
    Stop-Process -Id $listenerPid -Force -ErrorAction Stop
    $deadline = (Get-Date).AddSeconds(10)
    do {
        Start-Sleep -Milliseconds 200
        try {
            Get-Process -Id $listenerPid -ErrorAction Stop | Out-Null
        } catch {
            return
        }
    } while ((Get-Date) -lt $deadline)
    throw "Recognized process $listenerPid did not stop within 10 seconds."
}

try {
    if ($Action -eq "StopKnownBackend") {
        Stop-VerifiedListener -Port 8765 -ExpectedProcessNames @("python", "pythonw") -VerifyService {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/v1/health" -TimeoutSec 3
            $runtimeName = [string]$health.data.runtime_name
            if (-not $runtimeName.StartsWith("local-ai-systems-lab-stage-15", [StringComparison]::Ordinal)) {
                throw "Port 8765 does not expose a recognized Local AI runtime identity."
            }
        }
    } else {
        Stop-VerifiedListener -Port 4173 -ExpectedProcessNames @("node") -VerifyService {
            $page = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:4173/" -TimeoutSec 3
            if ($page.Content -notmatch "<title>Local AI Systems Lab</title>" -or
                $page.Content -notmatch "Local AI Systems Lab runtime inspector and debugging workbench") {
                throw "Port 4173 does not expose the recognized Local AI frontend signature."
            }
        }
    }
    exit 0
} catch {
    Write-Host "[ERROR] Refusing automatic process replacement: $($_.Exception.Message)"
    exit 1
}

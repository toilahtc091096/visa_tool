# Shared helpers for start_server.ps1, watchdog.ps1 and install_tasks.ps1.

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ProjectRoot "logs"

function Get-InstanceName([string]$EnvFile) {
    $leaf = Split-Path -Leaf $EnvFile
    if ($leaf -eq ".env") { return "default" }
    return ($leaf -replace '^\.env\.', '')
}

function Get-EnvFilePath([string]$EnvFile) {
    if ([System.IO.Path]::IsPathRooted($EnvFile)) { return $EnvFile }
    return (Join-Path $ProjectRoot $EnvFile)
}

function Get-EnvValue([string]$EnvPath, [string]$Key, [string]$Default) {
    if (Test-Path $EnvPath) {
        foreach ($line in Get-Content -Path $EnvPath -Encoding UTF8) {
            if ($line -match "^\s*$Key\s*=\s*(.*)$") {
                return $Matches[1].Trim().Trim('"').Trim("'")
            }
        }
    }
    return $Default
}

function Get-ServerTaskName([string]$Name) { return "VisaTool Server ($Name)" }
function Get-WatchdogTaskName([string]$Name) { return "VisaTool Watchdog ($Name)" }

function Get-PortOwnerPids([int]$Port) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
}

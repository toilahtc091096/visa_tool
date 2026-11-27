# Update the code on the VPS and restart every server instance, then check /health of each.
#
#   powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1 -NoPull            # restart only
#   powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1 -EnvFiles .env.phong
#
# Instances are restarted one after another, so the other houses keep working meanwhile.
# Exit code 1 when git pull fails or an instance does not answer /health in time.
param(
    [string[]]$EnvFiles = @(".env", ".env.phong", ".env.nam"),
    [int]$HealthTimeoutSec = 90,
    [switch]$NoPull
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")
Set-Location $ProjectRoot

if (-not $NoPull) {
    $before = (git rev-parse --short HEAD).Trim()
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) { Write-Host "git pull FAILED, nothing restarted" -ForegroundColor Red; exit 1 }
    $after = (git rev-parse --short HEAD).Trim()
    if ($before -eq $after) { Write-Host "Code unchanged ($after), restarting anyway" }
    else { Write-Host "Code $before -> $after"; git log --oneline "$before..$after" }
}

$results = @()
foreach ($envFile in $EnvFiles) {
    $envPath = Get-EnvFilePath $envFile
    if (-not (Test-Path $envPath)) { Write-Host "skip $envFile (file not found)"; continue }
    $name = Get-InstanceName $envFile
    $port = [int](Get-EnvValue $envPath "PORT" "10000")
    $task = Get-ServerTaskName $name
    Write-Host "`n== $name (port $port) =="

    Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
    foreach ($processId in Get-PortOwnerPids $port) { Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
    Start-ScheduledTask -TaskName $task

    $ok = $false
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    while ($watch.Elapsed.TotalSeconds -lt $HealthTimeoutSec) {
        Start-Sleep -Seconds 3
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" -TimeoutSec 5 -UseBasicParsing
            if ($r.StatusCode -eq 200) { $ok = $true; break }
        } catch { }
    }
    $secs = [math]::Round($watch.Elapsed.TotalSeconds)
    if ($ok) { Write-Host "OK   $name up after ${secs}s" -ForegroundColor Green }
    else { Write-Host "FAIL $name no /health after ${secs}s, see logs\server-$name.log" -ForegroundColor Red }
    $results += [pscustomobject]@{ Instance = $name; Port = $port; Health = $(if ($ok) { "OK" } else { "FAIL" }) }
}

Write-Host ""
$results | Format-Table -AutoSize | Out-String | Write-Host
if ($results | Where-Object Health -eq "FAIL") { exit 1 }

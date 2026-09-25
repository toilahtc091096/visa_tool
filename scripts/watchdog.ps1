# Ping /health; if the server does not answer, restart its scheduled task.
# Results go to logs\watchdog-<name>.log (slow answers are logged too).
#
#   powershell -ExecutionPolicy Bypass -File scripts\watchdog.ps1 -EnvFile .env.viet
param(
    [string]$EnvFile = ".env",
    [int]$TimeoutSec = 15,
    [int]$SlowSec = 3,
    [int]$StartupGraceMinutes = 3
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")

$envPath = Get-EnvFilePath $EnvFile
$name = Get-InstanceName $EnvFile
$port = [int](Get-EnvValue $envPath "PORT" "10000")
$taskName = Get-ServerTaskName $name

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$log = Join-Path $LogDir "watchdog-$name.log"
function Write-WatchdogLog([string]$Message) {
    "[$(Get-Date -Format s)] $Message" | Out-File -FilePath $log -Append -Encoding utf8
}

$lastError = ""
for ($attempt = 1; $attempt -le 2; $attempt++) {
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" `
            -TimeoutSec $TimeoutSec -UseBasicParsing
        $seconds = [math]::Round($watch.Elapsed.TotalSeconds, 2)
        if ($response.StatusCode -eq 200) {
            if ($seconds -ge $SlowSec) {
                Write-WatchdogLog "SLOW health answer on port $port took ${seconds}s"
            }
            exit 0
        }
        $lastError = "HTTP $($response.StatusCode)"
    } catch {
        $lastError = $_.Exception.Message
    }
    Start-Sleep -Seconds 5
}

$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction SilentlyContinue
if ($taskInfo -and $taskInfo.LastRunTime -gt (Get-Date).AddMinutes(-$StartupGraceMinutes)) {
    Write-WatchdogLog "no answer on port $port ($lastError) but task started recently; waiting"
    exit 0
}

Write-WatchdogLog "no answer on port $port ($lastError); restarting '$taskName'"
Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
foreach ($processId in Get-PortOwnerPids $port) {
    Write-WatchdogLog "killing pid $processId listening on port $port"
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 3
Start-ScheduledTask -TaskName $taskName
Write-WatchdogLog "restart requested"

# Register (or remove) the Task Scheduler tasks for one server instance:
#   - "VisaTool Server (<name>)"   : starts the server at logon, hidden, logs to file
#   - "VisaTool Watchdog (<name>)" : pings /health every N minutes, restarts if dead
#
# Both run as the current user, only while that user is logged on, because
# Word COM automation (DOCX -> PDF) does not work from a background session.
#
#   powershell -ExecutionPolicy Bypass -File scripts\install_tasks.ps1 -EnvFile .env.viet
#   powershell -ExecutionPolicy Bypass -File scripts\install_tasks.ps1 -EnvFile .env.viet -Uninstall
param(
    [Parameter(Mandatory = $true)][string]$EnvFile,
    [string]$Python = "",
    [int]$WatchdogMinutes = 5,
    [switch]$Uninstall
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")

$name = Get-InstanceName $EnvFile
$serverTask = Get-ServerTaskName $name
$watchdogTask = Get-WatchdogTaskName $name

if ($Uninstall) {
    foreach ($task in @($watchdogTask, $serverTask)) {
        Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "Removed: $task"
    }
    return
}

if (-not (Test-Path (Get-EnvFilePath $EnvFile))) { throw "Env file not found: $EnvFile" }

$user = "$env:USERDOMAIN\$env:USERNAME"
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$baseArgs = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File"

$serverArgs = "$baseArgs `"$PSScriptRoot\start_server.ps1`" -EnvFile `"$EnvFile`""
if ($Python) { $serverArgs += " -Python `"$Python`"" }
Register-ScheduledTask -TaskName $serverTask -Force -Principal $principal `
    -Action (New-ScheduledTaskAction -Execute "powershell.exe" -Argument $serverArgs `
        -WorkingDirectory $ProjectRoot) `
    -Trigger (New-ScheduledTaskTrigger -AtLogOn -User $user) `
    -Settings (New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -MultipleInstances IgnoreNew `
        -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
        -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable) |
    Out-Null
Write-Host "Registered: $serverTask"

$watchdogArgs = "$baseArgs `"$PSScriptRoot\watchdog.ps1`" -EnvFile `"$EnvFile`""
Register-ScheduledTask -TaskName $watchdogTask -Force -Principal $principal `
    -Action (New-ScheduledTaskAction -Execute "powershell.exe" -Argument $watchdogArgs `
        -WorkingDirectory $ProjectRoot) `
    -Trigger (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
        -RepetitionInterval (New-TimeSpan -Minutes $WatchdogMinutes) `
        -RepetitionDuration (New-TimeSpan -Days 3650)) `
    -Settings (New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 2) `
        -MultipleInstances IgnoreNew `
        -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable) |
    Out-Null
Write-Host "Registered: $watchdogTask (every $WatchdogMinutes min)"

Start-ScheduledTask -TaskName $serverTask
Write-Host "Started: $serverTask -> logs\server-$name.log"

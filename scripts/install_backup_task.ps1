# Register (or remove) the nightly database backup task "VisaTool DB Backup".
# It runs scripts\backup_db.py (pg_dump -> backups\ -> R2 _db-backup/) every day at -At,
# output appended to logs\backup.log.
#
#   powershell -ExecutionPolicy Bypass -File scripts\install_backup_task.ps1 [-EnvFile .env] [-At 02:00]
#   powershell -ExecutionPolicy Bypass -File scripts\install_backup_task.ps1 -Uninstall
#   Run once now: Start-ScheduledTask "VisaTool DB Backup"
param(
    [string]$EnvFile = ".env",
    [string]$At = "02:00",
    [string]$Python = "",
    [switch]$Uninstall
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")

$taskName = "VisaTool DB Backup"
if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Removed: $taskName"
    return
}

if (-not $Python) {
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    $Python = if (Test-Path $venvPython) { $venvPython } else { "python" }
}
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$log = Join-Path $LogDir "backup.log"
$script = Join-Path $PSScriptRoot "backup_db.py"
# cmd /c so stdout and stderr of python both land in the log, with a timestamp line first
$cmdLine = "/c echo [%date% %time%] >> `"$log`" & `"$Python`" `"$script`" --env `"$EnvFile`" >> `"$log`" 2>&1"

$user = "$env:USERDOMAIN\$env:USERNAME"
Register-ScheduledTask -TaskName $taskName -Force `
    -Principal (New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited) `
    -Action (New-ScheduledTaskAction -Execute "cmd.exe" -Argument $cmdLine -WorkingDirectory $ProjectRoot) `
    -Trigger (New-ScheduledTaskTrigger -Daily -At $At) `
    -Settings (New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 40) `
        -MultipleInstances IgnoreNew `
        -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable) |
    Out-Null
Write-Host "Registered: $taskName (daily $At) -> $log"

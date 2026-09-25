# Run one server instance with all output written to logs\server-<name>.log
# instead of the console (so a console selection can never freeze the server).
# Start/stop messages of this script go to logs\launcher-<name>.log.
#
#   powershell -ExecutionPolicy Bypass -File scripts\start_server.ps1 -EnvFile .env.viet
param(
    [string]$EnvFile = ".env",
    [string]$Python = ""
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")

$envPath = Get-EnvFilePath $EnvFile
if (-not (Test-Path $envPath)) { throw "Env file not found: $envPath" }
$name = Get-InstanceName $EnvFile
$port = [int](Get-EnvValue $envPath "PORT" "10000")

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$log = Join-Path $LogDir "server-$name.log"
# cmd.exe holds server-<name>.log open while the server runs, so this script
# writes its own start/stop messages to a separate file.
$launcherLog = Join-Path $LogDir "launcher-$name.log"
function Write-ServerLog([string]$Message) {
    "[$(Get-Date -Format s)] $Message" | Out-File -FilePath $launcherLog -Append -Encoding utf8
}

# Rotate at 20 MB and keep the 5 most recent rotated files.
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 20MB)) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    Move-Item $log (Join-Path $LogDir "server-$name-$stamp.log")
}
Get-ChildItem -Path $LogDir -Filter "server-$name-*.log" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 5 |
    Remove-Item -Force

if (-not $Python) {
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $Python = $venvPython
    } else {
        $Python = (Get-Command python -ErrorAction Stop).Source
    }
}

$busy = Get-PortOwnerPids $port
if ($busy) {
    Write-ServerLog "port $port already in use by pid $($busy -join ','); not starting"
    exit 1
}

$env:ENV_FILE = $EnvFile
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-ServerLog "starting env=$EnvFile port=$port python=$Python"
# cmd.exe does the redirection so stdout/stderr bytes go straight to the file.
$cmdArgs = "/d /s /c `"`"$Python`" -u server.py >> `"$log`" 2>&1`""
$process = Start-Process -FilePath "cmd.exe" -ArgumentList $cmdArgs `
    -WorkingDirectory $ProjectRoot -NoNewWindow -Wait -PassThru
Write-ServerLog "server exited with code $($process.ExitCode)"
exit $process.ExitCode

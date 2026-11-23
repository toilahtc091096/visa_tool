# HTTPS for the /web page with a free DuckDNS domain, using Caddy (automatic Let's Encrypt
# certificate, renewed by itself). Run ONCE on the VPS, in an Administrator PowerShell:
#
#   powershell -ExecutionPolicy Bypass -File scripts\setup_https.ps1 -Domain visa-xyz.duckdns.org -DuckToken <token>
#   powershell -ExecutionPolicy Bypass -File scripts\setup_https.ps1 -Uninstall
#
# What it does:
#   1. Downloads Caddy (pinned version) into tools\caddy\ (not in git).
#   2. Writes tools\caddy\Caddyfile: https://<Domain>/web... and /health -> 127.0.0.1:<Port>;
#      "/" -> /web; every other path 404 (n8n and the Telegram curls keep using IP:port).
#   3. Opens TCP 80 + 443 in Windows Firewall (80 is needed by Let's Encrypt).
#   4. Task "VisaTool Caddy": runs Caddy as SYSTEM at boot, restarts it if it stops.
#   5. With -DuckToken: task "VisaTool DuckDNS" points the domain at this VPS every 30 min
#      (token kept in tools\caddy\duckdns.txt, readable by Administrators only).
#   6. Checks https://<Domain>/health.
#
# The server must trust Caddy's X-Forwarded-For only from 127.0.0.1: server.py runs uvicorn
# with proxy_headers=True, forwarded_allow_ips="127.0.0.1" (tests/test_https_proxy.py).
param(
    [string]$Domain = "",
    [int]$Port = 10000,
    [string]$DuckToken = "",
    [string]$CaddyVersion = "2.8.4",
    [switch]$Uninstall
)
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$CaddyDir = Join-Path $ProjectRoot "tools\caddy"
$CaddyExe = Join-Path $CaddyDir "caddy.exe"
$Caddyfile = Join-Path $CaddyDir "Caddyfile"
$DuckFile = Join-Path $CaddyDir "duckdns.txt"
$CaddyTask = "VisaTool Caddy"
$DuckTask = "VisaTool DuckDNS"
$FirewallRule = "VisaTool HTTPS (80, 443)"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { throw "Run this in an Administrator PowerShell (firewall + SYSTEM task)." }

if ($Uninstall) {
    foreach ($task in @($DuckTask, $CaddyTask)) {
        Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "Removed task: $task"
    }
    Get-NetFirewallRule -DisplayName $FirewallRule -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    Write-Host "Removed firewall rule. Files kept in $CaddyDir (certificates in data\)."
    return
}

$Domain = $Domain.Trim().ToLower()
if ($Domain -notmatch '^[a-z0-9-]+\.duckdns\.org$') {
    throw "-Domain must be <name>.duckdns.org (got '$Domain')"
}
$Sub = $Domain.Split('.')[0]

# ---- 0. ports 80 / 443 must be free (IIS, Skype... would block Caddy) ----
foreach ($p in 80, 443) {
    $busy = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
    if ($busy) {
        $procs = ($busy | ForEach-Object { (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName }) -join ", "
        if ($procs -notmatch 'caddy') { throw "Port $p is already used by: $procs. Stop it first." }
    }
}

# ---- 1. Caddy ----
New-Item -ItemType Directory -Force -Path $CaddyDir, (Join-Path $CaddyDir "data"), (Join-Path $CaddyDir "logs") | Out-Null
if (-not (Test-Path $CaddyExe)) {
    $zip = Join-Path $env:TEMP "caddy_$CaddyVersion.zip"
    $url = "https://github.com/caddyserver/caddy/releases/download/v$CaddyVersion/caddy_${CaddyVersion}_windows_amd64.zip"
    Write-Host "Downloading $url"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $CaddyDir -Force
    Remove-Item $zip -Force
}
Write-Host ("Caddy: " + (& $CaddyExe version))

# ---- 2. Caddyfile ----
$data = (Join-Path $CaddyDir "data").Replace('\', '/')
$log = (Join-Path $CaddyDir "logs\access.log").Replace('\', '/')
$conf = @"
{
	storage file_system {
		root "$data"
	}
}

$Domain {
	encode gzip
	log {
		output file "$log" {
			roll_size 10MiB
			roll_keep 5
		}
	}
	@app path /web /web/* /health
	handle @app {
		reverse_proxy 127.0.0.1:$Port
	}
	handle / {
		redir /web 302
	}
	handle {
		respond "Not found" 404
	}
}
"@
Set-Content -Path $Caddyfile -Value $conf -Encoding ascii
& $CaddyExe validate --config $Caddyfile --adapter caddyfile
if ($LASTEXITCODE -ne 0) { throw "Caddyfile is not valid" }
Write-Host "Caddyfile: $Caddyfile"

# ---- 3. firewall ----
if (-not (Get-NetFirewallRule -DisplayName $FirewallRule -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $FirewallRule -Direction Inbound -Protocol TCP -LocalPort 80, 443 -Action Allow | Out-Null
}
Write-Host "Firewall: TCP 80, 443 open (also open them in the VPS provider's panel if it has one)"

# ---- 4. Caddy task (SYSTEM, at boot, restart on failure) ----
$system = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Stop-ScheduledTask -TaskName $CaddyTask -ErrorAction SilentlyContinue
Get-Process caddy -ErrorAction SilentlyContinue | Stop-Process -Force
Register-ScheduledTask -TaskName $CaddyTask -Force -Principal $system -Settings $settings `
    -Action (New-ScheduledTaskAction -Execute $CaddyExe -Argument "run --config `"$Caddyfile`" --adapter caddyfile" -WorkingDirectory $CaddyDir) `
    -Trigger (New-ScheduledTaskTrigger -AtStartup) | Out-Null
Start-ScheduledTask -TaskName $CaddyTask
Write-Host "Task: $CaddyTask (started)"

# ---- 5. DuckDNS updater ----
if ($DuckToken) {
    Set-Content -Path $DuckFile -Value "$Sub`n$($DuckToken.Trim())" -Encoding ascii
    icacls $DuckFile /inheritance:r /grant:r "Administrators:F" "SYSTEM:F" | Out-Null
    $updater = Join-Path $PSScriptRoot "duckdns_update.ps1"
    Register-ScheduledTask -TaskName $DuckTask -Force -Principal $system `
        -Action (New-ScheduledTaskAction -Execute "powershell.exe" `
            -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$updater`" -TokenFile `"$DuckFile`"") `
        -Trigger (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 30) `
            -RepetitionDuration (New-TimeSpan -Days 3650)) `
        -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 2) -StartWhenAvailable) | Out-Null
    & $updater -TokenFile $DuckFile
    Write-Host "Task: $DuckTask (every 30 min)"
}

# ---- 6. check ----
Write-Host "Waiting for the certificate (up to 2 min)..."
$ok = $false
for ($i = 0; $i -lt 24 -and -not $ok; $i++) {
    Start-Sleep -Seconds 5
    try {
        $r = Invoke-WebRequest -Uri "https://$Domain/health" -UseBasicParsing -TimeoutSec 10
        $ok = $r.StatusCode -eq 200
    } catch { }
}
if ($ok) {
    Write-Host "OK: https://$Domain/web" -ForegroundColor Green
} else {
    Write-Host "Not reachable yet. Check: DuckDNS points to this VPS IP, ports 80/443 open at the provider, logs: $CaddyDir\logs" -ForegroundColor Yellow
}

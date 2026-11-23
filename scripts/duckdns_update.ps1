# Point the DuckDNS domain at this VPS (DuckDNS takes the caller's public IP when ip= is empty).
# Run by the "VisaTool DuckDNS" task (scripts/setup_https.ps1). The token file holds two lines:
# the sub-domain (without .duckdns.org) and the token.
param([Parameter(Mandatory = $true)][string]$TokenFile)
$ErrorActionPreference = "Stop"
$lines = Get-Content -Path $TokenFile | Where-Object { $_.Trim() }
$sub, $token = $lines[0].Trim(), $lines[1].Trim()
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$answer = Invoke-RestMethod -Uri "https://www.duckdns.org/update?domains=$sub&token=$token&ip=" -TimeoutSec 30
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path (Join-Path (Split-Path $TokenFile) "logs\duckdns.log") -Value "$stamp $sub $answer"
if ("$answer".Trim() -ne "OK") { Write-Host "DuckDNS answered: $answer (check the domain and token)"; exit 1 }
Write-Host "DuckDNS: $sub.duckdns.org -> this VPS (OK)"

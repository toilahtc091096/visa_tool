$ErrorActionPreference = "Stop"

$apiUrl = $env:VISA_SYNC_URL
if ([string]::IsNullOrWhiteSpace($apiUrl)) {
    $apiUrl = "http://127.0.0.1:8000/visa-registrations/sync-draft-status?page_num=1&page_size=10"
}

$auth = $env:VISA_SYNC_AUTHORIZATION
if (-not [string]::IsNullOrWhiteSpace($auth)) {
    $apiUrl = $apiUrl + "&authorization=" + [uri]::EscapeDataString($auth)
}

try {
    Invoke-RestMethod -Method Get -Uri $apiUrl | Out-String | Write-Output
} catch {
    Write-Error $_
    exit 1
}

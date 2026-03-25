param (
    [int]$Port = 8000
)

# 1. Read token from .env
$envFilePath = Join-Path $PSScriptRoot ".env"
if (-Not (Test-Path $envFilePath)) {
    Write-Host "[Error] .env file not found in the project root!" -ForegroundColor Red
    exit 1
}

$tgToken = ""
foreach ($line in Get-Content $envFilePath) {
    if ($line.Trim() -match "^TG_BOT_TOKEN=(.*)$") {
        $tgToken = $matches[1].Trim('"', "'", ' ', "`r", "`n")
        break
    }
}

if (-Not $tgToken) {
    Write-Host "[Error] TG_BOT_TOKEN not found in .env!" -ForegroundColor Red
    exit 1
}

# Clear old log file
$outFile = Join-Path $PSScriptRoot "lt_out.txt"
if (Test-Path $outFile) { Remove-Item $outFile }

# 2. Run localtunnel
Write-Host "[1/3] Starting localtunnel on port $Port..." -ForegroundColor Cyan
$ltProc = Start-Process -FilePath "npx.cmd" -ArgumentList "lt --port $Port" -NoNewWindow -PassThru -RedirectStandardOutput $outFile

# 3. Wait for URL
$url = ""
$attempts = 0
Write-Host "[2/3] Waiting for external URL from localtunnel..." -ForegroundColor Cyan

while ($url -eq "" -and $attempts -lt 15) {
    Start-Sleep -Seconds 1
    if (Test-Path $outFile) {
        $content = Get-Content $outFile -ErrorAction SilentlyContinue
        if ($content) {
            foreach ($line in $content) {
                if ($line -match "(https://[a-zA-Z0-9-]+\.loca\.lt)") {
                    $url = $matches[1].Trim()
                    break
                }
            }
        }
    }
    $attempts++
}

if (-Not $url) {
    Write-Host "[Error] Failed to get URL. Check your connection or npm/npx installation." -ForegroundColor Red
    if ($null -ne $ltProc) { Stop-Process -Id $ltProc.Id -Force }
    exit 1
}

Write-Host "-> Success! URL: $url" -ForegroundColor Green

# 4. Register Telegram Webhook
$webhookUrl = "$url/webhook/telegram"
Write-Host "[3/3] Registering Webhook in Telegram ($webhookUrl)..." -ForegroundColor Cyan

$teleApi = "https://api.telegram.org/bot$tgToken/setWebhook"
$finalUri = "$teleApi?url=$webhookUrl"

try {
    Write-Host "   -> Requesting: $finalUri" -ForegroundColor DarkGray
    $response = Invoke-RestMethod -Uri $finalUri -Method Get
    if ($response.ok) {
        Write-Host "-> Webhook successfully registered!" -ForegroundColor Green
        Write-Host "   Details: $($response.description)" -ForegroundColor DarkGray
    } else {
        Write-Host "-> Error registering Webhook:" -ForegroundColor Red
        $response | Out-String | Write-Host -ForegroundColor Red
    }
} catch {
    Write-Host "-> Error requesting Telegram API: $_" -ForegroundColor Red
}

Write-Host "`nAll done! Localtunnel is running in background. Press Ctrl+C in THIS window to leave the tunnel, or close the window to kill npx." -ForegroundColor Yellow

# Keep script running to prevent tunnel closure
try {
    Wait-Process -Id $ltProc.Id
} catch {
    # Ignore errors on close
}

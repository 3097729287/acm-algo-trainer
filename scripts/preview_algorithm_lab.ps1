param([switch]$Open)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$labFrontend = Join-Path $labRoot 'frontend'
$labVite = Join-Path $labFrontend 'node_modules\vite\bin\vite.js'
$labDirectory = Join-Path $labRoot '.backups\algorithm-lab-20261022'
$labUrl = 'http://127.0.0.1:18836/tests/algorithm-lab-fixture.html'
$labReady = $false

if (-not (Test-Path -LiteralPath $labVite -PathType Leaf)) {
    throw 'Frontend dependencies are missing. Run npm ci in frontend first.'
}
New-Item -ItemType Directory -Path $labDirectory -Force | Out-Null
try {
    $labResponse = Invoke-WebRequest -Uri $labUrl -UseBasicParsing -TimeoutSec 2
    if ($labResponse.StatusCode -eq 200 -and $labResponse.Content.Contains('algorithm-lab-fixture.jsx')) {
        $labReady = $true
    }
} catch { $labReady = $false }

if (-not $labReady) {
    $labNode = (Get-Command node -ErrorAction Stop).Source
    $env:TB_OFFLINE = '1'
    $labProcess = Start-Process -FilePath $labNode -ArgumentList @(('"' + $labVite + '"'), '--host', '127.0.0.1', '--port', '18836', '--strictPort') -WorkingDirectory $labFrontend -WindowStyle Hidden -RedirectStandardOutput (Join-Path $labDirectory 'preview.stdout.log') -RedirectStandardError (Join-Path $labDirectory 'preview.stderr.log') -PassThru
    for ($labAttempt = 0; $labAttempt -lt 40; $labAttempt++) {
        if ($labProcess.HasExited) { throw 'Preview server failed to start. See .backups/algorithm-lab-20261022/preview.stderr.log.' }
        try {
            $labResponse = Invoke-WebRequest -Uri $labUrl -UseBasicParsing -TimeoutSec 1
            if ($labResponse.StatusCode -eq 200 -and $labResponse.Content.Contains('algorithm-lab-fixture.jsx')) { $labReady = $true; break }
        } catch { }
        Start-Sleep -Milliseconds 250
    }
    if (-not $labReady) { throw 'Preview server did not become ready. See the preview logs.' }
    @{ url = $labUrl; processId = $labProcess.Id; source = $labRoot; personalState = 'isolated browser preview only' } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $labDirectory 'preview.json') -Encoding UTF8
}

Write-Output $labUrl
if ($Open) { Start-Process $labUrl }

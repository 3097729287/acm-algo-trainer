param(
    [string]$Destination = 'E:\项目\ToBe\版本\重构验证\2.0.0-alpha.1',
    [switch]$VerifyOnly
)
$ErrorActionPreference = 'Stop'
$sourceRoot = Split-Path -Parent $PSScriptRoot
$targetRoot = [IO.Path]::GetFullPath($Destination)
if ($VerifyOnly) {
    $info = Get-Content -LiteralPath (Join-Path $targetRoot 'BUILD-INFO.json') -Raw | ConvertFrom-Json
    $totalBytes = 0L
    foreach ($member in $info.members) {
        $target = [IO.Path]::GetFullPath((Join-Path $targetRoot $member.path))
        if (-not $target.StartsWith($targetRoot.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid candidate member path.' }
        if ((Get-Item -LiteralPath $target).Length -ne $member.bytes -or (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $member.sha256) { throw "Candidate verification failed: $($member.path)" }
        $totalBytes += [long]$member.bytes
    }
    [PSCustomObject]@{ CandidateBytes=$totalBytes; VerifiedMembers=$info.members.Count; Entry=(Join-Path $targetRoot $info.entry) }
    exit 0
}
if (Test-Path -LiteralPath $targetRoot) { throw 'Candidate destination already exists; choose a new directory so no existing data is replaced.' }
$binary = Join-Path $sourceRoot 'target\release\tobe-desktop.exe'
if (-not (Test-Path -LiteralPath $binary)) { throw 'Build the native desktop candidate first: scripts/native.ps1 -Action desktop' }
$members = [ordered]@{
    'ToBe-Rust.exe' = $binary
    'WebView2Loader.dll' = (Join-Path $sourceRoot 'target\release\WebView2Loader.dll')
    'data\library.sqlite3' = (Join-Path $sourceRoot 'data\library.sqlite3')
    'backend\resources\oi-wiki.sqlite3' = (Join-Path $sourceRoot 'backend\resources\oi-wiki.sqlite3')
    'backend\resources\code-templates.json' = (Join-Path $sourceRoot 'backend\resources\code-templates.json')
    'backend\resources\template-teaching.json' = (Join-Path $sourceRoot 'backend\resources\template-teaching.json')
}
foreach ($item in $members.Values) { if (-not (Test-Path -LiteralPath $item -PathType Leaf)) { throw "Missing candidate member: $item" } }
New-Item -ItemType Directory -Path $targetRoot | Out-Null
$manifest = @()
foreach ($entry in $members.GetEnumerator()) {
    $target = Join-Path $targetRoot $entry.Key
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $entry.Value -Destination $target
    $sourceHash = (Get-FileHash -LiteralPath $entry.Value -Algorithm SHA256).Hash.ToLowerInvariant()
    $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sourceHash -ne $targetHash) { throw "Candidate copy verification failed: $($entry.Key)" }
    $manifest += [ordered]@{ path=$entry.Key.Replace('\','/'); bytes=(Get-Item -LiteralPath $target).Length; sha256=$targetHash }
}
$commit = git -C $sourceRoot rev-parse HEAD
$info = [ordered]@{
    version='2.0.0-alpha.1'; status='native-migration-diagnostic'; releaseReady=$false
    createdAt=[DateTime]::UtcNow.ToString('o'); sourceCommit=$commit; sourceRoot=$sourceRoot
    entry='ToBe-Rust.exe'; runtime='Tauri 2 + React + Rust + SQLite'; pythonRuntime=$false
    replacesCurrentInstallation=$false; publicRelease=$false; members=$manifest
    scope='Migration verification only; complete feature parity, production migration and full resource comparison remain pending.'
}
$info | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $targetRoot 'BUILD-INFO.json') -Encoding UTF8
Copy-Item -LiteralPath (Join-Path $sourceRoot 'docs\native-migration.md') -Destination (Join-Path $targetRoot '重构进度.md')
$totalBytes = ($manifest | ForEach-Object { [long]$_['bytes'] } | Measure-Object -Sum).Sum
[PSCustomObject]@{ CandidateBytes=$totalBytes; Entry=(Join-Path $targetRoot 'ToBe-Rust.exe') }

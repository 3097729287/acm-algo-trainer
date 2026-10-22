param([switch]$Open)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$labEntry = [IO.Path]::GetFullPath((Join-Path $labRoot '..\..\版本\算法实验室体验版\开始体验.html'))
if (-not (Test-Path -LiteralPath $labEntry -PathType Leaf)) {
    throw 'Build the standalone course first: run npm run build:lab in frontend.'
}
Write-Output $labEntry
if ($Open) { Start-Process -FilePath $labEntry }

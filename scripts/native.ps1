param(
    [ValidateSet('check','test','build','desktop','dev','fmt')]
    [string]$Action = 'test',
    [string]$TargetDirectory = '',
    [string]$ToolchainBin = '',
    [string]$TestPython = ''
)
$ErrorActionPreference = 'Stop'
$sourceRoot = Split-Path -Parent $PSScriptRoot
$toolsRoot = 'E:\项目\ToBe\公共工具\Rust'
$env:CARGO_HOME = Join-Path $toolsRoot 'cargo'
$env:RUSTUP_HOME = Join-Path $toolsRoot 'rustup'
if (!$ToolchainBin) { $ToolchainBin = $env:TB_NATIVE_MINGW_BIN }
if (!$ToolchainBin) { $ToolchainBin = 'D:\Work\Msys64\ucrt64\bin' }
if (!(Test-Path -LiteralPath (Join-Path $ToolchainBin 'gcc.exe') -PathType Leaf)) {
    throw 'Provide -ToolchainBin with the prepared MinGW GCC directory.'
}
$env:PATH = "$env:CARGO_HOME\bin;$ToolchainBin;$env:PATH"
$env:CC = 'gcc'
$env:AR = 'ar'
$env:CARGO_TARGET_X86_64_PC_WINDOWS_GNU_LINKER = 'gcc'
if (!$TargetDirectory) { $TargetDirectory = $env:CARGO_TARGET_DIR }
$targetRecord = Join-Path $sourceRoot '.backups\native-target.json'
if (!$TargetDirectory -and (Test-Path -LiteralPath $targetRecord)) {
    $savedTarget = Get-Content -LiteralPath $targetRecord -Raw -Encoding UTF8 | ConvertFrom-Json
    if ([IO.Path]::GetFullPath($savedTarget.source) -eq [IO.Path]::GetFullPath($sourceRoot)) { $TargetDirectory = $savedTarget.target }
}
if ($TargetDirectory) { $env:CARGO_TARGET_DIR = [IO.Path]::GetFullPath($TargetDirectory) }
if ($Action -eq 'test') {
    if (!$TestPython) { $TestPython = $env:TB_NATIVE_TEST_PYTHON }
    if (!$TestPython) {
        $projectRoot = Split-Path -Parent (Split-Path -Parent $sourceRoot)
        $TestPython = Join-Path $projectRoot '版本\最新版\程序\_internal\python3\python.exe'
    }
    if (!(Test-Path -LiteralPath $TestPython -PathType Leaf)) { throw 'Provide -TestPython with the Windows test interpreter; the backend does not use Python.' }
    $env:TB_NATIVE_TEST_PYTHON = [IO.Path]::GetFullPath($TestPython)
}
Push-Location $sourceRoot
try {
    if ($Action -eq 'desktop') { cargo build -p tobe-desktop --release }
    elseif ($Action -eq 'dev') { $env:TB_NATIVE_SOURCE_ROOT=$sourceRoot; cargo run -p tobe-desktop }
    elseif ($Action -eq 'fmt') { cargo fmt --all -- --check }
    elseif ($Action -eq 'build') { cargo build -p tobe-core --release }
    elseif ($Action -eq 'check') { cargo check --workspace }
    else { cargo test -p tobe-core }
    if ($LASTEXITCODE -ne 0) { throw "Native command failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }

param(
    [ValidateSet('check','test','build','desktop','dev','fmt')]
    [string]$Action = 'test'
)
$ErrorActionPreference = 'Stop'
$sourceRoot = Split-Path -Parent $PSScriptRoot
$toolsRoot = 'E:\项目\ToBe\公共工具\Rust'
$env:CARGO_HOME = Join-Path $toolsRoot 'cargo'
$env:RUSTUP_HOME = Join-Path $toolsRoot 'rustup'
$env:PATH = "$env:CARGO_HOME\bin;D:\Software\Work\Msys64\ucrt64\bin;$env:PATH"
$env:CC = 'gcc'
$env:AR = 'ar'
$env:CARGO_TARGET_X86_64_PC_WINDOWS_GNU_LINKER = 'gcc'
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

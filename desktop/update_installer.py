"""Wait for a normal desktop exit, run the verified installer, then restart TB."""
import os
from pathlib import Path
import subprocess
import sys


def ps_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def launch_installer(installer, digest, version, app_dir, parent_pid=None):
    if os.name != "nt":
        raise RuntimeError("Windows installer required")
    installer, app_dir = Path(installer).resolve(), Path(app_dir).resolve()
    executable = app_dir / "TB新版.exe"
    script = installer.parent / "apply-update.ps1"
    log = installer.parent / "install-result.txt"
    # All values originate in validated release metadata or local paths. None is
    # evaluated as command text; quoted PowerShell literals also support apostrophes.
    content = f"""$ErrorActionPreference = 'Stop'
$setupPath = {ps_literal(installer)}
$targetDir = {ps_literal(app_dir)}
$exePath = {ps_literal(executable)}
$resultPath = {ps_literal(log)}
try {{
  $parent = Get-Process -Id {int(parent_pid or os.getpid())} -ErrorAction SilentlyContinue
  if ($parent) {{
    if (-not $parent.WaitForExit(180000)) {{ throw 'TB did not close; update cancelled.' }}
  }}
  if ((Get-FileHash -LiteralPath $setupPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne {ps_literal(digest)}) {{ throw 'Installer SHA-256 mismatch.' }}
  $arguments = @('/SILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', '/NOICONS', '/TASKS=""', ('/DIR="' + $targetDir + '"'))
  $installerProcess = Start-Process -FilePath $setupPath -ArgumentList $arguments -PassThru -Wait -WindowStyle Hidden
  if ($installerProcess.ExitCode -ne 0) {{ throw ('Installer failed: ' + $installerProcess.ExitCode) }}
  if ((Get-Content -LiteralPath (Join-Path $targetDir 'VERSION') -Raw).Trim() -ne {ps_literal(version)}) {{ throw 'Installed version does not match.' }}
  Set-Content -LiteralPath $resultPath -Value 'ok' -Encoding UTF8
  # TB is the interactive application the user requested to reopen.
  Start-Process -FilePath $exePath -WorkingDirectory $targetDir -WindowStyle Normal
  Remove-Item -LiteralPath $setupPath -Force
}} catch {{
  Set-Content -LiteralPath $resultPath -Value $_.Exception.Message -Encoding UTF8
  Add-Type -AssemblyName System.Windows.Forms
  [System.Windows.Forms.MessageBox]::Show('TB 更新没有完成，个人数据仍保留。请重新打开 TB 后重试。' + [Environment]::NewLine + $_.Exception.Message, 'TB 更新') | Out-Null
}}
"""
    script.write_text(content, encoding="utf-8-sig")
    # Windows PowerShell may silently exit without running -File when a detached
    # console and CREATE_NO_WINDOW are combined. A hidden independent process
    # survives the GUI parent's exit without DETACHED_PROCESS.
    with (installer.parent / "updater-launch.log").open("wb") as output:
        return subprocess.Popen([str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"),
                                 "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
                                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, close_fds=True)


"""Exercise the real Windows update helper using an isolated validation installer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

from check_release import ROOT, environment, OPENER
from check_current_release import personal_rows

sys.path.insert(0, str(ROOT / 'desktop'))
from update_installer import launch_installer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--validation-report', type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.validation_report.read_text(encoding='utf8'))
    app = Path(report['upgradeApp']).resolve()
    assert app.is_relative_to(ROOT / 'build') and 'release-check-' in str(app)
    before = personal_rows(app)
    destination = app / 'cache/updates' / Path(report['validationInstaller']).name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(report['validationInstaller'], destination)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    os.environ.update(environment(app))
    os.environ['TB_PACKAGE_PORT'] = str(port)
    parent = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(2)'], creationflags=subprocess.CREATE_NO_WINDOW)
    helper = launch_installer(destination, hashlib.sha256(destination.read_bytes()).hexdigest(), report['version'], app, parent_pid=parent.pid)
    parent.wait()
    deadline, api = time.monotonic() + 120, None
    while time.monotonic() < deadline:
        try:
            base = 'http://127.0.0.1:' + str(port)
            with OPENER.open(base + '/api/account', timeout=10) as response:
                account = json.load(response)
            with OPENER.open(base + '/api/software-update', timeout=10) as response:
                update = json.load(response)
            if not update.get('canInstall'):
                time.sleep(.2)
                continue
            api = {'account': account, 'update': update}
            break
        except Exception:
            if helper.poll() not in (None, 0):
                raise RuntimeError('Update helper failed; inspect updater-launch.log')
            time.sleep(.5)
    assert api is not None, 'Update helper did not restart isolated TB'
    assert api['account'].get('required') and not api['account'].get('authenticated')
    assert api['update']['currentVersion'] == report['version']
    assert api['update']['canInstall'] is True
    assert (app / 'cache/updates/install-result.txt').read_text(encoding='utf-8-sig').strip() == 'ok'
    # Wait for the actual visible desktop window, then close it normally.
    literal = str(app / 'TB新版.exe').replace("'", "''")
    command = "$deadline=(Get-Date).AddSeconds(40); do { $p=Get-Process | Where-Object {$_.Path -eq '" + literal + "' -and $_.MainWindowHandle -ne 0}; if($p){break}; Start-Sleep -Milliseconds 200 } while((Get-Date) -lt $deadline); if(-not $p){throw 'Updated desktop window did not become visible'}; foreach($item in $p){if(-not $item.CloseMainWindow()){throw 'Could not close updated TB normally'}; if(-not $item.WaitForExit(20000)){throw 'TB did not exit normally'}}"
    subprocess.run(['powershell', '-NoProfile', '-Command', command], check=True, timeout=70, creationflags=subprocess.CREATE_NO_WINDOW)
    assert helper.wait(timeout=20) == 0
    assert personal_rows(app) == before
    result = {'ok': True, 'waitedForOldProcess': True, 'verifiedInstallerHash': True, 'installedAndRestarted': True,
              'visibleWindowClosedNormally': True, 'personalTablesPreserved': True, 'desktopCanInstallUpdates': True}
    args.validation_report.with_name('update-helper.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()

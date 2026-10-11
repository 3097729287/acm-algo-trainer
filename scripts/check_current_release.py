"""Fresh install and current desktop upgrade with disposable data and registry AppId."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import uuid

from check_release import ROOT, run, install, serving, snapshot, CODE


def personal_rows(app):
    with closing(sqlite3.connect(app / 'state/tb-personal.sqlite3')) as db:
        return {table: db.execute('SELECT * FROM ' + table + ' ORDER BY rowid').fetchall()
                for table in ('training', 'drafts', 'submissions', 'ranking_profile', 'contests')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--legacy-package', type=Path, required=True)
    parser.add_argument('--inno', type=Path, required=True)
    parser.add_argument('--webview2', type=Path, required=True)
    args = parser.parse_args()
    version = (ROOT / 'VERSION').read_text().strip()
    package = args.stage.resolve() / 'release' / ('TB-' + version + '-win64')
    work = ROOT / 'build' / ('release-check-current-' + uuid.uuid4().hex[:10])
    work.mkdir(parents=True)
    result = {'ok': False, 'version': version, 'work': str(work)}
    try:
        output = work / 'setup'; output.mkdir()
        run([args.inno, '/DAppId=TB.Validation.' + work.name, '/DPackageDir=' + str(package),
             '/DOutputDir=' + str(output), '/DWebViewInstaller=' + str(args.webview2),
             '/DAppVersion=' + version, ROOT / 'packaging/installer/tb.iss'], work / 'compile.log')
        setup = output / ('TB-Setup-' + version + '-win64.exe')
        fresh = work / 'fresh'
        install(setup, fresh, work / 'fresh-install.log')
        assert not (fresh / 'state').exists()
        with serving(fresh, work / 'fresh-api.json') as api:
            assert api.get('workspace')['summary']['total'] == 0
            assert api.get('software-update')['currentVersion'] == version
            assert api.get('software-update')['autoCheck'] is True
            api.post('software-update/settings', {'autoCheck': False})
        personal = fresh / 'state/tb-personal.sqlite3'
        before = hashlib.sha256(personal.read_bytes()).hexdigest()
        run([fresh / 'unins000.exe', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'], work / 'fresh-uninstall.log')
        assert personal.is_file() and hashlib.sha256(personal.read_bytes()).hexdigest() == before
        result['freshInstallAndUninstall'] = True

        upgrade = work / 'upgrade'
        # Copy only distributed files. The real installation stays read-only.
        shutil.copytree(args.legacy_package, upgrade, ignore=shutil.ignore_patterns(
            'state', 'cache', 'logs', 'backups', '*.log', 'unins*'))
        with serving(upgrade, work / 'old-api.json') as api:
            problem = next(row['id'] for row in api.catalog['rows'] if row['contest'] == '入门赛 49' and row['problem'] == 'D')
            api.post('profile', {'nickname': '隔离升级验证', 'endpoint': ''})
            api.post('training/start', {'id': problem})
            api.post('draft', {'id': problem, 'code': CODE})
            before_view = snapshot(api, problem)
        before = personal_rows(upgrade)
        marker = upgrade / 'cache/retained-preferences.txt'
        marker.parent.mkdir(exist_ok=True); marker.write_text('fixture-cache-preserved')
        install(setup, upgrade, work / 'upgrade-install.log')
        assert personal_rows(upgrade) == before, 'Installer overwrote personal tables'
        with serving(upgrade, work / 'upgraded-api.json') as api:
            assert snapshot(api, problem) == before_view, 'Upgrade changed identity, drafts, history or training'
            assert api.get('software-update')['currentVersion'] == version
            api.post('software-update/settings', {'autoCheck': False})
        with serving(upgrade, work / 'restart-api.json') as api:
            assert api.get('software-update')['autoCheck'] is False
            assert snapshot(api, problem) == before_view
        assert marker.read_text() == 'fixture-cache-preserved'
        assert personal_rows(upgrade) == before
        result.update(ok=True, upgradePreservesIdentityDraftsTraining=True, updatePreferencePersists=True,
                      generatedCachePreserved=True, personalRows={key: len(value) for key, value in before.items()})
        # Retain disposable upgraded app until updater installation is exercised.
        result['validationInstaller'] = str(setup)
        result['upgradeApp'] = str(upgrade)
    finally:
        (work / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
        print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()

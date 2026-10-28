"""Build TB from explicit frontend/backend/desktop boundaries; stage has no personal data."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
VERSION = (ROOT / 'VERSION').read_text().strip()
NAME = 'ToBe'
PACKAGE = 'ToBe-' + VERSION + '-win64'


def manifest(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob('*')) if p.is_file()}


def build(args):
    stage = args.stage.resolve()
    if (stage / 'dist').exists():
        raise RuntimeError('Use a new stage; existing builds are never overwritten')
    stage.mkdir(parents=True, exist_ok=True)
    numbers = tuple(map(int, VERSION.split('.'))) + (0,)
    version_file = stage / 'windows-version-info.txt'
    strings = {'CompanyName': 'ToBe contributors', 'FileDescription': 'ToBe',
               'FileVersion': VERSION, 'InternalName': NAME, 'OriginalFilename': NAME + '.exe',
               'ProductName': 'ToBe', 'ProductVersion': VERSION}
    entries = ','.join('StringStruct(' + repr(key) + ',' + repr(value) + ')' for key, value in strings.items())
    version_file.write_text('VSVersionInfo(ffi=FixedFileInfo(filevers=' + repr(numbers) +
                           ',prodvers=' + repr(numbers) + ',mask=0x3f,flags=0,OS=0x40004,fileType=1,subtype=0,date=(0,0)),'
                           'kids=[StringFileInfo([StringTable("040904B0",[' + entries + '])]),'
                           'VarFileInfo([VarStruct("Translation",[1033,1200])])])', encoding='utf8')
    paths = [ROOT / 'backend', ROOT / 'backend' / 'common', ROOT / 'desktop']
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--windowed',
               '--name', NAME, '--distpath', str(stage / 'dist'), '--workpath', str(stage / 'build'),
               '--specpath', str(stage), '--version-file', str(version_file), '--icon', str(ROOT / 'desktop' / 'tb.ico')]
    modules = []
    for directory in paths:
        command += ['--paths', str(directory)]
        modules += [p.stem for p in directory.glob('*.py') if not p.name.startswith('test_')]
    for name in sorted(set(modules + ['webview', 'clr'])):
        command += ['--hidden-import', name]
    subprocess.run(command + [str(ROOT / 'desktop' / 'launch.py')], cwd=ROOT, check=True)
    sources = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for directory in paths for p in directory.rglob('*') if p.is_file() and p.suffix in ('.py', '.js', '.json')}
    (stage / 'source-manifest.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding='utf-8')


def assemble(args):
    stage = args.stage.resolve()
    package = stage / 'release' / PACKAGE
    if package.exists():
        raise RuntimeError('Use a new stage; existing packages are never overwritten')
    if not args.compiler_source or not (args.compiler_source / 'ucrt64' / 'bin' / 'g++.exe').is_file():
        raise RuntimeError('--compiler-source must contain a complete ucrt64 compiler')
    if not (ROOT / 'frontend' / 'dist' / 'index.html').is_file():
        raise RuntimeError('Build the frontend before assembling')
    seed = ROOT / 'data' / 'library.sqlite3'
    source = ROOT / 'data' / 'library'
    if not seed.is_file() and source.is_dir():
        sys.path.insert(0, str(ROOT / 'backend'))
        sys.path.insert(0, str(ROOT / 'backend' / 'common'))
        from library import LibraryDatabase
        LibraryDatabase.from_source(source, seed)
    with sqlite3.connect(seed.as_uri() + '?mode=ro', uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchall():
            raise RuntimeError('Invalid bundled SQLite library')
        problems = db.execute('SELECT COUNT(*) FROM problems').fetchone()[0]
        solutions = db.execute('SELECT COUNT(*) FROM solutions').fetchone()[0]
        if problems < solutions or solutions < 607:
            raise RuntimeError('Bundled solutions are incomplete')
        for raw, in db.execute('SELECT raw FROM problems'):
            row = json.loads(raw)
            if row['状态'] != '未做' or row['日期']:
                raise RuntimeError('The distribution contains personal progress')
    shutil.copytree(stage / 'dist' / NAME, package)
    shutil.copytree(ROOT / 'frontend' / 'dist', package / 'frontend' / 'dist')
    shutil.copytree(ROOT / 'backend' / 'resources', package / 'resources')
    shutil.copytree(args.compiler_source, package / 'compiler')
    if not args.python_source or not (args.python_source / 'python.exe').is_file() or not (args.python_source / 'LICENSE.txt').is_file():
        raise RuntimeError('--python-source must contain the verified CPython embeddable runtime')
    shutil.copytree(args.python_source, package / '_internal' / 'python3')
    shutil.copytree(ROOT / 'licenses', package / 'licenses')
    (package / 'data').mkdir()
    shutil.copy2(seed, package / 'data' / 'library.sqlite3')
    shutil.copy2(ROOT / 'desktop' / 'official_languages.js', package / 'official_languages.js')
    shutil.copy2(ROOT / 'desktop' / 'official_nowcoder.js', package / 'official_nowcoder.js')
    shutil.copy2(ROOT / 'desktop' / 'official_luogu.js', package / 'official_luogu.js')
    shutil.copy2(ROOT / 'desktop' / 'official_page.js', package / 'official_page.js')
    shutil.copy2(ROOT / 'desktop' / 'official_qoj.js', package / 'resources' / 'official_qoj.js')
    # Visible Edge/Chrome submission uses the local adapter directly. No
    # browser extension, cookie transport or extension installation is bundled.
    shutil.copy2(ROOT / 'desktop' / 'tb.ico', package / 'tb.ico')
    for name in ('VERSION', 'LICENSE', 'THIRDPARTY.md', 'TOOLCHAIN-SOURCES.md', 'third-party-inventory.json'):
        shutil.copy2(ROOT / name, package / name)
    shutil.copy2(ROOT / 'docs' / 'usage.md', package / '使用说明.md')
    shutil.copy2(ROOT / 'docs' / 'accounts.md', package / 'accounts.md')
    shutil.copy2(ROOT / 'docs' / 'browser-preparation.md', package / 'browser-preparation.md')
    files = manifest(package)
    forbidden = [key for key in files if key.startswith(('state/', 'cache/', 'logs/', 'backups/'))]
    if forbidden:
        raise RuntimeError('Package contains runtime data')
    (stage / 'release-manifest.json').write_text(json.dumps(files, ensure_ascii=False, indent=2), encoding='utf-8')
    (stage / 'assembly.json').write_text(json.dumps({'version': VERSION, 'package': str(package), 'problems': problems, 'solutions': solutions, 'files': len(files)}, ensure_ascii=False, indent=2), encoding='utf-8')
    destination = stage / 'release' / (PACKAGE + '.zip')
    with zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for relative in files:
            output.write(package / relative, Path(PACKAGE) / relative)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip():
            raise RuntimeError('Corrupt portable archive')
    print(json.dumps({'package': str(package), 'zipBytes': destination.stat().st_size, 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}))


def installer(args):
    if not args.inno or not args.webview2:
        raise RuntimeError('--inno ISCC.exe and --webview2 OFFLINE.exe are required')
    subprocess.run([str(args.inno), '/DPackageDir=' + str(args.stage.resolve() / 'release' / PACKAGE),
                    '/DOutputDir=' + str(args.stage.resolve() / 'release'), '/DWebViewInstaller=' + str(args.webview2),
                    '/DAppVersion=' + VERSION, str(ROOT / 'packaging' / 'installer' / 'tb.iss')], check=True)


def admin_assemble(args):
    """Owner-only build, outside the directory uploaded to GitHub releases."""
    stage=args.stage.resolve()
    original=stage/'release'/PACKAGE
    target=stage/'private-admin'/('ToBe-Admin-'+VERSION+'-win64')
    if target.exists() or not (original/'ToBe.exe').is_file():
        raise RuntimeError('Build the user package first; use a fresh admin destination')
    original_files=manifest(original)
    if any(name.split('/')[0] in ('state','cache','logs','backups','admin-workspace') for name in original_files):
        raise RuntimeError('Only a clean distributed package may create the admin edition')
    shutil.copytree(original,target)
    (target/'ToBe.exe').rename(target/'ToBe管理员版.exe')
    for name in ('BUILD-INFO.json','resources/BUILD-INFO.json'):
        path=target/name
        if path.is_file():
            value=json.loads(path.read_text(encoding='utf8'))
            value['edition']='admin'
            path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    files=manifest(target)
    (stage/'admin-release-manifest.json').write_text(json.dumps(files,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    shutil.copy2(stage/'admin-release-manifest.json',target.parent/'ADMIN-RELEASE-MANIFEST.json')
    print(json.dumps({'adminProgram':str(target),'files':len(files),'localOnly':True,'archiveCreated':False}))


def admin_installer(args):
    if not args.inno or not args.webview2:
        raise RuntimeError('--inno and --webview2 are required')
    subprocess.run([str(args.inno),'/DAdminEdition=1',
                    '/DPackageDir='+str(args.stage.resolve()/'private-admin'/('ToBe-Admin-'+VERSION+'-win64')),
                    '/DOutputDir='+str(args.stage.resolve()/'private-admin'),'/DWebViewInstaller='+str(args.webview2),
                    '/DAppVersion='+VERSION,str(ROOT/'packaging/installer/tb.iss')],check=True)


def main():
    parser = argparse.ArgumentParser(description='Build TB without patching production sources')
    parser.add_argument('action', choices=['build', 'assemble', 'installer', 'admin-assemble', 'admin-installer'])
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--compiler-source', type=Path)
    parser.add_argument('--python-source', type=Path)
    parser.add_argument('--inno', type=Path)
    parser.add_argument('--webview2', type=Path)
    args = parser.parse_args()
    globals()[args.action.replace('-','_')](args)


if __name__ == '__main__':
    main()

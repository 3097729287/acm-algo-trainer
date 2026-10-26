"""Verified file delta, applied by a copied helper after the desktop exits."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
import zipfile

from app_brand import executable

ROOT_FILES = {'ToBe.exe', 'TB新版.exe', 'VERSION', 'BUILD-INFO.json', 'SOURCE-MANIFEST.json', 'tb.ico', 'official_languages.js', 'official_nowcoder.js', 'official_luogu.js', 'official_page.js', 'LICENSE', 'THIRDPARTY.md', 'TOOLCHAIN-SOURCES.md', 'third-party-inventory.json', '使用说明.md', 'accounts.md', 'browser-preparation.md'}
PREFIXES = ('_internal/', 'frontend/dist/', 'resources/', 'browser-extension/', 'licenses/')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_name(name):
    if not isinstance(name, str) or '\\' in name or ':' in name or any(part in ('', '.', '..') or part.endswith((' ', '.')) for part in name.split('/')):
        raise ValueError('更新文件路径无效')
    if PurePosixPath(name).is_absolute() or not (name in ROOT_FILES or name.startswith(PREFIXES) or name == 'data/library.sqlite3'):
        raise ValueError('更新包试图修改程序以外的文件')
    if any(re.fullmatch(r'(?i)(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part) for part in name.split('/')):
        raise ValueError('更新路径包含 Windows 保留名称')
    return name


def inspect_patch(archive, app_dir, version):
    """Validate every path and byte before touching the installation."""
    app_dir = Path(app_dir).resolve()
    if len(archive.infolist()) > 20000 or sum(item.file_size for item in archive.infolist()) > 1024**3:
        raise ValueError('增量更新包体积无效')
    if archive.getinfo('update.json').file_size > 10*1024*1024:
        raise ValueError('增量清单体积无效')
    manifest = json.loads(archive.read('update.json'))
    if manifest.get('schema') != 1 or manifest.get('version') != version or (app_dir / 'VERSION').read_text().strip() != manifest.get('fromVersion'):
        raise ValueError('增量更新与当前版本不匹配')
    files, base, changed = manifest['files'], manifest['base'], manifest['changed']
    if not isinstance(files, dict) or not isinstance(base, dict) or not isinstance(changed, list):
        raise ValueError('增量清单无效')
    if any(not isinstance(sha,str) or not re.fullmatch(r'[a-f0-9]{64}',sha) for sha in list(files.values())+list(base.values())):
        raise ValueError('增量文件 SHA-256 格式无效')
    names = set(files) | set(base)
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError('更新文件重名')
    for name in names:
        safe_name(name)
        target = (app_dir / name).resolve()
        if not target.is_relative_to(app_dir) or target.relative_to(app_dir).as_posix().casefold() != name.casefold() or any((app_dir / Path(*PurePosixPath(name).parts[:i])).is_symlink() for i in range(1, len(PurePosixPath(name).parts)+1)):
            raise ValueError('更新路径离开了程序目录')
    expected = sorted(name for name in files if files[name] != base.get(name))
    if sorted(changed) != expected or len(changed) != len(set(changed)):
        raise ValueError('增量文件清单不完整')
    entries = [item.filename for item in archive.infolist()]
    if len(set(entries)) != len(entries) or set(entries) != {'update.json'} | {'files/' + name for name in changed}:
        raise ValueError('增量包包含未声明文件')
    for name, sha in base.items():
        if not (app_dir / name).is_file() or digest(app_dir / name) != sha:
            raise ValueError('当前程序文件已变化，请使用安装版修复后重试：' + name)
    for name in changed:
        if hashlib.sha256(archive.read('files/' + name)).hexdigest() != files[name]:
            raise ValueError('增量文件校验失败：' + name)
    if 'VERSION' not in changed or archive.read('files/VERSION').decode().strip() != version:
        raise ValueError('更新版本文件不一致')
    return manifest


def apply_patch_file(package, sha, version, app_dir, *, fail_after=None):
    package, app_dir = Path(package), Path(app_dir).resolve()
    if digest(package) != sha:
        raise ValueError('增量包 SHA-256 不匹配')
    with zipfile.ZipFile(package) as archive:
        manifest = inspect_patch(archive, app_dir, version)
        recovery = package.parent / ('rollback-' + uuid.uuid4().hex)
        recovery.mkdir()
        touched = manifest['changed'] + sorted(set(manifest['base']) - set(manifest['files']))
        existing = set()
        for name in touched:
            path = app_dir / name
            if path.exists():
                existing.add(name)
                backup = recovery / name
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup)
        journal = {'target': str(app_dir), 'existing': sorted(existing), 'touched': touched}
        (recovery / 'recovery.json').write_text(json.dumps(journal, ensure_ascii=False), encoding='utf-8')
        try:
            # VERSION changes last so a half-written update is never reported as done.
            order = sorted(manifest['changed'], key=lambda name: name == 'VERSION')
            for index, name in enumerate(order):
                path = app_dir / name
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_name(path.name + '.tb-update')
                temporary.write_bytes(archive.read('files/' + name))
                os.replace(temporary, path)
                if fail_after is not None and index >= fail_after:
                    raise OSError('isolated replacement failure')
            for name in set(manifest['base']) - set(manifest['files']):
                (app_dir / name).unlink()
            for name, sha in manifest['files'].items():
                if digest(app_dir / name) != sha:
                    raise ValueError('更新后的程序未通过校验：' + name)
        except Exception:
            for name in touched:
                path = app_dir / name
                if name in existing:
                    shutil.copy2(recovery / name, path)
                else:
                    path.unlink(missing_ok=True)
                path.with_name(path.name + '.tb-update').unlink(missing_ok=True)
            raise
        (recovery / 'complete').write_text(version)
        return {'version': version, 'replaced': len(manifest['changed']), 'recovery': str(recovery)}


def launch_patch(package, sha, version, app_dir):
    """Copy the helper/runtime so its own loaded DLLs do not lock the target."""
    package, app_dir = Path(package).resolve(), Path(app_dir).resolve()
    with zipfile.ZipFile(package) as archive:
        inspect_patch(archive, app_dir, version)
    helper = package.parent / ('helper-' + uuid.uuid4().hex)
    helper.mkdir()
    helper_exe = helper / executable(app_dir).name
    shutil.copy2(executable(app_dir), helper_exe)
    shutil.copytree(app_dir / '_internal', helper / '_internal')
    return subprocess.Popen([str(helper_exe), '--apply-update-patch', str(package), sha, version, str(app_dir), str(os.getpid())],
                            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def helper_main(args):
    package, sha, version, target, parent = args
    log = Path(package).parent / 'install-result.txt'
    try:
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x00100000, False, int(parent))
        if handle:
            try:
                if kernel.WaitForSingleObject(handle, 180000) != 0:
                    raise RuntimeError('ToBe 未正常关闭，已取消更新')
            finally:
                kernel.CloseHandle(handle)
        apply_patch_file(package, sha, version, target)
        log.write_text('ok', encoding='utf-8')
        command = [str(executable(target))]
        if os.environ.get('TB_OFFLINE') == '1' and os.environ.get('TB_UPDATE_TEST_REPORT'):
            command += ['--serve-check', os.environ['TB_UPDATE_TEST_REPORT']]
        subprocess.Popen(command, cwd=target)
        return 0
    except Exception as error:
        log.write_text(str(error), encoding='utf-8')
        ctypes.windll.user32.MessageBoxW(None, 'ToBe 更新未完成，个人数据保留，恢复文件位于更新缓存。\n' + str(error), 'ToBe 更新', 0x10)
        return 1

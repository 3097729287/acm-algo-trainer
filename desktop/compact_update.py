"""Reconstruct a verified program before replacing files; preserve private state.

This module is also packaged as a standard-library-only installer zipapp.
Personal databases, browser profiles and user imports are outside its allowlist.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import tempfile
import uuid
import zipfile

from binary_delta import file_delta

ROOT_FILES={'ToBe.exe','ToBeLoader.exe','TB新版.exe','VERSION','BUILD-INFO.json','SOURCE-MANIFEST.json','tb.ico','official_languages.js','official_nowcoder.js','official_luogu.js','official_page.js','LICENSE','THIRDPARTY.md','TOOLCHAIN-SOURCES.md','third-party-inventory.json','使用说明.md','accounts.md','browser-preparation.md'}
PREFIXES=('_internal/','frontend/dist/','resources/','browser-extension/','licenses/','compiler/')
MAX_OUTPUT=2*1024**3
MAX_CACHE=8*1024**3


class BaseMismatch(ValueError):pass


def sha(path):
    with Path(path).open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()


def valid_sha(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value)


def public_path(root,name):
    if not isinstance(name,str) or '\\' in name or ':' in name or name not in ROOT_FILES and name!='data/library.sqlite3' and not name.startswith(PREFIXES):raise ValueError('更新路径不属于程序文件')
    parts=name.split('/')
    if any(p in ('','.','..') or p.endswith((' ','.')) or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?',p) for p in parts) or PurePosixPath(name).is_absolute():raise ValueError('更新文件路径无效')
    path=root.joinpath(*parts)
    for item in [root,*[root.joinpath(*parts[:i]) for i in range(1,len(parts)+1)]]:
        if item.exists() and (item.is_symlink() or getattr(item.lstat(),'st_file_attributes',0)&0x400):raise ValueError('更新文件路径包含重定向')
    if not path.resolve().is_relative_to(root):raise ValueError('更新路径离开程序目录')
    return path


def document(path,value):
    temporary=path.with_name(path.name+'.tmp')
    with temporary.open('w',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,sort_keys=True);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def load(archive,version):
    entries=archive.infolist()
    if len(entries)>20000 or sum(e.file_size for e in entries)>512*1024**2 or archive.getinfo('compact.json').file_size>8*1024**2:raise ValueError('紧凑更新清单过大')
    value=json.loads(archive.read('compact.json'))
    if not isinstance(value,dict) or value.get('schema')!=1 or value.get('version')!=version or not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('紧凑更新版本无效')
    files,payloads,anchors=value.get('files'),value.get('payloads'),value.get('anchors')
    if not isinstance(files,dict) or 'VERSION' not in files or len(files)>15000 or not isinstance(payloads,dict) or not isinstance(anchors,dict) or not anchors:raise ValueError('紧凑更新清单无效')
    names=[e.filename for e in entries]
    if len(names)!=len(set(names)) or set(names)!={'compact.json',*payloads}:raise ValueError('紧凑更新包含未声明文件')
    if len({name.casefold() for name in files})!=len(files):raise ValueError('紧凑更新路径重名')
    total=0
    for entry in files.values():
        if not isinstance(entry,dict) or not valid_sha(entry.get('sha256')) or type(entry.get('bytes')) is not int or not 0<=entry['bytes']<=MAX_OUTPUT or not isinstance(entry.get('variants'),list):raise ValueError('紧凑更新文件描述无效')
        if type(entry.get('unchanged',False)) is not bool or entry.get('unchanged') and entry['variants']:raise ValueError('未变更文件描述无效')
        total+=entry['bytes']
        for variant in entry['variants']:
            if not isinstance(variant,dict) or variant.get('payload') not in payloads or variant.get('format') not in {'literal','binary'}:raise ValueError('紧凑更新差分描述无效')
            if variant['format']=='binary' and (not isinstance(variant.get('source'),str) or not valid_sha(variant.get('sourceSha256'))):raise ValueError('紧凑更新基线描述无效')
    if total>6*1024**3:raise ValueError('紧凑更新输出过大')
    for name,entry in payloads.items():
        if not re.fullmatch(r'payloads/[a-f0-9]{64}\.bin',name) or not isinstance(entry,dict) or not valid_sha(entry.get('sha256')) or type(entry.get('bytes')) is not int or not 0<=entry['bytes']<=64*1024**2 or archive.getinfo(name).file_size!=entry['bytes']:raise ValueError('紧凑更新数据块无效')
    for values in anchors.values():
        if not isinstance(values,list) or not values or not all(valid_sha(v) for v in values):raise ValueError('紧凑更新程序基线无效')
    return value


def select(root,value):
    hashes={}
    def current(name):
        if name not in hashes:
            path=public_path(root,name);hashes[name]=sha(path) if path.is_file() else None
        return hashes[name]
    for name,values in value['anchors'].items():
        if current(name) not in values:raise BaseMismatch('当前程序需要使用完整安装包修复：'+name)
    result={}
    for name,entry in value['files'].items():
        public_path(root,name)
        # These exact bytes are common to every approved baseline. They are
        # neither read, copied nor replaced; the builder and full upgrade
        # rehearsal verify their inventory. Runtime anchors are checked above.
        if entry.get('unchanged'):continue
        if current(name)==entry['sha256']:continue
        variant=next((v for v in entry['variants'] if v['format']=='binary' and current(v['source'])==v['sourceSha256']),None)
        if variant is None:variant=next((v for v in entry['variants'] if v['format']=='literal'),None)
        if variant is None:raise BaseMismatch('缺少匹配的程序差分：'+name)
        result[name]=variant
    return result,hashes


@contextmanager
def exclusive(path):
    if path.exists() and (path.is_symlink() or getattr(path.lstat(),'st_file_attributes',0)&0x400):raise ValueError('更新锁路径无效')
    with path.open('a+b') as stream:
        if not path.stat().st_size:stream.write(b'\0');stream.flush()
        stream.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def restore(root,folder,journal):
    for name in sorted(journal['previous'],key=lambda n:n=='VERSION'):
        previous=journal['previous'][name]
        target=public_path(root,name);saved=folder/'old'/name
        if previous is None:
            if target.exists():
                if sha(target)!=journal['new'][name]:raise ValueError('更新中途程序文件另有改动，已保留现场')
                target.unlink()
        else:
            if not saved.is_file() or sha(saved)!=previous:raise ValueError('更新恢复文件未通过校验')
            if target.exists() and sha(target) not in {previous,journal['new'][name]}:raise ValueError('更新中途程序文件另有改动，已保留现场')
            temporary=target.with_name(target.name+'.compact-restore-'+uuid.uuid4().hex)
            try:os.link(saved,temporary)
            except OSError:shutil.copyfile(saved,temporary)
            os.replace(temporary,target)
    document(folder/'journal.json',{**journal,'status':'rolled-back'})


def recycle_recovery(path):
    from system_recycle import recycle
    return recycle(path)


def trim_recoveries(app,cache):
    verified=[]
    for folder in cache.glob('compact-*'):
        try:
            if not folder.is_dir() or folder.is_symlink() or getattr(folder.lstat(),'st_file_attributes',0)&0x400:continue
            for path in folder.rglob('*'):
                if path.is_symlink() or getattr(path.lstat(),'st_file_attributes',0)&0x400:raise ValueError('Redirected recovery retained')
            journal=json.loads((folder/'journal.json').read_text(encoding='utf-8'))
            if journal.get('status')!='complete' or not isinstance(journal.get('previous'),dict):continue
            expected={'journal.json'}
            for name,checksum in journal['previous'].items():
                public_path(app,name)
                if checksum is None:continue
                if not valid_sha(checksum) or sha(folder/'old'/name)!=checksum:raise ValueError('Changed recovery retained')
                expected.add('old/'+name)
            for path in folder.rglob('*'):
                if not path.is_file():continue
                name=path.relative_to(folder).as_posix()
                if name in expected:continue
                match=re.fullmatch(r'payloads/([a-f0-9]{64})\.bin',name)
                if match is None or sha(path)!=match[1]:raise ValueError('Unknown recovery file retained')
            verified.append(folder)
        except (OSError,ValueError,KeyError,TypeError):continue
    for folder in sorted(verified,key=lambda p:(p/'journal.json').stat().st_mtime_ns)[:-2]:
        if folder.resolve().parent==cache:recycle_recovery(folder)


def apply(bundle,app,version,*,check=False,fail_after=None):
    app=Path(app).resolve(strict=True);bundle=Path(bundle).resolve(strict=True)
    if not (app/'VERSION').is_file():raise BaseMismatch('此目录不是现有 ToBe 安装')
    cache=app/'cache/updates'
    for path in [app/'cache',cache]:
        if path.exists() and (path.is_symlink() or getattr(path.lstat(),'st_file_attributes',0)&0x400):raise ValueError('更新缓存路径无效')
    cache.mkdir(parents=True,exist_ok=True)
    if not cache.resolve().is_relative_to(app) or any(p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400 for p in [app/'cache',cache]):raise ValueError('更新缓存路径无效')
    with exclusive(cache/'compact-update.lock'),zipfile.ZipFile(bundle) as archive:
        active=cache/'compact-active.json'
        if active.exists():
            old=json.loads(active.read_text(encoding='utf-8'));folder=Path(old['folder']).resolve()
            if folder.parent!=cache or not folder.name.startswith('compact-') or folder.is_symlink() or getattr(folder.lstat(),'st_file_attributes',0)&0x400:raise ValueError('更新恢复路径无效')
            journal=json.loads((folder/'journal.json').read_text(encoding='utf-8'))
            if journal['status']=='applying':
                if check:raise BaseMismatch('上次更新需要恢复后重试')
                restore(app,folder,journal)
        value=load(archive,version);selected,hashes=select(app,value)
        if check:return {'compatible':True,'changedFiles':len(selected),'version':version}
        if not selected:return {'ok':True,'version':version,'changedFiles':0,'privateStateChanged':False}
        # A manually launched bridge must stop before replacing any file when
        # the existing Windows application still maps this executable.
        with public_path(app,'ToBe.exe').open('r+b'):pass
        needed=sum(value['files'][name]['bytes']+(public_path(app,name).stat().st_size if public_path(app,name).is_file() else 0) for name in selected)
        needed+=max((public_path(app,name).stat().st_size for name in selected if public_path(app,name).is_file()),default=0)
        occupied=sum(p.stat().st_size for d in cache.glob('compact-*') if d.is_dir() and not d.is_symlink() for p in d.rglob('*') if p.is_file() and not p.is_symlink())
        if occupied+needed>MAX_CACHE or shutil.disk_usage(cache).free<needed+256*1024**2:raise ValueError('更新空间不足，原程序已保留')
        folder=Path(tempfile.mkdtemp(prefix='compact-',dir=cache));data=folder/'payloads';data.mkdir()
        journal={'status':'preparing','version':version,'previous':{},'new':{name:value['files'][name]['sha256'] for name in selected}}
        for name,variant in selected.items():
            entry=value['files'][name];payload=value['payloads'][variant['payload']];raw=archive.read(variant['payload'])
            if hashlib.sha256(raw).hexdigest()!=payload['sha256']:raise ValueError('紧凑更新数据块校验失败')
            target=folder/'new'/name;target.parent.mkdir(parents=True,exist_ok=True)
            if variant['format']=='literal':target.write_bytes(raw)
            else:
                source=public_path(app,variant['source']);patch=data/Path(variant['payload']).name
                if not patch.exists():patch.write_bytes(raw)
                file_delta(source,patch,target,expected_target=entry['sha256'])
            if target.stat().st_size!=entry['bytes'] or sha(target)!=entry['sha256']:raise ValueError('紧凑更新重建文件未通过校验')
            original=public_path(app,name);previous=sha(original) if original.is_file() else None
            if previous!=hashes[name]:raise ValueError('准备更新时程序文件发生变化，已停止替换')
            journal['previous'][name]=previous
            if previous is not None:
                saved=folder/'old'/name;saved.parent.mkdir(parents=True,exist_ok=True)
                try:os.link(original,saved)
                except OSError:shutil.copyfile(original,saved)
                if sha(saved)!=previous:raise ValueError('紧凑更新恢复副本未通过校验')
        journal['status']='applying';document(folder/'journal.json',journal);document(active,{'folder':str(folder)})
        try:
            for index,name in enumerate(sorted(selected,key=lambda n:n=='VERSION')):
                if name=='VERSION':
                    for other,entry in value['files'].items():
                        if other!='VERSION' and not entry.get('unchanged') and sha(public_path(app,other))!=entry['sha256']:raise ValueError('替换后的程序文件未通过校验')
                target=public_path(app,name);target.parent.mkdir(parents=True,exist_ok=True);os.replace(folder/'new'/name,target)
                if fail_after is not None and index>=fail_after:raise OSError('isolated compact update failure')
            for name,entry in value['files'].items():
                if not entry.get('unchanged') and sha(public_path(app,name))!=entry['sha256']:raise ValueError('完整程序未通过校验')
            if (app/'VERSION').read_text(encoding='utf-8').strip()!=version:raise ValueError('安装版本不一致')
            document(folder/'journal.json',{**journal,'status':'complete'})
        except Exception:
            restore(app,folder,journal);raise
        try:trim_recoveries(app,cache)
        except (OSError,ValueError):pass  # A retained old recovery does not undo a completed install.
        return {'ok':True,'version':version,'changedFiles':len(selected),'recovery':str(folder),'privateStateChanged':False}


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--app',type=Path,required=True);p.add_argument('--version',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    try:print(json.dumps(apply(a.bundle,a.app,a.version,check=a.check)));return 0
    except BaseMismatch as error:print(str(error));return 3
    except Exception as error:print(str(error));return 1


def launch_bundle(package,expected_sha,version,app):
    """Copy the verified frozen runner so the installed EXE can be replaced."""
    import subprocess
    from update_artifacts import prepare_tree,record_process
    package,app=Path(package).resolve(),Path(app).resolve()
    if sha(package)!=expected_sha:raise ValueError('紧凑更新包摘要不匹配')
    with zipfile.ZipFile(package) as archive:
        value=load(archive,version);select(app,value)
    names=[name for name in value['anchors'] if name=='ToBe.exe' or name.startswith('_internal/')]
    if 'ToBe.exe' not in names or not any(name.endswith('/base_library.zip') for name in names):raise ValueError('紧凑更新缺少受信任的运行器')
    specs={}
    for name in names:
        path=public_path(app,name);actual=sha(path)
        if actual not in value['anchors'][name]:raise BaseMismatch('更新运行器文件已变化：'+name)
        specs[name]=(path,actual)
    helper=prepare_tree(package.parent,'helper',str(app)+':'+expected_sha,specs)
    executable=helper/'ToBe.exe'
    child=subprocess.Popen([str(executable),'--apply-compact-update',str(package),expected_sha,version,str(app),str(os.getpid())],creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:record_process(helper,child.pid,executable)
    except Exception:child.terminate();child.wait(timeout=5);raise
    return child


def helper_main(args):
    import ctypes
    from ctypes import wintypes
    import subprocess
    package,expected_sha,version,target,parent=args
    log=Path(package).parent/'install-result.txt'
    try:
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        handle=kernel.OpenProcess(0x00100000,False,int(parent))
        if handle:
            try:
                if kernel.WaitForSingleObject(handle,180000)!=0:raise RuntimeError('ToBe 未正常关闭，已取消更新')
            finally:kernel.CloseHandle(handle)
        if sha(package)!=expected_sha:raise ValueError('紧凑更新包摘要不匹配')
        apply(package,target,version)
        executable=Path(target)/'ToBe.exe'
        subprocess.run([str(executable),'--prepare-startup'],cwd=target,check=True,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
        log.write_text('ok',encoding='utf-8')
        command=[str(executable)]
        if os.environ.get('TB_OFFLINE')=='1' and os.environ.get('TB_UPDATE_TEST_REPORT'):command+=['--serve-check',os.environ['TB_UPDATE_TEST_REPORT']]
        subprocess.Popen(command,cwd=target)
        return 0
    except Exception as error:
        log.write_text(str(error),encoding='utf-8')
        ctypes.windll.user32.MessageBoxW(None,'ToBe 更新未完成，个人数据与恢复副本已保留。\n'+str(error),'ToBe 更新',0x10)
        return 1


if __name__=='__main__':raise SystemExit(main())

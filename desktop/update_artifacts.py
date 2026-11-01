"""Bound and reuse updater-owned helper/runtime and program rollback copies."""
import hashlib
import os
from pathlib import Path,PurePosixPath
import shutil
import time

from persistence import load_document,save_document
from update_backups import files,ordinary,require_space,retire_directory,digest
from update_errors import UpdateStorageError

MAX_BYTES=8*1024**3
META='.artifact-proof/manifest.json'
META_DB='.artifact-proof/tb-documents.sqlite3'

def _read(path):
    proof=path/'.artifact-proof';database=path/META_DB
    if not path.is_dir() or not ordinary(path) or not proof.is_dir() or not ordinary(proof) or not database.is_file() or not ordinary(database):return {}
    return load_document(path/META,{})

def _active(value):
    pid=value.get('pid')
    if type(pid) is not int or pid<=0:return False
    if os.name!='nt':
        try:os.kill(pid,0);return True
        except OSError:return False
    import ctypes
    from ctypes import wintypes as w
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];kernel.OpenProcess.restype=w.HANDLE
    kernel.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];kernel.CloseHandle.argtypes=[w.HANDLE]
    handle=kernel.OpenProcess(0x100000|0x1000,False,pid)
    if not handle:return ctypes.get_last_error()==5
    try:
        if kernel.WaitForSingleObject(handle,0)!=258:return False
        name=ctypes.create_unicode_buffer(32768);size=w.DWORD(len(name))
        kernel.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
        return not kernel.QueryFullProcessImageNameW(handle,0,name,ctypes.byref(size)) or Path(name.value).resolve()==Path(value.get('exe','')).resolve()
    finally:kernel.CloseHandle(handle)

def _owned(root,kind):
    if not root.exists():return []
    result=[]
    for path in root.iterdir():
        if not path.name.startswith(kind+'-v1-') or not path.is_dir() or not ordinary(path):continue
        if not (path/'.artifact-proof').is_dir() or not ordinary(path/'.artifact-proof'):continue
        value=_read(path)
        if value.get('schema')==1 and value.get('kind')==kind and isinstance(value.get('files'),dict):result.append((path,value))
    return sorted(result,key=lambda pair:pair[1].get('createdAt',0))

def _valid(path,value):
    if not value.get('sealed'):return False
    for directory,children,names in os.walk(path,followlinks=False):
        if any(not ordinary(Path(directory)/name) for name in children+names):return False
    for name,sha in value['files'].items():
        if not isinstance(name,str) or '\\' in name or ':' in name or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:return False
        target=path/name
        if not target.is_file() or not target.resolve().is_relative_to(path.resolve()) or digest(target)!=sha:return False
    return {p.relative_to(path).as_posix() for p in files(path)}<=set(value['files'])|{META_DB}

def _trim(root,kind):
    valid=[(path,value) for path,value in _owned(root,kind) if _valid(path,value)]
    for path,value in valid[:-2]:
        if not _active(value):retire_directory(path)

def prepare_tree(root,kind,context,specs,*,staging_bytes=0):
    """Specs map relative names to (immutable source Path or bytes, SHA-256)."""
    assert kind in {'helper','rollback'}
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(context.encode('utf-8')).hexdigest()[:32]
    target=root/(kind+'-v1-'+key)
    expected={name:sha for name,(_,sha) in specs.items()}
    require_space(root,staging_bytes)
    if target.exists():
        value=_read(target)
        if _active(value):raise UpdateStorageError('更新辅助进程仍在运行，已暂停准备')
        if value.get('context')==context and value.get('files')==expected and _valid(target,value):return target
        raise UpdateStorageError('更新辅助文件未完成校验，已保留原文件并暂停准备')
    _trim(root,kind)
    if len(_owned(root,kind))>=3:raise UpdateStorageError('更新辅助文件已达保留上限，已暂停准备')
    occupied=sum(sum(p.stat().st_size for p in files(path)) for path in root.iterdir() if path.is_dir() and ordinary(path) and path.name.startswith(('helper-','rollback-')))
    needed=sum(len(source) if isinstance(source,bytes) else source.stat().st_size for source,_ in specs.values())+1024**2
    if occupied+needed>MAX_BYTES:raise UpdateStorageError('更新辅助文件总量已达上限，已停止复制')
    require_space(root,needed+staging_bytes)
    for name in specs:
        parts=PurePosixPath(name).parts
        if not name or '\\' in name or ':' in name or PurePosixPath(name).is_absolute() or '..' in parts or parts[0]=='.artifact-proof':raise ValueError('更新辅助文件路径无效')
    target.mkdir(exist_ok=False)
    value={'schema':1,'kind':kind,'context':context,'files':{},'sealed':False,'createdAt':time.time()}
    save_document(target/META,value)
    for name,(source,sha) in specs.items():
        require_space(root,staging_bytes)
        destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
        if isinstance(source,bytes):destination.write_bytes(source)
        else:
            if not ordinary(source) or digest(source)!=sha:raise ValueError('更新辅助源文件校验失败')
            shutil.copy2(source,destination)
        if digest(destination)!=sha:raise ValueError('更新辅助副本校验失败')
    value.update(files=expected,sealed=True);save_document(target/META,value);_trim(root,kind)
    return target

def record_process(tree,pid,exe):
    value=_read(tree)
    if type(pid) is not int or pid<=0:raise ValueError('更新辅助进程无效')
    if not _valid(tree,value):raise ValueError('更新辅助文件已变化')
    value.update(pid=pid,exe=str(exe));save_document(tree/META,value)

def record_file(tree,name):
    value=_read(tree)
    if value.get('schema')!=1 or not value.get('sealed'):raise ValueError('更新恢复清单无效')
    value['files'][name]=digest(tree/name);save_document(tree/META,value)

"""Bound update recovery writes; reuse exact snapshots and never delete legacy copies."""
from contextlib import closing
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import threading

from persistence import load_document,save_document
from update_errors import UpdateStorageError

LOCK=threading.RLock()
MAX_BYTES=8*1024**3
RESERVE=256*1024**2
META='.update-proof/manifest.json'

def ordinary(path):
    return not path.is_symlink() and not (getattr(path.lstat(),'st_file_attributes',0)&0x400)

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def files(root):
    for directory,children,names in os.walk(root,followlinks=False):
        children[:]=[name for name in children if ordinary(Path(directory)/name)]
        for name in names:
            path=Path(directory)/name
            if ordinary(path):yield path

def sources(state):
    result=[]
    for directory,children,names in os.walk(state,followlinks=False):
        children[:]=[name for name in children if name.casefold() not in {'backup','backups'} and ordinary(Path(directory)/name)]
        for name in names:
            path=Path(directory)/name
            if name.casefold().endswith('.sqlite3') and ordinary(path):result.append(path)
    return sorted(result)

def fingerprints(paths,state):
    result={}
    for path in paths:
        result[path.relative_to(state).as_posix()]=digest(path)
        wal=path.with_name(path.name+'-wal')
        if wal.is_file():result[wal.relative_to(state).as_posix()]=digest(wal)
    return result

def require_space(path,needed):
    path=Path(path)
    while not path.exists():path=path.parent
    if shutil.disk_usage(path).free<needed+RESERVE:
        raise UpdateStorageError('磁盘空间不足，更新已暂停，未继续创建备份或下载文件')

def update_backup_bytes(root):
    if not root.exists():return 0
    return sum((sum(p.stat().st_size for p in files(path)) if path.is_dir() else path.stat().st_size)
               for path in root.iterdir() if path.name.casefold().startswith('before-update-') and ordinary(path))

def _owned(root):
    result=[]
    if not root.exists():return result
    for path in root.iterdir():
        if not path.is_dir() or not path.name.startswith('before-update-') or not ordinary(path):continue
        proof=path/'.update-proof'
        if not proof.is_dir() or not ordinary(proof):continue
        metadata=proof/'tb-documents.sqlite3'
        if not metadata.is_file() or not ordinary(metadata):continue
        value=load_document(path/META,{})
        if value.get('schema')==1 and value.get('kind')=='software-update' and isinstance(value.get('files'),dict):result.append((path,value))
    return sorted(result,key=lambda pair:pair[1].get('createdAt',''))

def _valid(path,value):
    if not value.get('complete'):return False
    # An unrecorded junction must not make an owned backup eligible for removal.
    for directory,children,names in os.walk(path,followlinks=False):
        if any(not ordinary(Path(directory)/name) for name in children+names):return False
    for name,sha in value['files'].items():
        if not isinstance(name,str) or '\\' in name or Path(name).is_absolute() or '..' in Path(name).parts:return False
        target=path/name
        if not target.is_file() or not ordinary(target) or not target.resolve().is_relative_to(path.resolve()) or digest(target)!=sha:return False
    expected=set(value['files'])|{'.update-proof/tb-documents.sqlite3'}
    return {p.relative_to(path).as_posix() for p in files(path)}<=expected

def recycle_directory(path):
    from system_recycle import recycle
    return recycle(path)

def retire_directory(path):
    """Only called for old, verified updater-owned copies; keep two recoveries."""
    return recycle_directory(path)

def _trim(root):
    owned=_owned(root)
    valid=[(path,value) for path,value in owned if _valid(path,value)]
    # Keep two fully verified recovery generations. Unknown/legacy/partial
    # folders stay intact; inability to remove stops further accumulation.
    for path,value in valid[:-2]:
        if not path.resolve().is_relative_to(root.resolve()):continue
        retire_directory(path)

def backup(state,destination,*,context=None):
    state=Path(state).resolve();destination=Path(destination).absolute();root=destination.parent
    if destination.exists() or destination.is_symlink():raise ValueError('备份目标已存在，原文件保留')
    if root.resolve()!=state/'backups' or not destination.name.startswith('before-update-'):raise ValueError('更新备份路径无效')
    with LOCK:
        paths=sources(state);signature=fingerprints(paths,state)
        for path,value in _owned(root):
            if value.get('context')==context and value.get('sources')==signature and _valid(path,value):
                require_space(state,0)
                return path
        _trim(root)
        if len(_owned(root))>=3:raise UpdateStorageError('更新备份已达保留上限，原备份已保留，更新已暂停')
        estimated=sum(p.stat().st_size for p in paths)+sum(p.with_name(p.name+'-wal').stat().st_size for p in paths if p.with_name(p.name+'-wal').is_file())+1024**2
        occupied=update_backup_bytes(root)
        if estimated>MAX_BYTES or occupied+estimated>MAX_BYTES:raise UpdateStorageError('更新备份总量已达上限，原备份已保留，未继续复制')
        require_space(state,estimated)
        destination.mkdir(parents=True,exist_ok=False)
        value={'schema':1,'kind':'software-update','context':context,'sources':signature,'files':{},'complete':False,'createdAt':dt.datetime.now(dt.timezone.utc).isoformat()}
        save_document(destination/META,value)
        for source in paths:
            relative=source.relative_to(state);target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
            with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(target)) as dst:
                page_size=src.execute('PRAGMA page_size').fetchone()[0]
                completed=sum((destination/name).stat().st_size for name in value['files'])
                def progress(_status,_remaining,total):
                    if occupied+completed+total*page_size+1024**2>MAX_BYTES:raise UpdateStorageError('备份大小超过限制，已停止复制，原数据库保留')
                    require_space(destination,0)
                src.backup(dst,pages=128,progress=progress)
                if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('个人数据库备份未通过校验，已停止更新')
            value['files'][relative.as_posix()]=digest(target)
            save_document(destination/META,value)
        # A concurrent account write keeps this valid recovery point but stops
        # it being reused as if it contained later edits.
        value['complete']=True;value['reusable']=signature==fingerprints(paths,state)
        if not value['reusable']:value['sources']={}
        save_document(destination/META,value);_trim(root)
        return destination

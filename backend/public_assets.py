"""Immutable public learning resources, downloaded once into a separate SQLite cache."""
from contextlib import closing
import hashlib
import os
from pathlib import Path
import re
import shutil
import sqlite3
import threading
from urllib.parse import urlsplit
from urllib.request import Request

MAX_ASSET=32*1024*1024
PUBLIC_COMMIT='a4de0d4b160e1d2270422b8c84995feffc4e3269'
PUBLIC_ROOT='https://raw.githubusercontent.com/3097729287/acm-algo-trainer/'+PUBLIC_COMMIT+'/'
_locks=[threading.Lock() for _ in range(32)]

def descriptor(db,sha):
    if not re.fullmatch('[a-f0-9]{64}',sha):raise ValueError('Invalid public asset identity')
    exists=db.execute("SELECT 1 FROM sqlite_master WHERE name='remote_statement_assets'").fetchone()
    row=db.execute('SELECT mime,bytes,url FROM remote_statement_assets WHERE sha256=?',(sha,)).fetchone() if exists else None
    return dict(row) if row is not None else None

def validate_reference(sha,mime,size,url):
    if not re.fullmatch('[a-f0-9]{64}',sha) or mime not in {'application/pdf','image/png','image/jpeg','image/webp','image/gif','image/bmp','application/zip'}:raise ValueError('Invalid public asset metadata')
    parsed=urlsplit(url)
    direct=url==PUBLIC_ROOT+sha+'.bin'
    loopback=parsed.hostname in {'127.0.0.1','localhost','::1'}
    if (not isinstance(size,int) or not 0<size<=MAX_ASSET or parsed.username or parsed.password or parsed.query or parsed.fragment
        or parsed.scheme!='https' and not(loopback and parsed.scheme=='http') or not direct and parsed.path!='/updates/library-assets/'+sha+'.bin'):
        raise ValueError('Invalid public asset location')
    if not loopback and not direct:
        from leaderboard import bundled_endpoint
        if parsed.hostname!=urlsplit(bundled_endpoint()).hostname or parsed.port not in (None,443):raise ValueError('Untrusted public asset host')

def read_asset(library,sha,cache_path=None):
    from paths import STATE
    with library.connection() as db:
        row=db.execute('SELECT mime,data FROM statement_assets WHERE sha256=?',(sha,)).fetchone()
        if row is not None:
            raw=bytes(row['data'])
            if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Public asset checksum mismatch')
            return row['mime'],raw
        value=descriptor(db,sha)
    if value is None:raise FileNotFoundError('Public asset is unavailable')
    validate_reference(sha,value['mime'],value['bytes'],value['url'])
    cache_path=Path(cache_path or STATE.parent/'cache'/'public-assets.sqlite3')
    with _locks[int(sha[:2],16)%len(_locks)]:
        cache_path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(cache_path,timeout=30)) as cache:
            cache.execute('CREATE TABLE IF NOT EXISTS assets(sha256 TEXT PRIMARY KEY,mime TEXT NOT NULL,data BLOB NOT NULL)')
            row=cache.execute('SELECT mime,data FROM assets WHERE sha256=?',(sha,)).fetchone()
            if row:
                if len(row[1])!=value['bytes'] or hashlib.sha256(row[1]).hexdigest()!=sha:raise ValueError('Cached public asset checksum mismatch')
                return row[0],row[1]
            if os.environ.get('TB_OFFLINE')=='1':raise OSError('Resource has not been downloaded for offline reading')
            if shutil.disk_usage(cache_path.parent).free<value['bytes']*3+256*1024*1024:raise OSError('Insufficient space for public resource cache')
            from leaderboard import service_opener
            request=Request(value['url'],headers={'Accept':value['mime'],'Accept-Encoding':'identity','User-Agent':'ToBe-Public-Assets/1'})
            try:
                with service_opener(value['url']).open(request,timeout=20) as response:
                    if response.status!=200:raise OSError('Public asset download failed')
                    raw=response.read(value['bytes']+1)
            except OSError:
                if not value['url'].startswith(PUBLIC_ROOT):raise
                from leaderboard import bundled_endpoint
                fallback=bundled_endpoint().rstrip('/')+'/updates/library-assets/'+sha+'.bin'
                validate_reference(sha,value['mime'],value['bytes'],fallback)
                request=Request(fallback,headers={'Accept':value['mime'],'Accept-Encoding':'identity','User-Agent':'ToBe-Public-Assets/1'})
                with service_opener(fallback).open(request,timeout=45) as response:
                    if response.status!=200:raise OSError('Public asset download failed')
                    raw=response.read(value['bytes']+1)
            if len(raw)!=value['bytes'] or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Downloaded public asset checksum mismatch')
            cache.execute('INSERT INTO assets VALUES(?,?,?)',(sha,value['mime'],raw));cache.commit()
            return value['mime'],raw

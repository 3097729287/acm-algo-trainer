"""Deterministic local v4 bundle, with no remote code or session material."""
import json
from pathlib import Path
import shutil
import sys
from urllib.parse import urlsplit

from official_bridge import page_source
from platform_login import LOGIN_SCRIPT


def build(destination,base_url='http://127.0.0.1:18765'):
    if getattr(sys,'frozen',False):raise ValueError('Use the already assembled browser-extension directory')
    endpoint=urlsplit(base_url)
    if endpoint.scheme!='http' or endpoint.hostname!='127.0.0.1' or endpoint.username or endpoint.password or endpoint.path or endpoint.query or endpoint.fragment or not endpoint.port:
        raise ValueError('Use the exact loopback origin')
    root=Path(__file__).resolve().parent
    source=root/'browser_extension'
    destination=Path(destination).resolve()
    if destination==source or destination.is_relative_to(source):raise ValueError('Use a separate output directory')
    destination.mkdir(parents=True,exist_ok=True)
    files=('manifest.json','worker.js','main.js','content.js','reading.js','connection.html','connection.js','README.txt')
    generated={'official.js':page_source(),'identity.js':'function tbConnectedIdentity(){return '+LOGIN_SCRIPT+';}\n',
               'connection_config.js':'const TB_CONNECTION_BASE='+json.dumps(base_url)+';\n',
               'virtual.js':(root/'virtual_contest.js' if (root/'virtual_contest.js').is_file() else root/'resources/virtual_contest.js').read_text('utf-8')}
    for name in (*files,*generated):
        path=destination/name
        if path.is_symlink() or path.is_dir():raise ValueError('Bundle output must contain regular files')
    for name in files:shutil.copy2(source/name,destination/name)
    for name,value in generated.items():(destination/name).write_text(value,encoding='utf-8')
    return destination

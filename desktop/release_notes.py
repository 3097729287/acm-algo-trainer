"""Keep a versioned Markdown update history on the current user's Desktop."""
import ctypes
import hashlib
import os
from pathlib import Path
import re
import uuid


def desktop_directory():
    if os.name!='nt':return Path.home()/'Desktop'
    # The known folder also handles redirected/OneDrive/localized Desktops.
    guid=(ctypes.c_ubyte*16).from_buffer_copy(uuid.UUID('b4bfcc3a-db2c-424c-b029-7fe99a87c641').bytes_le)
    output=ctypes.c_void_p()
    shell=ctypes.WinDLL('shell32');ole=ctypes.WinDLL('ole32')
    shell.SHGetKnownFolderPath.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)]
    shell.SHGetKnownFolderPath.restype=ctypes.c_long
    ole.CoTaskMemFree.argtypes=[ctypes.c_void_p]
    if shell.SHGetKnownFolderPath(ctypes.byref(guid),0,None,ctypes.byref(output))!=0:
        raise OSError('Desktop known folder unavailable')
    try:return Path(ctypes.wstring_at(output))
    finally:ole.CoTaskMemFree(output)


def archive_current(app_dir,*,desktop=None):
    app_dir=Path(app_dir)
    version=(app_dir/'VERSION').read_text(encoding='utf8').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Invalid release version')
    source=app_dir/'resources'/'update-notes'/(version+'.md')
    if source.stat().st_size>256*1024:raise ValueError('Release notes exceed size limit')
    data=source.read_bytes();data.decode('utf8')
    directory=Path(desktop) if desktop is not None else desktop_directory()/'ToBe更新记录'
    directory.mkdir(parents=True,exist_ok=True)
    target=directory/('ToBe-'+version+'.md')
    if target.exists() and target.read_bytes()!=data:
        # A corrected same-version note must never replace an older history.
        target=directory/('ToBe-'+version+'-'+hashlib.sha256(data).hexdigest()[:8]+'.md')
    try:
        with target.open('xb') as output:output.write(data)
    except FileExistsError:
        if target.read_bytes()!=data:raise ValueError('Release-note history collision')
    return target

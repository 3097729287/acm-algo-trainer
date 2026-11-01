"""System Recycle Bin only; unknown capacity or any failure retains the source.

No permanent-delete API, bin-emptying API or registry write is used. The shell
receives FOFX_RECYCLEONDELETE and FOFX_EARLYFAILURE, documented at:
https://learn.microsoft.com/windows/win32/api/shobjidl_core/nf-shobjidl_core-ifileoperation-setoperationflags
"""
import logging
import os
from pathlib import Path
import shutil
import stat
import struct
import threading
import time

LOG=logging.getLogger('tb.recycle')
LOCK=threading.Lock()
IS_WINDOWS=os.name=='nt'
SHELL_FLAGS=0x00080000|0x00100000|0x2000|0x400|0x40|0x10|0x4


def _plain(path):
    value=path.lstat()
    return not path.is_symlink() and not (getattr(value,'st_file_attributes',0)&0x400)


def _size(path):
    if path==Path(path.anchor) or any(not _plain(parent) for parent in (path,*path.parents)):
        raise ValueError('Root or linked path')
    if path.is_file():return path.stat().st_size
    if not path.is_dir():raise ValueError('Not a regular filesystem item')
    total=0
    for directory,children,names in os.walk(path,followlinks=False):
        for name in children+names:
            child=Path(directory)/name
            if not _plain(child):raise ValueError('Linked child retained')
            mode=child.stat().st_mode
            if stat.S_ISREG(mode):total+=child.stat().st_size
            elif not stat.S_ISDIR(mode):raise ValueError('Special item retained')
    return total


def _capacity(path):
    """Read the actual per-volume configured quota; never infer or resize it."""
    import ctypes,winreg
    from ctypes import wintypes as w
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    shell=ctypes.WinDLL('shell32',use_last_error=True)
    drive=path.drive+'\\'
    kernel.GetDriveTypeW.argtypes=[w.LPCWSTR];kernel.GetDriveTypeW.restype=w.UINT
    if kernel.GetDriveTypeW(drive)!=3:raise ValueError('Only fixed local volumes are eligible')
    kernel.GetVolumeNameForVolumeMountPointW.argtypes=[w.LPCWSTR,w.LPWSTR,w.DWORD]
    volume=ctypes.create_unicode_buffer(128)
    if not kernel.GetVolumeNameForVolumeMountPointW(drive,volume,len(volume)):raise OSError('Volume identity unavailable')
    guid=volume.value.split('{',1)[1].split('}',1)[0]
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Explorer\BitBucket\Volume\{'+guid+'}') as key:
        quota=winreg.QueryValueEx(key,'MaxCapacity')[0]
        try:disabled=winreg.QueryValueEx(key,'NukeOnDelete')[0]
        except FileNotFoundError:disabled=0
    if disabled or not isinstance(quota,int) or quota<=0:raise ValueError('Recycling disabled or quota unknown')
    maximum=quota*1024**2
    if maximum>shutil.disk_usage(path).total:raise ValueError('Invalid recycle quota')
    class Info(ctypes.Structure):
        _fields_=[('size',w.DWORD),('bytes',ctypes.c_longlong),('items',ctypes.c_longlong)]
    info=Info();info.size=ctypes.sizeof(info)
    shell.SHQueryRecycleBinW.argtypes=[w.LPCWSTR,ctypes.POINTER(Info)];shell.SHQueryRecycleBinW.restype=ctypes.c_long
    if shell.SHQueryRecycleBinW(drive,ctypes.byref(info))!=0:raise OSError('Recycle Bin unavailable')
    if info.bytes<0 or info.items<0:raise ValueError('Invalid bin observation')
    return maximum,info.bytes


def _shell_recycle(path):
    """IFileOperation runs in this thread's STA, with no fallback delete call."""
    import ctypes,uuid
    from ctypes import wintypes as w
    class GUID(ctypes.Structure):_fields_=[('value',ctypes.c_ubyte*16)]
    def guid(value):return GUID.from_buffer_copy(uuid.UUID(value).bytes_le)
    ole=ctypes.OleDLL('ole32');shell=ctypes.WinDLL('shell32')
    ole.CoInitializeEx.argtypes=[ctypes.c_void_p,w.DWORD]
    ole.CoInitializeEx.restype=ctypes.c_long
    initialized=ole.CoInitializeEx(None,2)
    if initialized<0:raise OSError('STA initialization unavailable')
    operation=ctypes.c_void_p();item=ctypes.c_void_p()
    def method(pointer,index,result,*arguments):
        address=ctypes.cast(pointer,ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents[index]
        return ctypes.WINFUNCTYPE(result,ctypes.c_void_p,*arguments)(address)
    def check(result):
        if result<0:raise OSError(result,'Recycle operation failed')
    try:
        clsid=guid('3ad05575-8857-4850-9277-11b85bdb8e09');iid=guid('947aab5f-0a5c-4c13-b4d6-4bf7836fc9f8')
        ole.CoCreateInstance.argtypes=[ctypes.POINTER(GUID),ctypes.c_void_p,w.DWORD,ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)]
        ole.CoCreateInstance.restype=ctypes.c_long
        check(ole.CoCreateInstance(ctypes.byref(clsid),None,1,ctypes.byref(iid),ctypes.byref(operation)))
        shell.SHCreateItemFromParsingName.argtypes=[w.LPCWSTR,ctypes.c_void_p,ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)]
        shell.SHCreateItemFromParsingName.restype=ctypes.c_long
        shell_item=guid('43826d1e-e718-42ee-bc55-a1e261c37bfe')
        check(shell.SHCreateItemFromParsingName(str(path),None,ctypes.byref(shell_item),ctypes.byref(item)))
        check(method(operation,5,ctypes.c_long,w.DWORD)(operation,SHELL_FLAGS))
        check(method(operation,18,ctypes.c_long,ctypes.c_void_p,ctypes.c_void_p)(operation,item,None))
        check(method(operation,21,ctypes.c_long)(operation))
        aborted=w.BOOL()
        check(method(operation,22,ctypes.c_long,ctypes.POINTER(w.BOOL))(operation,ctypes.byref(aborted)))
        return not aborted.value and not path.exists()
    finally:
        for pointer in (item,operation):
            if pointer:method(pointer,2,w.ULONG)(pointer)
        ole.CoUninitialize.argtypes=[];ole.CoUninitialize.restype=None
        ole.CoUninitialize()


def _receipts(path):
    """Read target-specific system metadata and require its retained payload."""
    result=set()
    for folder in Path(path.drive+'/$Recycle.Bin').iterdir():
        if not folder.is_dir():continue
        try:
            entries=list(folder.glob('$I*'))
        except PermissionError:
            continue
        for entry in entries:
            try:
                data=entry.read_bytes()
            except PermissionError:
                continue
            if len(data)<26:continue
            version=struct.unpack_from('<Q',data)[0]
            if version not in (1,2):continue
            original=Path(data[28 if version==2 else 24:].decode('utf-16-le').rstrip('\0'))
            if original==path and (folder/('$R'+entry.name[2:])).exists():
                result.add(str(entry))
    return result


def can_recycle(path):
    if not IS_WINDOWS:return False
    try:
        needed=_size(Path(path).absolute());maximum,occupied=_capacity(Path(path).absolute())
        return occupied+needed+16*1024**2<maximum*0.8
    except (OSError,ValueError,IndexError,TypeError):return False


def recycle(path):
    if not IS_WINDOWS:return False
    path=Path(path).absolute()
    with LOCK:
        try:
            if not can_recycle(path):
                LOG.info('Retained obsolete item: safe Recycle Bin capacity unavailable')
                return False
            before=_receipts(path)
            if not _shell_recycle(path):return False
            deadline=time.monotonic()+3
            while True:
                if _receipts(path)-before:return True
                if time.monotonic()>=deadline:
                    LOG.warning('Recycle result unverified: no new system metadata and payload receipt')
                    return False
                # Retry observation only. Never retry the filesystem mutation.
                time.sleep(.05)
        except (OSError,ValueError,IndexError,TypeError):
            LOG.info('Retained obsolete item: safe system recycling unavailable')
            return False

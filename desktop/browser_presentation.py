"""Show or hide only the managed browser window tagged by its own target."""
import ctypes
from ctypes import wintypes as w
import os
import time


def present_window(pid, marker, visible, *, activate=False, timeout=.5):
    if os.name!='nt':return False
    user=ctypes.WinDLL('user32',use_last_error=True)
    callback=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    user.EnumWindows.argtypes=[callback,w.LPARAM]
    user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    user.GetWindowThreadProcessId.restype=w.DWORD
    user.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    user.GetForegroundWindow.restype=w.HWND
    user.ShowWindowAsync.argtypes=[w.HWND,ctypes.c_int]
    user.SetForegroundWindow.argtypes=[w.HWND]
    user.SetWindowPos.argtypes=[w.HWND,w.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,w.UINT]
    user.BringWindowToTop.argtypes=[w.HWND]
    user.IsIconic.argtypes=[w.HWND]
    user.AttachThreadInput.argtypes=[w.DWORD,w.DWORD,w.BOOL]
    handle=None;deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        matches=[]
        @callback
        def visit(window,_):
            owner=w.DWORD();user.GetWindowThreadProcessId(window,ctypes.byref(owner))
            if owner.value!=pid:return True
            title=ctypes.create_unicode_buffer(32768);user.GetWindowTextW(window,title,len(title))
            if title.value.startswith(marker):matches.append(window)
            return True
        user.EnumWindows(visit,0)
        if len(matches)==1:handle=matches[0];break
        time.sleep(.025)
    if handle is None:return False
    if not visible:
        user.ShowWindowAsync(handle,0)
        return True
    if not activate:
        user.ShowWindowAsync(handle,4)  # SW_SHOWNOACTIVATE; no foreground APIs.
        return True
    user.ShowWindowAsync(handle,9 if user.IsIconic(handle) else 5)
    foreground=user.GetForegroundWindow();unused=w.DWORD()
    foreground_thread=user.GetWindowThreadProcessId(foreground,ctypes.byref(unused)) if foreground else 0
    target_thread=user.GetWindowThreadProcessId(handle,ctypes.byref(unused))
    kernel=ctypes.WinDLL('kernel32');kernel.GetCurrentThreadId.restype=w.DWORD
    current=kernel.GetCurrentThreadId();attached=[]
    try:
        for thread in {foreground_thread,target_thread}-{0,current}:
            if user.AttachThreadInput(current,thread,True):attached.append(thread)
        user.SetWindowPos(handle,w.HWND(-1),0,0,0,0,0x0001|0x0002)
        user.BringWindowToTop(handle);user.SetForegroundWindow(handle)
    finally:
        user.SetWindowPos(handle,w.HWND(-2),0,0,0,0,0x0001|0x0002|0x0010)
        for thread in attached:user.AttachThreadInput(current,thread,False)
    return True

"""Recover only the exact dedicated Chromium profile, never a normal browser."""
import ctypes
import json
import os
from pathlib import Path
import subprocess


def command_args(value):
    count=ctypes.c_int()
    split=ctypes.windll.shell32.CommandLineToArgvW
    split.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)]
    split.restype=ctypes.POINTER(ctypes.c_wchar_p)
    result=split(value,ctypes.byref(count))
    if not result:return []
    try:return [result[i] for i in range(count.value)]
    finally:ctypes.windll.kernel32.LocalFree(ctypes.cast(result,ctypes.c_void_p))


def candidates(profile, executable):
    if os.name!='nt':return []
    script="[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false); @(Get-CimInstance Win32_Process -Filter \"Name='msedge.exe' OR Name='chrome.exe'\" | Where-Object {$_.CommandLine -notmatch '--type='} | Select-Object ProcessId,ExecutablePath,CommandLine) | ConvertTo-Json -Compress"
    try:
        result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],capture_output=True,timeout=4,
                              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),check=True)
        rows=json.loads(result.stdout.decode('utf-8-sig'))
    except (OSError,ValueError,subprocess.SubprocessError):return []
    if isinstance(rows,dict):rows=[rows]
    found=[]
    for item in rows or []:
        try:
            if Path(item['ExecutablePath']).resolve()!=Path(executable).resolve():continue
            args=command_args(item['CommandLine'])
            values=dict(arg[2:].split('=',1) for arg in args if arg.startswith('--') and '=' in arg)
            if Path(values.get('user-data-dir','')).resolve()!=Path(profile).resolve():continue
            port=int(values.get('remote-debugging-port',0))
            if 0<port<65536:found.append((int(item['ProcessId']),port))
        except (KeyError,TypeError,ValueError,OSError):continue
    return found

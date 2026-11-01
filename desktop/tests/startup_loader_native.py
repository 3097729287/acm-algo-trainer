"""Measure the real Win32 loader before a deliberately delayed fixture child.

This checks first paint, dimensions and handoff, not frozen-app content speed.
All programs and screenshots are retained in the worktree's isolated backups.
"""
import argparse
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=r'''
#define UNICODE
#include <windows.h>
static LRESULT CALLBACK proc(HWND h,UINT m,WPARAM a,LPARAM b){
 if(m==WM_TIMER){DestroyWindow(h);return 0;}
 if(m==WM_DESTROY){PostQuitMessage(0);return 0;}
 return DefWindowProcW(h,m,a,b);
}
int WINAPI wWinMain(HINSTANCE i,HINSTANCE p,LPWSTR a,int n){
 (void)p;(void)a;(void)n;Sleep(2500);
 WNDCLASSW c={0};c.lpfnWndProc=proc;c.hInstance=i;c.lpszClassName=L"WindowsForms10.Window.Fixture";
 RegisterClassW(&c);HWND h=CreateWindowW(c.lpszClassName,L"Isolated handoff",WS_OVERLAPPEDWINDOW,0,0,1050,700,0,0,i,0);
 ShowWindow(h,SW_SHOWNOACTIVATE);SetTimer(h,1,500,0);MSG m;
 while(GetMessageW(&m,0,0,0)>0){TranslateMessage(&m);DispatchMessageW(&m);}return 0;
}
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work-dir',type=Path,required=True)
    parser.add_argument('--compiler',type=Path,help='The same bundled g++.exe used by the release assembler')
    args=parser.parse_args();folder=args.work_dir.resolve()
    assert folder.is_relative_to((ROOT/'.backups').resolve())
    folder.mkdir(parents=True,exist_ok=False)
    cpp=str(args.compiler.resolve()) if args.compiler else shutil.which('g++')
    assert cpp
    child=folder/'fixture.c';child.write_text(FIXTURE,'utf8')
    for source,target in [(ROOT/'desktop/startup_loader.c',folder/'ToBeLoader.exe'),(child,folder/'ToBe.exe')]:
        command=[cpp,'-x','c++','-static','-fno-exceptions','-fno-rtti','-finput-charset=UTF-8','-Wl,--no-insert-timestamp']
        result=subprocess.run(command+['-Os','-s','-municode','-mwindows','-Wall','-Wextra',str(source),'-o',str(target),'-luser32','-lgdi32'],env={**os.environ,'PATH':str(Path(cpp).parent)+os.pathsep+os.environ.get('PATH','')},capture_output=True,text=True,encoding='utf8',errors='replace',timeout=60)
        (folder/(target.stem+'.compile.log')).write_text(result.stdout+result.stderr,'utf8');assert result.returncode==0,result.stderr
    user=ctypes.WinDLL('user32',use_last_error=True)
    callback=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    user.EnumWindows.argtypes=[callback,w.LPARAM];user.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    user.IsWindowVisible.argtypes=[w.HWND];user.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
    user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    started=time.perf_counter();process=subprocess.Popen([str(folder/'ToBeLoader.exe')],cwd=folder,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    visible=None;first=None;screenshot=False
    try:
        while time.perf_counter()-started<2:
            found=[]
            @callback
            def inspect(handle,_):
                pid=w.DWORD();user.GetWindowThreadProcessId(handle,ctypes.byref(pid))
                if pid.value!=process.pid or not user.IsWindowVisible(handle):return True
                name=ctypes.create_unicode_buffer(100);user.GetClassNameW(handle,name,100)
                if name.value=='ToBe.NativeLoading':
                    rect=w.RECT();user.GetWindowRect(handle,ctypes.byref(rect));found.append((rect.left,rect.top,rect.right,rect.bottom))
                return True
            user.EnumWindows(inspect,0)
            if found:
                first=round((time.perf_counter()-started)*1000,2);visible=found[0];break
            time.sleep(.005)
        assert visible,'Loader framework did not appear'
        assert visible[2]-visible[0]>=1050 and visible[3]-visible[1]>=700,visible
        from PIL import ImageGrab
        time.sleep(.06);ImageGrab.grab(bbox=visible).save(folder/'first-window.png');screenshot=True
        assert process.wait(10)==0
        report={'passed':True,'frameworkVisibleMs':first,'window':visible,'screenshot':screenshot,
                'child':'delayed isolated Win32 fixture','frozenAppContentMeasured':False,'liveInstallationChanged':False}
        (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report,indent=2));return 0
    finally:
        if process.poll() is None:process.terminate();process.wait(5)


if __name__=='__main__':raise SystemExit(main())
